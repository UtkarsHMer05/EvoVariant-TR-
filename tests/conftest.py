"""Pytest bootstrap and test-tier gating for EvoVariant-TR.

Test taxonomy (Milestone 17):
- ``tests/unit``        pure logic, no I/O beyond temp files
- ``tests/contract``    external schemas and frozen file contracts
- ``tests/integration`` tiny local fixtures, no network
- ``tests/modal``       Modal / paid GPU compute (gated)
- ``tests/scientific``  slow scientific validation (gated)
- ``tests/e2e``         browser end-to-end (gated, lands at Milestone 97)

The default run never launches paid compute: gated tiers are deselected by
``addopts`` in pyproject.toml AND hard-blocked here unless the explicit flag
and (for modal) the cost acknowledgement are both present.
"""

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
for import_root in (REPO_ROOT, SRC):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

COST_ACK_ENV = "EVOVARIANT_TR_PAID_COMPUTE_ACK"
COST_ACK_VALUE = "I_ACCEPT_COSTS"

GATED_MARKERS = ("modal", "scientific", "e2e")


def pytest_addoption(parser):
    parser.addoption(
        "--run-modal",
        action="store_true",
        default=False,
        help="run Modal/paid-compute tests (also requires "
        f"{COST_ACK_ENV}={COST_ACK_VALUE})",
    )
    parser.addoption(
        "--run-scientific",
        action="store_true",
        default=False,
        help="run slow scientific validation tests",
    )
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="run end-to-end browser tests",
    )


def _gate_enabled(marker_name: str, config) -> bool:
    if marker_name == "modal":
        flag = config.getoption("--run-modal")
        acknowledged = os.environ.get(COST_ACK_ENV) == COST_ACK_VALUE
        return flag and acknowledged
    if marker_name == "scientific":
        return config.getoption("--run-scientific")
    if marker_name == "e2e":
        return config.getoption("--run-e2e")
    return False


def pytest_collection_modifyitems(config, items):
    """Hard block: gated tests are skipped unless explicitly unlocked.

    This is a second safeguard on top of the ``-m`` deselect in addopts, so a
    bare ``pytest -m modal`` can never accidentally spend money.
    """
    for item in items:
        for marker_name in GATED_MARKERS:
            if item.get_closest_marker(marker_name) and not _gate_enabled(
                marker_name, config
            ):
                reason = (
                    f"{marker_name} tests are gated; pass the explicit flag"
                    + (
                        f" and set {COST_ACK_ENV}={COST_ACK_VALUE}"
                        if marker_name == "modal"
                        else ""
                    )
                )
                item.add_marker(pytest.mark.skip(reason=reason))
