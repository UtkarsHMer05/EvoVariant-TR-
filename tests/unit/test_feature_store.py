"""No-spend tests for the Modal embedding-to-feature-store adapter."""

from __future__ import annotations

import hashlib
import json

import pytest

from evovariant_tr.feature_store import feature_record_from_embedding_payload


def _hash(values: list[float]) -> str:
    encoded = json.dumps(values, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload() -> dict[str, object]:
    forward = {"reference": [1.0, 2.0], "alternate": [2.0, 4.0]}
    reverse = {"reference": [3.0, 5.0], "alternate": [4.0, 8.0]}
    for orientation in (forward, reverse):
        difference = [
            alternate - reference
            for reference, alternate in zip(
                orientation["reference"], orientation["alternate"], strict=True
            )
        ]
        orientation["difference"] = difference
        orientation["shape"] = [2]
        orientation["dtype"] = "float32"
        for key in ("reference", "alternate", "difference"):
            orientation[f"{key}_sha256"] = _hash(orientation[key])
    return {
        "status": "completed",
        "normalized_variant_id": "GRCh38:chr1:100:A>T",
        "embedding_features": {"forward": forward, "reverse": reverse},
        "provenance": {"layer": "blocks.28.mlp.l3", "pooling": "mean_tokens"},
    }


def test_embedding_payload_becomes_compact_hashed_feature_record() -> None:
    record = feature_record_from_embedding_payload(_payload(), split="TRAIN")

    assert record.model_id == "evo2"
    assert record.layer == "blocks.28.mlp.l3:orientation_concat_difference"
    assert record.values == (1.0, 2.0, 1.0, 3.0)
    assert record.dtype == "float32"
    assert len(record.content_sha256) == 64
    assert record.to_dict()["shape"] == [4]


def test_embedding_payload_adapter_supports_mean_orientation_contract() -> None:
    record = feature_record_from_embedding_payload(
        _payload(),
        split="VALIDATION",
        representation="orientation_mean_difference",
    )

    assert record.values == (1.0, 2.5)


def test_embedding_payload_adapter_rejects_tampering_and_unfrozen_pooling() -> None:
    payload = _payload()
    payload["embedding_features"]["forward"]["difference"][0] = 99.0
    with pytest.raises(ValueError, match="hash"):
        feature_record_from_embedding_payload(payload, split="TRAIN")

    payload = _payload()
    payload["provenance"]["pooling"] = "max_tokens"
    with pytest.raises(ValueError, match="mean_tokens"):
        feature_record_from_embedding_payload(payload, split="TRAIN")
