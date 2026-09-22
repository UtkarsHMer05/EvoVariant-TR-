import json
import pickle
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from evovariant_tr.adaptation import (
    PREDECLARED_SEEDS,
    calibration,
    checkpointing,
    folds,
    selection_seed_allowed,
    state,
    statistics,
)
from evovariant_tr.adaptation.data import (
    DataIntegrityError,
    VariantRow,
    iter_paired_sequences,
    reference_window,
    resolve_contig,
)
from evovariant_tr.adaptation.models import _last_hidden

ROOT = Path(__file__).resolve().parents[2]


class FakeTensorState:
    def cpu(self):
        return self


class ModelOutputTest(unittest.TestCase):
    def test_hidden_states_support_masked_lm_output(self):
        final_hidden = object()
        output = SimpleNamespace(hidden_states=(object(), final_hidden))
        self.assertIs(_last_hidden(output), final_hidden)


class SeedSelectionTest(unittest.TestCase):
    def test_only_predeclared_robustness_seeds_can_vary(self):
        self.assertEqual(PREDECLARED_SEEDS, (42, 1337, 2026))
        self.assertTrue(selection_seed_allowed(42, 42))
        self.assertTrue(selection_seed_allowed(1337, 42, robustness=True))
        self.assertTrue(selection_seed_allowed(2026, 42, robustness=True))
        self.assertFalse(selection_seed_allowed(42, 42, robustness=True))
        self.assertFalse(selection_seed_allowed(1337, 42))
        self.assertFalse(selection_seed_allowed(7, 42, robustness=True))


class CalibrationTest(unittest.TestCase):
    def test_temperature_and_abstention(self):
        labels = [0, 0, 1, 1]
        logits = [-2.0, -1.0, 1.0, 2.0]
        temperature = calibration.fit_temperature(labels, logits)
        self.assertGreater(temperature, 0)
        probabilities = calibration.apply_temperature(logits, temperature)
        self.assertEqual(len(probabilities), len(labels))
        self.assertEqual(calibration.select_abstention_threshold(labels, probabilities)["mcc"], 1.0)
        with self.assertRaises(ValueError):
            calibration.apply_temperature(logits, 0)
        with self.assertRaises(ValueError):
            calibration.fit_temperature([1], [0.0, 1.0])
        with self.assertRaises(ValueError):
            calibration.select_abstention_threshold(labels, probabilities[:2])

    def test_calibrator_comparison_and_selective_metrics(self):
        labels = [0, 0, 0, 1, 1, 1]
        logits = [-3.0, -1.0, 0.2, 0.3, 1.0, 3.0]
        model = calibration.fit_calibrators(labels, logits)
        self.assertEqual(model["fit_scope"], "TRAIN_OOF_ONLY")
        self.assertIn(
            model["selected_method"], {"uncalibrated", "temperature", "platt", "isotonic"}
        )
        probabilities = calibration.apply_calibrator(logits, model)
        self.assertEqual(len(probabilities), len(labels))
        self.assertTrue(all(0 <= value <= 1 for value in probabilities))
        coverage = calibration.selective_metrics(labels, [0.05, 0.15, 0.35, 0.7, 0.85, 0.95])
        self.assertEqual([point["target_coverage"] for point in coverage], [0.5, 0.75, 0.9, 1.0])
        self.assertEqual(coverage[-1]["coverage"], 1.0)
        self.assertEqual(coverage[-1]["risk"], coverage[-1]["error_rate"])
        fixed = calibration.selective_metrics_at_thresholds(
            [0, 1, 1],
            [0.95, 0.7, 0.3],
            [
                {"target_coverage": 0.5, "confidence_threshold": 0.8},
                {"target_coverage": 0.9, "confidence_threshold": 0.7},
            ],
        )
        self.assertEqual([point["coverage"] for point in fixed], [1 / 3, 1.0])
        self.assertEqual([point["risk"] for point in fixed], [1.0, 2 / 3])
        none_selected = calibration.selective_metrics_at_thresholds(
            [0, 1], [0.6, 0.4], [{"target_coverage": 0.5, "confidence_threshold": 1.0}]
        )
        self.assertIsNone(none_selected[0]["risk"])
        with self.assertRaises(ValueError):
            calibration.fit_calibrators([1, 1], [0.0, 1.0])
        for method in ("uncalibrated", "temperature", "platt", "isotonic"):
            candidate = dict(model, selected_method=method)
            self.assertEqual(len(calibration.apply_calibrator(logits, candidate)), len(labels))
        with self.assertRaises(ValueError):
            calibration.fit_platt([1], [0.0])
        with self.assertRaises(ValueError):
            calibration._fit_isotonic([1], [0.0])
        with self.assertRaises(ValueError):
            calibration._apply_isotonic([0.0], {"upper_bounds": [], "values": []})
        with self.assertRaises(ValueError):
            calibration.apply_calibrator(
                logits, {"selected_method": "temperature", "temperature": None}
            )
        with self.assertRaises(ValueError):
            calibration.apply_calibrator(logits, {"selected_method": "platt", "platt": None})
        with self.assertRaises(ValueError):
            calibration.apply_calibrator(logits, {"selected_method": "isotonic", "isotonic": None})
        with self.assertRaises(ValueError):
            calibration.apply_calibrator(logits, {"selected_method": "unknown"})
        with self.assertRaises(ValueError):
            calibration.selective_metrics(labels, [0.1], [0.5])
        with self.assertRaises(ValueError):
            calibration.selective_metrics(labels, [0.1] * len(labels), [1.1])


