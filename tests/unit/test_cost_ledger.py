"""Tests for append-only cost records and explicit unavailable work."""

from __future__ import annotations

from pathlib import Path

import pytest

from evovariant_tr.cost_ledger import append_entry, load_entries, new_entry


def test_cost_ledger_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "runs" / "cost.jsonl"
    entry = new_entry(
        run_id="modal-smoke-deferred",
        workload="evo2_modal_smoke",
        backend="unavailable",
        status="DEFERRED",
        notes="Modal authentication and paid-compute acknowledgement unavailable",
    )
    append_entry(path, entry)
    rows = load_entries(path)
    assert rows[0]["run_id"] == "modal-smoke-deferred"
    assert rows[0]["backend"] == "unavailable"
    assert rows[0]["measured_usd"] is None


def test_cost_ledger_rejects_negative_values(tmp_path: Path) -> None:
    entry = new_entry(
        run_id="bad",
        workload="test",
        backend="local",
        status="FAILED",
    )
    bad = type(entry)(**{**entry.to_dict(), "gpu_count": -1})
    with pytest.raises(ValueError, match="gpu_count"):
        append_entry(tmp_path / "cost.jsonl", bad)


def test_load_missing_ledger_is_empty(tmp_path: Path) -> None:
    assert load_entries(tmp_path / "missing.jsonl") == []
