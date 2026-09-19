from itertools import product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from partial_calibration import PartialCalibration, crc_policy, shipped_loss_row


class CalibrationTests(unittest.TestCase):
    def test_cached_rows_and_budget_zero(self):
        p = PartialCalibration(10, 3, 0.2, cached={i: (0, 0, 0) for i in range(9)})
        result = p.run(lambda i: self.fail("Should not execute"), budget=0)
        self.assertEqual(result["policy"], 0)
        self.assertTrue(result["exact"])
        self.assertEqual(result["reader_calls"], 0)

    def test_partial_stops_before_all_calls(self):
        p = PartialCalibration(10, 3, 0.4)
        result = p.run(lambda i: (0, 0, 0))
        self.assertEqual(result["policy"], 0)
        self.assertTrue(result["exact"])
        self.assertLess(result["reader_calls"], 10)

    def test_stale_rows_can_select_a_more_permissive_policy(self):
        old = [(0, 0, 0)] * 10
        new = [(1, 1, 0)] * 10
        self.assertLess(crc_policy(old, 0.2), crc_policy(new, 0.2))
        self.assertEqual(PartialCalibration(10, 3, 0.2).run(lambda i: new[i])["policy"], 2)

    def test_reject_invalid_rows(self):
        for row in [(0, 1, 0), (1, 1, 1), (float('nan'), 0, 0), (-1, 0, 0)]:
            with self.assertRaises(ValueError):
                crc_policy([row], 0.2)

    def test_loss_and_coverage_have_different_denominators(self):
        self.assertEqual(shipped_loss_row(False, 0.7, [0, 0.5, 0.8, 1.01]), (1, 1, 0, 0))
        self.assertEqual(shipped_loss_row(True, 0.7, [0, 0.5, 0.8, 1.01]), (0, 0, 0, 0))

    def test_every_small_binary_matrix_and_mask_satisfies_sandwich(self):
        patterns = [tuple(int(j < cutoff) for j in range(4)) for cutoff in range(4)]
        for n in range(1, 5):
            for matrix in product(patterns, repeat=n):
                for alpha in [0.1, 0.2, 0.4, 0.6]:
                    reference = crc_policy(matrix, alpha)
                    for mask in product([False, True], repeat=n):
                        p = PartialCalibration(n, 4, alpha,
                              cached={i: row for i, row in enumerate(matrix) if mask[i]})
                        b = p.bounds()
                        self.assertLessEqual(b.optimistic, reference)
                        self.assertGreaterEqual(b.conservative, reference)
                        if b.exact:
                            self.assertEqual(b.conservative, reference)

    def test_all_small_adaptive_runs_recover_reference(self):
        patterns = [(0, 0, 0), (1, 0, 0), (1, 1, 0)]
        for matrix in product(patterns, repeat=4):
            for alpha in [0.2, 0.4, 0.6]:
                p = PartialCalibration(4, 3, alpha)
                result = p.run(lambda i: matrix[i], priority=[0.8, 0.1, 0.9, 0.2])
                self.assertTrue(result["exact"])
                self.assertEqual(result["policy"], crc_policy(matrix, alpha))


if __name__ == "__main__":
    unittest.main()