class StatisticsTest(unittest.TestCase):
    def test_gene_bootstrap_and_holm(self):
        labels = [0, 1, 0, 1, 0, 1]
        scores = [0.1, 0.9, 0.2, 0.8, 0.3, 0.7]
        genes = ["A", "A", "B", "B", "C", "C"]
        report = statistics.gene_bootstrap_auc(labels, scores, genes, replicates=40, seed=7)
        self.assertEqual(report["replicates"], 40)
        self.assertLessEqual(report["ci_lower"], report["ci_upper"])
        self.assertEqual(statistics.holm_adjust([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
        with self.assertRaises(ValueError):
            statistics.gene_bootstrap_auc([1], [0.1], ["A"], replicates=0)
        with self.assertRaises(ValueError):
            statistics.gene_bootstrap_auc([0, 1], [0.1], ["A", "B"])

    def test_gene_metric_and_paired_bootstrap(self):
        labels = [0, 1, 0, 1, 0, 1]
        left = [0.2, 0.8, 0.4, 0.6, 0.3, 0.7]
        right = [0.1, 0.9, 0.2, 0.8, 0.3, 0.7]
        genes = ["A", "A", "B", "B", "C", "C"]
        summary = statistics.gene_bootstrap_metrics(labels, right, genes, replicates=40, seed=7)
        self.assertEqual(set(summary), set(statistics.CORE_METRICS))
        paired = statistics.paired_gene_bootstrap(
            labels, left, right, genes, replicates=40, seed=7
        )
        self.assertEqual(set(paired), set(statistics.CORE_METRICS))
        self.assertTrue(all(0 <= value["two_sided_p"] <= 1 for value in paired.values()))
        with self.assertRaises(ValueError):
            statistics.holm_adjust([0.1, 1.1])
        with self.assertRaises(ValueError):
            statistics.gene_bootstrap_metrics([0], [0.1], ["A"], replicates=0)
        with self.assertRaises(ValueError):
            statistics.gene_bootstrap_metrics([], [], [], replicates=10)
        with self.assertRaises(ValueError):
            statistics.paired_gene_bootstrap([0, 1], [0.1], [0.2, 0.3], ["A", "B"])
        with self.assertRaises(ValueError):
            statistics.paired_gene_bootstrap([], [], [], [])
        one_class = statistics.paired_gene_bootstrap(
            [0, 0], [0.1, 0.2], [0.2, 0.3], ["A", "B"], replicates=4
        )
        self.assertNotIn("auroc", one_class)


class FoldAdapterTest(unittest.TestCase):
    def test_fixed_three_fold_adapter_and_protocol_guard(self):
        class Indices(list):
            def tolist(self):
                return list(self)

        class Splitter:
            def __init__(self, n_splits, shuffle, random_state):
                self.settings = (n_splits, shuffle, random_state)

            def split(self, samples, labels, groups):
                self.inputs = (samples, labels, groups)
                yield Indices([0, 1]), Indices([2, 3])
                yield Indices([2, 3]), Indices([0, 1])
                yield Indices([0, 2]), Indices([1, 3])

        fake_model_selection = SimpleNamespace(StratifiedGroupKFold=Splitter)
        fake_sklearn = SimpleNamespace(model_selection=fake_model_selection)
        rows = [SimpleNamespace(label=index % 2, gene_symbol=f"G{index}") for index in range(4)]
        with patch.dict(
            sys.modules,
            {
                "sklearn": fake_sklearn,
                "sklearn.model_selection": fake_model_selection,
            },
        ):
            result = folds.make_grouped_folds(rows, seed=13)
        self.assertEqual(len(result), 3)
        with self.assertRaises(ValueError):
            folds.make_grouped_folds(rows, n_splits=2)


class CheckpointTest(unittest.TestCase):
    def test_save_load_and_protocol_guards(self):
        class Cuda:
            states = None

            @staticmethod
            def is_available():
                return True

            @staticmethod
            def get_rng_state_all():
                return [FakeTensorState()]

            @classmethod
            def set_rng_state_all(cls, values):
                cls.states = values

        torch = SimpleNamespace(
            cuda=Cuda,
            get_rng_state=FakeTensorState,
            set_rng_state=lambda value: None,
            save=lambda value, path: path.write_bytes(pickle.dumps(value)),
            load=lambda path, map_location: pickle.loads(path.read_bytes()),
        )

        class Model:
            weights = {"weight": 1}

            def state_dict(self):
                return self.weights.copy()

            def load_state_dict(self, values):
                self.weights = values

        class Optimizer:
            values = {"step": 1}

            def state_dict(self):
                return self.values.copy()

            def load_state_dict(self, values):
                self.values = values

        model, optimizer = Model(), Optimizer()
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {"torch": torch}):
            path = Path(directory) / "checkpoint.pt"
            checkpointing.save_checkpoint(
                path,
                model=model,
                optimizer=optimizer,
                epoch=2,
                metrics={"auc": 0.8},
                protocol_hash="protocol",
                metadata={"revision": "pinned"},
            )
            model.weights = {"weight": -1}
            payload = checkpointing.load_checkpoint(
                path,
                model=model,
                optimizer=optimizer,
                expected_protocol_hash="protocol",
                expected_metadata={"revision": "pinned"},
            )
            self.assertEqual(payload["epoch"], 2)
            self.assertEqual(model.weights, {"weight": 1})
            self.assertIsNotNone(Cuda.states)
            with self.assertRaises(ValueError):
                checkpointing.load_checkpoint(path, model=model, expected_protocol_hash="other")
            with self.assertRaises(ValueError):
                checkpointing.load_checkpoint(
                    path, model=model, expected_metadata={"revision": "other"}
                )


class StateTest(unittest.TestCase):
    def test_atomic_history_and_missing_artifact_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            artifact = directory / "result.json"
            artifact.write_text("{}\n", encoding="utf-8")
            state_path = directory / "state.json"
            state.record_stage(
                state_path,
                project_root=ROOT,
                stage="FIRST",
                artifacts=(artifact,),
                details={"ok": True},
            )
            report = state.record_stage(state_path, project_root=ROOT, stage="SECOND")
            stored = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual([item["stage"] for item in stored["history"]], ["FIRST", "SECOND"])
            self.assertEqual(report["stage"], "SECOND")
            with self.assertRaises(FileNotFoundError):
                state.record_stage(
                    state_path,
                    project_root=ROOT,
                    stage="MISSING",
                    artifacts=(directory / "absent",),
                )


class DataHelpersTest(unittest.TestCase):
    def test_reference_boundaries_and_iterator(self):
        fasta = {"chr1": "ACGT" * 2500}
        self.assertEqual(resolve_contig(fasta, "1"), "chr1")
        row = VariantRow("1", 4096, "T", "A", "GENE", 0, "id")
        window, offset = reference_window(fasta, row, window_size=128)
        self.assertEqual(len(window), 128)
        self.assertEqual(window[offset], "T")
        self.assertEqual(len(list(iter_paired_sequences(fasta, [row], window_size=128))), 1)
        with self.assertRaises(ValueError):
            reference_window(fasta, row, window_size=127)
        with self.assertRaises(DataIntegrityError):
            resolve_contig(fasta, "unavailable")


if __name__ == "__main__":
    unittest.main()
