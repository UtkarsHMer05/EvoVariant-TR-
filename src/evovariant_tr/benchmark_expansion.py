"""Small, protocol-facing helpers for the benchmark-expansion suite."""

from __future__ import annotations

from datetime import date


def review_group(stars: int) -> str:
    """Return the predeclared evidence-quality bucket for a ClinVar star count."""
    if stars <= 0:
        return "0 stars"
    if stars == 1:
        return "1 star"
    if stars == 2:
        return "2 stars"
    return "3 stars"


def substitution_class(reference: str, alternate: str) -> str:
    """Return a canonical SNV substitution class."""
    ref = reference.upper()
    alt = alternate.upper()
    if ref == alt or len(ref) != 1 or len(alt) != 1:
        return "not_applicable"
    return f"{ref}>{alt}"


def transition_category(reference: str, alternate: str) -> str:
    """Classify an SNV without using labels or model outputs."""
    ref = reference.upper()
    alt = alternate.upper()
    if {ref, alt} in ({"A", "G"}, {"C", "T"}):
        return "transition"
    if ref in "ACGT" and alt in "ACGT" and ref != alt:
        return "transversion"
    return "not_applicable"


def temporal_duration(start: date | None, resolution: date | None) -> int | None:
    """Return an authoritative non-negative duration, or ``None`` if invalid."""
    if start is None or resolution is None:
        return None
    days = (resolution - start).days
    return days if days >= 0 else None


def temporal_bin(days: int | None) -> str:
    """Use the fixed, performance-independent temporal bins."""
    if days is None:
        return "missing/invalid"
    if days <= 180:
        return "<=180"
    if days <= 365:
        return "181-365"
    if days <= 545:
        return "366-545"
    return ">545"


def budget_plan(
    live_balance: float | None,
    *,
    safety_stop: float = 5.50,
    soft_maximum: float = 24.00,
) -> dict[str, float | None | str]:
    """Calculate spendable budget without treating an unavailable balance as zero."""
    if live_balance is None:
        return {
            "live_balance_usd": None,
            "safe_spendable_usd": None,
            "program_budget_usd": None,
            "status": "COMPUTE_BLOCKED_BALANCE_UNVERIFIED",
        }
    safe_spendable = max(0.0, live_balance - safety_stop)
    return {
        "live_balance_usd": live_balance,
        "safe_spendable_usd": safe_spendable,
        "program_budget_usd": min(soft_maximum, safe_spendable),
        "status": "READY" if live_balance >= safety_stop else "COMPUTE_BLOCKED_RESERVE",
    }
