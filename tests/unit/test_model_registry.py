"""Tests for the schema-validated ML-extension model registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evovariant_tr.model_registry import (
    ModelRegistryError,
    included_models,
    load_model_manifest,
    load_model_registry,
    verify_model_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = REPO_ROOT / "research/schemas/model_manifest.schema.json"
MODELS = REPO_ROOT / "research/ml_extension/models"


def _manifest(model_id: str = "fixture_model", **overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "model_id": model_id,
        "status": "PLANNED",
        "model_name": "Fixture model",
        "source": "https://example.invalid/fixture",
        "license": "NOT_VERIFIED",
        "checkpoint": None,
        "revision": None,
        "input_contract": {
            "assembly": None,
            "alphabet": "ACGT",
            "context_lengths_bp": [],
            "variant_scoring": False,
        },
        "score_contract": {
            "score_semantics": "not_verified",
            "score_direction": "unknown",
            "orientation_support": "unknown",
        },
        "capabilities": {
            "raw_score": False,
            "embeddings": False,
            "fine_tuning": False,
            "batch": False,
        },
        "hardware": {"backend": "not_verified", "gpu": None, "memory_gb": None},
        "provenance": {
            "verified_at": None,
            "verification_status": "NOT_VERIFIED",
            "notes": "fixture",
            "asset_checksum": None,
        },
    }
    data.update(overrides)
    return data


def test_checked_in_registry_is_valid_and_includes_verified_evo2() -> None:
    models = load_model_registry(MODELS, schema_path=SCHEMA)
    assert len(models) == 7
    assert {model.model_id for model in models} == {
        "alphamissense_valid_subset",
        "cadd",
        "caduceus",
        "evo2",
        "gpn",
        "nucleotide_transformer",
        "phylop",
    }
    assert [model.model_id for model in included_models(models)] == ["evo2"]
    assert verify_model_registry(MODELS, schema_path=SCHEMA) == []


def test_manifest_loader_rejects_missing_malformed_and_non_object(tmp_path: Path) -> None:
    with pytest.raises(ModelRegistryError, match="does not exist"):
        load_model_manifest(tmp_path / "missing.json", schema_path=SCHEMA)

    malformed = tmp_path / "malformed.json"
    malformed.write_text("{broken", encoding="utf-8")
    with pytest.raises(ModelRegistryError, match="cannot read"):
        load_model_manifest(malformed, schema_path=SCHEMA)

    non_object = tmp_path / "list.json"
    non_object.write_text("[]", encoding="utf-8")
    with pytest.raises(ModelRegistryError, match="JSON object"):
        load_model_manifest(non_object, schema_path=SCHEMA)


def test_registry_rejects_empty_duplicate_and_invalid_manifests(tmp_path: Path) -> None:
    with pytest.raises(ModelRegistryError, match="does not exist"):
        load_model_registry(tmp_path / "missing", schema_path=SCHEMA)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ModelRegistryError, match="empty"):
        load_model_registry(empty, schema_path=SCHEMA)

    first = tmp_path / "first"
    first.mkdir()
    (first / "a.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    (first / "b.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    with pytest.raises(ModelRegistryError, match="duplicate"):
        load_model_registry(first, schema_path=SCHEMA)

    invalid = tmp_path / "invalid"
    invalid.mkdir()
    bad = _manifest()
    bad["unexpected"] = True
    (invalid / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
    failures = verify_model_registry(invalid, schema_path=SCHEMA)
    assert len(failures) == 1
    assert "schema validation failed" in failures[0]


def test_included_manifest_requires_verified_provenance(tmp_path: Path) -> None:
    directory = tmp_path / "models"
    directory.mkdir()
    included = _manifest(
        status="INCLUDED",
        provenance={
            "verified_at": None,
            "verification_status": "NOT_VERIFIED",
            "notes": "not enough evidence",
            "asset_checksum": None,
        },
    )
    path = directory / "fixture.json"
    path.write_text(json.dumps(included), encoding="utf-8")
    models = load_model_registry(directory, schema_path=SCHEMA)
    with pytest.raises(ModelRegistryError, match="VERIFIED provenance"):
        included_models(models)

    verified = _manifest(
        status="AVAILABLE",
        provenance={
            "verified_at": "2026-09-21T00:00:00Z",
            "verification_status": "VERIFIED",
            "notes": "verified fixture",
            "asset_checksum": "a" * 64,
        },
    )
    path.write_text(json.dumps(verified), encoding="utf-8")
    loaded = load_model_registry(directory, schema_path=SCHEMA)
    assert [model.model_id for model in included_models(loaded)] == ["fixture_model"]
    assert loaded[0].to_dict() == verified
