"""No-spend contract tests for the source-level Modal batch helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("modal")

_APP_PATH = Path(__file__).resolve().parents[2] / "evo2_scorer_app.py"
_SPEC = importlib.util.spec_from_file_location("evovariant_modal_source", _APP_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)
Evo2ScorerService = _MODULE.Evo2ScorerService


class _FakeModel:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def score_sequences(self, sequences: list[str]) -> list[float]:
        self.calls.append(list(sequences))
        return [float(len(sequence)) for sequence in sequences]


def test_modal_source_normalizes_transport_aliases_without_remote_call() -> None:
    service = SimpleNamespace()

    parsed = Evo2ScorerService._parse_variant_input(
        service,
        {
            "chromosome": "10",
            "variant_position": 100,
            "ref": "a",
            "alternative": "t",
        },
    )

    assert parsed.chromosome == "chr10"
    assert parsed.normalized_variant_id == "GRCh38:chr10:100:A>T"


def test_modal_source_batch_helper_chunks_sequences_without_gpu() -> None:
    fake_model = _FakeModel()
    service = SimpleNamespace(model=fake_model)

    sequences = ["A" * 8192] * 9
    scores = Evo2ScorerService._score_sequence_batch(service, sequences)

    assert scores == [8192.0] * 9
    assert [len(call) for call in fake_model.calls] == [8, 1]
