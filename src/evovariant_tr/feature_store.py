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


def feature_record_from_embedding_payload(
    payload: dict[str, Any],
    *,
    split: str,
    model_id: str = "evo2",
    representation: str = "orientation_concat_difference",
    gene_symbol: str | None = None,
) -> FeatureRecord:
    """Convert one validated Modal embedding payload into a compact feature record.

    The default representation concatenates the forward and reverse-complement
    alternate-minus-reference vectors in that fixed order.  The payload hashes,
    vector shapes, finite values, and orientation dimensions are verified before
    the downstream record is created.  This is a storage adapter only; it does
    not select a layer or tune a representation against locked labels.
    """
    if payload.get("status") != "completed":
        raise ValueError("embedding payload must have completed status")
    normalized_variant_id = payload.get("normalized_variant_id")
    if not isinstance(normalized_variant_id, str) or not normalized_variant_id:
        raise ValueError("embedding payload is missing normalized_variant_id")
    if not model_id.strip():
        raise ValueError("model_id must be non-empty")

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("embedding payload is missing provenance")
    layer = provenance.get("layer")
    pooling = provenance.get("pooling")
    if not isinstance(layer, str) or not layer:
        raise ValueError("embedding payload is missing a layer")
    if pooling != "mean_tokens":
        raise ValueError("embedding payload must use the frozen mean_tokens pooling rule")

    embedding_features = payload.get("embedding_features")
    if not isinstance(embedding_features, dict):
        raise ValueError("embedding payload is missing embedding_features")

    def read_orientation(name: str) -> tuple[list[float], list[float], list[float]]:
        raw = embedding_features.get(name)
        if not isinstance(raw, dict):
            raise ValueError(f"embedding payload is missing {name} orientation")
        vectors: list[list[float]] = []
        for key in ("reference", "alternate", "difference"):
            values = raw.get(key)
            if not isinstance(values, list) or not values:
                raise ValueError(f"{name} {key} vector is empty or malformed")
            try:
                vector = [float(value) for value in values]
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name} {key} vector is non-numeric") from exc
            if not all(math.isfinite(value) for value in vector):
                raise ValueError(f"{name} {key} vector contains non-finite values")
            if raw.get("shape") != [len(vector)]:
                raise ValueError(f"{name} vector shape metadata is inconsistent")
            expected_hash = _content_hash(tuple(vector))
            if raw.get(f"{key}_sha256") != expected_hash:
                raise ValueError(f"{name} {key} vector hash does not match payload")
            vectors.append(vector)
        reference, alternate, difference = vectors
        expected_difference = [alt - ref for ref, alt in zip(reference, alternate, strict=True)]
        if difference != expected_difference:
            raise ValueError(f"{name} difference vector is not alternate minus reference")
        return reference, alternate, difference

    forward = read_orientation("forward")
    reverse = read_orientation("reverse")
    if len(forward[2]) != len(reverse[2]):
        raise ValueError("forward and reverse difference dimensions do not match")

    if representation == "orientation_concat_difference":
        values = forward[2] + reverse[2]
    elif representation == "orientation_mean_difference":
        values = [
            (forward_value + reverse_value) / 2.0
            for forward_value, reverse_value in zip(forward[2], reverse[2], strict=True)
        ]
    elif representation == "forward_difference":
        values = forward[2]
    elif representation == "reverse_difference":
        values = reverse[2]
    else:
        raise ValueError(f"unknown embedding representation: {representation}")

    return make_feature_record(
        normalized_variant_id=normalized_variant_id,
        model_id=model_id,
        layer=f"{layer}:{representation}",
        split=split,
        values=values,
        dtype="float32",
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
