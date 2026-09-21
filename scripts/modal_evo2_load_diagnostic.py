"""Load-only Modal diagnostic for the pinned Evo2 7B checkpoint."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import modal

APP_NAME = "evovariant-tr-modal-evo2-load-diagnostic"
ARTIFACT_PATH = Path("artifacts/modal_diagnostics/evo2_load_20260921.json")
MODEL_NAME = "evo2_7b"
MODEL_REVISION = "4b509ec2a22d6de472659f908bcb0714265ad3a7"
GPU_TYPE = "H100"
HF_CACHE_PATH = "/root/.cache/huggingface"
EVO2_CACHE_PATH = (
    Path(HF_CACHE_PATH) / "hub" / "models--arcinstitute--evo2_7b"
)

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
        f"&& cd evo2 && git checkout {MODEL_REVISION} "
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

app = modal.App(APP_NAME)
hf_cache = modal.Volume.from_name("hf_cache", create_if_missing=False)


def _first_parameter(model: Any) -> Any:
    parameters = getattr(model, "parameters", None)
    if callable(parameters):
        return next(parameters(), None)
    inner = getattr(model, "model", None)
    parameters = getattr(inner, "parameters", None)
    if callable(parameters):
        return next(parameters(), None)
    return None


@app.function(
    image=EVO2_IMAGE,
    gpu=GPU_TYPE,
    volumes={HF_CACHE_PATH: hf_cache},
    timeout=1200,
    startup_timeout=1200,
    retries=0,
)
def load_probe() -> dict[str, Any]:
    """Load Evo2 without scoring or constructing a cohort request."""

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    import _codecs

    import torch
    from evo2 import Evo2

    try:
        torch.serialization.add_safe_globals([_codecs.encode])
    except Exception:
        pass

    cache_checkpoint = EVO2_CACHE_PATH / "snapshots"
    cache_hit = bool(EVO2_CACHE_PATH.is_dir() and any(cache_checkpoint.iterdir()))
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    model = Evo2(MODEL_NAME)
    torch.cuda.synchronize()
    parameter = _first_parameter(model)
    dtype = str(getattr(parameter, "dtype", "unknown"))
    load_seconds = time.perf_counter() - started
    return {
        "loaded": True,
        "model_name": MODEL_NAME,
        "revision": MODEL_REVISION,
        "device": "cuda:0",
        "dtype": dtype,
        "load_seconds": float(load_seconds),
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "cache_hit": bool(cache_hit),
        "gpu_name": str(torch.cuda.get_device_name(0)),
        "torch_version": str(torch.__version__),
        "cuda_runtime_version": str(torch.version.cuda),
    }


def _write(payload: dict[str, Any]) -> None:
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _call_id(call: modal.FunctionCall[Any]) -> str:
    call.hydrate()
    object_id = call.object_id
    if not object_id:
        raise RuntimeError("Modal did not return a FunctionCall object ID")
    return object_id


@app.local_entrypoint()
def main() -> None:
    started = time.perf_counter()
    submitted_at = time.time_ns()
    call = load_probe.spawn()
    call_id = _call_id(call)
    try:
        result = call.get(timeout=1200)
    except Exception as exc:  # noqa: BLE001 - preserve exact remote failure
        _write(
            {
                "artifact_id": "modal-evo2-load-20260921",
                "app_name": APP_NAME,
                "function": "load_probe",
                "model_name": MODEL_NAME,
                "revision": MODEL_REVISION,
                "gpu": GPU_TYPE,
                "volume": "hf_cache",
                "function_call_id": call_id,
                "submitted_at_ns": submitted_at,
                "status": "FAIL",
                "elapsed_ms": (time.perf_counter() - started) * 1000,
                "exception": f"{type(exc).__name__}: {exc}",
            }
        )
        raise
    _write(
        {
            "artifact_id": "modal-evo2-load-20260921",
            "app_name": APP_NAME,
            "function": "load_probe",
            "model_name": MODEL_NAME,
            "revision": MODEL_REVISION,
            "gpu": GPU_TYPE,
            "volume": "hf_cache",
            "function_call_id": call_id,
            "submitted_at_ns": submitted_at,
            "status": "PASS" if result.get("loaded") is True else "FAIL",
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "result": result,
        }
    )


if __name__ == "__main__":
    main()
