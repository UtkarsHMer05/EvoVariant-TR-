"""Tests for the protocol-facing benchmark-expansion helpers."""

from __future__ import annotations

from datetime import date

from evovariant_tr.benchmark_expansion import (
    budget_plan,
    review_group,
    substitution_class,
    temporal_bin,
    temporal_duration,
    transition_category,
)


def test_review_groups_cover_declared_buckets() -> None:
    assert [review_group(stars) for stars in (-1, 0, 1, 2, 3, 4)] == [
        "0 stars",
        "0 stars",
        "1 star",
        "2 stars",
        "3 stars",
        "3 stars",
    ]


def test_substitution_and_transition_classification() -> None:
    assert substitution_class("a", "g") == "A>G"
    assert substitution_class("A", "A") == "not_applicable"
    assert substitution_class("AA", "G") == "not_applicable"
    assert transition_category("a", "g") == "transition"
    assert transition_category("C", "A") == "transversion"
    assert transition_category("N", "A") == "not_applicable"
    assert transition_category("A", "A") == "not_applicable"


def test_temporal_duration_and_bins() -> None:
    start = date(2025, 1, 1)
    assert temporal_duration(None, start) is None
    assert temporal_duration(start, date(2024, 12, 31)) is None
    assert temporal_duration(start, date(2025, 1, 2)) == 1
    assert [temporal_bin(days) for days in (None, 180, 181, 365, 366, 545, 546)] == [
        "missing/invalid",
        "<=180",
        "181-365",
        "181-365",
        "366-545",
        "366-545",
        ">545",
    ]


def test_budget_plan_blocks_unknown_and_respects_reserve_and_cap() -> None:
    assert budget_plan(None)["status"] == "COMPUTE_BLOCKED_BALANCE_UNVERIFIED"
    blocked = budget_plan(5.49)
    assert blocked["safe_spendable_usd"] == 0.0
    assert blocked["status"] == "COMPUTE_BLOCKED_RESERVE"
    ready = budget_plan(10.0)
    assert ready["safe_spendable_usd"] == 4.5
    assert ready["program_budget_usd"] == 4.5
    assert ready["status"] == "READY"
    assert budget_plan(100.0)["program_budget_usd"] == 24.0
