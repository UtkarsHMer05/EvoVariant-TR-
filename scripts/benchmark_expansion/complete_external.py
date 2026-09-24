#!/usr/bin/env python3
"""Complete the frozen external benchmark continuation without touching B01-B60."""

# ruff: noqa: E501

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np

import modal

_MODULE_PATH = Path(__file__).resolve()
ROOT = _MODULE_PATH.parents[2] if len(_MODULE_PATH.parents) > 2 else Path("/root")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from evovariant_tr.metrics import compute_auc_pr, compute_auc_roc  # noqa: E402
from evovariant_tr.prediction_calibration import apply_isotonic  # noqa: E402
from evovariant_tr.sequence_mutate import reverse_complement  # noqa: E402
from evovariant_tr.sequence_window import (  # noqa: E402
    CONTEXT_LENGTH_BP,
    generate_reference_window_with_par_alias,
)
from evovariant_tr.supervised import LogisticModel  # noqa: E402

MODEL_ID = "evo2_7b"
MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"
GPU_TYPE = "H100"
GPU_RATE_USD_PER_HOUR = 3.95
MODEL_SEQUENCE_BATCH_SIZE = 8
hf_cache = modal.Volume.from_name("hf_cache", create_if_missing=False)


def build_evo2_image() -> Any:
    base = modal.Image.from_registry("nvcr.io/nvidia/pytorch:24.07-py3", add_python="3.12")
    return (
        base.apt_install(["build-essential", "cmake", "ninja-build", "git", "gcc", "g++", "clang", "libclang-dev"])
        .run_commands(
            "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124",
            "git clone --recurse-submodules https://github.com/ArcInstitute/evo2.git evo2 "
            f"&& cd evo2 && git checkout {MODEL_REVISION} "
            "&& git submodule update --init --recursive && pip install .",
        )
        .run_commands(
            "pip uninstall -y transformer-engine transformer_engine",
            "pip install wheel",
            "pip install 'transformer_engine[pytorch]==1.13' --no-build-isolation",
            "pip install --force-reinstall --no-deps "
            "https://github.com/Dao-AILab/flash-attention/releases/download/v2.6.3/"
            "flash_attn-2.6.3%2Bcu123torch2.4cxx11abiFALSE-cp312-cp312-linux_x86_64.whl",
        )
        .add_local_dir("scripts", "/opt/scripts", copy=True)
        .add_local_dir("src", "/opt/evovariant_tr", copy=True)
        .env({"PYTHONPATH": "/opt/evovariant_tr"})
        .run_commands("python3 /opt/scripts/patch_vortex.py")
    )


EVO2_IMAGE = build_evo2_image() if modal.is_local() else None

local: Any = None


def load_local_helpers() -> Any:
    global local
    if local is None:
        import importlib

        local = importlib.import_module("benchmark_expansion.run_local")
    return local

MANIFEST = ROOT / "artifacts/benchmarks/external_clinvar_manifest.json"
FORMAL_MANIFEST = ROOT / "research/ml_extension/splits/formal_budgeted_20260921/formal_development_manifest.json"
LOCKED_MANIFEST = ROOT / "research/ml_extension/splits/authoritative_locked_test_manifest.json"
REFERENCE = ROOT / "data/reference/Homo_sapiens_assembly38.fasta"
REFERENCE_FAI = ROOT / "data/reference/Homo_sapiens_assembly38.fasta.fai"
REFERENCE_AUDIT = ROOT / "artifacts/reference/grch38_validation_20260921.json"
FROZEN_CONFIG = ROOT / "research/runs/formal_cpu_20260922/phase13/frozen_config_materialized.json"
MODEL_ARTIFACT = ROOT / "research/runs/formal_cpu_20260922/phase13/fitted_model_evo2_logistic_regression_hpo.json"
CALIBRATION_ARTIFACT = ROOT / "research/runs/formal_cpu_20260922/phase12/calibration_abstention.json"
LOCKED_ROWS = ROOT / "research/benchmarks/expansion_v1/locked_rows.json"
RUN_ROOT = ROOT / "research/runs/external_clinvar_completion_v1"
ARTIFACTS = ROOT / "artifacts/benchmarks"
DOCS = ROOT / "docs/benchmarks"
WEB = ROOT / "apps/web/public/benchmarks"
RAW_PREDICTIONS = RUN_ROOT / "external_raw_predictions.jsonl"
RAW_RECEIPT = ARTIFACTS / "external_clinvar_raw_prediction_receipt.json"
EVALUATION = ARTIFACTS / "external_clinvar_evaluation.json"
METRICS = ARTIFACTS / "external_clinvar_metrics.json"
PROVENANCE = ARTIFACTS / "external_clinvar_provenance.json"
RUNTIME = ARTIFACTS / "external_clinvar_runtime.json"
DRY_RUN = ARTIFACTS / "external_clinvar_dry_run.json"
MANIFEST_RECEIPT = ARTIFACTS / "external_clinvar_manifest_receipt.json"
COMPARATORS = ARTIFACTS / "external_classical_comparators.json"
COMPARATOR_REAUDIT = ARTIFACTS / "comparator_coverage_reaudit.json"
COMPARATOR_AUDIT = ARTIFACTS / "comparator_audit.json"
MAVEDB_MANIFEST = ARTIFACTS / "mavedb_assay_manifest.json"
EXTERNAL_LABELS = ARTIFACTS / "external_clinvar_predictions_summary.csv"

HARD_RESERVE_USD = 5.0
SAFETY_STOP_USD = 5.5
SOFT_MAXIMUM_USD = 24.0
MAX_BATCH_VARIANTS = 8
MAX_RETRIES = 2
ID_RE = re.compile(r"^GRCh38:([^:]+):(\d+):([ACGT])>([ACGT])$")


