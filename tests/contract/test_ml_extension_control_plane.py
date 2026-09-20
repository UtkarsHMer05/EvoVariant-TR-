"""Contract tests for the additive ML-extension control plane."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

from evovariant_tr.control_plane import (
    ORIGINAL_PROTOCOL_SHA256,
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
