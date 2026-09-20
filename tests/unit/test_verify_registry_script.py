"""Tests for scripts/verify_registry.py (Milestone 20).

Exercises the script's failure paths against tiny on-disk fixtures:
- a corrupt run record must be reported;
- a malformed event log must be reported;
- a missing registry dir is a clean no-op.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify_registry.py"


def _run(
    registry_dir: Path, *, repo_root: Path | None = None
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), "--registry-dir", str(registry_dir)]
    if repo_root is not None:
        command.extend(["--repo-root", str(repo_root)])
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def test_missing_registry_dir_is_clean() -> None:
    result = _run(REPO_ROOT / "does" / "not" / "exist")
    assert result.returncode == 0
    assert "nothing to verify" in result.stdout


def test_corrupt_run_record_reported(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "run_20260819T000000Z_00000001.json").write_text(
        "{not valid json", encoding="utf-8"
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "cannot enumerate run records" in result.stdout + result.stderr


def test_malformed_event_log_reported(tmp_path: Path) -> None:
    (tmp_path / "runs").mkdir()
    (tmp_path / "log.jsonl").write_text(
        '{"ok": true}\n{broken json}\n', encoding="utf-8"
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "log.jsonl:2" in result.stdout + result.stderr


def test_dangling_parent_link_reported(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    record = {
        "run_id": "run_20260819T000000Z_00000001",
        "title": "fixture",
        "evidence_stage": "ENGINEERING_PILOT",
        "status": "COMPLETED",
        "protocol_hash": "a" * 64,
        "git_commit": None,
        "git_dirty": False,
        "data_manifests": {},
        "reference_checksum": None,
        "model_identity": None,
        "scorer_config": {},
        "comparator_versions": {},
        "seed": None,
        "hardware": {},
        "command": "fixture",
        "created_at": "2026-08-19T00:00:00Z",
        "updated_at": "2026-08-19T00:00:00Z",
        "parent_run_id": "run_20260819T000000Z_99999999",
        "output_paths": [],
        "output_hashes": {},
    }
    (runs / "run_20260819T000000Z_00000001.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "does not resolve" in result.stdout + result.stderr


def test_clean_registry_passes(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "run_20260819T000000Z_00000001.json").write_text(
        json.dumps(
            {
                "run_id": "run_20260819T000000Z_00000001",
                "title": "fixture",
                "evidence_stage": "ENGINEERING_PILOT",
                "status": "COMPLETED",
                "protocol_hash": "a" * 64,
                "git_commit": None,
                "git_dirty": False,
                "data_manifests": {},
                "reference_checksum": None,
                "model_identity": None,
                "scorer_config": {},
                "comparator_versions": {},
                "seed": None,
                "hardware": {},
                "command": "fixture",
                "created_at": "2026-08-19T00:00:00Z",
                "updated_at": "2026-08-19T00:00:00Z",
                "parent_run_id": None,
                "output_paths": [],
                "output_hashes": {},
            }
        ),
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verified" in result.stdout


def test_tampered_completed_output_is_reported(tmp_path: Path) -> None:
    runs = tmp_path / "runs"
    runs.mkdir()
    output = tmp_path / "artifacts" / "metrics.json"
    output.parent.mkdir(parents=True)
    output.write_text('{"status": "fixture"}\n', encoding="utf-8")
    import hashlib

    record = {
        "run_id": "run_20260819T000000Z_00000001",
        "title": "completed fixture",
        "evidence_stage": "ENGINEERING_PILOT",
        "status": "COMPLETED",
        "protocol_hash": "a" * 64,
        "git_commit": None,
        "git_dirty": False,
        "data_manifests": {},
        "reference_checksum": None,
        "model_identity": None,
        "scorer_config": {},
        "comparator_versions": {},
        "seed": None,
        "hardware": {},
        "command": "fixture",
        "created_at": "2026-08-19T00:00:00Z",
        "updated_at": "2026-08-19T00:00:00Z",
        "parent_run_id": None,
        "output_paths": ["artifacts/metrics.json"],
        "output_hashes": {
            "artifacts/metrics.json": hashlib.sha256(output.read_bytes()).hexdigest()
        },
    }
    (runs / "run_20260819T000000Z_00000001.json").write_text(
        json.dumps(record), encoding="utf-8"
    )
    output.write_text('{"status": "tampered"}\n', encoding="utf-8")

    result = _run(tmp_path, repo_root=tmp_path)
    assert result.returncode == 1
    assert "output hashes are not reproducible" in result.stdout + result.stderr
