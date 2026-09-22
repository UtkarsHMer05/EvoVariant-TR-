"""Contract checks for the research-workbench navigation and empty states."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKBENCH = REPO_ROOT / "apps" / "web" / "src" / "app" / "analysis" / "page.tsx"
REGISTRY_ROUTE = REPO_ROOT / "apps" / "web" / "src" / "app" / "api" / "registry" / "route.ts"
RESEARCH_STATUS_ROUTE = (
    REPO_ROOT / "apps" / "web" / "src" / "app" / "api" / "research" / "status" / "route.ts"
)


def test_workbench_exposes_all_required_top_level_areas() -> None:
    source = WORKBENCH.read_text(encoding="utf-8")
    required_labels = (
        "Overview",
        "Single Variant Research Analysis",
        "Temporal VUS Explorer",
        "Model Benchmark",
        "Representation / Layer Analysis",
        "Training & Hyperparameter Experiments",
        "Fine-Tuning Experiments",
        "Ensemble Analysis",
        "Calibration & Abstention",
        "Robustness & Ablation",
        "Error Analysis",
        "Batch VCF/CSV",
        "Methods & Provenance",
        "Experiment Registry",
    )
    for label in required_labels:
        assert label in source


def test_workbench_does_not_derive_clinical_labels_or_placeholder_metrics() -> None:
    source = WORKBENCH.read_text(encoding="utf-8")
    assert "No clinical label is derived here" in source
    assert "invent metrics" in source
    assert "Calibrated study probability" in source
    assert "Uncertainty / abstention" in source
    assert "Comparator evidence" in source
    assert "pathogenic" not in source.lower()
    assert "benign" not in source.lower()


def test_registry_surface_is_read_only_and_metadata_only() -> None:
    source = REGISTRY_ROUTE.read_text(encoding="utf-8")
    assert "export async function GET" in source
    assert "completed_scientific_run_count" in source
    assert "artifact_count" in source
    assert "metrics" not in source.lower()
    assert "model_source" not in source
    assert "license_record" not in source


def test_workbench_reads_hash_verified_development_evidence() -> None:
    page = WORKBENCH.read_text(encoding="utf-8")
    route = RESEARCH_STATUS_ROUTE.read_text(encoding="utf-8")
    assert "Development evidence" in page
    assert "/api/research/status" in page
    assert "locked_test_evaluated" in route
    assert "output_hashes" in route
    assert "context_length.json" not in page
