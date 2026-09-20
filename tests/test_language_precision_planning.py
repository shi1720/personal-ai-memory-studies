"""Independent numerical and contract checks for the fixed planning gate."""
from copy import deepcopy
from math import sqrt
from pathlib import Path
from statistics import NormalDist
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from language_precision_planning import CONTRAST_KEYS, plan_precision


def constant_family(value=0.0):
    return {key: [value] * 60 for key in CONTRAST_KEYS}


class LanguagePrecisionPlanningChecks(unittest.TestCase):
    def test_constants_have_zero_dispersion_even_with_large_positive_effect(self):
        report = plan_precision(constant_family(4.0))
        self.assertTrue(report["complete"])
        self.assertTrue(report["joint_go"])
        self.assertEqual(report["decision"], "GO")
        self.assertEqual(len(report["contrasts"]), 8)
        for row in report["contrasts"].values():
            self.assertEqual(row["sample_sd"], 0.0)
            self.assertEqual(row["bootstrap_sd_upper_95_quantile"], 0.0)
            self.assertEqual(row["projected_adjusted_half_width"], 0.0)
        self.assertEqual(report["settings"]["confirmation_users"], 200)
        self.assertEqual(report["settings"]["family_size"], 8)
        self.assertEqual(report["settings"]["target_half_width"], 0.10)

    def test_alternating_bounds_have_independently_known_upper_sd(self):
        data = constant_family()
        data[CONTRAST_KEYS[0]] = [-4.0, 4.0] * 30
        report = plan_precision(data)
        row = report["contrasts"][CONTRAST_KEYS[0]]
        # A balanced +/-4 bootstrap draw has the maximum possible sample SD.
        # More than 5% of draws are balanced for this seed, so it is also q95.
        expected_sd = sqrt(16.0 * 60.0 / 59.0)
        expected_half_width = NormalDist().inv_cdf(1 - 0.05 / 16) * expected_sd / sqrt(200)
        self.assertAlmostEqual(row["sample_sd"], expected_sd, places=13)
        self.assertAlmostEqual(row["bootstrap_sd_upper_95_quantile"], expected_sd, places=13)
        self.assertAlmostEqual(row["projected_adjusted_half_width"], expected_half_width, places=13)
        self.assertFalse(row["meets_target"])
        self.assertFalse(report["joint_go"])
        self.assertEqual(report["decision"], "NO_GO")
        self.assertEqual(sum(not x["meets_target"] for x in report["contrasts"].values()), 1)

    def test_low_dispersion_passes_and_sign_does_not_affect_gate(self):
        positive = {key: [0.99, 1.01] * 30 for key in CONTRAST_KEYS}
        negative = {key: [-x for x in values] for key, values in positive.items()}
        a = plan_precision(positive)
        b = plan_precision(negative)
        self.assertTrue(a["joint_go"])
        self.assertEqual(a, b)

    def test_fixed_half_width_threshold_separates_near_boundary_cases(self):
        critical = NormalDist().inv_cdf(1 - 0.05 / 16)
        boundary_amplitude = 0.10 * sqrt(200) / (critical * sqrt(60 / 59))
        for factor, expected in ((0.999999, True), (1.000001, False)):
            data = constant_family()
            amplitude = boundary_amplitude * factor
            data[CONTRAST_KEYS[0]] = [-amplitude, amplitude] * 30
            result = plan_precision(data)
            with self.subTest(factor=factor):
                self.assertEqual(result["joint_go"], expected)
                half_width = result["contrasts"][CONTRAST_KEYS[0]]["projected_adjusted_half_width"]
                self.assertAlmostEqual(half_width, 0.10 * factor, places=13)

    def test_bootstrap_sd_quantile_matches_independent_variance_formula(self):
        data = constant_family()
        values = np.array([-1.0, 0.25, 0.5, 2.0] * 15)
        data[CONTRAST_KEYS[0]] = values
        rng = np.random.Generator(np.random.PCG64(20260923))
        draws = values[rng.integers(0, 60, size=(20000, 60))]
        # Independent raw-moment sample-variance calculation and interpolation.
        variance = ((draws * draws).sum(axis=1) - draws.sum(axis=1) ** 2 / 60) / 59
        ordered_sds = np.sort(np.sqrt(variance))
        position = 0.95 * (20000 - 1)
        lower = int(position)
        expected_upper = ordered_sds[lower] + (position - lower) * (ordered_sds[lower + 1] - ordered_sds[lower])
        actual = plan_precision(data)["contrasts"][CONTRAST_KEYS[0]]
        self.assertAlmostEqual(actual["bootstrap_sd_upper_95_quantile"], expected_upper, places=13)

    def test_mapping_order_is_canonical_and_inputs_are_not_mutated(self):
        original = {key: [-0.3 + index * 0.01, 0.7] * 30
                    for index, key in enumerate(CONTRAST_KEYS)}
        preserved = deepcopy(original)
        reversed_mapping = dict(reversed(list(original.items())))
        a = plan_precision(original)
        b = plan_precision(reversed_mapping)
        self.assertEqual(a, b)
        self.assertEqual(tuple(a["contrasts"]), CONTRAST_KEYS)
        self.assertEqual(original, preserved)

    def test_rejects_incomplete_extra_unknown_and_nonmapping_input(self):
        missing = constant_family()
        missing.pop(CONTRAST_KEYS[0])
        extra = constant_family()
        extra["extra"] = [0.0] * 60
        renamed = constant_family()
        renamed["incorrect_contrast"] = renamed.pop(CONTRAST_KEYS[0])
        for invalid in (missing, extra, renamed, [], None):
            with self.subTest(invalid_type=type(invalid).__name__):
                with self.assertRaises(ValueError):
                    plan_precision(invalid)

    def test_rejects_malformed_values_and_dimensions(self):
        bad_values = [True, np.bool_(False), float("nan"), float("inf"),
                      -float("inf"), 4.000001, -4.000001, "0.1", None, 1 + 0j,
                      10 ** 1000]
        invalid_arrays = ([0.0] * 59, [0.0] * 61, np.zeros((60, 1)),
                          np.zeros(()), "0" * 60, iter([0.0] * 60))
        for bad in bad_values:
            data = constant_family()
            data[CONTRAST_KEYS[0]][5] = bad
            with self.subTest(value=repr(bad)):
                with self.assertRaises(ValueError):
                    plan_precision(data)
        for bad in invalid_arrays:
            data = constant_family()
            data[CONTRAST_KEYS[0]] = bad
            with self.subTest(array_type=type(bad).__name__):
                with self.assertRaises(ValueError):
                    plan_precision(data)


if __name__ == "__main__":
    unittest.main()
