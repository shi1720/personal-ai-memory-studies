"""Invented-data checks of prospective joint confirmation uncertainty."""
from copy import deepcopy
from math import floor, fsum
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from language_confirmation_uncertainty import (
    CONTRAST_KEYS, _direction, bootstrap_confirmation,
)


def family(value=0.0):
    return {key: [value] * 200 for key in CONTRAST_KEYS}


def reference_quantile(values, probability):
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = floor(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


class ConfirmationUncertaintyChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        x = np.asarray([((i * 37) % 101 - 50) / 25 for i in range(200)])
        z = np.asarray([((i * 13) % 59 - 29) / 20 for i in range(200)])
        columns = (x, x.copy(), -x, x / 2, x + .25, z, -z, z / 4)
        cls.inputs = dict(zip(CONTRAST_KEYS, columns))
        cls.original = deepcopy(cls.inputs)
        cls.result = bootstrap_confirmation(cls.inputs)

    def test_full_family_and_prespecified_settings(self):
        expected_keys = tuple(sorted(
            f"{comparison}__writer_{writer}__reader_{reader}"
            for comparison in ("native_minus_full", "native_minus_matched_summary")
            for writer in ("phi", "qwen") for reader in ("phi", "qwen")
        ))
        self.assertEqual(CONTRAST_KEYS, expected_keys)
        self.assertEqual(tuple(self.result["contrasts"]), expected_keys)
        self.assertTrue(self.result["complete"])
        self.assertEqual(self.result["users"], 200)
        settings = self.result["settings"]
        self.assertEqual(settings["bootstrap_resamples"], 200000)
        self.assertEqual(settings["bootstrap_seed"], 20260924)
        self.assertEqual(settings["batch_size"], 1000)
        self.assertEqual(settings["family_size"], 8)
        self.assertEqual(settings["ordinary_quantiles"], [.025, .975])
        self.assertEqual(settings["bonferroni_quantiles"], [.003125, .996875])
        self.assertEqual(settings["direction_tolerance"], 1e-12)
        self.assertIn("do not guarantee", self.result["scope"])
        self.assertIn("does not establish equivalence", self.result["scope"])

    def test_independent_frequency_weighted_reference_all_eight(self):
        # Different implementation: multinomial user counts followed by weighted
        # sums, with hand-written order-statistic interpolation, not np.quantile.
        rng = np.random.Generator(np.random.PCG64(20260924))
        matrix = np.column_stack([self.inputs[key] for key in CONTRAST_KEYS])
        samples = np.empty((200000, 8))
        for start in range(0, 200000, 1000):
            draws = rng.integers(0, 200, size=(1000, 200))
            flat_ids = (draws + np.arange(1000)[:, None] * 200).ravel()
            counts = np.bincount(flat_ids, minlength=200000).reshape(1000, 200)
            samples[start:start + 1000] = counts @ matrix / 200
        for column, key in enumerate(CONTRAST_KEYS):
            result = self.result["contrasts"][key]
            self.assertAlmostEqual(result["mean_difference"],
                                   fsum(self.inputs[key]) / 200, places=13)
            for name, quantiles in (("ordinary_95", (.025, .975)),
                                    ("bonferroni_99_375", (.003125, .996875))):
                for side, probability in zip(("lower", "upper"), quantiles):
                    expected = reference_quantile(samples[:, column], probability)
                    self.assertAlmostEqual(result[name][side], expected, places=12)

    def test_shared_indices_preserve_identical_negative_and_affine_columns(self):
        rows = [self.result["contrasts"][key] for key in CONTRAST_KEYS]
        self.assertEqual(rows[0], rows[1])
        for name in ("ordinary_95", "bonferroni_99_375"):
            self.assertAlmostEqual(rows[2][name]["lower"], -rows[0][name]["upper"], places=13)
            self.assertAlmostEqual(rows[2][name]["upper"], -rows[0][name]["lower"], places=13)
            for side in ("lower", "upper"):
                self.assertAlmostEqual(rows[3][name][side], rows[0][name][side] / 2, places=13)
                self.assertAlmostEqual(rows[4][name][side], rows[0][name][side] + .25, places=13)

    def test_mapping_order_determinism_and_no_mutation(self):
        reversed_input = dict(reversed(list(self.inputs.items())))
        self.assertEqual(bootstrap_confirmation(reversed_input), self.result)
        for key in CONTRAST_KEYS:
            np.testing.assert_array_equal(self.inputs[key], self.original[key])

    def test_constants_and_zero_tolerance(self):
        values = [-4., 4., 0., -1e-12, 1e-12, -2e-12, 2e-12, .5]
        result = bootstrap_confirmation({key: [value] * 200
                                         for key, value in zip(CONTRAST_KEYS, values)})
        expected_directions = ["native_lower_error", "native_higher_error", "inconclusive",
                               "inconclusive", "inconclusive", "native_lower_error",
                               "native_higher_error", "native_higher_error"]
        for key, value, direction in zip(CONTRAST_KEYS, values, expected_directions):
            row = result["contrasts"][key]
            self.assertAlmostEqual(row["mean_difference"], value, places=15)
            for name in ("ordinary_95", "bonferroni_99_375"):
                self.assertAlmostEqual(row[name]["lower"], value, places=15)
                self.assertAlmostEqual(row[name]["upper"], value, places=15)
                self.assertNotIn("direction", row[name])
            self.assertEqual(row["direction"], direction)

    def test_endpoint_rule_is_strict_and_inconclusive_is_not_equivalence(self):
        for lower, upper in ((-1, 1), (0, 0), (-1, -1e-12), (1e-12, 1)):
            self.assertEqual(_direction(lower, upper), "inconclusive")
        self.assertEqual(_direction(-1, -1.01e-12), "native_lower_error")
        self.assertEqual(_direction(1.01e-12, 1), "native_higher_error")

    def test_reject_incomplete_extra_or_nonmapping_family(self):
        missing = family()
        del missing[CONTRAST_KEYS[0]]
        extra = family()
        extra["unplanned"] = [0] * 200
        wrong = family()
        wrong["changed"] = wrong.pop(CONTRAST_KEYS[0])
        for value in (None, [], {}, missing, extra, wrong):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                bootstrap_confirmation(value)

    def test_reject_wrong_size_shape_or_container(self):
        for values in ([0] * 199, [0] * 201, np.zeros((200, 1)), np.array(0),
                       [[0]] * 200, "0" * 200, iter([0] * 200), None):
            data = family()
            data[CONTRAST_KEYS[0]] = values
            with self.subTest(value_type=type(values).__name__), self.assertRaises(ValueError):
                bootstrap_confirmation(data)

    def test_reject_nonreal_nonfinite_boolean_and_outside_bound_values(self):
        for value in (True, False, np.bool_(True), "1", 1j, None, float("nan"),
                      float("inf"), -float("inf"), 4.000001, -4.000001, 10 ** 1000):
            data = family()
            data[CONTRAST_KEYS[-1]][-1] = value
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                bootstrap_confirmation(data)

    def test_no_runtime_overrides(self):
        for name in ("seed", "resamples", "alpha", "batch_size", "users"):
            with self.subTest(name=name), self.assertRaises(TypeError):
                bootstrap_confirmation(family(), **{name: 1})


if __name__ == "__main__":
    unittest.main()
