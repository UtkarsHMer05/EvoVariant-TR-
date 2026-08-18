"""Contract tests: the frozen on-disk protocol file is the contract.

These tests validate external/frozen artifacts (the protocol YAML and its
recorded hash) rather than pure logic, so they live in tests/contract.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from evovariant_tr.config import load_protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = REPO_ROOT / "research" / "protocol" / "protocol.yaml"

# Frozen at Milestone 11; any change requires a dated DEVIATION_LOG.md entry.
FROZEN_PROTOCOL_SHA256 = (
    "78799000023ca157b72836a0ec603abb20c93960b15fba09485bd0dffbbb1525"
)


def test_protocol_file_hash_matches_frozen_value() -> None:
    digest = hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()
    assert digest == FROZEN_PROTOCOL_SHA256, (
        "protocol.yaml drifted from its Milestone 11 frozen hash; "
        "record a dated deviation before any change"
    )


def test_protocol_contract_fields() -> None:
    protocol = load_protocol(PROTOCOL_PATH)
    assert protocol.temporal_design.reference_assembly == "GRCh38"
    assert protocol.sequence_contract.context_length_bp == 8192
    assert protocol.statistics.primary_endpoint == "AUROC"
    assert protocol.calibration_contract.test_cohort_used_for_fitting == "never"
    assert protocol.scoring_contract.retain_all_raw_components is True


def test_experiment_run_schema_is_valid_json_schema() -> None:
    import json

    import jsonschema

    schema_path = REPO_ROOT / "research" / "schemas" / "experiment_run.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert "evidence_stage" in schema["required"]
