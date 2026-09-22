"""Atomic checkpoints and resumable run metadata."""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, cast


def save_checkpoint(
    path: str | Path,
    *,
    model: Any,
    optimizer: Any | None,
    epoch: int,
    metrics: dict[str, Any],
    protocol_hash: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    import torch

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "epoch": int(epoch),
        "metrics": metrics,
        "protocol_hash": protocol_hash,
        "metadata": metadata or {},
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict() if optimizer is not None else None,
        "python_random_state": random.getstate(),
        "torch_random_state": torch.get_rng_state(),
        "torch_cuda_random_state": torch.cuda.get_rng_state_all()
        if torch.cuda.is_available()
        else None,
    }
    temporary = target.with_name(target.name + ".tmp")
    torch.save(payload, temporary)
    os.replace(temporary, target)


def load_checkpoint(
    path: str | Path,
    *,
    model: Any,
    optimizer: Any | None = None,
    expected_protocol_hash: str | None = None,
    expected_metadata: dict[str, Any] | None = None,
    map_location: str = "cpu",
) -> dict[str, Any]:
    import torch

    payload = torch.load(Path(path), map_location=map_location)
    if expected_protocol_hash and payload.get("protocol_hash") != expected_protocol_hash:
        raise ValueError("checkpoint protocol hash mismatch")
    if expected_metadata and any(
        payload.get("metadata", {}).get(key) != value for key, value in expected_metadata.items()
    ):
        raise ValueError("checkpoint metadata mismatch")
    model.load_state_dict(payload["model"])
    if optimizer is not None and payload.get("optimizer") is not None:
        optimizer.load_state_dict(payload["optimizer"])
    if "python_random_state" in payload:
        random.setstate(payload["python_random_state"])
    if "torch_random_state" in payload:
        torch.set_rng_state(payload["torch_random_state"].cpu())
    if payload.get("torch_cuda_random_state") is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all([state.cpu() for state in payload["torch_cuda_random_state"]])
    return cast(dict[str, Any], payload)
