"""Validated CSV/VCF batch planning, resumability, and result export.

This module owns the local batch contract. It deliberately accepts an injected
scorer instead of constructing a model or contacting Modal. That keeps the
default path free and makes the same validation/resume boundary usable by a
future remote worker and by CPU-only contract tests.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, TextIO

from evovariant_tr.batch import classify_error
from evovariant_tr.variant_schema import CanonicalVariant, normalize_chromosome

REQUIRED_VARIANT_COLUMNS = (
    "assembly",
    "chromosome",
    "position_1based",
    "reference",
    "alternate",
)
_FORBIDDEN_LABEL_FIELDS = frozenset(
    {
        "label",
        "outcome",
        "t1_significance",
        "t1_stars",
        "resolution",
    }
)


@dataclass(frozen=True)
class BatchVariant:
    """A validated, label-free variant submitted to a batch scorer."""

    assembly: str
    chromosome: str
    position_1based: int
    reference: str
    alternate: str
    normalized_variant_id: str
    source_row: int = 0

    def canonical(self) -> CanonicalVariant:
        """Return the shared canonical variant representation."""
        return CanonicalVariant(
            assembly=self.assembly,
            chromosome=self.chromosome,
            position_1based=self.position_1based,
            reference=self.reference,
            alternate=self.alternate,
        )


class BatchScorer(Protocol):
    """Minimal injected scorer contract used by :func:`execute_batch`."""

    def __call__(
        self, variants: Sequence[BatchVariant]
    ) -> Sequence[Mapping[str, Any]]: ...


def _required_value(row: Mapping[str, Any], name: str, row_number: int) -> str:
    value = row.get(name)
    if value is None or not str(value).strip():
        raise ValueError(f"batch row {row_number} has an empty {name}")
    return str(value).strip()


def _make_variant(
    *,
    assembly_raw: str,
    chromosome_raw: str,
    position_raw: str,
    reference_raw: str,
    alternate_raw: str,
    row_number: int,
) -> BatchVariant:
    assembly = assembly_raw.strip()
    if assembly != "GRCh38":
        raise ValueError(f"batch row {row_number} violates GRCh38 assembly contract")
    try:
        position = int(position_raw.strip())
    except ValueError as exc:
        raise ValueError(f"batch row {row_number} has an invalid position") from exc

    try:
        chromosome = normalize_chromosome(chromosome_raw)
    except ValueError as exc:
        raise ValueError(f"batch row {row_number} has an invalid chromosome") from exc
    if chromosome == "chr":
        raise ValueError(f"batch row {row_number} has an invalid chromosome")
    reference = reference_raw.strip().upper()
    alternate = alternate_raw.strip().upper()
    if len(reference) != 1 or len(alternate) != 1:
        raise ValueError(f"batch row {row_number} is not a biallelic SNV")
    if reference not in "ACGT" or alternate not in "ACGT":
        raise ValueError(f"batch row {row_number} contains a non-ACGT allele")
    if reference == alternate:
        raise ValueError(f"batch row {row_number} has identical reference and alternate alleles")

    canonical = CanonicalVariant(
        assembly=assembly,
        chromosome=chromosome,
        position_1based=position,
        reference=reference,
        alternate=alternate,
    )
    return BatchVariant(
        assembly=canonical.assembly,
        chromosome=canonical.chromosome,
        position_1based=canonical.position_1based,
        reference=canonical.reference,
        alternate=canonical.alternate,
        normalized_variant_id=canonical.normalized_variant_id,
        source_row=row_number,
    )


def _validate_unique(variants: list[BatchVariant]) -> list[BatchVariant]:
    identities = [variant.normalized_variant_id for variant in variants]
    if len(identities) != len(set(identities)):
        raise ValueError("batch contains duplicate normalized variant IDs")
    return variants


def parse_variant_csv(path: str | Path) -> list[BatchVariant]:
    """Parse a canonical CSV and reject malformed rows before queueing work."""
    target = Path(path)
    with target.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        missing = [column for column in REQUIRED_VARIANT_COLUMNS if column not in fields]
        if missing:
            raise ValueError(f"batch CSV is missing required columns: {missing}")
        variants: list[BatchVariant] = []
        for line_number, row in enumerate(reader, start=2):
            if not any(value and str(value).strip() for value in row.values()):
                raise ValueError(f"batch row {line_number} is empty")
            variants.append(
                _make_variant(
                    assembly_raw=_required_value(row, "assembly", line_number),
                    chromosome_raw=_required_value(row, "chromosome", line_number),
                    position_raw=_required_value(row, "position_1based", line_number),
                    reference_raw=_required_value(row, "reference", line_number),
                    alternate_raw=_required_value(row, "alternate", line_number),
                    row_number=line_number,
                )
            )
    return _validate_unique(variants)


def _open_text(path: Path) -> TextIO:
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def parse_variant_vcf(path: str | Path) -> list[BatchVariant]:
    """Parse a biallelic SNV VCF without using annotations or outcome labels."""
    target = Path(path)
    variants: list[BatchVariant] = []
    header: list[str] | None = None
    with _open_text(target) as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                header = line.rstrip("\r\n").split("\t")
                continue
            if not line.strip():
                continue
            if header is None:
                raise ValueError("VCF is missing the #CHROM header")
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) < 5:
                raise ValueError(f"VCF row {line_number} has fewer than five columns")
            alternate = fields[4]
            if "," in alternate:
                raise ValueError(f"VCF row {line_number} is multiallelic")
            variants.append(
                _make_variant(
                    assembly_raw="GRCh38",
                    chromosome_raw=fields[0],
                    position_raw=fields[1],
                    reference_raw=fields[3],
                    alternate_raw=alternate,
                    row_number=line_number,
                )
            )
    if header is None:
        raise ValueError("VCF is missing the #CHROM header")
    if not variants:
        raise ValueError("VCF contains no variant rows")
    return _validate_unique(variants)


def parse_variant_input(path: str | Path, *, input_format: str | None = None) -> list[BatchVariant]:
    """Parse CSV or VCF input using an explicit format or a safe suffix default."""
    target = Path(path)
    normalized_format = input_format.lower() if input_format else ""
    if not normalized_format:
        name = target.name.lower()
        normalized_format = "vcf" if name.endswith((".vcf", ".vcf.gz")) else "csv"
    if normalized_format == "csv":
        return parse_variant_csv(target)
    if normalized_format == "vcf":
        return parse_variant_vcf(target)
    raise ValueError("input_format must be csv or vcf")


def sha256_file(path: str | Path) -> str:
    """Hash an input file in bounded memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def batch_progress(*, total: int, completed: int, failed: int) -> dict[str, Any]:
    """Report resumable progress without treating failed rows as completed."""
    if total < 0 or completed < 0 or failed < 0 or completed + failed > total:
        raise ValueError("invalid batch progress counts")
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "remaining": total - completed - failed,
        "coverage": completed / total if total else 0.0,
        "resumable": failed > 0 or completed < total,
    }


