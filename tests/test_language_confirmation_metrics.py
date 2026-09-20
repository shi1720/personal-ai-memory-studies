"""Invented-array tests only; never load prepared participants or outcomes."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import language_confirmation_metrics as metrics


def fixture():
    cases = [f"invented-{i:03d}" for i in range(200)]
    targets = {case: ([1, 3, 5] if i % 2 == 0 else [2, 2, 2])
               for i, case in enumerate(cases)}
    histories = {case: ([1] * 6 + [5] * 6 if i % 2 == 0 else [2] * 12)
                 for i, case in enumerate(cases)}
    cells = {(reader, arm): {
        case: {"valid": True, "predictions": list(targets[case])} for case in cases
    } for reader in metrics.READERS for arm in metrics.ARMS}
    return cases, targets, histories, cells


class ConfirmationMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = fixture()
        # One hundred perfectly parsed diagnostic answers from invalid whole
        # pipelines: the scorer must ignore their apparently perfect predictions.
        for case in cls.inputs[0][::2]:
            cls.inputs[3][("qwen", "native_phi")][case]["valid"] = False
        # Deliberately wrong Qwen summary under Phi reading, leaving Phi's
        # same-writer summary untouched. This tests writer-reader indexing.
        for case in cls.inputs[0][::2]:
            cls.inputs[3][("phi", "summary_qwen")][case]["predictions"] = [5, 3, 1]
        cls.before = deepcopy(cls.inputs)
        cls.result = metrics.score_confirmation(*cls.inputs)

    def test_complete_fixed_grid_and_shared_uncertainty(self):
        result = self.result
        self.assertEqual(result["users"], 200)
        self.assertEqual(result["target_ratings"], 600)
        self.assertEqual(len(result["systems"]), 17)
        self.assertEqual(sum(len(s["users"]) for s in result["systems"].values()), 3400)
        self.assertEqual(set(result["contrasts"]), set(metrics.CONTRAST_KEYS))
        self.assertEqual(result["uncertainty_settings"]["bootstrap_resamples"], 200000)
        self.assertEqual(result["uncertainty_settings"]["family_size"], 8)
        self.assertNotIn("precision_planning", result)
        self.assertNotIn("complete", result)

    def test_invalid_writer_pipeline_retained_with_constant_three(self):
        summary = self.result["systems"]["qwen/native_phi"]["summary"]
        self.assertEqual(summary["users"], 200)
        self.assertEqual(summary["valid_users"], 100)
        self.assertAlmostEqual(summary["mae"], 2 / 3)
        self.assertAlmostEqual(summary["rmse"], (4 / 3) ** .5)
        self.assertEqual(summary["ordering_eligible_users"], 100)
        self.assertEqual(summary["pairwise_concordance"], .5)
        contrast = self.result["contrasts"]["native_minus_full__writer_phi__reader_qwen"]
        self.assertAlmostEqual(contrast["mean_difference"], 2 / 3)
        self.assertEqual(contrast["common_valid_users"], 100)
        self.assertEqual(contrast["common_valid_mean_difference"], 0.)
        self.assertEqual(contrast["direction"], "native_higher_error")
        self.assertGreater(contrast["bonferroni_99_375"]["lower"], 0.)

    def test_same_writer_summary_and_reader_not_swapped(self):
        rows = self.result["contrasts"]
        q = rows["native_minus_matched_summary__writer_qwen__reader_phi"]
        p = rows["native_minus_matched_summary__writer_phi__reader_phi"]
        self.assertAlmostEqual(q["mean_difference"], -4 / 3)
        self.assertEqual(q["direction"], "native_lower_error")
        self.assertLess(q["bonferroni_99_375"]["upper"], 0.)
        self.assertEqual(p["mean_difference"], 0.)
        self.assertEqual(p["direction"], "inconclusive")
        self.assertEqual(p["bonferroni_99_375"], {"lower": 0., "upper": 0.})

    def test_numerical_references_use_history_only_and_root_of_mean_square(self):
        systems = self.result["systems"]
        constant = systems["constant_3"]["summary"]
        self.assertAlmostEqual(constant["mae"], 7 / 6)
        self.assertAlmostEqual(constant["rmse"], (11 / 6) ** .5)
        self.assertAlmostEqual(constant["signed_error"], .5)
        self.assertAlmostEqual(systems["history_mean"]["summary"]["mae"], 2 / 3)
        self.assertEqual(systems["history_mean"], systems["history_median"])

    def test_retains_case_order_and_never_mutates_inputs(self):
        self.assertEqual(self.inputs, self.before)
        self.assertEqual(self.result["cases"], self.inputs[0])
        for system in self.result["systems"].values():
            self.assertEqual([r["case_id"] for r in system["users"]], self.inputs[0])

    def assert_rejected_before_bootstrap(self, args):
        with patch.object(metrics, "bootstrap_confirmation") as boot:
            with self.assertRaises(ValueError):
                metrics.score_confirmation(*args)
            boot.assert_not_called()

    def test_rejects_wrong_sample_and_malformed_identity(self):
        for replacement in (self.inputs[0][:-1], self.inputs[0] + ["extra"],
                            ["same"] * 200, [True] + self.inputs[0][1:],
                            [""] + self.inputs[0][1:], set(self.inputs[0])):
            args = list(fixture()); args[0] = replacement
            with self.subTest(replacement_type=type(replacement).__name__):
                self.assert_rejected_before_bootstrap(args)

    def test_rejects_missing_extra_or_malformed_cells_and_outcomes(self):
        for mutation in ("arm", "user", "extra", "cell", "target", "history", "mapping"):
            args = fixture(); c = args[0][0]
            if mutation == "arm": del args[3][("qwen", "full_history")]
            elif mutation == "user": del args[3][("qwen", "full_history")][c]
            elif mutation == "extra": args[3][("qwen", "extra")] = {}
            elif mutation == "cell": args[3][("qwen", "full_history")][c] = None
            elif mutation == "target": args[1][c] = [3, 3]
            elif mutation == "history": args[2][c] = [3] * 11
            else: args = list(args); args[2] = []
            with self.subTest(mutation=mutation): self.assert_rejected_before_bootstrap(args)

    def test_rejects_invalid_numbers_and_nonboolean_validity(self):
        for field in ("targets", "histories", "predictions", "valid"):
            for bad in (True, float("nan"), float("inf"), 0, 6, "3"):
                if field == "valid" and bad is True: continue
                args = fixture(); c = args[0][0]
                if field == "targets": args[1][c][0] = bad
                elif field == "histories": args[2][c][0] = bad
                elif field == "predictions": args[3][("qwen", "full_history")][c]["predictions"][0] = bad
                else: args[3][("qwen", "full_history")][c]["valid"] = bad
                with self.subTest(field=field, bad=bad): self.assert_rejected_before_bootstrap(args)


if __name__ == "__main__":
    unittest.main()
