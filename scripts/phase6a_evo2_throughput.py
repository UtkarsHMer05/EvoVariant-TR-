#!/usr/bin/env python3
"""Run the bounded Phase6A Evo2 throughput and GPU comparison study.

The study sends only deterministic, unlabeled 8,192-bp sequence windows from
the authoritative locked cohort to a warm Modal worker.  It measures the
canonical Evo2 7B raw-score primitive in both orientations, without writing a
prediction cache or evaluating any label.  The same sample is tested at model
sequence batch sizes 1, 2, 4, and 8, with sample sizes 8, 16, and 32.  A
single H100 and one lower-cost A100-40GB comparison are attempted only while
the user-authorized Phase6A rate estimate remains below its safety margin.

Run through Modal only after the local cache/comparator preflight:

    .venv/bin/modal run scripts/phase6a_evo2_throughput.py
"""

from __future__ import annotations

import hashlib
import json
import resource
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import modal

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evovariant_tr.sequence_mutate import reverse_complement  # noqa: E402
from evovariant_tr.sequence_window import generate_reference_window  # noqa: E402

APPROVAL_PATH = REPO_ROOT / "artifacts/approvals/phase6a_throughput_20260921.json"
MANIFEST_PATH = REPO_ROOT / "research/ml_extension/splits/authoritative_locked_test_manifest.json"
REFERENCE_MANIFEST_PATH = REPO_ROOT / "data/manifests/grch38.json"
FASTA_PATH = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta"
FAI_PATH = REPO_ROOT / "data/reference/Homo_sapiens_assembly38.fasta.fai"
OUTPUT_PATH = REPO_ROOT / "artifacts/phase6a/phase6a_evo2_throughput_20260921.json"
LEDGER_PATH = REPO_ROOT / "research/runs/cost_ledger.jsonl"

EXPECTED_PROTOCOL_HASH = "39de386dcf952af0b4d03de770b68ad2c44d49a113510cafab184d6eebc0c6e3"
LOCKED_MANIFEST_SHA256 = "9f9e052d21f4a6a32f595cb20f48cb81e033c0481942820d04f9b67d410a16cb"
LOCKED_RECORD_SET_SHA256 = "ae4f6f1c1ad7c8d9ea78a9e5ce0380b1d8862a125592be5474b7826de165a6a0"
EVO2_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"
CONTEXT_LENGTH_BP = 8192
MODEL_ID = "evo2_7b"
MODEL_SEQUENCE_BATCH_SIZES = (1, 2, 4, 8)
SAMPLE_SIZES = (8, 16, 32)
GPU_TYPES = ("H100", "A100-40GB")
GPU_RATES_USD_PER_HOUR = {"H100": 3.95, "A100-40GB": 2.0988}
MODAL_PRICING_SOURCE = "https://modal.com/pricing"
MAX_RATE_ESTIMATE_USD = 1.25
AUTHORIZATION_CAP_USD = 1.50

