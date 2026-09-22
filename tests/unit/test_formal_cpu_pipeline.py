from __future__ import annotations

from scripts.run_formal_cpu_pipeline import fit_fast_stump, metric_panel

from evovariant_tr.supervised import TrainingRow


def test_formal_cpu_stump_and_metric_panel() -> None:
    rows = [
        TrainingRow("a", "TRAIN", 0, (0.0,), "GA"),
        TrainingRow("b", "TRAIN", 0, (0.1,), "GB"),
        TrainingRow("c", "TRAIN", 1, (0.9,), "GC"),
        TrainingRow("d", "TRAIN", 1, (1.0,), "GD"),
    ]
    model = fit_fast_stump(rows)
    scores = [model.predict_proba(row.features) for row in rows]
    metrics = metric_panel(scores, [row.label for row in rows])
    assert metrics["auroc"] == 1.0
    assert metrics["mcc"] == 1.0
