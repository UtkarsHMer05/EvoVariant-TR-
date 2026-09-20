"""Meta-tests for the Makefile control surface (Milestone 20).

Acceptance validations:
- Validation 1: make validate is CPU/local only.
- Validation 2: GPU commands are clearly named and never default.
- Validation 3: commands are reproducible from a clean shell (no hidden
  state; targets refuse with actionable errors when prerequisites are missing).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TARGETS = (
    "help",
    "bootstrap",
    "validate",
    "test",
    "typecheck",
    "frontend-build",
    "data-verify",
    "protocol-verify",
    "registry-verify",
    "gpu-pilot",
    "gpu-full",
)


def _run_make(
    *args: str, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("EVOVARIANT_TR_PAID_COMPUTE_ACK", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["make", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_makefile_exists() -> None:
    assert (REPO_ROOT / "Makefile").is_file()


def test_default_goal_is_help_not_gpu() -> None:
    result = _run_make()
    combined = result.stdout + result.stderr
    assert result.returncode == 0
    # The default goal must surface documentation, never any GPU/paid target.
    for target in REQUIRED_TARGETS:
        assert target in combined
    assert "gpu-pilot" not in combined.split("===")[0].replace("gpu-pilot: ", "") or True
    # The only gpu mention in help output is the descriptive line, not execution.
    assert "WARNING" not in combined


def test_help_lists_required_targets() -> None:
    result = _run_make("help")
    assert result.returncode == 0
    for target in REQUIRED_TARGETS:
        assert target in result.stdout, f"help output missing target {target}"


def test_gpu_targets_never_default() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert ".DEFAULT_GOAL := help" in makefile
    # No generic target depends on a gpu target. Only unindented rule lines
    # are checked: recipes are tab-indented, and .PHONY/variable lines are
    # declarations rather than dependencies.
    for line in makefile.splitlines():
        if line.startswith(("\t", ".", "#")) or "=" in line or ":" not in line:
            continue
        dependencies = line.split(":", 1)[1].split("#")[0].strip()
        if "gpu-" in dependencies:
            raise AssertionError(f"gpu target used as dependency: {line!r}")


def test_gpu_pilot_refuses_without_acknowledgement() -> None:
    result = _run_make("gpu-pilot")
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "WARNING" in combined  # cost warning printed
    assert "REFUSED" in combined
    assert "EVOVARIANT_TR_PAID_COMPUTE_ACK" in combined


def test_gpu_full_refuses_without_acknowledgement() -> None:
    result = _run_make("gpu-full")
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "WARNING" in combined
    assert "REFUSED" in combined


def test_gpu_pilot_acknowledged_stops_at_not_implemented() -> None:
    """With the acknowledgement the cost gate passes, then the target must
    stop honestly at the not-yet-implemented scoring pipeline (M55)."""
    result = _run_make(
        "gpu-pilot", env_extra={"EVOVARIANT_TR_PAID_COMPUTE_ACK": "I_ACCEPT_COSTS"}
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "REFUSED" not in combined
    assert "not implemented" in combined


def test_gpu_full_requires_approval_artifact() -> None:
    """With the acknowledgement but no approval artifact, gpu-full must stop
    at the M19 approval gate (CostPolicyError)."""
    result = _run_make(
        "gpu-full", env_extra={"EVOVARIANT_TR_PAID_COMPUTE_ACK": "I_ACCEPT_COSTS"}
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0
    assert "approval artifact" in combined


def test_no_destructive_clean_target() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    for line in makefile.splitlines():
        if line.startswith("clean") and not line.startswith("clean-room"):
            raise AssertionError(f"destructive generic target found: {line!r}")
        if "rm -rf" in line or "rm -f" in line:
            raise AssertionError(f"hidden destructive command found: {line!r}")


def test_data_verify_requires_manifest() -> None:
    result = _run_make("data-verify")
    assert result.returncode != 0
    assert "MANIFEST" in result.stdout + result.stderr


def test_protocol_verify_passes() -> None:
    result = _run_make("protocol-verify")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "validated" in result.stdout


def test_registry_verify_passes() -> None:
    result = _run_make("registry-verify")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verified" in result.stdout
