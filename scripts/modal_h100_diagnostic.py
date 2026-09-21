"""Bounded H100/CUDA diagnostic with no model, volume, or Hugging Face access."""

from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path
from typing import Any

import modal

APP_NAME = "evovariant-tr-modal-h100-diagnostic"
ARTIFACT_PATH = Path("artifacts/modal_diagnostics/h100_cuda_probe_20260921.json")
BASE_IMAGE = (
    modal.Image.from_registry("nvcr.io/nvidia/pytorch:24.07-py3", add_python="3.12")
    .run_commands(
        "pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu124"
    )
)

app = modal.App(APP_NAME)


@app.function(
    image=BASE_IMAGE,
    gpu="H100",
    timeout=120,
    startup_timeout=120,
    retries=0,
)
def cuda_probe() -> dict[str, Any]:
    """Verify only CUDA allocation and a deterministic tensor operation."""

    import torch

    from modal import current_function_call_id

    started = time.perf_counter()
    if not torch.cuda.is_available():
        raise RuntimeError("torch.cuda.is_available() returned false")
    tensor = torch.tensor([1.0], device="cuda")
    result = tensor * 2.0
    torch.cuda.synchronize()
    return {
        "function_call_id": str(current_function_call_id()),
        "container_id": os.environ.get("MODAL_CONTAINER_ID"),
        "hostname": socket.gethostname(),
        "torch_version": str(torch.__version__),
        "cuda_runtime_version": str(torch.version.cuda),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_name": str(torch.cuda.get_device_name(0)),
        "compute_capability": [int(value) for value in torch.cuda.get_device_capability(0)],
        "device_count": int(torch.cuda.device_count()),
        "tensor_result": float(result.item()),
        "execution_latency_ms": (time.perf_counter() - started) * 1000,
    }


def _write(payload: dict[str, Any]) -> None:
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    call = cuda_probe.spawn()
    call_id = _call_id(call)
    try:
        result = call.get(timeout=120)
    except Exception as exc:  # noqa: BLE001 - diagnostic must preserve the exact failure.
        _write(
            {
                "artifact_id": "modal-h100-cuda-probe-20260921",
                "app_name": APP_NAME,
                "function": "cuda_probe",
                "gpu": "H100",
                "model_access": False,
                "volume": None,
                "hf_access": False,
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
            "artifact_id": "modal-h100-cuda-probe-20260921",
            "app_name": APP_NAME,
            "function": "cuda_probe",
            "gpu": "H100",
            "model_access": False,
            "volume": None,
            "hf_access": False,
            "function_call_id": call_id,
            "submitted_at_ns": submitted_at,
            "status": "PASS" if result["tensor_result"] == 2.0 else "FAIL",
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "result": result,
        }
    )
