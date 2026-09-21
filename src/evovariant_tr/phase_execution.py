"""Approval-gated, resumable execution primitives for Phases 6 and 7.

The repository already contains the Modal service and the scientific contracts,
but a full-cohort runner must also make the following properties explicit:

* manifest identities are validated before any request is sent;
* labels are never included in a remote request payload;
* source-manifest IDs and UCSC/API ``chr`` IDs are reconciled explicitly;
* completed shards are content-verified and skipped on restart;
* partial, duplicate, or out-of-cohort responses fail closed; and
* raw outputs carry enough provenance to be registered later without
  manufacturing metrics.

This module deliberately does not call Modal at import time.  A caller must
construct a transport, pass a current protocol hash, and separately satisfy
the paid-compute approval gate before invoking :func:`execute_cohort`.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from evovariant_tr.cost_policy import (
    CostPolicyError,
    FullRunApproval,
    assert_paid_compute_allowed,
    require_full_run_approval,
)
from evovariant_tr.feature_store import feature_record_from_embedding_payload
from evovariant_tr.variant_schema import CanonicalVariant, normalize_chromosome

EndpointKind = Literal["score", "embedding"]


class PhaseExecutionError(RuntimeError):
    """Raised when a cohort execution cannot be proven scientifically safe."""


@dataclass(frozen=True)
class CohortRecord:
    """One manifest row with both source and transport identity."""

    source_normalized_variant_id: str
    canonical_variant: CanonicalVariant
    split: str
    label: int | None
    gene_symbol: str | None
    source_record_hash: str | None

    @property
    def canonical_normalized_variant_id(self) -> str:
        return self.canonical_variant.normalized_variant_id

    def request_payload(self) -> dict[str, object]:
        """Return the label-free payload allowed across the remote boundary."""
        return {
            "assembly": self.canonical_variant.assembly,
            "chromosome": self.canonical_variant.chromosome,
            "position_1based": self.canonical_variant.position_1based,
            "reference": self.canonical_variant.reference,
            "alternate": self.canonical_variant.alternate,
        }


@dataclass(frozen=True)
class ExecutionPlan:
    """Deterministic plan metadata written before remote execution."""

    phase: int
    family: str
    endpoint_kind: EndpointKind
    model_id: str
    checkpoint: str
    model_revision: str
    protocol_hash: str
    cohort_manifest_sha256: str
    split_manifest_sha256: str | None
    record_count: int
    shard_size: int
    batch_size: int
    include_labels_in_output: bool
    embedding_layer: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "family": self.family,
            "endpoint_kind": self.endpoint_kind,
            "model_id": self.model_id,
            "checkpoint": self.checkpoint,
            "model_revision": self.model_revision,
            "protocol_hash": self.protocol_hash,
            "cohort_manifest_sha256": self.cohort_manifest_sha256,
            "split_manifest_sha256": self.split_manifest_sha256,
            "record_count": self.record_count,
            "shard_size": self.shard_size,
            "batch_size": self.batch_size,
            "include_labels_in_output": self.include_labels_in_output,
            "embedding_layer": self.embedding_layer,
        }


class JsonEndpointClient:
    """Small standard-library JSON client for an explicitly supplied endpoint."""

    def __init__(self, endpoint: str, *, timeout_seconds: float = 120.0) -> None:
        if not endpoint.startswith(("http://", "https://")):
            raise ValueError("endpoint must be an explicit http:// or https:// URL")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def __call__(self, payload: dict[str, object]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.endpoint,
            data=_stable_bytes(payload),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise PhaseExecutionError(f"JSON endpoint request failed: {exc}") from exc
        if not isinstance(decoded, dict):
            raise PhaseExecutionError("JSON endpoint response must be an object")
        return cast(dict[str, Any], decoded)


def require_current_paid_approval(
    approval_path: str | Path,
    *,
    scope_tokens: Iterable[str],
) -> FullRunApproval:
    """Require acknowledgement, a fresh protocol hash, and an exact scope.

    This is intentionally separate from :func:`execute_cohort`: the latter is
    also used by no-spend tests with injected transports, while production
    callers must opt into this gate before constructing a remote transport.
    """
    try:
        assert_paid_compute_allowed()
        approval = require_full_run_approval(approval_path)
    except CostPolicyError as exc:
        raise PhaseExecutionError(str(exc)) from exc
    scope = approval.run_scope.casefold()
    missing = [token for token in scope_tokens if token.casefold() not in scope]
    if missing:
        raise PhaseExecutionError(
            "approval scope does not cover required workload token(s): "
            + ", ".join(missing)
        )
    return approval


def _stable_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Hash a manifest or output using a streaming read."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = value.encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _source_variant_id(variant: CanonicalVariant) -> str:
    """Return the split-manifest spelling without a ``chr`` prefix."""
    chromosome = variant.chromosome.removeprefix("chr")
    return (
        f"{variant.assembly}:{chromosome}:{variant.position_1based}:"
        f"{variant.reference}>{variant.alternate}"
    )


def _parse_variant_id(value: str) -> CanonicalVariant:
    try:
        assembly, chromosome, position_text, allele_text = value.split(":", 3)
        reference, alternate = allele_text.split(">", 1)
        position = int(position_text)
    except (AttributeError, TypeError, ValueError) as exc:
        raise PhaseExecutionError(f"malformed normalized variant ID: {value!r}") from exc
    return CanonicalVariant(
        assembly=assembly,
        chromosome=normalize_chromosome(chromosome),
        position_1based=position,
        reference=reference.upper(),
        alternate=alternate.upper(),
    )


def _record_from_manifest(raw: object, *, requested_splits: set[str] | None) -> CohortRecord | None:
    if not isinstance(raw, dict):
        raise PhaseExecutionError("manifest records must be JSON objects")
    split = str(raw.get("split", ""))
    if requested_splits is not None and split not in requested_splits:
        return None
    try:
        assembly = str(raw["assembly"])
        chromosome = normalize_chromosome(str(raw["chromosome"]))
        position = int(raw["position_1based"])
        reference = str(raw["reference"]).upper()
        alternate = str(raw["alternate"]).upper()
        source_id = str(raw["normalized_variant_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PhaseExecutionError("manifest record is missing a canonical variant field") from exc

    variant = CanonicalVariant(
        assembly=assembly,
        chromosome=chromosome,
        position_1based=position,
        reference=reference,
        alternate=alternate,
    )
    accepted_ids = {_source_variant_id(variant), variant.normalized_variant_id}
    if source_id not in accepted_ids:
        raise PhaseExecutionError(
            f"manifest normalized ID does not match its variant fields: {source_id!r}"
        )
    if split not in {"TRAIN", "VALIDATION", "LOCKED_TEST"}:
        raise PhaseExecutionError(f"unsupported manifest split: {split!r}")

    raw_label = raw.get("label")
    label: int | None
    if raw_label is None:
        label = None
    else:
        try:
            label = int(raw_label)
        except (TypeError, ValueError) as exc:
            raise PhaseExecutionError("manifest label must be binary") from exc
        if label not in {0, 1}:
            raise PhaseExecutionError("manifest label must be binary")

    return CohortRecord(
        source_normalized_variant_id=source_id,
        canonical_variant=variant,
        split=split,
        label=label,
        gene_symbol=(str(raw["gene_symbol"]) if raw.get("gene_symbol") else None),
        source_record_hash=(
            str(raw["source_record_hash"]) if raw.get("source_record_hash") else None
        ),
    )


def load_cohort_records(
    manifest_path: str | Path,
    *,
    splits: Iterable[str] | None = None,
) -> tuple[list[CohortRecord], str]:
    """Load and validate manifest rows, returning rows and the file hash."""
    target = Path(manifest_path)
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PhaseExecutionError(f"could not read cohort manifest {target}: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("records"), list):
        raise PhaseExecutionError("cohort manifest must contain a records list")
    requested = set(splits) if splits is not None else None
    records = [
        record
        for raw in document["records"]
        if (record := _record_from_manifest(raw, requested_splits=requested)) is not None
    ]
    records.sort(key=lambda row: row.source_normalized_variant_id)
    source_ids = [row.source_normalized_variant_id for row in records]
    canonical_ids = [row.canonical_normalized_variant_id for row in records]
    if len(source_ids) != len(set(source_ids)):
        raise PhaseExecutionError("cohort manifest contains duplicate source normalized IDs")
    if len(canonical_ids) != len(set(canonical_ids)):
        raise PhaseExecutionError("cohort manifest contains duplicate canonical IDs")
    if not records:
        raise PhaseExecutionError("selected cohort is empty")
    return records, sha256_file(target)


def build_execution_plan(
    records: list[CohortRecord],
    *,
    phase: int,
    family: str,
    endpoint_kind: EndpointKind,
    model_id: str,
    checkpoint: str,
    model_revision: str,
    protocol_hash: str,
    cohort_manifest_sha256: str,
    split_manifest_sha256: str | None,
    shard_size: int = 8,
    batch_size: int = 8,
    include_labels_in_output: bool = False,
    embedding_layer: str | None = None,
) -> ExecutionPlan:
    """Freeze all execution dimensions before a remote request is possible."""
    if phase not in {6, 7}:
        raise ValueError("this runner only supports Phase 6 and Phase 7")
    if not family.strip() or not model_id.strip() or not checkpoint.strip():
        raise ValueError("family, model_id, and checkpoint must be non-empty")
    if len(protocol_hash) != 64 or any(c not in "0123456789abcdef" for c in protocol_hash):
        raise ValueError("protocol_hash must be a lowercase SHA-256 value")
    if shard_size < 1 or batch_size < 1:
        raise ValueError("shard_size and batch_size must be positive")
    if not records:
        raise ValueError("execution plan requires at least one record")
    if endpoint_kind == "embedding" and not embedding_layer:
        raise ValueError("embedding_layer is required for embedding execution")
    if endpoint_kind == "score" and embedding_layer is not None:
        raise ValueError("embedding_layer is only valid for embedding execution")
    return ExecutionPlan(
        phase=phase,
        family=family,
        endpoint_kind=endpoint_kind,
        model_id=model_id,
        checkpoint=checkpoint,
        model_revision=model_revision,
        protocol_hash=protocol_hash,
        cohort_manifest_sha256=cohort_manifest_sha256,
        split_manifest_sha256=split_manifest_sha256,
        record_count=len(records),
        shard_size=shard_size,
        batch_size=batch_size,
        include_labels_in_output=include_labels_in_output,
        embedding_layer=embedding_layer,
    )


def _shard_id(records: list[CohortRecord], index: int) -> str:
    value = {
        "index": index,
        "source_ids": [row.source_normalized_variant_id for row in records],
        "canonical_ids": [row.canonical_normalized_variant_id for row in records],
    }
    return _sha256_bytes(_stable_bytes(value))[:32]


def _response_canonical_id(result: dict[str, Any]) -> str:
    raw_id = result.get("normalized_variant_id")
    if isinstance(raw_id, str):
        return _parse_variant_id(raw_id).normalized_variant_id
    try:
        variant = CanonicalVariant(
            assembly=str(result["assembly"]),
            chromosome=normalize_chromosome(str(result["chromosome"])),
            position_1based=int(result["position_1based"]),
            reference=str(result["reference"]).upper(),
            alternate=str(result["alternate"]).upper(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PhaseExecutionError("endpoint result has no valid variant identity") from exc
    return variant.normalized_variant_id


def _read_verified_shard(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise PhaseExecutionError(f"invalid shard artifact {path}: expected an object")
        payload = dict(document)
        recorded = payload.pop("payload_sha256")
        if recorded != _sha256_bytes(_stable_bytes(payload)):
            raise PhaseExecutionError(f"tampered shard payload: {path}")
        return cast(dict[str, Any], document)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, PhaseExecutionError):
            raise
        raise PhaseExecutionError(f"invalid shard artifact {path}: {exc}") from exc


def _write_verified_shard(path: Path, payload: dict[str, Any]) -> None:
    document = dict(payload)
    document["payload_sha256"] = _sha256_bytes(_stable_bytes(payload))
    _atomic_write_json(path, document)


def _score_row(
    result: dict[str, Any],
    record: CohortRecord,
    *,
    include_label: bool,
    model_id: str,
) -> dict[str, Any]:
    if result.get("status") != "completed":
        raise PhaseExecutionError("score endpoint returned a non-completed row")
    canonical_id = _response_canonical_id(result)
    if canonical_id != record.canonical_normalized_variant_id:
        raise PhaseExecutionError(
            "endpoint returned a variant outside the requested row identity"
        )
    raw_score = result.get("delta_primary", result.get("score_delta"))
    if not isinstance(raw_score, (int, float)) or not math.isfinite(float(raw_score)):
        raise PhaseExecutionError("score endpoint did not return a finite raw score")
    row: dict[str, Any] = {
        "normalized_variant_id": record.source_normalized_variant_id,
        "canonical_variant_id": canonical_id,
        "split": record.split,
        "model_name": model_id,
        "raw_score": float(raw_score),
        "coverage_status": "COMPLETED",
        "failure_reason": None,
        "provenance": result.get("provenance", {}),
        "raw_result": result,
    }
    if include_label:
        row["label"] = record.label
    return row


def _embedding_row(
    result: dict[str, Any],
    record: CohortRecord,
    *,
    include_label: bool,
    model_id: str,
    expected_layer: str,
) -> dict[str, Any]:
    if _response_canonical_id(result) != record.canonical_normalized_variant_id:
        raise PhaseExecutionError(
            "embedding endpoint returned a variant outside the requested row identity"
        )
    provenance = result.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("layer") != expected_layer:
        raise PhaseExecutionError(
            "embedding endpoint returned an unexpected embedding layer"
        )
    feature = feature_record_from_embedding_payload(
        result,
        split=record.split,
        model_id=model_id,
    ).to_dict()
    feature["model_normalized_variant_id"] = feature["normalized_variant_id"]
    feature["normalized_variant_id"] = record.source_normalized_variant_id
    feature["coverage_status"] = "COMPLETED"
    feature["provenance"] = result.get("provenance", {})
    if include_label:
        feature["label"] = record.label
    return feature


def execute_cohort(
    records: list[CohortRecord],
    *,
    plan: ExecutionPlan,
    output_dir: str | Path,
    endpoint: Callable[[dict[str, object]], dict[str, Any]],
    include_labels_in_output: bool | None = None,
    embedding_layer: str | None = None,
) -> dict[str, Any]:
    """Execute a frozen cohort plan with shard-level resume and verification.

    The endpoint callback is the only injected transport boundary.  Production
    callers must wrap it in an explicit paid-compute and current-approval gate;
    tests can provide a deterministic local callback without contacting Modal.
    """
    if len(records) != plan.record_count:
        raise PhaseExecutionError("records do not match the frozen execution plan")
    expected_ids = [row.source_normalized_variant_id for row in records]
    if expected_ids != sorted(expected_ids):
        raise PhaseExecutionError("records must be sorted by source normalized ID")
    include_labels = (
        plan.include_labels_in_output
        if include_labels_in_output is None
        else include_labels_in_output
    )
    if include_labels != plan.include_labels_in_output:
        raise PhaseExecutionError("label output policy differs from the frozen plan")
    if embedding_layer != plan.embedding_layer:
        raise PhaseExecutionError("embedding layer differs from the frozen plan")

    root = Path(output_dir)
    shards_dir = root / "shards"
    root.mkdir(parents=True, exist_ok=True)
    plan_path = root / "execution_plan.json"
    if plan_path.exists():
        existing_plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if existing_plan != plan.to_dict():
            raise PhaseExecutionError("existing execution plan differs from the requested plan")
    else:
        _atomic_write_json(plan_path, plan.to_dict())

    all_rows: list[dict[str, Any]] = []
    completed_shards = 0
    shard_count = (len(records) + plan.shard_size - 1) // plan.shard_size
    for shard_index, start in enumerate(range(0, len(records), plan.shard_size)):
        shard_records = records[start : start + plan.shard_size]
        shard_id = _shard_id(shard_records, shard_index)
        shard_path = shards_dir / f"{shard_id}.json"
        stored = _read_verified_shard(shard_path)
        if stored is not None:
            if stored.get("status") != "completed":
                raise PhaseExecutionError(f"stored shard is not completed: {shard_path}")
            stored_source_ids = [
                row.source_normalized_variant_id for row in shard_records
            ]
            if stored.get("source_ids") != stored_source_ids:
                raise PhaseExecutionError(f"stored shard identity mismatch: {shard_path}")
            all_rows.extend(list(stored.get("rows", [])))
            completed_shards += 1
            continue

        variants = [record.request_payload() for record in shard_records]
        request: dict[str, object] = {"variants": variants}
        if plan.endpoint_kind == "embedding":
            request["layer"] = plan.embedding_layer
        response = endpoint(request)
        if not isinstance(response, dict):
            raise PhaseExecutionError("endpoint response must be a JSON object")
        if response.get("status") != "completed":
            raise PhaseExecutionError(
                f"endpoint returned {response.get('status')!r} for shard {shard_id}"
            )
        raw_results = response.get("results")
        if not isinstance(raw_results, list) or len(raw_results) != len(shard_records):
            returned_count = len(raw_results) if isinstance(raw_results, list) else "invalid"
            raise PhaseExecutionError(
                f"endpoint returned {returned_count} rows for shard size "
                f"{len(shard_records)}"
            )
        by_canonical = {
            record.canonical_normalized_variant_id: record for record in shard_records
        }
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw_result in raw_results:
            if not isinstance(raw_result, dict):
                raise PhaseExecutionError("endpoint returned a non-object result row")
            canonical_id = _response_canonical_id(raw_result)
            if canonical_id in seen or canonical_id not in by_canonical:
                raise PhaseExecutionError("endpoint returned duplicate or unknown variant IDs")
            seen.add(canonical_id)
            record = by_canonical[canonical_id]
            if plan.endpoint_kind == "score":
                rows.append(
                    _score_row(
                        raw_result,
                        record,
                        include_label=include_labels,
                        model_id=plan.model_id,
                    )
                )
            else:
                if plan.embedding_layer is None:
                    raise PhaseExecutionError(
                        "embedding execution plan is missing its frozen layer"
                    )
                rows.append(
                    _embedding_row(
                        raw_result,
                        record,
                        include_label=include_labels,
                        model_id=plan.model_id,
                        expected_layer=plan.embedding_layer,
                    )
                )
        if seen != set(by_canonical):
            raise PhaseExecutionError("endpoint omitted one or more requested variants")
        shard_payload = {
            "shard_id": shard_id,
            "shard_index": shard_index,
            "status": "completed",
            "source_ids": [row.source_normalized_variant_id for row in shard_records],
            "rows": sorted(rows, key=lambda row: str(row["normalized_variant_id"])),
        }
        _write_verified_shard(shard_path, shard_payload)
        all_rows.extend(cast(list[dict[str, Any]], shard_payload["rows"]))
        completed_shards += 1

    all_rows.sort(key=lambda row: str(row["normalized_variant_id"]))
    if len(all_rows) != len(records):
        raise PhaseExecutionError("completed row count does not match the cohort")
    output_name = "predictions.jsonl" if plan.endpoint_kind == "score" else "features.jsonl"
    output_path = root / output_name
    output_text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in all_rows)
    _atomic_write_text(output_path, output_text)
    summary = {
        "status": "COMPLETED",
        "phase": plan.phase,
        "family": plan.family,
        "endpoint_kind": plan.endpoint_kind,
        "record_count": len(records),
        "shard_count": shard_count,
        "completed_shards": completed_shards,
        "label_output": include_labels,
        "output_path": str(output_path),
        "output_sha256": sha256_file(output_path),
        "plan_sha256": _sha256_bytes(_stable_bytes(plan.to_dict())),
        "metrics": {},
    }
    _atomic_write_json(root / "run_summary.json", summary)
    return summary
