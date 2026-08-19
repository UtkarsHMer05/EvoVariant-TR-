"""Meta-tests for the test taxonomy and gating policy (Milestone 17).

Acceptance validations:
- Validation 1: the default test command never launches paid compute.
- Validation 2: Modal/scientific tests require explicit marker + acknowledgement.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

GATED_DIRS = ("contract", "integration", "modal", "scientific", "e2e")


def test_taxonomy_directories_exist() -> None:
    for name in ("unit", *GATED_DIRS):
        assert (REPO_ROOT / "tests" / name).is_dir(), f"tests/{name} missing"


def _run_pytest(
    *args: str, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("EVOVARIANT_TR_PAID_COMPUTE_ACK", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_default_run_deselects_all_gated_tiers() -> None:
    # With the default addopts marker filter, collecting only gated dirs
    # yields zero runnable tests (pytest exit code 5 = nothing collected).
    result = _run_pytest("--collect-only", "-q", "tests/modal", "tests/scientific", "tests/e2e")
    # Exit code 5 = nothing collected: the default marker filter deselected all.
    assert result.returncode == 5, result.stdout + result.stderr


def test_modal_flag_without_acknowledgement_still_blocked() -> None:
    result = _run_pytest("-rs", "--run-modal", "-m", "modal", "tests/modal")
    combined = result.stdout + result.stderr
    assert "skipped" in combined
    assert "gated" in combined  # the gate's skip reason, not the placeholder's
    assert "passed" not in combined


def test_modal_gate_opens_only_with_flag_and_acknowledgement() -> None:
    result = _run_pytest(
        "-rs",
        "--run-modal",
        "-m",
        "modal",
        "tests/modal",
        env_extra={"EVOVARIANT_TR_PAID_COMPUTE_ACK": "I_ACCEPT_COSTS"},
    )
    combined = result.stdout + result.stderr
    # Gate no longer blocks: tests run (some may skip via placeholder).
    assert "gated" not in combined
    assert "paid compute" not in combined


def test_scientific_gate_requires_explicit_flag() -> None:
    blocked = _run_pytest("-rs", "-m", "scientific", "tests/scientific")
    combined = blocked.stdout + blocked.stderr
    assert "skipped" in combined
    assert "gated" in combined
    opened = _run_pytest("-rs", "--run-scientific", "-m", "scientific", "tests/scientific")
    combined = opened.stdout + opened.stderr
    assert "gated" not in combined  # gate passed; tests may run or skip


def test_validate_local_script_exists_and_is_executable() -> None:
    script = REPO_ROOT / "scripts" / "validate_local.sh"
    assert script.is_file()
    assert os.access(script, os.X_OK)
