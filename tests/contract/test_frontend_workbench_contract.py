"""Contract checks for the research-workbench navigation and empty states."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKBENCH = REPO_ROOT / "apps" / "web" / "src" / "app" / "analysis" / "page.tsx"


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
