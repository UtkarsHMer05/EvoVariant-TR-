import unittest

from evovariant_tr.adaptation.data import VariantRow, paired_sequences
from evovariant_tr.sequence_mutate import reverse_complement


class FakeFasta:
    def __init__(self):
        self._records = {"1": "ACGT" * 3000}

    def __getitem__(self, key):
        if key not in self._records:
            raise KeyError(key)
        return self._records[key]


class SequencePairTest(unittest.TestCase):
    def test_reference_and_reverse_complement_lengths(self):
        row = VariantRow("1", 5000, "T", "C", "GENE", 0, "id")
        pair = paired_sequences(FakeFasta(), row, window_size=128)
        self.assertEqual(len(pair.reference), 128)
        self.assertEqual(len(pair.reference), len(pair.alternate))
        self.assertEqual(reverse_complement(pair.reference), pair.reference_rc)
        self.assertEqual(reverse_complement(pair.alternate), pair.alternate_rc)
        self.assertNotEqual(pair.reference, pair.alternate)


if __name__ == "__main__":
    unittest.main()
