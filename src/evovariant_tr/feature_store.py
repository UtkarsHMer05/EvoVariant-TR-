"""Content-addressed frozen feature records for representation experiments."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FeatureRecord:
    normalized_variant_id: str
    model_id: str
    layer: str
    split: str
    values: tuple[float, ...]
    dtype: str
    content_sha256: str
    gene_symbol: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "normalized_variant_id": self.normalized_variant_id,
            "model_id": self.model_id,
            "layer": self.layer,
            "split": self.split,
            "values": list(self.values),
            "shape": [len(self.values)],
            "dtype": self.dtype,
            "content_sha256": self.content_sha256,
            "gene_symbol": self.gene_symbol,
        }


def _content_hash(values: tuple[float, ...]) -> str:
    encoded = json.dumps(list(values), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def make_feature_record(
    *,
    normalized_variant_id: str,
    model_id: str,
    layer: str,
    split: str,
    values: list[float] | tuple[float, ...],
    dtype: str = "float32",
    gene_symbol: str | None = None,
) -> FeatureRecord:
    """Validate and hash one ref/alt-derived feature vector."""
    vector = tuple(float(value) for value in values)
    if not vector:
        raise ValueError("feature vector cannot be empty")
    if not all(math.isfinite(value) for value in vector):
        raise ValueError("feature vector must contain only finite values")
    if split not in {"TRAIN", "VALIDATION", "LOCKED_TEST"}:
        raise ValueError(f"unknown split: {split}")
    return FeatureRecord(
        normalized_variant_id=normalized_variant_id,
        model_id=model_id,
        layer=layer,
        split=split,
        values=vector,
        dtype=dtype,
        content_sha256=_content_hash(vector),
        gene_symbol=gene_symbol,
    )


def assemble_feature_matrix(
    records: list[FeatureRecord],
    *,
    split: str,
    allow_locked_test: bool = False,
) -> tuple[list[str], list[list[float]]]:
    """Assemble a deterministic matrix and reject duplicate/mixed dimensions."""
    if split == "LOCKED_TEST" and not allow_locked_test:
        raise ValueError("locked-test feature extraction is not enabled for this operation")
    selected = sorted(
        (record for record in records if record.split == split),
        key=lambda record: record.normalized_variant_id,
    )
    ids = [record.normalized_variant_id for record in selected]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate normalized variant IDs in feature records")
    dimensions = {len(record.values) for record in selected}
    if len(dimensions) > 1:
        raise ValueError("feature vectors have inconsistent dimensions")
    return ids, [list(record.values) for record in selected]


def validate_feature_split_disjointness(records: list[FeatureRecord]) -> dict[str, int]:
    """Check that the same variant is not represented in multiple split buckets."""
    by_split: dict[str, set[str]] = {"TRAIN": set(), "VALIDATION": set(), "LOCKED_TEST": set()}
    for record in records:
        by_split.setdefault(record.split, set()).add(record.normalized_variant_id)
    overlap = sum(
        len(by_split[left] & by_split[right])
        for left, right in (
            ("TRAIN", "VALIDATION"),
            ("TRAIN", "LOCKED_TEST"),
            ("VALIDATION", "LOCKED_TEST"),
        )
    )
    return {"normalized_id_overlap": overlap}