def stable_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write(path: Path, value: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        mode = "wb" if isinstance(value, bytes) else "w"
        kwargs: dict[str, Any] = {} if mode == "wb" else {"encoding": "utf-8"}
        with os.fdopen(fd, mode, **kwargs) as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value: object) -> None:
    atomic_write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    atomic_write(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def append_once(path: Path, marker: str, text: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker not in existing:
        atomic_write(path, existing.rstrip() + "\n\n" + text.rstrip() + "\n")


def billing_snapshot() -> dict[str, Any]:
    binary = Path(sys.executable).with_name("modal")
    result = subprocess.run(
        [str(binary), "billing", "summary", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    try:
        summary: Any = json.loads(result.stdout)
    except json.JSONDecodeError:
        summary = {"stdout": result.stdout}
    return {
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "command": "modal billing summary --json",
        "returncode": result.returncode,
        "summary": summary,
        "stderr": result.stderr,
    }


def modal_profile() -> str:
    binary = Path(sys.executable).with_name("modal")
    result = subprocess.run([str(binary), "profile", "current"], cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def parse_identity(identity: str) -> dict[str, Any]:
    match = ID_RE.fullmatch(identity)
    if not match:
        raise ValueError(f"invalid frozen external identity: {identity}")
    chrom, position, reference, alternate = match.groups()
    return {
        "normalized_variant_id": identity,
        "assembly": "GRCh38",
        "chromosome": chrom,
        "position_1based": int(position),
        "reference": reference,
        "alternate": alternate,
    }


def reference_candidates(chromosome: str) -> tuple[str, ...]:
    if chromosome in {"MT", "M"}:
        return (chromosome, f"chr{chromosome}", "chrM")
    if chromosome == "chrM":
        return (chromosome,)
    return (chromosome, f"chr{chromosome}") if not chromosome.startswith("chr") else (chromosome,)


def prepare_sequence_row(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    window = None
    reference_provenance: dict[str, Any] | None = None
    last_error: Exception | None = None
    for candidate in reference_candidates(str(row["chromosome"])):
        try:
            window, reference_provenance = generate_reference_window_with_par_alias(
                REFERENCE,
                REFERENCE_FAI,
                candidate,
                int(row["position_1based"]),
                str(row["reference"]),
                allow_par_alias=True,
            )
            break
        except ValueError as exc:
            last_error = exc
    if window is None or reference_provenance is None:
        raise RuntimeError(f"reference preparation failed for {row['normalized_variant_id']}: {last_error}")
    reference = window.ref_sequence
    alternate = reference[: window.variant_offset] + str(row["alternate"]) + reference[window.variant_offset + 1 :]
    sequences = [reference, alternate, reverse_complement(reference), reverse_complement(alternate)]
    if len(reference) != CONTEXT_LENGTH_BP or any(len(sequence) != CONTEXT_LENGTH_BP for sequence in sequences):
        raise RuntimeError("external sequence construction did not preserve 8192 bp")
    sequence_hash = hashlib.sha256(json.dumps(sequences, separators=(",", ":")).encode()).hexdigest()
    reference_provenance = {
        **reference_provenance,
        "reference_asset": str(REFERENCE.relative_to(ROOT)),
        "window_start_1based": int(window.start),
        "window_stop_1based": int(window.stop),
        "variant_offset": int(window.variant_offset),
        "sequence_sha256": sequence_hash,
    }
    payload = {"normalized_variant_id": row["normalized_variant_id"], "sequences": sequences}
    return payload, reference_provenance


def validate_manifest() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    document = read_json(MANIFEST)
    records = document.get("records")
    if not isinstance(records, list) or len(records) != 200:
        raise RuntimeError("frozen external manifest does not contain exactly 200 rows")
    recorded_inner_hash = document.get("manifest_sha256")
    without_hash = dict(document)
    without_hash.pop("manifest_sha256", None)
    if recorded_inner_hash != json_hash(without_hash):
        raise RuntimeError("frozen external manifest internal hash mismatch")
    if document.get("selected_n") != 200 or document.get("selected_class_counts") != {"0": 100, "1": 100}:
        raise RuntimeError("frozen external manifest is not 100/100 balanced")
    if document.get("strict_gene_disjoint") is not True or document.get("reference_status") != "READY":
        raise RuntimeError("frozen external manifest readiness claims are not present")
    formal = read_json(FORMAL_MANIFEST).get("records", [])
    locked = read_json(LOCKED_MANIFEST).get("records", [])
    formal_locked_ids = {str(row["normalized_variant_id"]) for row in formal + locked}
    formal_locked_genes = {str(row.get("gene_symbol")) for row in formal + locked if row.get("gene_symbol")}
    ids = {str(row["normalized_variant_id"]) for row in records}
    genes = {str(row["gene_symbol"]) for row in records if row.get("gene_symbol")}
    if len(ids) != 200 or ids & formal_locked_ids or genes & formal_locked_genes:
        raise RuntimeError("external ID or claimed gene disjointness failed")
    expected_reference = read_json(REFERENCE_AUDIT)["fasta"]["sha256"]
    if sha256_file(REFERENCE) != expected_reference or not REFERENCE_FAI.is_file():
        raise RuntimeError("GRCh38 reference asset hash/index gate failed")
    normalized: list[dict[str, Any]] = []
    reference_rows: list[dict[str, Any]] = []
    for raw in records:
        identity_row = parse_identity(str(raw["normalized_variant_id"]))
        if int(raw["label"]) not in {0, 1} or int(raw["review_stars"]) < 2:
            raise RuntimeError(f"invalid frozen external label/review row: {identity_row['normalized_variant_id']}")
        identity_row.update({key: raw.get(key) for key in ("label", "gene_symbol", "review_stars", "review_status", "last_evaluated", "selection_key", "allele_id", "variation_id", "source_row")})
        _, provenance = prepare_sequence_row(identity_row)
        reference_rows.append({"normalized_variant_id": identity_row["normalized_variant_id"], **provenance})
        normalized.append(identity_row)
    normalized.sort(key=lambda row: str(row["selection_key"]))
    audit = {
        "artifact_id": "evovariant-tr-external-clinvar-manifest-receipt-v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "manifest_path": str(MANIFEST.relative_to(ROOT)),
        "manifest_file_sha256": sha256_file(MANIFEST),
        "manifest_inner_sha256": recorded_inner_hash,
        "selected_n": len(normalized),
        "class_counts": dict(Counter(str(row["label"]) for row in normalized)),
        "development_id_overlap": len(ids & {str(row["normalized_variant_id"]) for row in formal}),
        "locked_id_overlap": len(ids & {str(row["normalized_variant_id"]) for row in locked}),
        "development_gene_overlap": len(genes & {str(row.get("gene_symbol")) for row in formal if row.get("gene_symbol")}),
        "locked_gene_overlap": len(genes & {str(row.get("gene_symbol")) for row in locked if row.get("gene_symbol")}),
        "reference_asset": str(REFERENCE.relative_to(ROOT)),
        "reference_asset_sha256": expected_reference,
        "reference_validated_n": len(reference_rows),
        "reference_rows_sha256": json_hash(reference_rows),
        "selection_frozen_before_inference": True,
        "labels_used_for_fitting": False,
        "labels_used_for_threshold_selection": False,
        "labels_used_for_calibration_fitting": False,
    }
    write_json(MANIFEST_RECEIPT, audit)
    return document, normalized, audit


def pilot_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_label: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_label[int(row["label"])].append(row)
    for rows in by_label.values():
        rows.sort(key=lambda item: str(item["selection_key"]))
    selected = by_label[0][:4] + by_label[1][:4]
    return sorted(selected, key=lambda row: str(row["selection_key"]))


def stable_plan(records: list[dict[str, Any]], start_balance: float, mode: str) -> dict[str, Any]:
    ids = [str(row["normalized_variant_id"]) for row in records]
    pilot = pilot_rows(records)
    return {
        "plan_id": "evovariant-tr-external-clinvar-completion-v1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "mode": mode,
        "profile": "utkarshkhajuria59",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "gpu_type": GPU_TYPE,
        "context_length_bp": CONTEXT_LENGTH_BP,
        "orientation": "forward_and_reverse",
        "score_semantics": "alternate_minus_reference_log_likelihood",
        "max_batch_variants": MAX_BATCH_VARIANTS,
        "model_sequence_batch_size": MODEL_SEQUENCE_BATCH_SIZE,
        "manifest_file_sha256": sha256_file(MANIFEST),
        "manifest_inner_sha256": read_json(MANIFEST).get("manifest_sha256"),
        "target_ids_sha256": json_hash(ids),
        "pilot_selection": "four smallest selection_key rows per frozen label, then selection_key order; no model outputs",
        "pilot_ids": [str(row["normalized_variant_id"]) for row in pilot],
        "full_selection": "all 200 frozen manifest rows in selection_key order, subject only to the predeclared budget rule",
        "starting_verified_credit_usd": start_balance,
        "hard_reserve_usd": HARD_RESERVE_USD,
        "safety_stop_usd": SAFETY_STOP_USD,
        "soft_maximum_usd": SOFT_MAXIMUM_USD,
        "program_budget_usd": min(SOFT_MAXIMUM_USD, max(0.0, start_balance - SAFETY_STOP_USD)),
        "labels_sent_to_remote": False,
        "raw_artifact_before_label_join": True,
        "calibration_refit": False,
        "threshold_retuned": False,
        "fine_tuning": False,
    }


def read_raw_cache() -> dict[str, dict[str, Any]]:
    if not RAW_PREDICTIONS.is_file():
        return {}
    cache: dict[str, dict[str, Any]] = {}
    for line in RAW_PREDICTIONS.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        identity = str(row.get("normalized_variant_id", ""))
        if not identity or "label" in row or "labels" in row:
            raise RuntimeError("raw external prediction cache contains labels")
        raw_scores = row.get("raw_scores")
        if not isinstance(raw_scores, list) or len(raw_scores) != 4 or not all(math.isfinite(float(value)) for value in raw_scores):
            raise RuntimeError(f"raw external prediction cache has invalid scores: {identity}")
        if identity in cache:
            raise RuntimeError(f"duplicate raw external prediction cache row: {identity}")
        cache[identity] = row
    return cache


def remote_raw_row(
    identity_row: dict[str, Any],
    remote_row: dict[str, Any],
    remote_provenance: dict[str, Any],
    reference_provenance: dict[str, Any],
) -> dict[str, Any]:
    if any(key in remote_row or key in remote_provenance for key in ("label", "labels")):
        raise RuntimeError("remote external response transported a label")
    raw_scores = remote_row.get("raw_scores")
    if not isinstance(raw_scores, list) or len(raw_scores) != 4:
        raise RuntimeError("remote external response did not contain four orientation scores")
    values = [float(value) for value in raw_scores]
    if not all(math.isfinite(value) for value in values):
        raise RuntimeError("remote external response contained a non-finite score")
    forward_ref, forward_alt, reverse_ref, reverse_alt = values
    delta_forward = forward_alt - forward_ref
    delta_reverse = reverse_alt - reverse_ref
    delta_primary = (delta_forward + delta_reverse) / 2.0
    return {
        "normalized_variant_id": identity_row["normalized_variant_id"],
        "raw_scores": values,
        "delta_forward": delta_forward,
        "delta_reverse": delta_reverse,
        "delta_primary": delta_primary,
        "orientation_disagreement": abs(delta_forward - delta_reverse),
        "coverage_status": "COMPLETED",
        "failure_reason": None,
        "provenance": {**remote_provenance, "reference": reference_provenance},
        "remote_labels_transported": False,
        "locked_test_accessed": False,
    }


def _call_id(call: Any) -> str:
    call.hydrate()
    value = getattr(call, "object_id", None)
    if not value:
        raise RuntimeError("Modal did not return a durable function-call ID")
    return str(value)


def run_remote(mode: str, records: list[dict[str, Any]], plan: dict[str, Any], start_balance: float) -> dict[str, Any]:
    targets = pilot_rows(records) if mode == "pilot" else records
    target_ids = {str(row["normalized_variant_id"]) for row in targets}
    cache = read_raw_cache()
    cache = {identity: row for identity, row in cache.items() if identity in target_ids}
    fresh = [row for row in targets if str(row["normalized_variant_id"]) not in cache]
    dry = {
        "target_n": len(targets),
        "cache_hit_n": len(cache),
        "fresh_n": len(fresh),
        "target_ids_sha256": json_hash([str(row["normalized_variant_id"]) for row in targets]),
    }
    if mode == "dry-run":
        write_json(DRY_RUN, {"artifact_id": "evovariant-tr-external-dry-run-v1", "recorded_at_utc": datetime.now(UTC).isoformat(), "plan": plan, **dry, "remote_started": False})
        return dry
    if mode == "full" and not (RUN_ROOT / "pilot_runtime.json").is_file() and not cache:
        raise RuntimeError("full external inference requires the completed deterministic pilot first")

    billing_before = billing_snapshot()

    pilot_runtime: dict[str, Any] = read_json(RUN_ROOT / "pilot_runtime.json") if (RUN_ROOT / "pilot_runtime.json").is_file() else {}
    projected_cost = None
    if mode == "full" and pilot_runtime:
        pilot_seconds = float(pilot_runtime.get("client_wall_seconds", 0.0))
        pilot_n = max(1, int(pilot_runtime.get("fresh_rows", 8)))
        projected_cost = (pilot_seconds / pilot_n * len(fresh)) / 3600.0 * GPU_RATE_USD_PER_HOUR
        projected_cost *= 1.25
        if projected_cost > min(SOFT_MAXIMUM_USD, max(0.0, start_balance - SAFETY_STOP_USD)):
            affordable = int(len(records) * min(1.0, max(0.0, start_balance - SAFETY_STOP_USD) / max(projected_cost, 1e-9)))
            affordable -= affordable % 2
            affordable = max(0, min(len(records), affordable))
            by_label: dict[int, list[dict[str, Any]]] = defaultdict(list)
            for row in records:
                by_label[int(row["label"])].append(row)
            half = affordable // 2
            selected = sorted(by_label[0][:half] + by_label[1][:half], key=lambda row: str(row["selection_key"]))
            targets = selected
            target_ids = {str(row["normalized_variant_id"]) for row in targets}
            cache = {identity: row for identity, row in cache.items() if identity in target_ids}
            fresh = [row for row in targets if str(row["normalized_variant_id"]) not in cache]
            dry.update({"budget_limited": True, "budget_limited_target_n": len(targets), "budget_limited_selection": "largest deterministic balanced prefix fitting projected cost"})
        else:
            dry["budget_limited"] = False
    worker = ExternalEvo2Worker()
    remote_runtime_seconds = 0.0
    client_wall_seconds = 0.0
    retries = 0
    fresh_remote_rows = 0
    remote_provenance: list[dict[str, Any]] = []
    for start in range(0, len(fresh), MAX_BATCH_VARIANTS):
        batch_rows = fresh[start : start + MAX_BATCH_VARIANTS]
        payload: list[dict[str, Any]] = []
        reference_map: dict[str, dict[str, Any]] = {}
        for row in batch_rows:
            payload_row, reference_provenance = prepare_sequence_row(row)
            payload.append(payload_row)
            reference_map[str(row["normalized_variant_id"])] = reference_provenance
        response: dict[str, Any] | None = None
        call_id = None
        batch_started = time.perf_counter()
        for attempt in range(MAX_RETRIES):
            try:
                call = worker.score_batch.spawn(payload)
                call_id = _call_id(call)
                response = call.get(timeout=1800)
                break
            except Exception:
                if attempt + 1 >= MAX_RETRIES:
                    raise
                retries += 1
        batch_seconds = time.perf_counter() - batch_started
        client_wall_seconds += batch_seconds
        if response is None or response.get("status") != "completed":
            raise RuntimeError("external Modal batch did not complete")
        provenance = response.get("provenance")
        remote_rows = response.get("results")
        if not isinstance(provenance, dict) or not isinstance(remote_rows, list):
            raise RuntimeError("external Modal response is missing results/provenance")
        if provenance.get("model_revision") != MODEL_REVISION or provenance.get("model_id") != MODEL_ID:
            raise RuntimeError("external Modal response model provenance mismatch")
        if provenance.get("context_length_bp") != CONTEXT_LENGTH_BP or provenance.get("orientation") != "forward_and_reverse":
            raise RuntimeError("external Modal response sequence contract mismatch")
        if any(key in provenance for key in ("label", "labels")):
            raise RuntimeError("external Modal provenance contains a label")
        ids = [str(row["normalized_variant_id"]) for row in batch_rows]
        response_ids = [str(row.get("normalized_variant_id")) for row in remote_rows if isinstance(row, dict)]
        if response_ids != ids:
            raise RuntimeError("external Modal response IDs/order do not match the frozen request")
        for identity_row, remote_row in zip(batch_rows, remote_rows, strict=True):
            cache[str(identity_row["normalized_variant_id"])] = remote_raw_row(identity_row, remote_row, provenance, reference_map[str(identity_row["normalized_variant_id"])])
        method_seconds = float(provenance.get("remote_method_seconds", 0.0))
        if not math.isfinite(method_seconds) or method_seconds < 0:
            raise RuntimeError("remote method runtime is not finite")
        remote_runtime_seconds += method_seconds
        remote_provenance.append({"call_id": call_id, "provenance": provenance})
        fresh_remote_rows += len(batch_rows)
        write_jsonl(RAW_PREDICTIONS, [cache[str(row["normalized_variant_id"])] for row in targets if str(row["normalized_variant_id"]) in cache])
        raw_hash = sha256_file(RAW_PREDICTIONS)
        write_json(RAW_RECEIPT, {
            "artifact_id": "evovariant-tr-external-raw-prediction-receipt-v1",
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "execution_plan_sha256": json_hash(plan),
            "raw_predictions_path": str(RAW_PREDICTIONS.relative_to(ROOT)),
            "raw_predictions_sha256": raw_hash,
            "raw_rows": len(cache),
            "labels_present": False,
            "remote_labels_transported": False,
            "prediction_artifact_persisted_before_evaluation_join": True,
        })
    ordered = [cache[str(row["normalized_variant_id"])] for row in targets if str(row["normalized_variant_id"]) in cache]
    if len(ordered) != len(targets):
        raise RuntimeError(f"external raw inference is incomplete: {len(ordered)}/{len(targets)}")
    cache_parity = read_raw_cache()
    if any(cache_parity.get(row["normalized_variant_id"]) != row for row in ordered):
        raise RuntimeError("external raw prediction cache write/read parity failed")
    ended_billing = billing_snapshot()
    runtime = {
        "artifact_id": "evovariant-tr-external-runtime-v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "mode": mode,
        "profile": modal_profile(),
        "gpu_type": GPU_TYPE,
        "gpu_rate_usd_per_hour": GPU_RATE_USD_PER_HOUR,
        "starting_verified_credit_usd": start_balance,
        "ending_verified_credit_usd": None,
        "cache_hit_rows": len(targets) - fresh_remote_rows,
        "fresh_rows": fresh_remote_rows,
        "target_rows": len(targets),
        "cache_hit_rate": (len(targets) - fresh_remote_rows) / len(targets) if targets else 0.0,
        "remote_invocations": len(remote_provenance),
        "retries": retries,
        "client_wall_seconds": client_wall_seconds,
        "remote_method_seconds": remote_runtime_seconds,
        "variants_per_second_remote": fresh_remote_rows / remote_runtime_seconds if remote_runtime_seconds else None,
        "rate_estimated_cost_usd": client_wall_seconds / 3600.0 * GPU_RATE_USD_PER_HOUR,
        "provider_billed_delta_usd": None,
        "cost_per_fresh_variant_usd": (client_wall_seconds / 3600.0 * GPU_RATE_USD_PER_HOUR) / fresh_remote_rows if fresh_remote_rows else 0.0,
        "call_ids": [item["call_id"] for item in remote_provenance],
        "remote_provenance": remote_provenance,
        "billing_before": billing_before,
        "billing_after": ended_billing,
        "raw_predictions_sha256": sha256_file(RAW_PREDICTIONS),
        "raw_labels_present": False,
        "budget": {
            "hard_reserve_usd": HARD_RESERVE_USD,
            "safety_stop_usd": SAFETY_STOP_USD,
            "soft_maximum_usd": SOFT_MAXIMUM_USD,
            "projected_cost_usd": projected_cost,
            "projected_ending_credit_usd": start_balance - (projected_cost or 0.0),
        },
    }
    write_json(RUN_ROOT / ("pilot_runtime.json" if mode == "pilot" else "full_runtime.json"), runtime)
    write_json(RUNTIME, runtime)
    return {**dry, **runtime}


def load_frozen_probability_model() -> tuple[LogisticModel, dict[str, Any], dict[str, Any]]:
    config = read_json(FROZEN_CONFIG)
    model_raw = read_json(MODEL_ARTIFACT)
    calibration_raw = read_json(CALIBRATION_ARTIFACT)
    parameters = model_raw["parameters"]
    model = LogisticModel(tuple(float(value) for value in parameters["weights"]), float(parameters["bias"]), int(parameters["seed"]), int(parameters["steps"]))
    isotonic = calibration_raw["methods"]["isotonic"]
    return model, isotonic, config


def reliability_rows(scores: list[float], labels: list[int], bins: int = 10) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(bins):
        lower = index / bins
        upper = 1.0 if index == bins - 1 else (index + 1) / bins
        selected = []
        for i, score in enumerate(scores):
            if (lower <= score <= upper) if index == bins - 1 else (lower <= score < upper):
                selected.append(i)
        rows.append({
            "bin": f"{lower:.1f}-{upper:.1f}",
            "lower": lower,
            "upper": upper,
            "n": len(selected),
            "mean_probability": float(np.mean([scores[i] for i in selected])) if selected else None,
            "observed_rate": float(np.mean([labels[i] for i in selected])) if selected else None,
        })
    return rows


def evaluate_external(records: list[dict[str, Any]], runtime: dict[str, Any]) -> dict[str, Any]:
    raw_cache = read_raw_cache()
    target_ids = set(raw_cache)
    selected = [row for row in records if str(row["normalized_variant_id"]) in target_ids]
    if len(selected) != len(target_ids):
        raise RuntimeError("raw cache contains an ID outside the frozen external selection")
    model, isotonic, config = load_frozen_probability_model()
    threshold = float(config["score_threshold"])
    rows: list[dict[str, Any]] = []
    for identity_row in selected:
        raw = raw_cache[str(identity_row["normalized_variant_id"])]
        features = (float(raw["delta_primary"]), float(raw["delta_forward"]), float(raw["delta_reverse"]), float(raw["orientation_disagreement"]))
        classifier_score = float(model.predict_proba(features))
        calibrated = float(apply_isotonic([classifier_score], isotonic)[0])
        rows.append({
            **raw,
            "label": int(identity_row["label"]),
            "gene_symbol": identity_row.get("gene_symbol"),
            "review_stars": int(identity_row["review_stars"]),
            "review_group": local.review_group(int(identity_row["review_stars"])),
            "review_status": identity_row.get("review_status"),
            "last_evaluated": identity_row.get("last_evaluated"),
            "feature_values": list(features),
            "classifier_score": classifier_score,
            "calibrated_probability": calibrated,
            "prediction": int(calibrated >= threshold),
            "error": int((calibrated >= threshold) != bool(identity_row["label"])),
            "label_joined_after_raw_hash": True,
        })
    labels = [int(row["label"]) for row in rows]
    probabilities = [float(row["calibrated_probability"]) for row in rows]
    scores = [float(row["delta_primary"]) for row in rows]
    metric_values = local.metric_bundle(probabilities, labels, threshold=threshold, groups=[str(row.get("gene_symbol") or "") for row in rows], bootstrap=True)
    metric_values["raw_delta_auroc"] = compute_auc_roc(scores, labels)
    metric_values["raw_delta_auprc"] = compute_auc_pr(scores, labels)
    metric_values["frozen_model_artifact_sha256"] = sha256_file(MODEL_ARTIFACT)
    metric_values["frozen_calibration_artifact_sha256"] = sha256_file(CALIBRATION_ARTIFACT)
    metric_values["calibration_method"] = "isotonic"
    metric_values["calibration_refit"] = False
    metric_values["threshold"] = threshold
    metric_values["label_join_gate"] = "raw_predictions_sha256 persisted before local manifest label join"
    reliability = reliability_rows(probabilities, labels)
    locked_artifact = read_json(ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json")
    locked_prob = locked_artifact["metrics"].get("probability_metrics", {})
    subgroup: dict[str, Any] = {}
    for group in sorted({str(row["review_group"]) for row in rows}):
        group_rows = [row for row in rows if row["review_group"] == group]
        group_labels = [int(row["label"]) for row in group_rows]
        group_scores = [float(row["calibrated_probability"]) for row in group_rows]
        group_record: dict[str, Any] = {"group": group, "n": len(group_rows), "class_counts": dict(Counter(str(label) for label in group_labels))}
        if len(set(group_labels)) == 2:
            group_record.update({"status": "PASS", "metrics": local.metric_bundle(group_scores, group_labels, threshold=threshold, groups=[str(row.get("gene_symbol") or "") for row in group_rows], bootstrap=True)})
        else:
            group_record["status"] = "INSUFFICIENT_SUPPORT"
        subgroup[group] = group_record
    evaluation = {
        "artifact_id": "evovariant-tr-external-clinvar-evaluation-v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": "PASS" if len(rows) == 200 else "COMPLETED_WITH_LIMITATIONS",
        "population": "frozen external ClinVar manifest",
        "n": len(rows),
        "class_counts": dict(Counter(str(label) for label in labels)),
        "manifest_path": str(MANIFEST.relative_to(ROOT)),
        "manifest_file_sha256": sha256_file(MANIFEST),
        "raw_predictions_path": str(RAW_PREDICTIONS.relative_to(ROOT)),
        "raw_predictions_sha256": sha256_file(RAW_PREDICTIONS),
        "prediction_artifact_persisted_before_evaluation_join": True,
        "labels_used_for_fitting": False,
        "labels_used_for_threshold_selection": False,
        "labels_used_for_calibration_fitting": False,
        "metrics": metric_values,
        "review_quality_subgroups": subgroup,
        "reliability": reliability,
        "locked_calibration_comparison": {key: locked_prob.get(key) for key in ("brier", "ece", "nll", "accuracy", "auroc", "auprc")},
        "rows": rows,
        "runtime_artifact": str(RUNTIME.relative_to(ROOT)),
    }
    write_json(EVALUATION, evaluation)
    write_json(METRICS, {key: value for key, value in evaluation.items() if key not in {"rows"}})
    write_jsonl(RUN_ROOT / "external_evaluated_predictions.jsonl", rows)
    with EXTERNAL_LABELS.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["normalized_variant_id", "gene_symbol", "label", "review_stars", "review_group", "delta_primary", "classifier_score", "calibrated_probability", "prediction", "error"])
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in writer.fieldnames} for row in rows)
    return evaluation


def audit_external_comparators(records: list[dict[str, Any]]) -> dict[str, Any]:
    from phase6a_comparators import _cadd_url, _lookup_many, _parse_cadd, _parse_phylop, _phylop_url

    rows = [{key: row[key] for key in ("normalized_variant_id", "assembly", "chromosome", "position_1based", "reference", "alternate")} for row in records]
    cache_path = RUN_ROOT / "comparator_lookup_cache.json"
    cache = {"cache_version": 1, "entries": {"cadd": {}, "phylop": {}}}
    try:
        from phase6a_comparators import _load_cache  # noqa: PLC0415
        cache = _load_cache(cache_path)
        cadd_obs, cadd_status, cadd_seconds = _lookup_many(kind="cadd", rows=rows, url_for=_cadd_url, cache=cache, cache_path=cache_path, max_workers=4)
        cadd_rows = [_parse_cadd(row, obs) for row, obs in zip(rows, cadd_obs, strict=True)]
        phylop_obs, phylop_status, phylop_seconds = _lookup_many(kind="phylop", rows=rows, url_for=_phylop_url, cache=cache, cache_path=cache_path, max_workers=4)
        phylop_rows = [_parse_phylop(row, obs) for row, obs in zip(rows, phylop_obs, strict=True)]
        payload = {
            "artifact_id": "evovariant-tr-external-classical-comparators-v1",
            "recorded_at_utc": datetime.now(UTC).isoformat(),
            "status": "PASS_WITH_MISSINGNESS",
            "source": {"cadd": "https://cadd.bihealth.org/api", "phylop": "https://api.genome.ucsc.edu/getData/track"},
            "rows": {"cadd": cadd_rows, "phylop": phylop_rows},
            "coverage": {"cadd": coverage(cadd_rows), "phylop": coverage(phylop_rows)},
            "request_status_counts": {"cadd": cadd_status, "phylop": phylop_status},
            "lookup_runtime_seconds": {"cadd": cadd_seconds, "phylop": phylop_seconds},
            "labels_read": False,
        }
    except Exception as exc:
        payload = {"artifact_id": "evovariant-tr-external-classical-comparators-v1", "recorded_at_utc": datetime.now(UTC).isoformat(), "status": "DATA_BLOCKED", "error": f"{type(exc).__name__}: {exc}", "rows": {"cadd": [], "phylop": []}, "coverage": {"cadd": {"total": len(rows), "available": 0, "missing": len(rows)}, "phylop": {"total": len(rows), "available": 0, "missing": len(rows)}}, "labels_read": False}
    write_json(COMPARATORS, payload)
    return payload


def coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    available = sum(row.get("status") == "AVAILABLE" for row in rows)
    return {"total": len(rows), "available": available, "missing": len(rows) - available, "coverage_fraction": available / len(rows) if rows else 0.0}


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda index: values[index])
        output = [0.0] * len(values)
        index = 0
        while index < len(order):
            end = index + 1
            while end < len(order) and values[order[end]] == values[order[index]]:
                end += 1
            value = (index + 1 + end) / 2.0
            for position in order[index:end]:
                output[position] = value
            index = end
        return output
    rx, ry = ranks(xs), ranks(ys)
    mx, my = float(np.mean(rx)), float(np.mean(ry))
    denom = math.sqrt(sum((value - mx) ** 2 for value in rx) * sum((value - my) ** 2 for value in ry))
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True)) / denom if denom else None


def model_agreement(evaluation: dict[str, Any], comparator: dict[str, Any]) -> dict[str, Any]:
    rows = evaluation["rows"]
    models: dict[str, dict[str, float]] = {"Evo2 frozen calibrated": {str(row["normalized_variant_id"]): float(row["calibrated_probability"]) for row in rows}}
    for name, score_key in (("CADD v1.7", "scaled_phred"), ("PhyloP 100-way", "sitewise_score")):
        values = {str(row["normalized_variant_id"]): float(row[score_key]) for row in comparator.get("rows", {}).get("cadd" if name.startswith("CADD") else "phylop", []) if row.get("status") == "AVAILABLE" and row.get(score_key) is not None}
        models[name] = values
    pairwise: list[dict[str, Any]] = []
    names = list(models)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            ids = sorted(set(models[left]) & set(models[right]))
            pairwise.append({"left": left, "right": right, "n_common": len(ids), "spearman": spearman([models[left][identity] for identity in ids], [models[right][identity] for identity in ids])})
    evo2 = models["Evo2 frozen calibrated"]
    labels = {str(row["normalized_variant_id"]): int(row["label"]) for row in rows}
    disagreements: list[dict[str, Any]] = []
    for name in names[1:]:
        ids = sorted(set(evo2) & set(models[name]))
        if not ids:
            continue
        left_median = float(np.median([evo2[i] for i in ids]))
        right_median = float(np.median([models[name][i] for i in ids]))
        disagreement_n = sum((evo2[i] >= left_median) != (models[name][i] >= right_median) for i in ids)
        disagreements.append({"comparator": name, "n_common": len(ids), "median_split_disagreement_n": disagreement_n, "median_split_disagreement_rate": disagreement_n / len(ids), "evo2_error_overlap_n": sum(((evo2[i] >= 0.5) != bool(labels[i])) and ((models[name][i] >= right_median) != (labels[i] == 1)) for i in ids)})
    return {
        "artifact_id": "evovariant-tr-external-model-agreement-v1",
        "status": "PASS_WITH_LIMITATIONS" if len(names) > 1 else "COMPUTE_BLOCKED",
        "n_evo2": len(evo2),
        "models": {name: {"available_n": len(values), "coverage_fraction": len(values) / len(evo2) if evo2 else 0.0} for name, values in models.items()},
        "pairwise": pairwise,
        "disagreement": disagreements,
        "consensus_rule": "descriptive above/below within-pair median; no comparator threshold was tuned",
        "nt_status": "NO_EXTERNAL_PREDICTION_ASSET",
        "caduceus_status": "NO_EXTERNAL_PREDICTION_ASSET",
    }


def audit_b11_b12() -> dict[str, Any]:
    helpers = load_local_helpers()
    formal = read_json(FORMAL_MANIFEST)["records"]
    formal_ids = {str(row["normalized_variant_id"]) for row in formal}
    cadd = helpers.load_comparator(ROOT / "artifacts/phase6a/comparators/formal_budgeted_20260921/cadd_grch38_v1.7_20260921.json")
    phylop = helpers.load_comparator(ROOT / "artifacts/phase6a/comparators/formal_budgeted_20260921/phylop100way_hg38_20260921.json", ("sitewise_score", "score", "value", "raw_score"))
    missing_cadd = sorted(formal_ids - set(cadd))
    missing_phylop = sorted(formal_ids - set(phylop))
    payload = {
        "artifact_id": "evovariant-tr-comparator-coverage-reaudit-v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "B11": {"comparator": "CADD", "total": len(formal_ids), "available": len(cadd.keys() & formal_ids), "missing": len(missing_cadd), "missing_ids": missing_cadd, "source_artifact": "artifacts/phase6a/comparators/formal_budgeted_20260921/cadd_grch38_v1.7_20260921.json", "decision": "retain COMPLETED_WITH_LIMITATIONS; no compatible authoritative completion asset was added"},
        "B12": {"comparator": "PhyloP", "total": len(formal_ids), "available": len(phylop.keys() & formal_ids), "missing": len(missing_phylop), "missing_ids": missing_phylop, "source_artifact": "artifacts/phase6a/comparators/formal_budgeted_20260921/phylop100way_hg38_20260921.json", "decision": "retain COMPLETED_WITH_LIMITATIONS; no compatible authoritative completion asset was added"},
        "imputation": False,
        "mixed_builds": False,
    }
    write_json(COMPARATOR_REAUDIT, payload)
    return payload


def audit_mavedb(records: list[dict[str, Any]]) -> dict[str, Any]:
    current = read_json(MAVEDB_MANIFEST) if MAVEDB_MANIFEST.is_file() else {}
    genes = sorted({str(row["gene_symbol"]) for row in records if row.get("gene_symbol")})[:12]
    searches: list[dict[str, Any]] = []
    for gene in genes:
        url = "https://api.mavedb.org/api/v1/score-sets/search"
        request = Request(url, data=json.dumps({"text": gene}).encode(), headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "EvoVariant-TR/B63-audit"}, method="POST")
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode())
            candidates = payload if isinstance(payload, list) else payload.get("results", []) if isinstance(payload, dict) else []
            searches.append({"gene": gene, "status": "HTTP_OK", "candidate_count": len(candidates), "candidates": [{key: item.get(key) for key in ("urn", "title", "numVariants", "published") if isinstance(item, dict) and item.get(key) is not None} for item in candidates[:10]]})
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            searches.append({"gene": gene, "status": "REQUEST_ERROR", "error": f"{type(exc).__name__}:{exc}"})
    current.update({
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": "DATA_BLOCKED",
        "query_plan": {**current.get("query_plan", {}), "genes_queried": genes, "correlations_inspected": False},
        "official_sources": ["https://www.mavedb.org/docs/mavedb/programmatic-access/api-quickstart.html", "https://www.mavedb.org/docs/mavedb/reference/variant-mapping.html"],
        "search_observations": searches,
        "assays": [],
        "decision": "DATA_BLOCKED: official search metadata did not freeze a predeclared assay with exact one-to-one GRCh38 SNV mapping, score direction, and >=20 overlapping variants; no correlations were inspected or computed.",
    })
    write_json(MAVEDB_MANIFEST, current)
    return current