def estimate_batch_cost_usd(
    *,
    total_variants: int,
    seconds_per_variant: float,
    gpu_usd_per_hour: float,
    fixed_seconds: float = 0.0,
) -> float:
    """Estimate cost from caller-supplied measurements; never embeds a price."""
    if total_variants < 0:
        raise ValueError("total_variants must be non-negative")
    for name, value in (
        ("seconds_per_variant", seconds_per_variant),
        ("gpu_usd_per_hour", gpu_usd_per_hour),
        ("fixed_seconds", fixed_seconds),
    ):
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be finite and non-negative")
    if gpu_usd_per_hour <= 0.0:
        raise ValueError("gpu_usd_per_hour must be positive")
    return ((fixed_seconds + total_variants * seconds_per_variant) / 3600.0) * gpu_usd_per_hour


@dataclass(frozen=True)
class BatchPlan:
    """Immutable, label-free plan persisted before any scorer is called."""

    job_id: str
    input_sha256: str
    input_format: str
    variant_ids: tuple[str, ...]
    shard_size: int
    batch_size: int
    model_id: str
    checkpoint: str
    model_revision: str
    context_length_bp: int
    orientation: str
    estimated_seconds: float | None
    estimated_cost_usd: float | None

    @property
    def total_variants(self) -> int:
        return len(self.variant_ids)

    @property
    def total_shards(self) -> int:
        if not self.variant_ids:
            return 0
        return (len(self.variant_ids) + self.shard_size - 1) // self.shard_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "job_id": self.job_id,
            "input_sha256": self.input_sha256,
            "input_format": self.input_format,
            "variant_ids": list(self.variant_ids),
            "total_variants": self.total_variants,
            "shard_size": self.shard_size,
            "batch_size": self.batch_size,
            "total_shards": self.total_shards,
            "model_id": self.model_id,
            "checkpoint": self.checkpoint,
            "model_revision": self.model_revision,
            "context_length_bp": self.context_length_bp,
            "orientation": self.orientation,
            "estimated_seconds": self.estimated_seconds,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


