"""Modal tests — gated, never run by default.

These tests exercise Modal/GPU infrastructure and COST MONEY. They require
BOTH the explicit flag and the cost acknowledgement:

    EVOVARIANT_TR_PAID_COMPUTE_ACK=I_ACCEPT_COSTS pytest --run-modal

Until Milestone 52+ lands the new Modal service, this module only proves the
gating contract: the marker exists and the tests are skipped by default.
"""

from __future__ import annotations

import pytest


@pytest.mark.modal
def test_modal_placeholder_requires_real_infrastructure() -> None:
    """Placeholder for the M55 model-load smoke test.

    Replaced by real Modal tests once services/modal exists (M52+). If this
    body ever runs, the paid-compute gate was explicitly unlocked.
    """
    pytest.skip("real Modal tests land with Milestone 52-55; gate verified")