def audit_comparator() -> dict[str, Any]:
    gpn = read_json(ROOT / "research/ml_extension/models/gpn.json")
    payload = {
        "artifact_id": "evovariant-tr-comparator-audit-v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": "NOT_APPLICABLE",
        "candidates": [{"name": "GPN-Star hg38 V100 200M", "official_source": gpn["source"], "license": gpn["license"], "build": gpn["input_contract"]["assembly"], "score_semantics": gpn["score_contract"]["score_semantics"], "variant_type": "SNV-compatible only with exact 100-way MSA context", "coverage": "not measured; required approximately 42 GB alignment archive is absent", "cost": "not acquired or run", "decision": "DEFERRED_DATA_AND_COMPUTE"}],
        "decision": "No additional public comparator is eligible for this continuation. GPN is a serious candidate with a compatible hg38 checkpoint and MIT license, but its required alignment asset is absent and the score-direction/orientation contract remains unverified. No proxy was substituted.",
        "official_audit_reused": "research/ml_extension/models/gpn.json",
    }
    write_json(COMPARATOR_AUDIT, payload)
    return payload


def drift_analysis(evaluation: dict[str, Any]) -> dict[str, Any]:
    external = evaluation["rows"]
    locked = read_json(LOCKED_ROWS)
    def count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
        return dict(Counter(str(row.get(key) or "missing") for row in rows))
    payload = {
        "artifact_id": "evovariant-tr-external-drift-v1",
        "status": "COMPLETED_WITH_LIMITATIONS",
        "external_n": len(external),
        "locked_n": len(locked),
        "label_proportion": {"external": sum(int(row["label"]) for row in external) / len(external), "locked": sum(int(row["label"]) for row in locked) / len(locked)},
        "review_group": {"external": count(external, "review_group"), "locked": count(locked, "t1_review_group")},
        "chromosome": {"external": count(external, "chromosome"), "locked": count(locked, "chromosome")},
        "gene_counts": {"external_unique": len({str(row.get("gene_symbol")) for row in external}), "locked_unique": len({str(row.get("gene_symbol")) for row in locked})},
        "source_dates": {"external_non_missing": sum(bool(row.get("last_evaluated")) for row in external), "locked_non_missing": sum(bool(row.get("t1_last_evaluated")) for row in locked)},
        "variant_classes": {"external": dict(Counter(local.substitution_class(str(row["normalized_variant_id"]).split(":")[-1].split(">", 1)[0], str(row["normalized_variant_id"]).split(":")[-1].split(">", 1)[1]) for row in external)), "locked": dict(Counter(str(row.get("substitution_class") or "missing") for row in locked))},
        "interpretation": "Descriptive distributional drift only; no causal or clinical interpretation.",
    }
    return payload