def build_batch_plan(
    variants: Sequence[BatchVariant],
    *,
    input_sha256: str,
    input_format: str,
    shard_size: int,
    batch_size: int,
    model_id: str,
    checkpoint: str,
    model_revision: str,
    context_length_bp: int,
    orientation: str,
    seconds_per_variant: float | None = None,
    gpu_usd_per_hour: float | None = None,
    fixed_seconds: float = 0.0,
) -> BatchPlan:
    """Create a deterministic plan and optional caller-measured cost estimate."""
    if shard_size <= 0 or batch_size <= 0:
        raise ValueError("shard_size and batch_size must be positive")
    if context_length_bp <= 0:
        raise ValueError("context_length_bp must be positive")
    if not model_id.strip() or not checkpoint.strip() or not model_revision.strip():
        raise ValueError("model identity fields must be non-empty")
    ids = tuple(variant.normalized_variant_id for variant in variants)
    if len(ids) != len(set(ids)):
        raise ValueError("batch plan contains duplicate normalized variant IDs")
    if input_format not in {"csv", "vcf"}:
        raise ValueError("input_format must be csv or vcf")
    if len(input_sha256) != 64 or any(char not in "0123456789abcdef" for char in input_sha256):
        raise ValueError("input_sha256 must be a lowercase SHA-256 digest")
    estimated_seconds: float | None = None
    estimated_cost: float | None = None
    if seconds_per_variant is not None or gpu_usd_per_hour is not None:
        if seconds_per_variant is None or gpu_usd_per_hour is None:
            raise ValueError("both seconds_per_variant and gpu_usd_per_hour are required")
        estimated_seconds = fixed_seconds + len(ids) * seconds_per_variant
        estimated_cost = estimate_batch_cost_usd(
            total_variants=len(ids),
            seconds_per_variant=seconds_per_variant,
            gpu_usd_per_hour=gpu_usd_per_hour,
            fixed_seconds=fixed_seconds,
        )
    raw_job_id = json.dumps(
        {
            "input_sha256": input_sha256,
            "variant_ids": ids,
            "shard_size": shard_size,
            "batch_size": batch_size,
            "model_id": model_id,
            "checkpoint": checkpoint,
            "model_revision": model_revision,
            "context_length_bp": context_length_bp,
            "orientation": orientation,
        },
        sort_keys=True,
    ).encode("utf-8")
    job_id = hashlib.sha256(raw_job_id).hexdigest()[:24]
    return BatchPlan(
        job_id=job_id,
        input_sha256=input_sha256,
        input_format=input_format,
        variant_ids=ids,
        shard_size=shard_size,
        batch_size=batch_size,
        model_id=model_id,
        checkpoint=checkpoint,
        model_revision=model_revision,
        context_length_bp=context_length_bp,
        orientation=orientation,
        estimated_seconds=estimated_seconds,
        estimated_cost_usd=estimated_cost,
    )


def _stable_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(_stable_bytes(payload))
    temporary.replace(path)


def write_batch_plan(plan: BatchPlan, path: str | Path) -> Path:
    """Atomically persist a plan before scoring begins."""
    target = Path(path)
    _atomic_write_json(target, plan.to_dict())
    return target


def _shard_ids(plan: BatchPlan) -> list[tuple[int, tuple[str, ...]]]:
    return [
        (index, plan.variant_ids[start : start + plan.shard_size])
        for index, start in enumerate(range(0, plan.total_variants, plan.shard_size))
    ]