BASE_IMAGE = modal.Image.from_registry("nvcr.io/nvidia/pytorch:24.07-py3", add_python="3.12")
EVO2_IMAGE = (
    BASE_IMAGE.apt_install(
        [
            "build-essential",
            "cmake",
            "ninja-build",
            "git",
            "gcc",
            "g++",
            "clang",
            "libclang-dev",
        ]
    )
    .run_commands(
        "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124",
        "git clone --recurse-submodules https://github.com/ArcInstitute/evo2.git evo2 "
        f"&& cd evo2 && git checkout {EVO2_REVISION} "
        "&& git submodule update --init --recursive && pip install .",
    )
    .run_commands(
        "pip uninstall -y transformer-engine transformer_engine",
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

app = modal.App("evovariant-tr", image=EVO2_IMAGE)
hf_cache = modal.Volume.from_name("hf_cache", create_if_missing=False)
VOLUMES = {"/root/.cache/huggingface": hf_cache}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _billing_snapshot() -> dict[str, Any]:
    """Capture the provider summary without interpreting it as per-request spend."""
    modal_binary = shutil.which("modal") or str(Path(sys.executable).with_name("modal"))
    try:
        result = subprocess.run(
            [modal_binary, "billing", "summary"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "command": "modal billing summary",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "captured_at_utc": datetime.now(UTC).isoformat(),
            "command": "modal billing summary",
            "returncode": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}:{exc}",
        }


def _load_approval() -> dict[str, Any]:
    approval_value = json.loads(APPROVAL_PATH.read_text(encoding="utf-8"))
    if not isinstance(approval_value, dict):
        raise ValueError("Phase6A approval artifact must be a JSON object")
    approval = cast(dict[str, Any], approval_value)
    if approval.get("protocol_hash") != EXPECTED_PROTOCOL_HASH:
        raise RuntimeError("Phase6A approval protocol hash does not match the current protocol")
    if float(approval.get("max_budget_usd", 0)) != AUTHORIZATION_CAP_USD:
        raise RuntimeError("Phase6A approval cap must be exactly the user-authorized 1.50 USD")
    if int(approval.get("sample_limit", 0)) != 32:
        raise RuntimeError("Phase6A approval sample limit must be 32")
    scope = str(approval.get("run_scope", ""))
    if "Phase6A" not in scope or "no full 946-record Evo2 benchmark" not in scope:
        raise RuntimeError("approval scope does not authorize only bounded Phase6A work")
    return approval


def _load_sample() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = manifest.get("records")
    if not isinstance(rows, list) or len(rows) != 946:
        raise ValueError("authoritative locked manifest must contain exactly 946 records")
    if _sha256_file(MANIFEST_PATH) != LOCKED_MANIFEST_SHA256:
        raise ValueError("locked manifest SHA-256 changed before Phase6A throughput")
    if _canonical_hash(rows) != LOCKED_RECORD_SET_SHA256:
        raise ValueError("locked record-set SHA-256 changed before Phase6A throughput")
    ranked = sorted(
        (row for row in rows if isinstance(row, dict)),
        key=lambda row: hashlib.sha256(str(row["normalized_variant_id"]).encode()).hexdigest(),
    )
    selected = ranked[:32]
    payload: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []
    for row in selected:
        chromosome = str(row["chromosome"])
        window = None
        lookup_chromosome = chromosome
        for candidate in (chromosome, f"chr{chromosome}"):
            try:
                window = generate_reference_window(
                    FASTA_PATH,
                    FAI_PATH,
                    candidate,
                    int(row["position_1based"]),
                )
                lookup_chromosome = candidate
                break
            except ValueError:
                continue
        if window is None:
            raise ValueError(f"could not load reference window for {row['normalized_variant_id']}")
        if len(window.ref_sequence) != CONTEXT_LENGTH_BP:
            raise ValueError("reference window is not the frozen 8192-bp context")
        if window.ref_sequence[window.variant_offset] != str(row["reference"]):
            raise ValueError(f"reference base mismatch for {row['normalized_variant_id']}")
        alternate = (
            window.ref_sequence[: window.variant_offset]
            + str(row["alternate"])
            + window.ref_sequence[window.variant_offset + 1 :]
        )
        sequences = [
            window.ref_sequence,
            alternate,
            reverse_complement(window.ref_sequence),
            reverse_complement(alternate),
        ]
        if any(len(sequence) != CONTEXT_LENGTH_BP for sequence in sequences):
            raise ValueError("throughput sample contains a non-8192-bp sequence")
        payload.append(
            {
                "normalized_variant_id": row["normalized_variant_id"],
                "sequences": sequences,
            }
        )
        metadata_rows.append(
            {
                "normalized_variant_id": row["normalized_variant_id"],
                "reference_chromosome_used": lookup_chromosome,
                "window_start_1based": window.start,
                "window_stop_1based": window.stop,
                "variant_offset_0based": window.variant_offset,
                "sequence_sha256": hashlib.sha256(
                    json.dumps(sequences, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            }
        )
    return payload, {
        "sampling_rule": (
            "SHA-256 rank of normalized_variant_id, ascending; labels are not read or "
            "sent to Modal"
        ),
        "sample_size_max": len(payload),
        "selected_rows": metadata_rows,
        "reference_manifest_path": str(REFERENCE_MANIFEST_PATH.relative_to(REPO_ROOT)),
        "reference_manifest_sha256": _sha256_file(REFERENCE_MANIFEST_PATH),
        "fasta_sha256": _sha256_file(FASTA_PATH),
        "fai_sha256": _sha256_file(FAI_PATH),
    }


class _Evo2ThroughputBase:
    """Shared implementation kept undecorated for Modal class wrappers."""

    gpu_type: str
    gpu_rate_usd_per_hour: float

    def _load_model(self) -> None:
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
        self.invocation_count = 0
        self.gpu_name = torch.cuda.get_device_name(0)
        self.gpu_total_memory_bytes = int(torch.cuda.get_device_properties(0).total_memory)
        self.gpu_memory_at_load_bytes = int(torch.cuda.memory_allocated())

    def _run_config(self, sample: list[dict[str, Any]], batch_size: int) -> dict[str, Any]:
        import torch

        if batch_size not in MODEL_SEQUENCE_BATCH_SIZES:
            raise ValueError(f"unsupported model sequence batch size: {batch_size}")
        if not sample or len(sample) > 32:
            raise ValueError("Phase6A sample must contain between 1 and 32 variants")
        sequences: list[str] = []
        for row in sample:
            row_sequences = row.get("sequences")
            if not isinstance(row_sequences, list) or len(row_sequences) != 4:
                raise ValueError("each sample row must contain four orientation sequences")
            if any(
                not isinstance(sequence, str) or len(sequence) != CONTEXT_LENGTH_BP
                for sequence in row_sequences
            ):
                raise ValueError("all model inputs must be exact 8192-bp strings")
            sequences.extend(row_sequences)

        self.invocation_count += 1
        cold_container = self.invocation_count == 1
        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        scores: list[float] = []
        with torch.inference_mode():
            for start in range(0, len(sequences), batch_size):
                raw = self.model.score_sequences(sequences[start : start + batch_size])
                values = list(raw)
                if len(values) != min(batch_size, len(sequences) - start):
                    raise RuntimeError("Evo2 returned a score count different from the input batch")
                for value in values:
                    scores.append(float(value.item() if hasattr(value, "item") else value))
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - started
        scores_json = json.dumps(scores, separators=(",", ":"), allow_nan=False).encode("utf-8")
        memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        rate = float(self.gpu_rate_usd_per_hour)
        return {
            "status": "PASS",
            "gpu_type": self.gpu_type,
            "gpu_name": self.gpu_name,
            "checkpoint": MODEL_ID,
            "model_revision": EVO2_REVISION,
            "context_length_bp": CONTEXT_LENGTH_BP,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
            "sample_variants": len(sample),
            "sequence_count": len(sequences),
            "model_sequence_batch_size": batch_size,
            "model_batches": (len(sequences) + batch_size - 1) // batch_size,
            "cold_container": cold_container,
            "container_invocation_index": self.invocation_count,
            "model_load_seconds": round(float(self.model_load_seconds), 6),
            "remote_method_seconds": round(elapsed, 6),
            "variants_per_second": round(len(sample) / elapsed, 6),
            "seconds_per_variant": round(elapsed / len(sample), 6),
            "peak_gpu_memory_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "peak_gpu_memory_reserved_bytes": int(torch.cuda.max_memory_reserved()),
            "gpu_memory_at_model_load_bytes": int(self.gpu_memory_at_load_bytes),
            "gpu_total_memory_bytes": int(self.gpu_total_memory_bytes),
            "gpu_memory_margin_bytes": int(
                self.gpu_total_memory_bytes - torch.cuda.max_memory_reserved()
            ),
            "peak_container_rss_bytes": int(memory),
            "all_scores_finite": all(torch.isfinite(torch.tensor(scores)).tolist()),
            "score_output_sha256": hashlib.sha256(scores_json).hexdigest(),
            "estimated_gpu_rate_cost_usd": round(elapsed / 3600.0 * rate, 6),
            "pricing_source": MODAL_PRICING_SOURCE,
            "gpu_rate_usd_per_hour": rate,
        }


@app.cls(
    gpu="H100",
    volumes=VOLUMES,  # type: ignore[arg-type]
    max_containers=1,
    retries=0,
    scaledown_window=120,
    timeout=900,
)
class H100Evo2Throughput(_Evo2ThroughputBase):
    """Canonical H100 throughput worker."""

    gpu_type = "H100"
    gpu_rate_usd_per_hour = GPU_RATES_USD_PER_HOUR[gpu_type]

    @modal.enter()
    def load_model(self) -> None:
        self._load_model()

    @modal.method()
    def run_config(self, sample: list[dict[str, Any]], batch_size: int) -> dict[str, Any]:
        return self._run_config(sample, batch_size)


@app.cls(
    gpu="A100-40GB",
    volumes=VOLUMES,  # type: ignore[arg-type]
    max_containers=1,
    retries=0,
    scaledown_window=120,
    timeout=900,
)
class A100Evo2Throughput(_Evo2ThroughputBase):
    """Lower-cost A100 comparison worker."""

    gpu_type = "A100-40GB"
    gpu_rate_usd_per_hour = GPU_RATES_USD_PER_HOUR[gpu_type]

    @modal.enter()
    def load_model(self) -> None:
        self._load_model()

    @modal.method()
    def run_config(self, sample: list[dict[str, Any]], batch_size: int) -> dict[str, Any]:
        return self._run_config(sample, batch_size)


def _append_ledger(entry: dict[str, Any]) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _estimate_full_cohort(results: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [row for row in results if row.get("status") == "PASS"]
    by_gpu: dict[str, list[dict[str, Any]]] = {}
    for row in completed:
        by_gpu.setdefault(str(row["gpu_type"]), []).append(row)
    estimates: dict[str, Any] = {}
    for gpu_type, rows in by_gpu.items():
        best = max(rows, key=lambda row: float(row["variants_per_second"]))
        throughput = float(best["variants_per_second"])
        model_seconds = float(best["model_load_seconds"]) + 946.0 / throughput
        rate = float(best["gpu_rate_usd_per_hour"])
        estimates[gpu_type] = {
            "best_sample_variants": best["sample_variants"],
            "best_model_sequence_batch_size": best["model_sequence_batch_size"],
            "measured_variants_per_second": throughput,
            "estimated_warm_plus_one_model_load_seconds_for_946": round(model_seconds, 3),
            "estimated_rate_cost_usd_for_946": round(model_seconds / 3600.0 * rate, 4),
            "basis": (
                "measured bounded model-only sequence throughput; excludes full-cohort reference "
                "preparation, network, image build, and cache writes; no 946-record inference "
                "was run"
            ),
        }
    return estimates


@app.local_entrypoint()
def main() -> None:
    """Prepare the sample, run bounded GPU configurations, and persist evidence."""
    approval = _load_approval()
    for required in (MANIFEST_PATH, REFERENCE_MANIFEST_PATH, FASTA_PATH, FAI_PATH):
        if not required.is_file():
            raise FileNotFoundError(f"missing Phase6A input: {required}")
    sample, sample_metadata = _load_sample()
    billing_before = _billing_snapshot()
    started_study = time.monotonic()
    results: list[dict[str, Any]] = []
    cumulative_estimate = 0.0
    stop_reason = "all approved bounded configurations completed"

    for gpu_type, service_class in (
        ("H100", H100Evo2Throughput),
        ("A100-40GB", A100Evo2Throughput),
    ):
        service = service_class()
        for sample_size in SAMPLE_SIZES:
            for batch_size in MODEL_SEQUENCE_BATCH_SIZES:
                if cumulative_estimate >= MAX_RATE_ESTIMATE_USD:
                    stop_reason = "stopped before the Phase6A safety margin was exceeded"
                    break
                call_started = time.monotonic()
                try:
                    result = dict(service.run_config.remote(sample[:sample_size], batch_size))
                    result["client_wall_seconds"] = round(time.monotonic() - call_started, 6)
                    result["client_wall_rate_estimate_usd"] = round(
                        result["client_wall_seconds"] / 3600.0 * GPU_RATES_USD_PER_HOUR[gpu_type],
                        6,
                    )
                    cumulative_estimate += float(result["client_wall_rate_estimate_usd"])
                except Exception as exc:  # noqa: BLE001 - preserve bounded failure evidence
                    client_seconds = time.monotonic() - call_started
                    estimate = client_seconds / 3600.0 * GPU_RATES_USD_PER_HOUR[gpu_type]
                    cumulative_estimate += estimate
                    result = {
                        "status": "FAILED_CONFIG",
                        "gpu_type": gpu_type,
                        "sample_variants": sample_size,
                        "model_sequence_batch_size": batch_size,
                        "client_wall_seconds": round(client_seconds, 6),
                        "client_wall_rate_estimate_usd": round(estimate, 6),
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                results.append(result)
                print(json.dumps(result, sort_keys=True))
            if cumulative_estimate >= MAX_RATE_ESTIMATE_USD:
                break
        if cumulative_estimate >= MAX_RATE_ESTIMATE_USD:
            break

    billing_after = _billing_snapshot()
    completed = [row for row in results if row.get("status") == "PASS"]
    failure_count = len(results) - len(completed)
    artifact = {
        "artifact_id": "phase6a-evo2-throughput-20260921",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": "PASS_BOUNDED_THROUGHPUT" if completed else "FAILED_NO_COMPLETED_CONFIG",
        "protocol_hash": EXPECTED_PROTOCOL_HASH,
        "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
        "approval_scope": approval["run_scope"],
        "authorization": {
            "max_budget_usd": AUTHORIZATION_CAP_USD,
            "safety_margin_rate_estimate_usd": MAX_RATE_ESTIMATE_USD,
            "cumulative_client_wall_rate_estimate_usd": round(cumulative_estimate, 6),
            "stop_reason": stop_reason,
        },
        "locked_cohort": {
            "manifest": str(MANIFEST_PATH.relative_to(REPO_ROOT)),
            "manifest_sha256": LOCKED_MANIFEST_SHA256,
            "record_set_sha256": LOCKED_RECORD_SET_SHA256,
            "total_records": 946,
            "inference_target_records": 0,
            "sample_is_unlabeled": True,
            "sample_metadata": sample_metadata,
        },
        "model": {
            "model_id": MODEL_ID,
            "model_revision": EVO2_REVISION,
            "checkpoint": MODEL_ID,
            "assembly": "GRCh38",
            "context_length_bp": CONTEXT_LENGTH_BP,
            "orientation": "forward_and_reverse",
            "score_semantics": "alternate_minus_reference_log_likelihood",
            "sequence_batch_sizes_tested": list(MODEL_SEQUENCE_BATCH_SIZES),
            "sample_sizes_tested": sorted({int(row["sample_variants"]) for row in results}),
            "duplicate_sequence_or_cache_reuse": (
                "none; each remote config bypassed prediction cache and scored the supplied "
                "sequence payload directly"
            ),
        },
        "gpu_pricing": {
            "source": MODAL_PRICING_SOURCE,
            "rates_usd_per_hour": GPU_RATES_USD_PER_HOUR,
            "note": (
                "Rate estimates are not a Modal per-request invoice; workspace billing "
                "snapshots are recorded separately."
            ),
        },
        "results": results,
        "summary": {
            "completed_configurations": len(completed),
            "failed_configurations": failure_count,
            "full_946_estimates": _estimate_full_cohort(results),
            "recommendation": (
                "Select the lowest estimated USD per variant among scientifically valid completed "
                "configs, subject to memory margin and reliability. Do not launch full Phase6 "
                "from this artifact."
            ),
        },
        "modal_billing": {
            "before": billing_before,
            "after": billing_after,
            "pilot_reference": "artifacts/modal/phase2_phase4_pilot_20260921_success.json",
            "billed_cost_interpretation": (
                "The CLI summary is workspace-level and may include deployed apps, volumes, "
                "image/container activity, and prior work; no per-request billed USD is "
                "asserted unless the provider exposes it."
            ),
        },
        "prior_phase6a_attempts": [
            {
                "run_url": "https://modal.com/apps/utkarshmer05/main/ap-k0MkCjWZrmpygC1LVKEpcM",
                "status": "ABORTED_BEFORE_GPU_WORKER",
                "failure": (
                    "image build dependency resolution for unnecessary container-side "
                    "modal/requests installation"
                ),
                "inference_started": False,
            },
            {
                "run_url": "https://modal.com/apps/utkarshmer05/main/ap-wIkvWNAz4qRobWPs9NTCga",
                "status": "ABORTED_BEFORE_MODEL_LOAD",
                "failure": (
                    "worker hydration failed because evovariant_tr was not included in the "
                    "image"
                ),
                "inference_started": False,
            },
        ],
        "phase_boundary": {
            "phase6_started": False,
            "phase7_started": False,
            "full_locked_test_evaluation": False,
            "training_hpo_finetuning": False,
        },
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _append_ledger(
        {
            "approval_artifact": str(APPROVAL_PATH.relative_to(REPO_ROOT)),
            "backend": "modal",
            "cache_hit": False,
            "estimated_seconds": round(time.monotonic() - started_study, 6),
            "estimated_usd": round(cumulative_estimate, 6),
            "gpu_count": 1,
            "gpu_type": "H100+A100-40GB comparison",
            "measured_seconds": None,
            "measured_usd": None,
            "notes": (
                "Phase6A bounded throughput only; no full cohort, labels, training, HPO, "
                "fine-tuning, or locked evaluation."
            ),
            "run_id": "phase6a-evo2-throughput-20260921",
            "status": "COMPLETED" if completed else "FAILED",
            "timestamp": datetime.now(UTC).isoformat(),
            "workload": "evo2_modal_phase6a_throughput",
        }
    )
    print(json.dumps({"artifact": str(OUTPUT_PATH), "status": artifact["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