def make_external_figures(evaluation: dict[str, Any], subgroup: dict[str, Any], calibration: list[dict[str, Any]], agreement: dict[str, Any], runtime: dict[str, Any], drift: dict[str, Any]) -> list[dict[str, Any]]:
    from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve

    rows = evaluation["rows"]
    labels = [int(row["label"]) for row in rows]
    probabilities = [float(row["calibrated_probability"]) for row in rows]
    figures: list[dict[str, Any]] = []
    figures.append(local.make_figure("External cohort flow", "B61", "frozen external ClinVar cohort", len(rows), [{"stage": "manifest selected", "n": 200}, {"stage": "reference validated", "n": 200}, {"stage": "raw predictions persisted", "n": len(rows)}, {"stage": "evaluated", "n": len(rows)}], lambda axis: (axis.bar(["manifest", "reference", "raw", "evaluated"], [200, 200, len(rows), len(rows)], color="#2f6f63"), axis.set_ylabel("variants"))))
    figures.append(local.make_figure("External class balance", "B61", "frozen external ClinVar cohort", len(rows), [{"label": "benign", "n": sum(label == 0 for label in labels)}, {"label": "pathogenic", "n": sum(label == 1 for label in labels)}], lambda axis: (axis.bar(["benign", "pathogenic"], [sum(label == 0 for label in labels), sum(label == 1 for label in labels)], color=["#457b9d", "#de8246"]), axis.set_ylabel("variants"))))
    fpr, tpr, _ = roc_curve(labels, probabilities)
    figures.append(local.make_figure("External ROC", "B61", "frozen external ClinVar cohort", len(rows), [{"fpr": float(x), "tpr": float(y)} for x, y in zip(fpr, tpr, strict=True)], lambda axis: (axis.plot(fpr, tpr, color="#2f6f63", label=f"AUROC={evaluation['metrics']['auroc']:.3f}"), axis.plot([0, 1], [0, 1], "--", color="#9aa9a2"), axis.set_xlabel("false positive rate"), axis.set_ylabel("true positive rate"), axis.legend(loc="lower right"), axis.set_xlim(0, 1), axis.set_ylim(0, 1))))
    precision, recall, _ = precision_recall_curve(labels, probabilities)
    figures.append(local.make_figure("External precision-recall", "B61", "frozen external ClinVar cohort", len(rows), [{"recall": float(x), "precision": float(y)} for x, y in zip(recall, precision, strict=True)], lambda axis: (axis.plot(recall, precision, color="#de8246", label=f"AUPRC={evaluation['metrics']['auprc']:.3f}"), axis.set_xlabel("recall"), axis.set_ylabel("precision"), axis.legend(loc="lower left"), axis.set_xlim(0, 1), axis.set_ylim(0, 1))))
    matrix = confusion_matrix(labels, [int(row["prediction"]) for row in rows], labels=[0, 1])
    figures.append(local.make_figure("External confusion matrix", "B61", "frozen external ClinVar cohort", len(rows), [{"actual": int(actual), "predicted": int(predicted), "n": int(matrix[actual, predicted])} for actual in range(2) for predicted in range(2)], lambda axis: (axis.imshow(matrix, cmap="Greens"), axis.set_xlabel("predicted"), axis.set_ylabel("actual"), axis.set_xticks([0, 1]), axis.set_yticks([0, 1]), [[axis.text(predicted, actual, int(matrix[actual, predicted]), ha="center", va="center") for predicted in range(2)] for actual in range(2)])))
    classification_keys = ("accuracy", "balanced_accuracy", "precision", "recall", "specificity", "f1", "mcc")
    figures.append(local.make_figure("External classification dashboard", "B61", "frozen external ClinVar cohort", len(rows), [{"metric": key, "value": evaluation["metrics"].get(key)} for key in classification_keys], lambda axis: (axis.bar([key.replace("_", " ") for key in classification_keys], [evaluation["metrics"].get(key) or 0 for key in classification_keys], color="#2f6f63"), axis.set_ylim(0, 1), axis.tick_params(axis="x", rotation=35))))
    f1_keys = ("f1", "macro_f1", "micro_f1", "weighted_f1")
    figures.append(local.make_figure("External F1-family dashboard", "B61", "frozen external ClinVar cohort", len(rows), [{"metric": key, "value": evaluation["metrics"].get(key)} for key in f1_keys], lambda axis: (axis.bar([key.replace("_", " ") for key in f1_keys], [evaluation["metrics"].get(key) or 0 for key in f1_keys], color="#457b9d"), axis.set_ylim(0, 1), axis.tick_params(axis="x", rotation=25))))
    figures.append(local.make_figure("External calibration reliability", "B66", "frozen external ClinVar cohort", len(rows), calibration, lambda axis: (axis.plot([row["mean_probability"] for row in calibration if row["mean_probability"] is not None], [row["observed_rate"] for row in calibration if row["observed_rate"] is not None], marker="o", color="#2f6f63"), axis.plot([0, 1], [0, 1], "--", color="#9aa9a2"), axis.set_xlabel("mean predicted probability"), axis.set_ylabel("observed fraction"), axis.set_xlim(0, 1), axis.set_ylim(0, 1))))
    quality_keys = ("brier", "ece", "nll", "probability_mae")
    figures.append(local.make_figure("External probability quality", "B66", "frozen external ClinVar cohort", len(rows), [{"metric": key, "value": evaluation["metrics"].get(key)} for key in quality_keys], lambda axis: (axis.bar([key.replace("_", " ") for key in quality_keys], [evaluation["metrics"].get(key) or 0 for key in quality_keys], color="#bc6c25"), axis.tick_params(axis="x", rotation=25))))
    locked = read_json(ROOT / "artifacts/phase14/phase14_locked_evo2_20260922.json")["metrics"]["probability_metrics"]
    compare_keys = ("auroc", "auprc", "brier", "ece", "nll")
    figures.append(local.make_figure("Locked versus external calibration and discrimination", "B61-B66", "frozen locked versus external cohorts", len(rows), [{"metric": key, "locked": locked.get(key), "external": evaluation["metrics"].get(key)} for key in compare_keys], lambda axis: (axis.bar(np.arange(len(compare_keys)) - 0.18, [locked.get(key) or 0 for key in compare_keys], width=0.36, label="locked", color="#457b9d"), axis.bar(np.arange(len(compare_keys)) + 0.18, [evaluation["metrics"].get(key) or 0 for key in compare_keys], width=0.36, label="external", color="#de8246"), axis.set_xticks(np.arange(len(compare_keys)), [key.upper() for key in compare_keys]), axis.legend(), axis.tick_params(axis="x", rotation=20))))
    subgroup_records = [{"group": group, "n": item.get("n"), "auroc": item.get("metrics", {}).get("auroc") if item.get("metrics") else None, "f1": item.get("metrics", {}).get("f1") if item.get("metrics") else None} for group, item in subgroup.items()]
    figures.append(local.make_figure("External review-quality subgroup performance", "B62", "frozen external ClinVar cohort", len(rows), subgroup_records, lambda axis: (axis.bar([item["group"] for item in subgroup_records], [item["auroc"] or 0 for item in subgroup_records], color="#6a4c93"), axis.set_ylabel("AUROC where supported"), axis.set_ylim(0, 1), axis.tick_params(axis="x", rotation=20))))
    agreement_records = [{"pair": f"{item['left']} vs {item['right']}", "n_common": item["n_common"], "spearman": item.get("spearman")} for item in agreement.get("pairwise", [])]
    if not agreement_records:
        agreement_records = [{"pair": "Evo2 only; comparator asset unavailable", "n_common": agreement.get("n_evo2", 0), "spearman": None}]
    figures.append(local.make_figure("External model agreement", "B65", "frozen external ClinVar cohort", agreement.get("n_evo2"), agreement_records, lambda axis: (axis.bar([item["pair"] for item in agreement_records], [item["spearman"] or 0 for item in agreement_records], color="#2a9d8f"), axis.set_ylabel("Spearman; descriptive"), axis.set_ylim(-1, 1), axis.tick_params(axis="x", rotation=30))))
    runtime_records = [{"metric": "cache hit rows", "value": runtime.get("cache_hit_rows", 0)}, {"metric": "fresh rows", "value": runtime.get("fresh_rows", 0)}, {"metric": "remote invocations", "value": runtime.get("remote_invocations", 0)}, {"metric": "remote seconds", "value": runtime.get("remote_method_seconds", 0)}, {"metric": "rate-estimated USD", "value": runtime.get("rate_estimated_cost_usd", 0)}]
    figures.append(local.make_figure("External runtime and cache economics", "B67", "frozen external ClinVar inference", runtime.get("target_rows"), runtime_records, lambda axis: (axis.bar([item["metric"] for item in runtime_records], [item["value"] or 0 for item in runtime_records], color="#264653"), axis.tick_params(axis="x", rotation=35))))
    drift_records = [{"measure": "external label proportion", "external": drift["label_proportion"]["external"], "locked": drift["label_proportion"]["locked"]}, {"measure": "external unique genes / 200", "external": drift["gene_counts"]["external_unique"] / drift["external_n"], "locked": drift["gene_counts"]["locked_unique"] / drift["locked_n"]}]
    figures.append(local.make_figure("External versus locked cohort drift", "B68", "descriptive external versus locked cohorts", drift["external_n"], drift_records, lambda axis: (axis.bar(np.arange(len(drift_records)) - 0.18, [item["external"] for item in drift_records], width=0.36, label="external", color="#de8246"), axis.bar(np.arange(len(drift_records)) + 0.18, [item["locked"] for item in drift_records], width=0.36, label="locked", color="#457b9d"), axis.set_xticks(np.arange(len(drift_records)), [item["measure"] for item in drift_records]), axis.legend(), axis.tick_params(axis="x", rotation=25))))
    return figures


