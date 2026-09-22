"""Atomic, hash-bound records of completed adaptation stages."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .data import EXPECTED_LOCKED_MANIFEST_SHA256, EXPECTED_MANIFEST_SHA256
from .models import MODEL_REVISIONS

PROTOCOL = Path("research/adaptation/protocol.yaml")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_stage(
    state_path: str | Path,
    *,
    project_root: str | Path,
    stage: str,
    artifacts: Iterable[str | Path] = (),
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a stage only after its referenced artifacts exist and are hashed."""
    root = Path(project_root).resolve()
    state_file = Path(state_path)
    artifact_paths = [Path(path) for path in artifacts]
    missing = [str(path) for path in artifact_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"stage artifacts are missing: {missing}")
    git_head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    event = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "stage": stage,
        "git_head": git_head,
        "protocol_sha256": _sha256(root / PROTOCOL),
        "data_manifest_sha256": {
            **EXPECTED_MANIFEST_SHA256,
            "authoritative_locked_test_manifest.json": EXPECTED_LOCKED_MANIFEST_SHA256,
        },
        "model_revisions": MODEL_REVISIONS,
        "artifact_sha256": {str(path): _sha256(path) for path in artifact_paths},
        "details": details or {},
    }
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
    else:
        state = {"study_id": "POSTHOC-FOUNDATION-ADAPTATION-001", "history": []}
    state.setdefault("history", []).append(event)
    state["stage"] = stage
    state["latest"] = event
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_file.with_name(state_file.name + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, state_file)
    return event
