from __future__ import annotations

import json

import numpy as np
import pytest
from scripts.materialize_formal_features import (
    DEFAULT_MANIFEST,
    MaterializationError,
    load_manifest,
    materialize,
)


def _minimal_representation_npz(path, *, wrong_id: bool = False) -> None:
    records = load_manifest(DEFAULT_MANIFEST)
    count = len(records)
    ids = [str(row["normalized_variant_id"]) for row in records]
    if wrong_id:
        ids[0] = "not-a-formal-id"
    splits = [str(row["split"]) for row in records]
    genes = [str(row["gene_symbol"]) for row in records]
    labels = np.asarray([int(row["label"]) for row in records], dtype=np.int8)
    arrays = {
        "variant_ids": np.asarray(ids),
        "splits": np.asarray(splits),
        "gene_symbols": np.asarray(genes),
        "labels": labels,
        "layers": np.asarray([8, 16, 24], dtype=np.int32),
    }
    for key in (
        "forward_delta",
        "reverse_delta",
        "alt_minus_ref_aggregate",
        "abs_alt_minus_ref_aggregate",
    ):
        arrays[key] = np.zeros((count, 3, 2), dtype=np.float32)
    for key in ("cosine_similarity", "distance_l2", "orientation_disagreement_l2"):
        arrays[key] = np.zeros((count, 3), dtype=np.float32)
    np.savez_compressed(path, **arrays)


def test_formal_representation_materializer_rejects_id_drift(tmp_path) -> None:
    npz_path = tmp_path / "representations.npz"
    _minimal_representation_npz(npz_path, wrong_id=True)
    with pytest.raises(MaterializationError, match="variant IDs"):
        materialize(
            npz_path,
            tmp_path / "features",
            candidate="nucleotide_transformer",
        )


def test_formal_representation_materializer_writes_verified_jsonl(tmp_path) -> None:
    npz_path = tmp_path / "representations.npz"
    _minimal_representation_npz(npz_path)
    summary = materialize(
        npz_path,
        tmp_path / "features",
        candidate="nucleotide_transformer",
    )
    assert summary["status"] == "PASS_FORMAL_FEATURE_MATERIALIZATION"
    assert summary["record_count"] == 4_000
    assert summary["locked_test_count"] == 0
    assert summary["output_count"] == 21
    first = tmp_path / "features/nucleotide_transformer_layer_8_alt_minus_ref_aggregate.jsonl"
    row = json.loads(first.read_text(encoding="utf-8").splitlines()[0])
    assert row["split"] in {"TRAIN", "VALIDATION"}
    assert row["labels_attached_locally"] is True
    assert row["locked_test_present"] is False
