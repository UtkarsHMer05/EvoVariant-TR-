import unittest
from pathlib import Path

from evovariant_tr.adaptation.data import (
    DataIntegrityError,
    VariantRow,
    load_formal_rows,
    load_train_rows,
    verify_formal_data,
    verify_reference_rows,
)

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
        self.assertFalse(
            {row.gene_symbol for row in train} & {row.gene_symbol for row in validation}
        )
        self.assertFalse(
            {row.normalized_variant_id for row in train}
            & {row.normalized_variant_id for row in validation}
        )

    def test_model_selection_loader_reads_only_train(self):
        rows = load_train_rows(ROOT)
        self.assertEqual(len(rows), 3199)
        self.assertTrue(all(row.label in (0, 1) for row in rows))

    def test_reference_ref_allele_check(self):
        row = VariantRow("1", 4096, "A", "T", "GENE", 1, "1:4096:A:T")
        matching = "C" * 4095 + "A" + "C" * 4096
        self.assertEqual(verify_reference_rows({"chr1": matching}, [row]), 1)
        with self.assertRaises(DataIntegrityError):
            verify_reference_rows({"chr1": "C" * 8192}, [row])


if __name__ == "__main__":
    unittest.main()