def _shard_path(output_dir: Path, index: int, shard_ids: Sequence[str]) -> Path:
    digest = hashlib.sha256("\n".join(shard_ids).encode()).hexdigest()[:16]
    return output_dir / "shards" / f"{index:06d}_{digest}.json"


def _payload_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_stable_bytes(payload)).hexdigest()


def _read_valid_shard(
    path: Path,
    *,
    expected_ids: Sequence[str],
) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(envelope, dict):
        return None
    payload = envelope.get("payload")
    if not isinstance(payload, dict) or envelope.get("payload_sha256") != _payload_hash(payload):
        return None
    if payload.get("status") != "completed":
        return None
    if payload.get("variant_ids") != list(expected_ids):
        return None
    rows = payload.get("rows")
    if not isinstance(rows, list):
        return None
    row_ids = [row.get("normalized_variant_id") for row in rows if isinstance(row, dict)]
    if row_ids != list(expected_ids):
        return None
    if len(row_ids) != len(set(row_ids)):
        return None
    if any(
        not isinstance(row, dict)
        or not isinstance(row.get("normalized_variant_id"), str)
        or _FORBIDDEN_LABEL_FIELDS.intersection(row)
        for row in rows
    ):
        return None
    return payload


def _write_shard(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_write_json(
        path,
        {"payload": dict(payload), "payload_sha256": _payload_hash(payload)},
    )


def execute_batch(
    variants: Sequence[BatchVariant],
    *,
    plan: BatchPlan,
    output_dir: str | Path,
    scorer: BatchScorer,
    retry_failed: bool = False,
) -> dict[str, Any]:
    """Execute/resume a batch through an injected scorer and return its status.

    Completed shards are reused only when their exact ordered IDs, payload hash,
    and label-free rows validate. Any scorer exception becomes a persisted
    failure record; callers can retry explicitly without losing prior evidence.
    """
    actual_ids = tuple(variant.normalized_variant_id for variant in variants)
    if actual_ids != plan.variant_ids:
        raise ValueError("execution variants do not match the immutable batch plan")
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    write_batch_plan(plan, target / "batch_plan.json")
    variant_by_id = {variant.normalized_variant_id: variant for variant in variants}
    completed_shards = 0
    failed_shards = 0
    completed_rows = 0
    failed_rows = 0
    reused_shards = 0

    for index, shard_ids in _shard_ids(plan):
        shard_path = _shard_path(target, index, shard_ids)
        existing = _read_valid_shard(shard_path, expected_ids=shard_ids)
        if existing is not None:
            completed_shards += 1
            completed_rows += len(shard_ids)
            reused_shards += 1
            continue
        if shard_path.is_file() and not retry_failed:
            try:
                existing_raw = json.loads(shard_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                existing_raw = {}
            if isinstance(existing_raw, dict) and isinstance(existing_raw.get("payload"), dict):
                if existing_raw["payload"].get("status") == "failed":
                    failed_shards += 1
                    failed_rows += len(shard_ids)
                    continue
        shard_variants = [variant_by_id[identity] for identity in shard_ids]
        try:
            rows = list(scorer(shard_variants))
            if len(rows) != len(shard_ids):
                raise ValueError("scorer returned a row count different from the shard")
            normalized_rows: list[dict[str, Any]] = []
            for expected_id, row in zip(shard_ids, rows, strict=True):
                if not isinstance(row, Mapping):
                    raise ValueError("scorer returned a non-object row")
                if row.get("normalized_variant_id") != expected_id:
                    raise ValueError("scorer returned rows in a different order")
                if _FORBIDDEN_LABEL_FIELDS.intersection(row):
                    raise ValueError("scorer output contains prohibited outcome labels")
                normalized_rows.append(dict(row))
            payload = {
                "status": "completed",
                "shard_index": index,
                "variant_ids": list(shard_ids),
                "rows": normalized_rows,
            }
            _write_shard(shard_path, payload)
            completed_shards += 1
            completed_rows += len(shard_ids)
        except Exception as exc:  # noqa: BLE001 - failure is persisted for explicit retry
            payload = {
                "status": "failed",
                "shard_index": index,
                "variant_ids": list(shard_ids),
                "rows": [],
                "failure_kind": classify_error(str(exc)).value,
                "error": str(exc),
            }
            _write_shard(shard_path, payload)
            failed_shards += 1
            failed_rows += len(shard_ids)

    if failed_shards:
        status = "PARTIAL" if completed_shards else "FAILED"
    else:
        status = "COMPLETED"
    summary = {
        "schema_version": "1.0",
        "job_id": plan.job_id,
        "status": status,
        "total_variants": plan.total_variants,
        "completed_variants": completed_rows,
        "failed_variants": failed_rows,
        "total_shards": plan.total_shards,
        "completed_shards": completed_shards,
        "failed_shards": failed_shards,
        "reused_shards": reused_shards,
        "progress": batch_progress(
            total=plan.total_variants,
            completed=completed_rows,
            failed=failed_rows,
        ),
        "estimated_seconds": plan.estimated_seconds,
        "estimated_cost_usd": plan.estimated_cost_usd,
    }
    _atomic_write_json(target / "batch_summary.json", summary)
    return summary


def export_batch_results(output_dir: str | Path, output_path: str | Path) -> dict[str, Any]:
    """Export completed rows in plan order, retaining partial status explicitly."""
    root = Path(output_dir)
    plan_raw = json.loads((root / "batch_plan.json").read_text(encoding="utf-8"))
    summary = json.loads((root / "batch_summary.json").read_text(encoding="utf-8"))
    ordered_ids = list(plan_raw["variant_ids"])
    shard_size = plan_raw["shard_size"]
    if (
        not isinstance(ordered_ids, list)
        or any(not isinstance(identity, str) for identity in ordered_ids)
        or len(ordered_ids) != len(set(ordered_ids))
        or not isinstance(shard_size, int)
        or shard_size <= 0
    ):
        raise ValueError("batch plan has invalid ordered variant IDs or shard size")
    rows_by_id: dict[str, dict[str, Any]] = {}
    expected_paths: set[Path] = set()
    for index, start in enumerate(range(0, len(ordered_ids), shard_size)):
        shard_ids = tuple(ordered_ids[start : start + shard_size])
        path = _shard_path(root, index, shard_ids)
        expected_paths.add(path)
        if not path.is_file():
            continue
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid batch shard envelope: {path.name}") from exc
        if not isinstance(envelope, dict):
            raise ValueError(f"invalid batch shard envelope: {path.name}")
        payload = envelope.get("payload")
        if (
            not isinstance(payload, dict)
            or envelope.get("payload_sha256") != _payload_hash(payload)
        ):
            raise ValueError(f"tampered batch shard payload: {path.name}")
        status = payload.get("status")
        if status == "failed":
            if payload.get("variant_ids") != list(shard_ids) or payload.get("rows") != []:
                raise ValueError(f"invalid failed batch shard: {path.name}")
            continue
        if status != "completed":
            raise ValueError(f"invalid batch shard status: {path.name}")
        validated = _read_valid_shard(path, expected_ids=shard_ids)
        if validated is None:
            raise ValueError(f"invalid completed batch shard: {path.name}")
        for row in validated["rows"]:
            identity = row["normalized_variant_id"]
            if identity in rows_by_id:
                raise ValueError(f"duplicate completed batch result: {identity}")
            rows_by_id[identity] = row
    shard_dir = root / "shards"
    if shard_dir.exists():
        unexpected = sorted(
            path.name
            for path in shard_dir.glob("*.json")
            if path not in expected_paths
        )
        if unexpected:
            raise ValueError(f"unexpected batch shard files: {unexpected}")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        for identity in ordered_ids:
            row = rows_by_id.get(identity)
            if row is not None:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    temporary.replace(target)
    exported = {
        "job_id": plan_raw["job_id"],
        "status": summary["status"],
        "output_path": str(target),
        "exported_rows": len(rows_by_id),
        "missing_rows": len(ordered_ids) - len(rows_by_id),
        "output_sha256": sha256_file(target),
    }
    _atomic_write_json(root / "export_summary.json", exported)
    return exported
