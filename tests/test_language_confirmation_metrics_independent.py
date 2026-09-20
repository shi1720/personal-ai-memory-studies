"""Independent arithmetic checks on invented confirmation inputs only."""
from copy import deepcopy
from fractions import Fraction
from math import sqrt
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import language_confirmation_metrics as candidate


READERS = ("qwen", "phi")
ARMS = ("no_history", "full_history", "native_qwen", "summary_qwen",
        "native_phi", "summary_phi", "bm25_history")


def invented_inputs():
    cases = [f"synthetic-review-{index:03d}" for index in range(200)]
    patterns = ([1, 2, 4], [2, 2, 5], [3, 3, 3])
    targets = {case: list(patterns[index % 3]) for index, case in enumerate(cases)}
    histories = {case: [1 + (index + j) % 5 for j in range(12)]
                 for index, case in enumerate(cases)}
    cells = {}
    for r, reader in enumerate(READERS):
        for a, arm in enumerate(ARMS):
            cells[(reader, arm)] = {}
            for index, case in enumerate(cases):
                valid = arm != "native_phi" and (index + a + 2 * r) % 13 != 0
                # Invalid output is deliberately not a usable vector. The full
                # pipeline fallback must ignore it without trying to parse it.
                prediction = ([1 + (index + a + 2 * r + k) % 5 for k in (0, 2, 4)]
                              if valid else ["unusable", None, float("inf")])
                cells[(reader, arm)][case] = {"valid": valid, "predictions": prediction}
    return cases, targets, histories, cells


def independent_user(predictions, targets):
    errors = [Fraction(p) - Fraction(t) for p, t in zip(predictions, targets)]
    pair_scores = []
    for left, right in ((0, 1), (0, 2), (1, 2)):
        if targets[left] == targets[right]:
            continue
        if predictions[left] == predictions[right]:
            pair_scores.append(Fraction(1, 2))
        else:
            pair_scores.append(Fraction(int((predictions[left] < predictions[right]) ==
                                            (targets[left] < targets[right]))))
    return {
        "mae": sum(abs(e) for e in errors) / 3,
        "mse": sum(e * e for e in errors) / 3,
        "signed_error": sum(errors) / 3,
        "pairwise_concordance": sum(pair_scores) / len(pair_scores) if pair_scores else None,
        "unequal_target_pairs": len(pair_scores),
    }


class IndependentConfirmationMetricChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = invented_inputs()
        cls.original = deepcopy(cls.inputs)
        cls.result = candidate.score_confirmation(*cls.inputs)
        cases, targets, histories, cells = cls.inputs
        cls.expected = {}
        for reader in READERS:
            for arm in ARMS:
                cls.expected[reader + "/" + arm] = []
                for case in cases:
                    cell = cells[(reader, arm)][case]
                    prediction = cell["predictions"] if cell["valid"] else [3, 3, 3]
                    cls.expected[reader + "/" + arm].append({
                        "case_id": case, "valid": cell["valid"],
                        **independent_user(prediction, targets[case]),
                    })
        for name in ("history_mean", "history_median", "constant_3"):
            cls.expected[name] = []
            for case in cases:
                ordered = sorted(histories[case])
                reference = {"history_mean": Fraction(sum(ordered), 12),
                             "history_median": Fraction(ordered[5] + ordered[6], 2),
                             "constant_3": Fraction(3)}[name]
                cls.expected[name].append({"case_id": case, "valid": True,
                    **independent_user([reference] * 3, targets[case])})

    def test_all_3400_user_rows_against_independent_fraction_arithmetic(self):
        self.assertEqual(set(self.expected), set(self.result["systems"]))
        for name, expected in self.expected.items():
            actual = self.result["systems"][name]["users"]
            self.assertEqual(len(actual), 200)
            for a, b in zip(actual, expected):
                for key in ("case_id", "valid", "unequal_target_pairs"):
                    self.assertEqual(a[key], b[key])
                for key in ("mae", "mse", "signed_error", "pairwise_concordance"):
                    if b[key] is None:
                        self.assertIsNone(a[key])
                    else:
                        self.assertAlmostEqual(a[key], float(b[key]), places=12)

    def test_macro_summaries_equal_user_weighting_not_pair_weighting(self):
        different_from_pair_weighted = False
        for name, rows in self.expected.items():
            actual = self.result["systems"][name]["summary"]
            self.assertEqual(actual["users"], 200)
            self.assertEqual(actual["valid_users"], sum(row["valid"] for row in rows))
            for key in ("mae", "signed_error"):
                expected = sum(row[key] for row in rows) / 200
                self.assertAlmostEqual(actual[key], float(expected), places=12)
            expected_rmse = sqrt(float(sum(row["mse"] for row in rows) / 200))
            self.assertAlmostEqual(actual["rmse"], expected_rmse, places=12)
            eligible = [row for row in rows if row["pairwise_concordance"] is not None]
            macro = sum(row["pairwise_concordance"] for row in eligible) / len(eligible)
            weighted = sum(row["pairwise_concordance"] * row["unequal_target_pairs"]
                           for row in eligible) / sum(row["unequal_target_pairs"] for row in eligible)
            different_from_pair_weighted |= macro != weighted
            self.assertEqual(actual["ordering_eligible_users"], 134)
            self.assertAlmostEqual(actual["pairwise_concordance"], float(macro), places=12)
        self.assertTrue(different_from_pair_weighted)

    def test_all_eight_pairings_and_empty_common_valid_sensitivity(self):
        keys = set()
        empty = 0
        for writer in READERS:
            for reader in READERS:
                native = self.expected[reader + "/native_" + writer]
                for comparison, arm in (("native_minus_full", "full_history"),
                                        ("native_minus_matched_summary", "summary_" + writer)):
                    key = f"{comparison}__writer_{writer}__reader_{reader}"
                    keys.add(key)
                    other = self.expected[reader + "/" + arm]
                    differences = [a["mae"] - b["mae"] for a, b in zip(native, other)]
                    common = [a["mae"] - b["mae"] for a, b in zip(native, other)
                              if a["valid"] and b["valid"]]
                    row = self.result["contrasts"][key]
                    self.assertEqual(row["users"], 200)
                    self.assertAlmostEqual(row["mean_difference"], float(sum(differences) / 200), places=12)
                    for got, expected in zip(row["paired_user_differences"], differences):
                        self.assertAlmostEqual(got, float(expected), places=12)
                    self.assertEqual(row["common_valid_users"], len(common))
                    if common:
                        self.assertAlmostEqual(row["common_valid_mean_difference"], float(sum(common) / len(common)), places=12)
                    else:
                        empty += 1
                        self.assertIsNone(row["common_valid_mean_difference"])
                    self.assertEqual(set(row["ordinary_95"]), {"lower", "upper"})
                    self.assertEqual(set(row["bonferroni_99_375"]), {"lower", "upper"})
                    self.assertNotIn("common_valid_interval", row)
                    interval = row["bonferroni_99_375"]
                    expected_direction = ("native_higher_error" if interval["lower"] > 1e-12 else
                                          "native_lower_error" if interval["upper"] < -1e-12 else "inconclusive")
                    self.assertEqual(row["direction"], expected_direction)
        self.assertEqual(empty, 4)
        self.assertEqual(set(self.result["contrasts"]), keys)

    def test_reversing_every_mapping_preserves_case_order_and_results(self):
        cases, targets, histories, cells = self.inputs
        reversed_cells = {key: dict(reversed(list(value.items())))
                          for key, value in reversed(list(cells.items()))}
        result = candidate.score_confirmation(cases, dict(reversed(list(targets.items()))),
                                             dict(reversed(list(histories.items()))), reversed_cells)
        self.assertEqual(result, self.result)
        self.assertEqual(self.inputs, self.original)

    def test_rejects_same_size_grid_with_wrong_user_identity_before_bootstrap(self):
        cases, targets, histories, cells = invented_inputs()
        first = cases[0]
        cells[("phi", "summary_phi")]["outside-user"] = cells[("phi", "summary_phi")].pop(first)
        with patch.object(candidate, "bootstrap_confirmation") as bootstrap:
            with self.assertRaises(ValueError):
                candidate.score_confirmation(cases, targets, histories, cells)
            bootstrap.assert_not_called()


if __name__ == "__main__":
    unittest.main()
