from pathlib import Path
import unittest

from evovariant_tr.adaptation.data import load_formal_rows, verify_formal_data


ROOT = Path(__file__).resolve().parents[2]


class FormalDataContractTest(unittest.TestCase):
    def test_hashes_and_split_invariants(self):
        report = verify_formal_data(ROOT)
        self.assertEqual(report["formal_record_count"], 4000)
        self.assertEqual(report["train_record_count"], 3199)
        self.assertEqual(report["validation_record_count"], 801)
        self.assertEqual(report["locked_id_overlap"], 0)

    def test_rows_are_disjoint_by_gene_and_id(self):
        train, validation = load_formal_rows(ROOT)
        self.assertFalse({row.gene_symbol for row in train} & {row.gene_symbol for row in validation})
        self.assertFalse(
            {row.normalized_variant_id for row in train}
            & {row.normalized_variant_id for row in validation}
        )


if __name__ == "__main__":
    unittest.main()

