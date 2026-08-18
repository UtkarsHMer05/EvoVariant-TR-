"""Protocol and configuration schemas for EvoVariant-TR.

The frozen scientific protocol (``research/protocol/protocol.yaml``) is validated
against strict Pydantic models that reject unknown keys, so a frozen scientific
configuration cannot be silently extended or drifted. Runtime/deployment
configuration is a separate schema that cannot mutate scientific choices.

Design rules (Milestone 12):
- Invalid configs fail loudly with actionable ``ValidationError`` context.
- Immutable primary fields are enforced with exact-value validators.
- Scientific config is separated from deployment config.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator

PRIMARY_CONTEXT_LENGTH_BP = 8192
PRIMARY_MIN_REVIEW_STARS = 2
PRIMARY_BOOTSTRAP_REPLICATES = 2000
PRIMARY_BOOTSTRAP_SEED = 20260814
PRIMARY_DELTA_FORMULA = "(delta_fwd + delta_rc) / 2"


class StrictModel(BaseModel):
    """Base model that rejects unknown keys in every nested block."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ReleaseSpec(StrictModel):
    source: str
    release_date: date
    mutability: Literal["immutable_primary"]

    @field_validator("release_date", mode="before")
    @classmethod
    def _parse_date(cls, value: object) -> object:
        # Pydantic already parses ISO strings; this guard makes failures actionable.
        if isinstance(value, str) and not value:
            raise ValueError("release_date must be a non-empty ISO date (YYYY-MM-DD)")
        return value


class T1Outcomes(StrictModel):
    positive: str
    negative: str


class LabelQualityGate(StrictModel):
    min_review_stars: int
    mutability: Literal["immutable_primary"]

    @field_validator("min_review_stars")
    @classmethod
    def _primary_gate_is_two_stars(cls, value: int) -> int:
        if value != PRIMARY_MIN_REVIEW_STARS:
            raise ValueError(
                "primary t1 label-quality gate is frozen at >=2 review stars; "
                "changing it requires a dated protocol deviation entry"
            )
        return value


class TemporalDesign(StrictModel):
    t0_release: ReleaseSpec
    t1_release: ReleaseSpec
    reference_assembly: Literal["GRCh38"]
    primary_unit: str
    t0_state: str
    t1_outcomes: T1Outcomes
    primary_label_quality_gate: LabelQualityGate


class Estimand(StrictModel):
    question: str
    design: str
    conditional_on: str
    does_not_estimate: list[str]


class QACheckpoint(StrictModel):
    note: str
    t0_unique_vus: int
    absent_at_t1: int
    not_definitive_at_t1: int
    below_two_stars: int
    final_temporal_n: int
    n_blb: int
    n_plp: int
    gene_labels: int
    reference_mismatch_among_final_candidates: int


class ScoreDefinitions(StrictModel):
    delta_fwd: str
    delta_rc: str
    delta_primary: str

    @field_validator("delta_primary")
    @classmethod
    def _primary_orientation_formula(cls, value: str) -> str:
        if value.replace(" ", "") != PRIMARY_DELTA_FORMULA.replace(" ", ""):
            raise ValueError(
                f"delta_primary is frozen as '{PRIMARY_DELTA_FORMULA}'"
            )
        return value


class ScoringContract(StrictModel):
    model_policy: Literal["zero_shot_frozen"]
    score_definitions: ScoreDefinitions
    retain_all_raw_components: Literal[True]
    required_fields_per_variant: list[str]
    forbid_mean_only_retention: Literal[True]
    forbid_direct_clinical_label_from_raw_score: Literal[True]


class SequenceContract(StrictModel):
    context_length_bp: int
    window_convention_frozen_at_milestone: int
    assertions: list[str]
    legacy_formula_inherited: Literal[False]

    @field_validator("context_length_bp")
    @classmethod
    def _exact_context_length(cls, value: int) -> int:
        if value != PRIMARY_CONTEXT_LENGTH_BP:
            raise ValueError(
                f"primary context length is frozen at exactly {PRIMARY_CONTEXT_LENGTH_BP} bases"
            )
        return value


class CalibrationContract(StrictModel):
    test_cohort_used_for_fitting: Literal["never"]
    calibration_source: str
    primary_method: str
    fold_grouping: Literal["gene"]
    unseen_gene_analysis: str
    isotonic: str
    forbidden_test_informed_choices: list[str]


class PrimaryUncertainty(StrictModel):
    method: str
    confidence_level: float
    replicates: int
    seed: int

    @field_validator("replicates")
    @classmethod
    def _frozen_replicates(cls, value: int) -> int:
        if value != PRIMARY_BOOTSTRAP_REPLICATES:
            raise ValueError(
                f"primary bootstrap replicates are frozen at {PRIMARY_BOOTSTRAP_REPLICATES}"
            )
        return value

    @field_validator("seed")
    @classmethod
    def _frozen_seed(cls, value: int) -> int:
        if value != PRIMARY_BOOTSTRAP_SEED:
            raise ValueError(
                f"primary bootstrap seed is frozen at {PRIMARY_BOOTSTRAP_SEED}"
            )
        return value


class ConfirmatoryComparisons(StrictModel):
    resampling: str
    multiple_comparison_correction: str


class Statistics(StrictModel):
    primary_endpoint: Literal["AUROC"]
    primary_uncertainty: PrimaryUncertainty
    secondary_endpoints: list[str]
    confirmatory_comparisons: ConfirmatoryComparisons


class Comparators(StrictModel):
    core_feasible: list[str]
    conditional_preferred: str
    conditional_parity_fallback: str
    conditional_valid_subset: str
    stretch: str
    required_metadata: list[str]
    missing_scores_policy: str


class Policy(StrictModel):
    claim_safety: str
    fabrication: str
    unavailable_marker: str
    not_run_marker: str


class ProtocolConfig(StrictModel):
    """Validated, immutable representation of the frozen research protocol."""

    protocol_version: str
    frozen_date: date
    project: str
    estimand: Estimand
    temporal_design: TemporalDesign
    qa_checkpoint_validation_target_only: QACheckpoint
    scoring_contract: ScoringContract
    sequence_contract: SequenceContract
    calibration_contract: CalibrationContract
    statistics: Statistics
    comparators: Comparators
    policy: Policy


class RuntimeConfig(StrictModel):
    """Deployment-only configuration.

    Deliberately disjoint from :class:`ProtocolConfig`: runtime fields cannot
    mutate scientific choices because they live in a separate validated object.
    """

    modal_app_name: str = "evovariant-tr-v2"
    modal_volume_name: str = "evovariant-tr-model-cache"
    gpu: str = "H100"
    hf_cache_mount_path: str = "/root/.cache/huggingface"


def load_protocol(path: str | Path) -> ProtocolConfig:
    """Load and validate the frozen protocol YAML.

    Raises ``pydantic.ValidationError`` with actionable context on any invalid or
    unknown field, and ``FileNotFoundError`` if the protocol file is absent.
    """
    protocol_path = Path(path)
    if not protocol_path.is_file():
        raise FileNotFoundError(f"protocol file not found: {protocol_path}")
    with protocol_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"protocol file must contain a mapping: {protocol_path}")
    return ProtocolConfig.model_validate(raw)
