"""Atomic checkpoints and resumable run metadata."""

from __future__ import annotations

import os
import random
import shutil
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from .data import sha256_file


def check_sqlite_database(path: str | Path) -> None:
    """Check a local SQLite copy, never the mounted Drive file."""
    database = Path(path)
    with closing(sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True)) as conn:
        result = conn.execute("PRAGMA integrity_check").fetchone()
    if result != ("ok",):
        raise RuntimeError(f"SQLite integrity check failed for {database}: {result}")


def restore_hpo_database(drive_database: str | Path, local_database: str | Path) -> Path | None:
    """Restore a verified Drive snapshot to local disk; retain the legacy DB as evidence."""
    drive_database = Path(drive_database)
    local_database = Path(local_database)
    if local_database.exists():
        try:
            check_sqlite_database(local_database)
            return local_database
        except (RuntimeError, sqlite3.DatabaseError):
            forensic = local_database.with_name(
                local_database.name + ".forensic_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            )
            os.replace(local_database, forensic)
    snapshot = drive_database.with_name(drive_database.name + ".snapshot")
    local_database.parent.mkdir(parents=True, exist_ok=True)
    for source in (snapshot, drive_database):
        if not source.exists():
            continue
        shutil.copyfile(source, local_database)
        try:
            check_sqlite_database(local_database)
        except (RuntimeError, sqlite3.DatabaseError):
            forensic = source.with_name(
                source.name + ".forensic_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            )
            shutil.copyfile(source, forensic)
            local_database.unlink()
            continue
        return source
    if snapshot.exists() or drive_database.exists():
        raise RuntimeError(
            "no valid HPO SQLite snapshot; reconstruct from checkpoints before training"
        )
    return None


def snapshot_hpo_database(local_database: str | Path, drive_database: str | Path) -> Path:
    """Back up active SQLite to local disk, then atomically replace the Drive snapshot."""
    local_database = Path(local_database)
    snapshot = Path(drive_database).with_name(Path(drive_database).name + ".snapshot")
    temporary_local = local_database.with_name(local_database.name + ".backup.tmp")
    temporary_drive = snapshot.with_name(snapshot.name + ".tmp")
    try:
        temporary_local.unlink(missing_ok=True)
        with closing(sqlite3.connect(local_database)) as source:
            with closing(sqlite3.connect(temporary_local)) as target:
                source.backup(target)
        check_sqlite_database(temporary_local)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(temporary_local, temporary_drive)
        if sha256_file(temporary_local) != sha256_file(temporary_drive):
            raise RuntimeError("Drive SQLite snapshot copy hash mismatch")
        os.replace(temporary_drive, snapshot)
    finally:
        temporary_local.unlink(missing_ok=True)
        temporary_drive.unlink(missing_ok=True)
    return snapshot


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
