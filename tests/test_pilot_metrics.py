from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyze_personamem_pilot import metrics, THRESHOLDS
from partial_calibration import shipped_loss_row


class MetricTests(unittest.TestCase):
    def test_abstention_does_not_imply_selective_accuracy(self):
        records = [{"changed": {"confidence": .9, "correct": False}}]
        records += [{"changed": {"confidence": .4, "correct": True}}] * 9
        m = metrics(records, .8)
        self.assertEqual(m["shipped_error_rate"], .1)
        self.assertEqual(m["coverage"], .1)
        self.assertEqual(m["conditional_error"], 1)
        self.assertEqual(m["always_answer_accuracy"], .9)
        stopped = metrics(records, 1.01)
        self.assertIsNone(stopped["conditional_error"])
        self.assertEqual(stopped["coverage"], 0)

    def test_threshold_ties_match_loss_function(self):
        records = [{"changed": {"confidence": .75, "correct": False}},
                   {"changed": {"confidence": .75, "correct": True}}]
        for j, threshold in enumerate(THRESHOLDS):
            losses = [shipped_loss_row(r["changed"]["correct"], r["changed"]["confidence"], THRESHOLDS)[j] for r in records]
            self.assertEqual(metrics(records, threshold)["shipped_error_rate"], sum(losses)/len(records))


if __name__ == "__main__":
    unittest.main()
