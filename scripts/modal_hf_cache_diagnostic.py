"""Read-only Modal probe for the existing Hugging Face cache volume."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import modal

APP_NAME = "evovariant-tr-modal-hf-cache-diagnostic"
ARTIFACT_PATH = Path("artifacts/modal_diagnostics/hf_cache_read_20260921.json")
HF_CACHE_PATH = "/root/.cache/huggingface"
MODEL_CACHE_RELATIVE = Path("hub/models--arcinstitute--evo2_7b")
EXPECTED_MODEL = "evo2_7b"

app = modal.App(APP_NAME)
hf_cache = modal.Volume.from_name("hf_cache", create_if_missing=False)


@app.function(
    image=modal.Image.debian_slim(python_version="3.12"),
    volumes={HF_CACHE_PATH: hf_cache},
    timeout=120,
    retries=0,
)
def cache_probe() -> dict[str, Any]:
    """Inspect only existing paths and small metadata files; never write or download."""

    root = Path(HF_CACHE_PATH)
    model_root = root / MODEL_CACHE_RELATIVE
    refs_main = model_root / "refs" / "main"
    snapshot_root = model_root / "snapshots"
    snapshot_dirs = sorted(path for path in snapshot_root.iterdir() if path.is_dir())
    snapshots: list[dict[str, Any]] = []
    for snapshot in snapshot_dirs:
        entries: list[dict[str, Any]] = []
        for path in sorted(snapshot.iterdir()):
            entry: dict[str, Any] = {
                "relative_path": str(path.relative_to(root)),
                "is_file": bool(path.is_file()),
                "is_symlink": bool(path.is_symlink()),
            }
            if path.is_symlink():
                entry["link_target"] = os.readlink(path)
            if path.is_file():
                entry["size_bytes"] = int(path.stat().st_size)
            entries.append(entry)
        snapshots.append(
            {
                "snapshot_revision": snapshot.name,
                "entries": entries,
            }
        )

    ref_value = refs_main.read_text(encoding="utf-8").strip()
    metadata: dict[str, Any] = {}
    for snapshot in snapshot_dirs:
        config_path = snapshot / "config.json"
        if config_path.is_file():
            parsed = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                metadata = {
                    "keys": sorted(str(key) for key in parsed),
                    "model_type": parsed.get("model_type"),
                    "architectures": parsed.get("architectures"),
                }
            break

    checkpoint_paths = [snapshot / "evo2_7b.pt" for snapshot in snapshot_dirs]
    config_paths = [snapshot / "config.json" for snapshot in snapshot_dirs]
    checkpoint_readable = any(
        path.is_file() and path.stat().st_size > 0 for path in checkpoint_paths
    )
    config_readable = any(path.is_file() and path.stat().st_size > 0 for path in config_paths)
    return {
        "status": "PASS" if checkpoint_readable and config_readable and ref_value else "FAIL",
        "cache_root": str(root),
        "model": EXPECTED_MODEL,
        "model_cache_path": str(MODEL_CACHE_RELATIVE),
        "model_cache_exists": bool(model_root.is_dir()),
        "refs_main": ref_value,
        "snapshot_count": int(len(snapshots)),
        "snapshots": snapshots,
        "metadata": metadata,
        "checkpoint_readable": bool(checkpoint_readable),
        "config_readable": bool(config_readable),
        "structurally_valid": bool(
            model_root.is_dir()
            and refs_main.is_file()
            and snapshot_dirs
            and checkpoint_readable
            and config_readable
        ),
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
    call = cache_probe.spawn()
    call_id = _call_id(call)
    try:
        result = call.get(timeout=120)
    except Exception as exc:  # noqa: BLE001 - preserve exact remote failure
        _write(
            {
                "artifact_id": "modal-hf-cache-read-20260921",
                "app_name": APP_NAME,
                "function": "cache_probe",
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
            "artifact_id": "modal-hf-cache-read-20260921",
            "app_name": APP_NAME,
            "function": "cache_probe",
            "volume": "hf_cache",
            "function_call_id": call_id,
            "submitted_at_ns": submitted_at,
            "status": result["status"],
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "result": result,
        }
    )


if __name__ == "__main__":
    main()
