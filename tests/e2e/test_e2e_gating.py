"""End-to-end browser tests — gated, land at Milestone 97.

Run with:

    pytest --run-e2e
"""

from __future__ import annotations

import pytest


@pytest.mark.e2e
def test_e2e_placeholder_until_milestone_97() -> None:
    pytest.skip("browser E2E tests land at Milestone 97; gate verified")
