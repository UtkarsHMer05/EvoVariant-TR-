"""Bounded Modal transport diagnostic with no model, GPU, or volume access."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any

import modal

APP_NAME = "evovariant-tr-modal-transport-diagnostic"
ARTIFACT_DIR = Path("artifacts/modal_diagnostics")
DETACHED_SUBMISSION = ARTIFACT_DIR / "cpu_detached_submission_20260921.json"
DETACHED_RESULT = ARTIFACT_DIR / "cpu_detached_result_20260921.json"

app = modal.App(APP_NAME)
image = modal.Image.debian_slim(python_version="3.12")


@app.function(image=image, timeout=120, retries=0)
def cpu_echo(value: int) -> dict[str, Any]:
    """Return deterministic data while exposing only transport diagnostics."""

    from modal import current_function_call_id

    return {
        "value": value,
        "double": value * 2,
        "function_call_id": current_function_call_id(),
        "hostname": socket.gethostname(),
        "python_version": sys.version.split()[0],
        "remote_finished_ns": time.time_ns(),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _call_id(call: modal.FunctionCall[Any]) -> str:
    call.hydrate()
    object_id = call.object_id
    if not object_id:
        raise RuntimeError("Modal did not return a FunctionCall object ID")
    return object_id


def run_cpu_round_trip() -> None:
    values = [0, 1, 7, 64]
    records: list[dict[str, Any]] = []
    for value in values:
        submitted_at = time.time_ns()
        started = time.perf_counter()
        call = cpu_echo.spawn(value)
        call_id = _call_id(call)
        submission_latency_ms = (time.perf_counter() - started) * 1000
        try:
            result = call.get(timeout=120)
        except Exception as exc:  # noqa: BLE001 - diagnostic must preserve the exact failure.
            records.append(
                {
                    "value": value,
                    "function_call_id": call_id,
                    "submitted_at_ns": submitted_at,
                    "submission_latency_ms": submission_latency_ms,
                    "return_latency_ms": None,
                    "status": "FAIL",
                    "exception": f"{type(exc).__name__}: {exc}",
                }
            )
            raise
        records.append(
            {
                "value": value,
                "function_call_id": call_id,
                "submitted_at_ns": submitted_at,
                "submission_latency_ms": submission_latency_ms,
                "return_latency_ms": (time.perf_counter() - started) * 1000,
                "status": "PASS" if result.get("double") == value * 2 else "FAIL",
                "result": result,
            }
        )

    _write_json(
        ARTIFACT_DIR / "cpu_trivial_round_trip_20260921.json",
        {
            "artifact_id": "modal-cpu-trivial-round-trip-20260921",
            "app_name": APP_NAME,
            "function": "cpu_echo",
            "image": "modal.Image.debian_slim(python_version='3.12')",
            "gpu": None,
            "volume": None,
            "hf_access": False,
            "model_access": False,
            "values": values,
            "records": records,
            "status": "PASS",
        },
    )


def submit_detached() -> None:
    submitted_at = time.time_ns()
    value = 20260921
    call = cpu_echo.spawn(value)
    call_id = _call_id(call)
    _write_json(
        DETACHED_SUBMISSION,
        {
            "artifact_id": "modal-cpu-detached-submission-20260921",
            "app_name": APP_NAME,
            "function": "cpu_echo",
            "value": value,
            "function_call_id": call_id,
            "submitted_at_ns": submitted_at,
            "detach_mechanism": "modal run --detach",
            "status": "SUBMITTED",
        },
    )
    print(json.dumps({"function_call_id": call_id, "submission": str(DETACHED_SUBMISSION)}))


def retrieve_detached() -> None:
    submission = json.loads(DETACHED_SUBMISSION.read_text(encoding="utf-8"))
    started = time.perf_counter()
    call = modal.FunctionCall.from_id(submission["function_call_id"])
    try:
        result = call.get(timeout=120)
    except Exception as exc:  # noqa: BLE001 - diagnostic must preserve the exact failure.
        _write_json(
            DETACHED_RESULT,
            {
                "artifact_id": "modal-cpu-detached-result-20260921",
                "submission": submission,
                "status": "FAIL",
                "return_latency_ms": (time.perf_counter() - started) * 1000,
                "exception": f"{type(exc).__name__}: {exc}",
            },
        )
        raise
    _write_json(
        DETACHED_RESULT,
        {
            "artifact_id": "modal-cpu-detached-result-20260921",
            "submission": submission,
            "status": "PASS" if result.get("double") == submission["value"] * 2 else "FAIL",
            "return_latency_ms": (time.perf_counter() - started) * 1000,
            "result": result,
        },
    )


@app.local_entrypoint()
def main() -> None:
    mode = os.environ.get("EVOVARIANT_TR_DIAGNOSTIC_MODE", "round-trip")
    if mode == "detached":
        submit_detached()
    elif mode == "round-trip":
        run_cpu_round_trip()
    else:
        raise SystemExit(f"Unsupported EVOVARIANT_TR_DIAGNOSTIC_MODE={mode!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retrieve-detached", action="store_true")
    args = parser.parse_args()
    if args.retrieve_detached:
        retrieve_detached()
    else:
        raise SystemExit("Use modal run for --mode round-trip or --mode detached")
