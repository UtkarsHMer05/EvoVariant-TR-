"""Contract tests for the additive ML-extension control plane."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

from evovariant_tr.control_plane import (
    ORIGINAL_PROTOCOL_SHA256,
    _validate_json_schema,
    load_yaml_mapping,
    sha256_file,
    verify_ml_control_plane,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ml_control_plane_is_valid_and_preserves_original_protocol() -> None:
    assert verify_ml_control_plane(REPO_ROOT) == []


def test_original_protocol_hash_is_immutable() -> None:
    original = REPO_ROOT / "research/protocol/protocol.yaml"
    assert sha256_file(original) == ORIGINAL_PROTOCOL_SHA256


def test_extension_protocol_declares_separate_locked_test() -> None:
    path = REPO_ROOT / "research/ml_extension/protocol.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["relationship_to_original"] == "separate_ml_extension"
    assert data["data_contract"]["locked_test"]["labels_must_not_be_read_before_freeze"] is True
    assert data["selection_policy"]["hpo_validation_only"] is True


def test_experiment_template_conforms_to_schema() -> None:
    schema_path = REPO_ROOT / "research/schemas/experiment_config.schema.json"
    template_path = REPO_ROOT / "experiments/templates/experiment_config.yaml"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    config = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    jsonschema.validate(config, schema)


def test_all_control_plane_schemas_are_draft_2020_12() -> None:
    for path in sorted((REPO_ROOT / "research/schemas").glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)


def test_missing_control_plane_is_reported_without_throwing(tmp_path: Path) -> None:
    failures = verify_ml_control_plane(tmp_path)
    assert any("frozen original protocol" in failure for failure in failures)
    assert any("ML control file" in failure for failure in failures)
    assert any("control-plane schema" in failure for failure in failures)
    assert any("control-plane hash record" in failure for failure in failures)


def test_control_plane_rejects_bad_yaml_and_schema(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("- not-a-mapping\n", encoding="utf-8")
    try:
        load_yaml_mapping(bad_yaml)
    except ValueError as exc:
        assert "mapping" in str(exc)
    else:
        raise AssertionError("non-mapping YAML should fail")

    malformed = tmp_path / "malformed.schema.json"
    malformed.write_text("{", encoding="utf-8")
    assert _validate_json_schema(malformed) is not None

    invalid_schema = tmp_path / "invalid.schema.json"
    invalid_schema.write_text('{"type": 17}\n', encoding="utf-8")
    assert _validate_json_schema(invalid_schema) is not None