def regenerate_contact_sheet(figures: list[dict[str, Any]]) -> dict[str, Any]:
    from PIL import Image, ImageDraw

    paths = [DOCS / "assets" / Path(figure["asset"]).name for figure in figures if (DOCS / "assets" / Path(figure["asset"]).name).is_file()]
    width, height = 640, 360
    contact = Image.new("RGB", (width * 2, height * math.ceil(len(paths) / 2)), "white")
    draw = ImageDraw.Draw(contact)
    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((width - 20, height - 40))
        x = (index % 2) * width + (width - image.width) // 2
        y = (index // 2) * height + 28
        contact.paste(image, (x, y))
        draw.text(((index % 2) * width + 12, (index // 2) * height + 8), figures[index]["title"], fill="black")
    path = DOCS / "assets/benchmark_contact_sheet.png"
    contact.save(path)
    shutil.copy2(path, DOCS / "assets/contact_sheet.png")
    shutil.copy2(path, WEB / "figures/benchmark_contact_sheet.png")
    shutil.copy2(path, WEB / "figures/contact_sheet.png")
    provenance = {"benchmark_id": "B01-B68", "population": "registered benchmark figures", "inputs": [local.rel(item) for item in paths], "output": local.rel(path), "sha256": sha256_file(path)}
    write_json(DOCS / "data/figures/contact_sheet.provenance.json", provenance)
    shutil.copy2(DOCS / "data/figures/contact_sheet.provenance.json", WEB / "data/figures/contact_sheet.provenance.json")
    return {"id": "contact_sheet", "title": "Benchmark figure contact sheet", "benchmark_id": "B01-B68", "population": "registered benchmark figures", "n": len(paths), "caption": "Contact sheet of generated benchmark figures.", "asset": "/benchmarks/figures/benchmark_contact_sheet.png", "source_data": "/benchmarks/data/figures/contact_sheet.provenance.json", "provenance": "/benchmarks/data/figures/contact_sheet.provenance.json", "sha256": {"png": provenance["sha256"]}}


def update_catalogs(evaluation: dict[str, Any], comparator: dict[str, Any], agreement: dict[str, Any], runtime: dict[str, Any], drift: dict[str, Any], mavedb: dict[str, Any], b11_b12: dict[str, Any], comp_audit: dict[str, Any], figures: list[dict[str, Any]], start_main_head: str) -> dict[str, Any]:
    manifest = read_json(WEB / "benchmark-manifest.json")
    registry = read_json(ARTIFACTS / "benchmark_registry.json")
    raw_hash = sha256_file(RAW_PREDICTIONS)
    eval_hash = sha256_file(EVALUATION)
    target_n = int(evaluation["n"])
    b61_status = "PASS" if target_n == 200 else "COMPLETED_WITH_LIMITATIONS"
    entry_updates = {
        "B11": {"status": "COMPLETED_WITH_LIMITATIONS", "summary": "Official CADD coverage was re-audited with exact missing IDs retained; no imputation or mixed build was used.", "limitations": [f"{b11_b12['B11']['missing']} formal rows remain missing from the authoritative CADD artifact."], "output_artifacts": ["artifacts/benchmarks/comparator_coverage_reaudit.json"]},
        "B12": {"status": "COMPLETED_WITH_LIMITATIONS", "summary": "Official PhyloP coverage was re-audited with exact missing IDs retained; no imputation or mixed build was used.", "limitations": [f"{b11_b12['B12']['missing']} formal rows remain missing from the authoritative PhyloP artifact."], "output_artifacts": ["artifacts/benchmarks/comparator_coverage_reaudit.json"]},
        "B45": {"status": "COMPLETED_WITH_LIMITATIONS", "summary": "Historical compute evidence is retained and the external continuation now has measured Modal runtime, cache and rate-estimated cost receipts.", "limitations": ["Modal provider billing is workspace-level; GPU wall-rate estimate and provider billing delta are reported separately."], "output_artifacts": ["artifacts/benchmarks/external_clinvar_runtime.json"]},
        "B61": {"status": b61_status, "summary": f"Frozen 200-row independent ClinVar inference completed for {target_n} rows with raw predictions persisted before the label join.", "limitations": [] if target_n == 200 else ["Budget rule selected a deterministic balanced subset; the original 200-row manifest remains frozen."], "output_artifacts": ["artifacts/benchmarks/external_clinvar_manifest.json", "artifacts/benchmarks/external_clinvar_manifest_receipt.json", "artifacts/benchmarks/external_clinvar_evaluation.json", "artifacts/benchmarks/external_clinvar_metrics.json", "artifacts/benchmarks/external_clinvar_provenance.json"]},
        "B62": {"status": "PASS" if evaluation["review_quality_subgroups"] else "COMPLETED_WITH_LIMITATIONS", "summary": "Unchanged B61 predictions were evaluated by frozen ClinVar review-quality strata without subgroup tuning.", "limitations": []},
        "B63": {"status": "DATA_BLOCKED", "summary": mavedb.get("decision", "Official MaveDB audit did not yield a defensible frozen assay mapping."), "limitations": ["Functional effect is not equivalent to clinical pathogenicity."], "output_artifacts": ["research/benchmarks/expansion_v1/mavedb_protocol.md", "artifacts/benchmarks/mavedb_assay_manifest.json"]},
        "B64": {"status": "NOT_APPLICABLE", "summary": comp_audit["decision"], "limitations": ["GPN was audited but required alignment data and a verified external run were unavailable; no proxy was substituted."], "output_artifacts": ["artifacts/benchmarks/comparator_audit.json"]},
        "B65": {"status": agreement.get("status", "COMPLETED_WITH_LIMITATIONS"), "summary": "External Evo2 agreement is compared with available official classical comparator rows; NT/Caduceus remain explicitly unavailable for this external cohort.", "limitations": ["No external NT/Caduceus prediction asset was available; classical comparator direction is descriptive, not retuned."], "output_artifacts": ["artifacts/benchmarks/external_classical_comparators.json", "artifacts/benchmarks/external_clinvar_metrics.json"]},
        "B66": {"status": "PASS", "summary": "The frozen TRAIN-fit isotonic calibrator was applied unchanged to external Evo2 predictions with reliability and probability-quality metrics.", "limitations": ["External probabilities are transported, not recalibrated."], "output_artifacts": ["artifacts/benchmarks/external_clinvar_evaluation.json", "artifacts/benchmarks/external_clinvar_metrics.json"]},
        "B67": {"status": "PASS", "summary": "External GPU runtime, throughput, cache reuse, retries, rate-estimated cost and billing snapshots are persisted.", "limitations": ["Provider billing is workspace-level and is not treated as a per-request invoice."], "output_artifacts": ["artifacts/benchmarks/external_clinvar_runtime.json"]},
        "B68": {"status": "COMPLETED_WITH_LIMITATIONS", "summary": "External and locked cohort class mix, review strata, chromosomes, genes, source dates and variant classes are compared descriptively.", "limitations": ["Drift is descriptive and does not establish causation."], "output_artifacts": ["artifacts/benchmarks/external_clinvar_metrics.json"]},
    }
    for entry in registry["entries"]:
        update = entry_updates.get(str(entry["id"]))
        if update:
            entry.update(update)
            links = set(str(item) for item in entry.get("artifact_links", []))
            links.update(str(item) for item in update.get("output_artifacts", []))
            entry["artifact_links"] = sorted(links)
            entry["source_artifacts"] = sorted(set(entry.get("source_artifacts", [])) | set(update.get("output_artifacts", [])))
            entry["new_inference"] = "YES" if entry["id"] in {"B61", "B62", "B65", "B66", "B67"} else entry.get("new_inference", "NO")
            entry["requires_new_inference"] = "YES" if entry["id"] in {"B61", "B62", "B65", "B66", "B67"} else entry.get("requires_new_inference", "NO")
            if entry["id"] in {"B61", "B62", "B65", "B66", "B67"}:
                entry["n"] = target_n
    all_figures = [figure for figure in manifest.get("figures", []) if figure.get("id") != "contact_sheet"]
    all_figures.extend(figure for figure in figures if figure.get("id") != "contact_sheet")
    all_figures = local.attach_figures(registry, all_figures)
    # attach_figures returns a registry; the variable is intentionally reused to keep B01-B60 intact.
    registry = all_figures
    contact = regenerate_contact_sheet(manifest.get("figures", []) if False else [figure for figure in manifest.get("figures", []) if figure.get("id") != "contact_sheet"] + [figure for figure in figures if figure.get("id") != "contact_sheet"])
    figure_catalog = [figure for figure in manifest.get("figures", []) if figure.get("id") != "contact_sheet"] + [figure for figure in figures if figure.get("id") != "contact_sheet"] + [contact]
    # Deduplicate by figure id while preserving the latest external replacement.
    deduped: dict[str, dict[str, Any]] = {}
    for figure in figure_catalog:
        deduped[str(figure["id"])] = figure
    figure_catalog = list(deduped.values())
    local.write_figure_qa(figure_catalog)
    counts = Counter(str(entry["status"]) for entry in registry["entries"])
    registry.update({"generated_at_utc": datetime.now(UTC).isoformat(), "status_counts": dict(counts), "entry_count": len(registry["entries"])})
    write_json(ARTIFACTS / "benchmark_registry.json", registry)
    write_json(ROOT / "research/benchmarks/expansion_v1/registry.json", registry)
    catalog = local.markdown_catalog(registry)
    atomic_write(DOCS / "BENCHMARK_CATALOG.md", catalog)
    atomic_write(DOCS / "FINAL_STATUS_MATRIX.md", "# Final Benchmark Status Matrix\n\n" + catalog)
    atomic_write(ROOT / "research/benchmarks/expansion_v1/BENCHMARK_CATALOG.md", catalog)
    analysis = read_json(ROOT / "research/benchmarks/expansion_v1/local_analysis_results.json")
    analysis.update({"external_clinvar": evaluation, "external_review_quality": evaluation["review_quality_subgroups"], "external_calibration": {"metrics": evaluation["metrics"], "reliability": evaluation["reliability"]}, "external_model_agreement": agreement, "external_runtime": runtime, "external_drift": drift, "mavedb": mavedb, "comparator_audit": comp_audit, "comparator_coverage_reaudit": b11_b12})
    write_json(ROOT / "research/benchmarks/expansion_v1/local_analysis_results.json", {key: value for key, value in analysis.items() if key != "locked_rows"})
    external_data = {"manifest": {"path": str(MANIFEST.relative_to(ROOT)), "file_sha256": sha256_file(MANIFEST), "inner_sha256": read_json(MANIFEST).get("manifest_sha256"), "selected_n": 200, "reference_validated_n": read_json(MANIFEST).get("reference_validated_n", 200), "class_counts": {"0": 100, "1": 100}}, "inference_status": "COMPLETED" if target_n == 200 else "COMPLETED_WITH_LIMITATIONS", "selected_n": target_n, "metrics": evaluation["metrics"], "review_quality_subgroups": evaluation["review_quality_subgroups"], "calibration": {"metrics": evaluation["metrics"], "reliability": evaluation["reliability"], "locked_comparison": evaluation["locked_calibration_comparison"]}, "agreement": agreement, "runtime": runtime, "drift": drift, "mavedb": mavedb, "comparator_audit": comp_audit, "coverage_reaudit": b11_b12, "prediction_artifact_sha256": raw_hash, "evaluation_artifact_sha256": eval_hash}
    manifest["generated_at_utc"] = datetime.now(UTC).isoformat()
    manifest["benchmarks"] = registry["entries"]
    manifest["what_we_contributed"] = [
        {"benchmark_id": entry["id"], "title": entry["title"], "status": entry["status"], "web_tab": entry["web_tab"], "evidence": entry["artifact_links"]}
        for entry in registry["entries"]
    ]
    manifest["figures"] = figure_catalog
    manifest["data"]["external"] = external_data
    manifest["data"]["compute"] = {"new_spend_usd": runtime.get("rate_estimated_cost_usd"), "provider_billed_delta_usd": runtime.get("provider_billed_delta_usd"), "modal_profile": runtime.get("profile"), "starting_verified_credit_usd": runtime.get("starting_verified_credit_usd"), "ending_verified_credit_usd": runtime.get("ending_verified_credit_usd"), "balance_status": "VERIFIED_STARTING_BALANCE_ENDING_CHECK_PENDING", "resources_started": runtime.get("remote_invocations", 0), "resources_running": 0}
    manifest["headline_cards"] = [{**card, "value": sum(dict(counts).get(status, 0) for status in ("PASS", "PASS_WITH_LIMITATIONS", "COMPLETED_WITH_LIMITATIONS")) if card["id"] == "completed" else card["value"]} for card in manifest["headline_cards"]]
    manifest["limitations"] = ["The frozen 946-row primary result remains unchanged.", "External model predictions are persisted before local label evaluation.", "MaveDB remains DATA_BLOCKED without a defensible exact GRCh38 assay mapping.", "GPN was audited but not integrated because its required alignment asset and run contract were unavailable."]
    manifest["reproducibility"].update({"external_manifest_file_sha256": sha256_file(MANIFEST), "external_manifest_inner_sha256": read_json(MANIFEST).get("manifest_sha256"), "external_raw_predictions_sha256": raw_hash, "external_evaluation_sha256": eval_hash, "external_provenance_sha256": sha256_file(PROVENANCE) if PROVENANCE.is_file() else None, "starting_main_head": start_main_head, "working_branch": local.git_value("branch", "--show-current")})
    downloads = {str(item["path"]): item for item in manifest.get("downloads", [])}
    for label, path in (("External metrics CSV", "/benchmarks/downloads/external_clinvar_predictions_summary.csv"), ("External evaluation JSON", "/benchmarks/downloads/external_clinvar_evaluation.json"), ("External runtime JSON", "/benchmarks/downloads/external_clinvar_runtime.json"), ("External provenance JSON", "/benchmarks/downloads/external_clinvar_provenance.json"), ("MaveDB audit manifest", "/benchmarks/downloads/mavedb_assay_manifest.json"), ("Comparator audit", "/benchmarks/downloads/comparator_audit.json")):
        downloads[path] = {"label": label, "path": path}
    manifest["downloads"] = list(downloads.values())
    write_json(WEB / "benchmark-manifest.json", manifest)
    summary = read_json(ARTIFACTS / "final_benchmark_summary.json")
    summary.update({"generated_at_utc": datetime.now(UTC).isoformat(), "status_counts": dict(counts), "completed_benchmark_families": sum(counts.get(status, 0) for status in ("PASS", "PASS_WITH_LIMITATIONS", "COMPLETED_WITH_LIMITATIONS")), "blockers": ["DATA_BLOCKED_MAVEDB: no defensible exact GRCh38 SNV assay mapping was frozen.", "NOT_APPLICABLE_GPN: required alignment asset and verified score contract were unavailable.", "PASS_WITH_LIMITATIONS_NT_CADUCEUS: no external prediction asset was available for this cohort."], "external_n": target_n, "modal_spend_usd": runtime.get("rate_estimated_cost_usd"), "external": external_data, "external_manifest_sha256": sha256_file(MANIFEST), "external_predictions_sha256": raw_hash, "external_evaluation_sha256": eval_hash, "new_external_figure_count": len(figures)})
    write_json(ARTIFACTS / "final_benchmark_summary.json", summary)
    return {"registry": registry, "web_manifest": manifest, "summary": summary, "figures": figure_catalog}


def write_provenance(evaluation: dict[str, Any], runtime: dict[str, Any], audit: dict[str, Any], agreement: dict[str, Any]) -> None:
    payload = {"artifact_id": "evovariant-tr-external-provenance-v1", "recorded_at_utc": datetime.now(UTC).isoformat(), "manifest": audit, "raw_predictions": {"path": str(RAW_PREDICTIONS.relative_to(ROOT)), "sha256": sha256_file(RAW_PREDICTIONS), "labels_present": False}, "evaluation": {"path": str(EVALUATION.relative_to(ROOT)), "sha256": sha256_file(EVALUATION), "labels_joined_after_raw_hash": True}, "runtime": runtime, "model": {"model_id": MODEL_ID, "revision": MODEL_REVISION, "gpu_type": GPU_TYPE, "context_length_bp": CONTEXT_LENGTH_BP, "orientation": "forward_and_reverse", "score_semantics": "alternate_minus_reference_log_likelihood"}, "frozen_downstream": {"model_artifact": str(MODEL_ARTIFACT.relative_to(ROOT)), "model_artifact_sha256": sha256_file(MODEL_ARTIFACT), "calibration_artifact": str(CALIBRATION_ARTIFACT.relative_to(ROOT)), "calibration_artifact_sha256": sha256_file(CALIBRATION_ARTIFACT), "threshold": 0.5, "calibration_refit": False}, "agreement": agreement, "leakage_gates": {"external_ids_disjoint_from_development": audit["development_id_overlap"] == 0, "external_ids_disjoint_from_locked": audit["locked_id_overlap"] == 0, "external_genes_disjoint_from_development": audit["development_gene_overlap"] == 0, "external_genes_disjoint_from_locked": audit["locked_gene_overlap"] == 0, "labels_used_for_fitting": False, "labels_used_for_threshold_selection": False, "labels_used_for_calibration_fitting": False, "raw_persisted_before_label_join": True}}
    write_json(PROVENANCE, payload)


def update_docs(evaluation: dict[str, Any], runtime: dict[str, Any], registry: dict[str, Any], mavedb: dict[str, Any], comp_audit: dict[str, Any], b11_b12: dict[str, Any]) -> None:
    metrics = evaluation["metrics"]
    summary = f"""## External benchmark continuation — 2026-09-24

The frozen ClinVar external manifest remains unchanged at 200 rows (100 benign,
100 pathogenic). Evo2 raw forward/alternate and reverse-complement scores were
persisted before joining the manifest labels. The frozen TRAIN-fit logistic
model, isotonic calibrator, and threshold 0.50 were applied without refitting.

External n={evaluation['n']}; AUROC={metrics.get('auroc')}; AUPRC={metrics.get('auprc')};
accuracy={metrics.get('accuracy')}; balanced accuracy={metrics.get('balanced_accuracy')};
F1={metrics.get('f1')}; MCC={metrics.get('mcc')}; Brier={metrics.get('brier')};
ECE={metrics.get('ece')}; NLL={metrics.get('nll')}. Rate-estimated new Modal
cost=${runtime.get('rate_estimated_cost_usd', 0.0):.6f}; fresh rows={runtime.get('fresh_rows')};
cache-hit rows={runtime.get('cache_hit_rows')}; remote seconds={runtime.get('remote_method_seconds')}.

B63 remains DATA_BLOCKED because official MaveDB search metadata did not freeze
an exact GRCh38 SNV assay mapping with predeclared score direction and support.
B64 remains NOT_APPLICABLE after the GPN audit because the required alignment
asset and run contract were unavailable; no proxy comparator was substituted.
B11/B12 retain exact missing-row coverage and no imputation or mixed builds.
"""
    append_once(DOCS / "FINAL_BENCHMARK_REPORT.md", "## External benchmark continuation — 2026-09-24", summary)
    append_once(DOCS / "RESULTS.md", "## External benchmark continuation — 2026-09-24", summary)
    append_once(DOCS / "COMPUTE.md", "## External benchmark continuation — 2026-09-24", summary)
    append_once(DOCS / "MODAL_COST_REPORT.md", "## External benchmark continuation — 2026-09-24", summary)
    # The marker must match the heading that is actually appended, otherwise a
    # re-run silently stacks duplicate sections.
    continuation_marker = "## External benchmark continuation — 2026-09-24"
    append_once(ROOT / "README.md", continuation_marker, summary)
    append_once(ROOT / "docs/JUDGE_DEMO.md", continuation_marker, summary)
    append_once(ROOT / "docs/agent/PROJECT_STATE.md", continuation_marker, summary)
    append_once(ROOT / "docs/agent/PHASE_LEDGER.md", "| 26 | External benchmark completion", f"| 26 | External benchmark completion | {registry['status_counts'].get('PASS', 0)} PASS registry entries; B61/B62/B66/B67 persisted with fresh evidence; B63/B64 remain explicitly bounded; raw prediction and leakage receipts are tracked. |")
    # Keep a compact current cost report generated from actual local artifacts.
    append_once(ROOT / "docs/benchmarks/FINAL_STATUS_MATRIX.md", continuation_marker, summary)


def update_notebook() -> None:
    path = ROOT / "notebooks/EvoVariant_TR_Benchmark_Expansion_Demo.ipynb"
    if not path.is_file():
        return
    notebook = read_json(path)
    marker = "EXTERNAL_BENCHMARK_COMPLETION_V1"
    if any(marker in "".join(cell.get("source", [])) for cell in notebook.get("cells", [])):
        return
    evaluation = read_json(EVALUATION)
    source = [
        f"# {marker}\n",
        "import json\n",
        "from pathlib import Path\n",
        "external = json.loads(Path('../artifacts/benchmarks/external_clinvar_evaluation.json').read_text())\n",
        "print({'n': external['n'], 'auroc': external['metrics']['auroc'], 'auprc': external['metrics']['auprc'], 'brier': external['metrics']['brier'], 'ece': external['metrics']['ece'], 'nll': external['metrics']['nll']})\n",
    ]
    notebook.setdefault("cells", []).append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source})
    atomic_write(path, json.dumps(notebook, indent=1) + "\n")
    shutil.copy2(path, WEB / "downloads/EvoVariant_TR_Benchmark_Expansion_Demo.ipynb")
    _ = evaluation


def write_downloads(catalog: dict[str, Any]) -> None:
    downloads = WEB / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    for source, name in ((EVALUATION, "external_clinvar_evaluation.json"), (RUNTIME, "external_clinvar_runtime.json"), (PROVENANCE, "external_clinvar_provenance.json"), (MAVEDB_MANIFEST, "mavedb_assay_manifest.json"), (COMPARATOR_AUDIT, "comparator_audit.json"), (ARTIFACTS / "final_benchmark_summary.json", "final_benchmark_summary.json")):
        shutil.copy2(source, downloads / name)
    shutil.copy2(EXTERNAL_LABELS, downloads / EXTERNAL_LABELS.name)
    write_json(downloads / "external_figure_index.json", {"figures": [figure for figure in catalog["figures"] if figure["benchmark_id"] != "B01-B68" or figure["id"] == "contact_sheet"]})
    summary_csv = downloads / "final_benchmark_summary.csv"
    summary = read_json(ARTIFACTS / "final_benchmark_summary.json")
    with summary_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["field", "value"])
        for key in ("primary_status", "external_n", "modal_spend_usd", "external_manifest_sha256", "external_predictions_sha256"):
            writer.writerow([key, summary.get(key)])


def finalize_verified_balance(balance: float) -> None:
    """Bind the completed run to the separately verified workspace balance."""
    if not math.isfinite(balance) or balance < SAFETY_STOP_USD:
        raise RuntimeError(f"ending verified credit {balance!r} is below the safety stop")
    runtime = read_json(RUNTIME)
    if runtime.get("mode") != "full" or int(runtime.get("target_rows", 0)) != 200:
        raise RuntimeError("full 200-row runtime receipt is required before finalization")
    billing_after = billing_snapshot()
    if billing_after.get("returncode") == 0:
        runtime["billing_after"] = billing_after
    before = float(runtime["billing_before"]["summary"]["metered_cost"])
    after = float(runtime["billing_after"]["summary"]["metered_cost"])
    starting = float(runtime["starting_verified_credit_usd"])
    total_spend = round(starting - balance, 8)
    runtime.update(
        {
            "ending_verified_credit_usd": balance,
            "provider_billed_delta_usd": round(after - before, 8),
            "actual_workspace_metered_cost_since_preflight_usd": round(after, 8),
            "credit_delta_from_start_usd": total_spend,
            "balance_verification": {
                "status": "VERIFIED",
                "method": "authenticated Modal dashboard Credits card",
                "observed_credit_usd": balance,
                "observed_at_utc": datetime.now(UTC).isoformat(),
                "url": "https://modal.com/utkarshkhajuria59/main",
            },
        }
    )
    write_json(RUNTIME, runtime)
    full_runtime = RUN_ROOT / "full_runtime.json"
    if full_runtime.is_file():
        write_json(full_runtime, runtime)
    if PROVENANCE.is_file():
        provenance = read_json(PROVENANCE)
        provenance["recorded_at_utc"] = datetime.now(UTC).isoformat()
        provenance["runtime"] = runtime
        write_json(PROVENANCE, provenance)

    budget = {
        "profile": runtime["profile"],
        "starting_verified_credit_usd": starting,
        "ending_verified_credit_usd": balance,
        "actual_workspace_metered_cost_since_preflight_usd": round(after, 8),
        "provider_billed_delta_usd": runtime["provider_billed_delta_usd"],
        "rate_estimated_inference_usd": runtime["rate_estimated_cost_usd"],
        "hard_reserve_usd": HARD_RESERVE_USD,
        "safety_stop_usd": SAFETY_STOP_USD,
        "program_budget_usd": SOFT_MAXIMUM_USD,
        "safe_spendable_usd": round(starting - SAFETY_STOP_USD, 8),
        "pilot_completed": True,
        "full_inference_completed": True,
        "status": "COMPLETED_WITHIN_RESERVE",
    }
    write_json(RUN_ROOT / "modal_budget_plan.json", budget)
    ledger = {
        "artifact_id": "evovariant-tr-modal-cost-ledger-v1",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "profile": runtime["profile"],
        "balance_status": "VERIFIED",
        "starting_verified_credit_usd": starting,
        "ending_verified_credit_usd": balance,
        "new_spend_usd": total_spend,
        "actual_workspace_metered_cost_since_preflight_usd": round(after, 8),
        "provider_billed_delta_usd": runtime["provider_billed_delta_usd"],
        "rate_estimated_inference_usd": runtime["rate_estimated_cost_usd"],
        "hard_reserve_usd": HARD_RESERVE_USD,
        "safety_stop_usd": SAFETY_STOP_USD,
        "program_budget_usd": SOFT_MAXIMUM_USD,
        "resources_started_by_expansion": [runtime["gpu_type"]],
        "remote_invocations": runtime["remote_invocations"],
        "cache_hit_rows": runtime["cache_hit_rows"],
        "fresh_rows": runtime["fresh_rows"],
        "status": "PASS_WITH_LIMITATIONS",
        "limitation": "Workspace billing is authoritative for credits consumed; the provider delta is not a per-request invoice.",
    }
    write_json(RUN_ROOT / "modal_cost_ledger.json", ledger)

    analysis_path = ROOT / "research/benchmarks/expansion_v1/local_analysis_results.json"
    if analysis_path.is_file():
        analysis = read_json(analysis_path)
        analysis["external_runtime"] = runtime
        write_json(analysis_path, analysis)
    manifest_path = WEB / "benchmark-manifest.json"
    manifest = read_json(manifest_path)
    external = manifest.setdefault("data", {}).setdefault("external", {})
    external["runtime"] = runtime
    compute = manifest["data"].setdefault("compute", {})
    compute.update(
        {
            "new_spend_usd": total_spend,
            "rate_estimated_inference_usd": runtime["rate_estimated_cost_usd"],
            "provider_billed_delta_usd": runtime["provider_billed_delta_usd"],
            "modal_profile": runtime["profile"],
            "starting_verified_credit_usd": starting,
            "ending_verified_credit_usd": balance,
            "balance_status": "VERIFIED",
            "resources_started": runtime["remote_invocations"],
            "resources_running": 0,
            "cache_hit_rows": runtime["cache_hit_rows"],
            "fresh_rows": runtime["fresh_rows"],
        }
    )
    manifest["reproducibility"]["external_runtime_sha256"] = sha256_file(RUNTIME)
    write_json(manifest_path, manifest)

    summary_path = ARTIFACTS / "final_benchmark_summary.json"
    summary = read_json(summary_path)
    summary.update(
        {
            "modal_spend_usd": total_spend,
            "modal_rate_estimated_inference_usd": runtime["rate_estimated_cost_usd"],
            "modal_provider_billed_delta_usd": runtime["provider_billed_delta_usd"],
            "modal_starting_verified_credit_usd": starting,
            "modal_ending_verified_credit_usd": balance,
            "external": {**summary.get("external", {}), "runtime": runtime},
        }
    )
    write_json(summary_path, summary)
    downloads = WEB / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    for source in (RUNTIME, PROVENANCE, summary_path):
        shutil.copy2(source, downloads / source.name)
    with (downloads / "final_benchmark_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["field", "value"])
        for key in ("primary_status", "external_n", "modal_spend_usd", "modal_rate_estimated_inference_usd", "modal_provider_billed_delta_usd", "modal_ending_verified_credit_usd", "external_manifest_sha256", "external_predictions_sha256"):
            writer.writerow([key, summary.get(key)])

    cost_note = f"""## Modal balance finalization — 2026-09-24

The authenticated Modal dashboard verified ending credit at **${balance:.2f}**
for profile `{runtime['profile']}`. Starting verified credit was **${starting:.2f}**;
workspace credit consumption since preflight was **${total_spend:.2f}**. The
billing summary metered-cost delta was **${runtime['provider_billed_delta_usd']:.2f}**;
the H100 rate estimate for fresh inference was **${runtime['rate_estimated_cost_usd']:.6f}**.
The distinction is intentional: workspace credit usage includes setup and other
metered overhead, while the provider delta is not a per-request invoice.
"""
    append_once(DOCS / "MODAL_COST_REPORT.md", "## Modal balance finalization — 2026-09-24", cost_note)


def local_finalize() -> dict[str, Any]:
    """Re-derive every external catalog from persisted predictions.

    This mode never constructs a Modal worker and never launches remote
    compute. It is the reproducible, no-spend completion path: the frozen raw
    predictions and the recorded runtime receipt must already exist on disk.
    """
    if not RAW_PREDICTIONS.is_file():
        raise RuntimeError(
            "local-finalize requires the persisted external raw predictions "
            f"at {RAW_PREDICTIONS.relative_to(ROOT)}"
        )
    if not RUNTIME.is_file():
        raise RuntimeError(
            "local-finalize requires the recorded external runtime artifact "
            f"at {RUNTIME.relative_to(ROOT)}"
        )
    runtime = read_json(RUNTIME)
    _, records, audit = validate_manifest()
    load_local_helpers()
    evaluation = evaluate_external(records, runtime)
    comparator = audit_external_comparators(records)
    b11_b12 = audit_b11_b12()
    mavedb = audit_mavedb(records)
    comp_audit = audit_comparator()
    agreement = model_agreement(evaluation, comparator)
    drift = drift_analysis(evaluation)
    write_provenance(evaluation, runtime, audit, agreement)
    figures = make_external_figures(
        evaluation,
        evaluation["review_quality_subgroups"],
        evaluation["reliability"],
        agreement,
        runtime,
        drift,
    )
    catalog = update_catalogs(
        evaluation,
        comparator,
        agreement,
        runtime,
        drift,
        mavedb,
        b11_b12,
        comp_audit,
        figures,
        local.git_value("rev-parse", "HEAD"),
    )
    write_downloads(catalog)
    update_docs(evaluation, runtime, catalog["registry"], mavedb, comp_audit, b11_b12)
    update_notebook()
    summary = {
        "status": evaluation["status"],
        "mode": "local-finalize",
        "remote_compute_started": False,
        "n": evaluation["n"],
        "metrics": evaluation["metrics"],
        "registry_status_counts": catalog["registry"]["status_counts"],
        "raw_predictions_sha256": sha256_file(RAW_PREDICTIONS),
        "figure_count": len(figures),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    mode = os.environ.get("EVOVARIANT_EXTERNAL_MODE", "full")
    if mode not in {"dry-run", "pilot", "full", "finalize", "local-finalize"}:
        raise SystemExit(f"unsupported EVOVARIANT_EXTERNAL_MODE={mode!r}")
    if mode == "finalize":
        finalize_verified_balance(float(os.environ["EVOVARIANT_MODAL_ENDING_BALANCE_USD"]))
        print(json.dumps(read_json(RUNTIME), indent=2, sort_keys=True))
        return
    if mode == "local-finalize":
        local_finalize()
        return
    start_balance = float(os.environ.get("EVOVARIANT_MODAL_STARTING_BALANCE_USD", "30.00"))
    if start_balance < SAFETY_STOP_USD:
        raise RuntimeError("verified starting credit is below the Modal safety stop")
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    _, records, audit = validate_manifest()
    plan = stable_plan(records, start_balance, mode)
    plan_path = RUN_ROOT / f"execution_plan_{mode.replace('-', '_')}.json"
    if plan_path.is_file() and mode != "dry-run":
        existing = read_json(plan_path)
        if any(existing.get(key) != plan.get(key) for key in ("model_revision", "manifest_file_sha256", "manifest_inner_sha256", "max_batch_variants")):
            raise RuntimeError("external execution plan changed across a resume")
    else:
        write_json(plan_path, plan)
    if mode == "dry-run":
        result = run_remote(mode, records, plan, start_balance)
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    result = run_remote(mode, records, plan, start_balance)
    if mode == "pilot":
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    load_local_helpers()
    evaluation = evaluate_external(records, result)
    comparator = audit_external_comparators(records)
    b11_b12 = audit_b11_b12()
    mavedb = audit_mavedb(records)
    comp_audit = audit_comparator()
    agreement = model_agreement(evaluation, comparator)
    drift = drift_analysis(evaluation)
    write_provenance(evaluation, result, audit, agreement)
    figures = make_external_figures(evaluation, evaluation["review_quality_subgroups"], evaluation["reliability"], agreement, result, drift)
    catalog = update_catalogs(evaluation, comparator, agreement, result, drift, mavedb, b11_b12, comp_audit, figures, local.git_value("rev-parse", "HEAD"))
    write_downloads(catalog)
    update_docs(evaluation, result, catalog["registry"], mavedb, comp_audit, b11_b12)
    update_notebook()
    print(json.dumps({"status": evaluation["status"], "n": evaluation["n"], "metrics": evaluation["metrics"], "registry_status_counts": catalog["registry"]["status_counts"], "raw_predictions_sha256": sha256_file(RAW_PREDICTIONS), "figure_count": len(figures)}, indent=2, sort_keys=True))


app = modal.App("evovariant-tr-external-benchmark-completion-v1")


@app.cls(
    image=EVO2_IMAGE,
    gpu=GPU_TYPE,
    volumes={"/root/.cache/huggingface": hf_cache},
    max_containers=1,
    retries=0,
    scaledown_window=120,
    timeout=1800,
    startup_timeout=1800,
)
class ExternalEvo2Worker:
    """Use the existing pinned Evo2 model contract for label-free external rows."""

    @modal.enter()
    def load_model(self) -> None:
        import _codecs

        import torch
        from evo2 import Evo2

        try:
            torch.serialization.add_safe_globals([_codecs.encode])
        except Exception:
            pass
        started = time.perf_counter()
        self.model = Evo2(MODEL_ID)
        torch.cuda.synchronize()
        self.model_load_seconds = time.perf_counter() - started
        self.gpu_name = str(torch.cuda.get_device_name(0))
        self.gpu_total_memory_bytes = int(torch.cuda.get_device_properties(0).total_memory)

    @modal.method()
    def score_batch(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        import resource

        import torch

        from modal import current_function_call_id

        if not rows or len(rows) > MAX_BATCH_VARIANTS:
            raise ValueError(f"external batch must contain 1..{MAX_BATCH_VARIANTS} rows")
        sequences: list[str] = []
        ids: list[str] = []
        for row in rows:
            if set(row) != {"normalized_variant_id", "sequences"}:
                raise ValueError("remote payload contains an unexpected field or label")
            if not isinstance(row["normalized_variant_id"], str) or not isinstance(row["sequences"], list) or len(row["sequences"]) != 4:
                raise ValueError("remote row requires an ID and four sequence views")
            if any(not isinstance(sequence, str) or len(sequence) != CONTEXT_LENGTH_BP for sequence in row["sequences"]):
                raise ValueError("remote sequence is not the frozen 8192-bp context")
            ids.append(row["normalized_variant_id"])
            sequences.extend(row["sequences"])
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        scores: list[float] = []
        with torch.inference_mode():
            for start in range(0, len(sequences), MODEL_SEQUENCE_BATCH_SIZE):
                values = list(self.model.score_sequences(sequences[start : start + MODEL_SEQUENCE_BATCH_SIZE]))
                if len(values) != len(sequences[start : start + MODEL_SEQUENCE_BATCH_SIZE]):
                    raise RuntimeError("Evo2 returned an incomplete sequence batch")
                scores.extend(float(value.item() if hasattr(value, "item") else value) for value in values)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        groups = [scores[index : index + 4] for index in range(0, len(scores), 4)]
        return {
            "status": "completed",
            "results": [{"normalized_variant_id": identity, "raw_scores": group} for identity, group in zip(ids, groups, strict=True)],
            "provenance": {
                "function_call_id": str(current_function_call_id()),
                "container_id": os.environ.get("MODAL_CONTAINER_ID"),
                "model_id": MODEL_ID,
                "checkpoint": MODEL_ID,
                "model_revision": MODEL_REVISION,
                "gpu_type": GPU_TYPE,
                "gpu_name": self.gpu_name,
                "context_length_bp": CONTEXT_LENGTH_BP,
                "orientation": "forward_and_reverse",
                "score_semantics": "alternate_minus_reference_log_likelihood",
                "model_sequence_batch_size": MODEL_SEQUENCE_BATCH_SIZE,
                "remote_method_seconds": float(elapsed),
                "variants_per_second": len(rows) / elapsed if elapsed else None,
                "model_load_seconds": float(self.model_load_seconds),
                "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
                "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved()),
                "gpu_total_memory_bytes": self.gpu_total_memory_bytes,
                "peak_container_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
                "all_scores_finite": bool(all(math.isfinite(value) for value in scores)),
                "labels_transported": False,
            },
        }


@app.local_entrypoint()
def entrypoint() -> None:
    main()


if __name__ == "__main__":
    main()
