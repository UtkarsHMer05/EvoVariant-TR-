import unittest

from evovariant_tr.adaptation.metrics import binary_metrics


class AdaptationMetricsTest(unittest.TestCase):
    def test_perfect_scores_and_confusion(self):
        result = binary_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
        self.assertEqual(result["auroc"], 1.0)
        self.assertEqual(result["auprc"], 1.0)
        self.assertEqual(result["confusion_matrix"], {"tn": 2, "fp": 0, "fn": 0, "tp": 2})

    def test_constant_class_is_explicit(self):
        result = binary_metrics([1, 1], [0.6, 0.7])
        self.assertIsNone(result["auroc"])
        self.assertIsNone(result["auprc"])

    def test_probability_mae_is_reported_as_supplementary_metric(self):
        result = binary_metrics([0, 1], [0.1, 0.7])
        self.assertAlmostEqual(result["probability_mae"], 0.2)


if __name__ == "__main__":
    unittest.main()
