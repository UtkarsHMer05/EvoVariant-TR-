"""Schema round-trip and invalid-config tests for the frozen research protocol.

Milestone 12 acceptance validations:
- invalid configs fail loudly;
- the frozen config cannot be silently extended (unknown keys rejected);
- runtime-only fields cannot mutate scientific choices.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from evovariant_tr.config import (
    PRIMARY_BOOTSTRAP_REPLICATES,
    PRIMARY_BOOTSTRAP_SEED,
    PRIMARY_CONTEXT_LENGTH_BP,
    ProtocolConfig,
    RuntimeConfig,
    load_protocol,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = REPO_ROOT / "research" / "protocol" / "protocol.yaml"


@pytest.fixture(scope="module")
def raw_protocol() -> dict:
    with PROTOCOL_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@pytest.fixture(scope="module")
def protocol() -> ProtocolConfig:
    return load_protocol(PROTOCOL_PATH)


# ---------------------------------------------------------------------------
# Loading the real frozen protocol
# ---------------------------------------------------------------------------


def test_real_protocol_loads_and_is_frozen(protocol: ProtocolConfig) -> None:
    assert protocol.protocol_version == "1.0.0"
    assert protocol.project == "EvoVariant-TR"
    assert protocol.temporal_design.reference_assembly == "GRCh38"
    assert str(protocol.temporal_design.t0_release.release_date) == "2025-01-02"
    assert str(protocol.temporal_design.t1_release.release_date) == "2026-08-06"
    assert (
        protocol.temporal_design.primary_label_quality_gate.min_review_stars == 2
    )
    assert protocol.sequence_contract.context_length_bp == PRIMARY_CONTEXT_LENGTH_BP
    assert protocol.statistics.primary_endpoint == "AUROC"
    assert protocol.statistics.primary_uncertainty.seed == PRIMARY_BOOTSTRAP_SEED
    assert (
        protocol.statistics.primary_uncertainty.replicates
        == PRIMARY_BOOTSTRAP_REPLICATES
    )
    assert protocol.calibration_contract.test_cohort_used_for_fitting == "never"


def test_qa_checkpoint_counts_match_validation_target(protocol: ProtocolConfig) -> None:
    qa = protocol.qa_checkpoint_validation_target_only
    assert qa.t0_unique_vus == 1_403_225
    assert qa.absent_at_t1 == 3_615
    assert qa.not_definitive_at_t1 == 1_389_535
    assert qa.below_two_stars == 9_051
    assert qa.final_temporal_n == 1_024
    assert qa.n_blb == 614
    assert qa.n_plp == 410
    assert qa.gene_labels == 389
    assert qa.reference_mismatch_among_final_candidates == 0
    # Internal consistency: the funnel must add up.
    resolved_funnel = (
        qa.absent_at_t1 + qa.not_definitive_at_t1 + qa.below_two_stars + qa.final_temporal_n
    )
    assert resolved_funnel == qa.t0_unique_vus
    assert qa.n_blb + qa.n_plp == qa.final_temporal_n


# ---------------------------------------------------------------------------
# Round-trip stability
# ---------------------------------------------------------------------------


def test_dict_round_trip_is_lossless(raw_protocol: dict) -> None:
    once = ProtocolConfig.model_validate(raw_protocol)
    twice = ProtocolConfig.model_validate(once.model_dump())
    assert once == twice
    assert twice.model_dump() == once.model_dump()


def test_json_round_trip_is_lossless(raw_protocol: dict) -> None:
    once = ProtocolConfig.model_validate(raw_protocol)
    as_json = once.model_dump_json()
    twice = ProtocolConfig.model_validate_json(as_json)
    assert once == twice


def test_yaml_round_trip_is_lossless(raw_protocol: dict) -> None:
    once = ProtocolConfig.model_validate(raw_protocol)
    # mode="json" yields YAML-safe scalars (ISO date strings, plain lists).
    reloaded = yaml.safe_load(yaml.safe_dump(once.model_dump(mode="json")))
    twice = ProtocolConfig.model_validate(reloaded)
    assert once == twice


# ---------------------------------------------------------------------------
# Frozen config cannot be silently extended
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "extra_key_path",
    [
        ("rogue_top_level",),
        ("temporal_design", "rogue_nested"),
        ("sequence_contract", "extra_assertion_mode"),
        ("statistics", "primary_uncertainty", "extra_knob"),
    ],
)
def test_unknown_keys_are_rejected(raw_protocol: dict, extra_key_path: tuple[str, ...]) -> None:
    mutated = copy.deepcopy(raw_protocol)
    node = mutated
    for key in extra_key_path[:-1]:
        node = node[key]
    node[extra_key_path[-1]] = "surprise"
    with pytest.raises(ValidationError) as excinfo:
        ProtocolConfig.model_validate(mutated)
    assert "extra" in str(excinfo.value).lower() or "Extra inputs" in str(excinfo.value)


def test_frozen_model_rejects_attribute_mutation(protocol: ProtocolConfig) -> None:
    with pytest.raises(ValidationError):
        protocol.protocol_version = "9.9.9"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        protocol.sequence_contract.context_length_bp = 4096  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Invalid scientific values fail loudly
# ---------------------------------------------------------------------------


def _set_path(data: dict, path: tuple[str, ...], value: object) -> dict:
    mutated = copy.deepcopy(data)
    node = mutated
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return mutated


@pytest.mark.parametrize(
    "path,bad_value,needle",
    [
        (
            ("sequence_contract", "context_length_bp"),
            8193,
            "context length",
        ),
        (
            ("temporal_design", "reference_assembly"),
            "hg19",
            "reference_assembly",
        ),
        (
            ("temporal_design", "primary_label_quality_gate", "min_review_stars"),
            1,
            "review stars",
        ),
        (
            ("statistics", "primary_uncertainty", "seed"),
            42,
            "bootstrap seed",
        ),
        (
            ("statistics", "primary_uncertainty", "replicates"),
            100,
            "replicates",
        ),
        (
            ("scoring_contract", "score_definitions", "delta_primary"),
            "delta_fwd",
            "delta_primary",
        ),
        (
            ("statistics", "primary_endpoint"),
            "AUPRC",
            "primary_endpoint",
        ),
        (
            ("calibration_contract", "test_cohort_used_for_fitting"),
            "allowed_if_small",
            "test_cohort_used_for_fitting",
        ),
        (
            ("temporal_design", "t0_release", "release_date"),
            "not-a-date",
            "release_date",
        ),
        (
            ("sequence_contract", "legacy_formula_inherited"),
            True,
            "legacy_formula_inherited",
        ),
    ],
)
def test_invalid_scientific_values_fail_loudly(
    raw_protocol: dict, path: tuple[str, ...], bad_value: object, needle: str
) -> None:
    mutated = _set_path(raw_protocol, path, bad_value)
    with pytest.raises(ValidationError) as excinfo:
        ProtocolConfig.model_validate(mutated)
    message = str(excinfo.value)
    assert needle in message, f"expected '{needle}' in error message:\n{message}"


def test_missing_required_block_fails(raw_protocol: dict) -> None:
    mutated = copy.deepcopy(raw_protocol)
    del mutated["sequence_contract"]
    with pytest.raises(ValidationError):
        ProtocolConfig.model_validate(mutated)


def test_load_protocol_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_protocol(tmp_path / "does_not_exist.yaml")


def test_load_protocol_non_mapping_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_protocol(bad)


# ---------------------------------------------------------------------------
# Scientific config is separated from deployment config
# ---------------------------------------------------------------------------


def test_runtime_config_cannot_carry_scientific_fields() -> None:
    with pytest.raises(ValidationError):
        RuntimeConfig(context_length_bp=8192)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        RuntimeConfig(primary_endpoint="AUROC")  # type: ignore[call-arg]


def test_protocol_config_cannot_carry_deployment_fields(raw_protocol: dict) -> None:
    mutated = copy.deepcopy(raw_protocol)
    mutated["modal_app_name"] = "evovariant-tr-v2"
    with pytest.raises(ValidationError):
        ProtocolConfig.model_validate(mutated)


def test_runtime_config_defaults_are_deployment_only() -> None:
    runtime = RuntimeConfig()
    assert runtime.gpu == "H100"
    assert runtime.modal_app_name == "evovariant-tr-v2"
    # Deployment config exposes no scientific knobs at all.
    scientific_fields = {
        "context_length_bp",
        "min_review_stars",
        "seed",
        "replicates",
        "primary_endpoint",
        "reference_assembly",
    }
    assert scientific_fields.isdisjoint(RuntimeConfig.model_fields)
