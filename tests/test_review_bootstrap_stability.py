"""Test pairing and batching against a separately constructed seeded sample."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from review_bootstrap_stability import paired_values, sampled_means, zero_status


class ReviewBootstrapStabilityChecks(unittest.TestCase):
    def test_batching_preserves_exact_resampling_sequence(self):
        values = np.array([-1.0, 0.25, 2.0, 4.0])
        rng = np.random.default_rng(101)
        indices = rng.integers(0, 4, size=(17, 4))
        expected = np.array([sum(values[int(i)] for i in row) / 4 for row in indices])
        for batch in (1, 3, 17, 100):
            np.testing.assert_array_equal(sampled_means(values, 101, 17, batch), expected)

    def test_pairing_uses_user_identity_and_preserves_left_order(self):
        rows = [{'user_row': user, 'system': system, 'mae': mae, 'targets': 16}
                for user, system, mae in [(9, 'a', 1.0), (4, 'a', 0.75),
                                          (4, 'b', 0.25), (9, 'b', 0.1)]]
        np.testing.assert_array_equal(paired_values(rows, 'a', 'b', 2), [0.9, 0.5])
        with self.assertRaises(ValueError):
            paired_values(rows + [rows[0]], 'a', 'b', 2)
        with self.assertRaises(ValueError):
            paired_values(rows[:-1], 'a', 'b', 2)
        rows[-1]['targets'] = 15
        with self.assertRaises(ValueError):
            paired_values(rows, 'a', 'b', 2)

    def test_zero_boundary_is_not_exclusion(self):
        self.assertEqual(zero_status([0, 1]), 'includes_zero')
        self.assertEqual(zero_status([-1, 0]), 'includes_zero')
        self.assertEqual(zero_status([0.1, 1]), 'positive')
        self.assertEqual(zero_status([-1, -0.1]), 'negative')


if __name__ == '__main__':
    unittest.main()
