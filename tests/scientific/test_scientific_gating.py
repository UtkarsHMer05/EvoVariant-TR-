"""Scientific tests — slow validation behind an explicit marker.

Run with:

    pytest --run-scientific

These are for expensive deterministic checks (full cohort recomputation,
parity sweeps). They never run in the default command.
"""

from __future__ import annotations

import pytest


@pytest.mark.scientific
def test_scientific_placeholder_for_full_cohort_recomputation() -> None:
    """Placeholder for M37 cohort-count recomputation.

    Replaced by real scientific validation once ClinVar cohorts exist (M22+).
    """
    pytest.skip("real scientific tests land with the data milestones; gate verified")
