import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from retrieval_pilot import bm25, rank_visible, score_retrieval


class RetrievalTests(unittest.TestCase):
    def test_bm25_matches_hand_computation(self):
        values = bm25("rare", ["rare common", "common common"])
        self.assertAlmostEqual(values[0], math.log(2))
        self.assertEqual(values[1], 0.0)

    def test_empty_and_missing_terms(self):
        self.assertEqual(bm25("x", []), [])
        self.assertEqual(bm25("x", ["", ""]), [0.0, 0.0])
        self.assertEqual(bm25("x", ["y"]), [0.0])

    def test_retrieval_denominators_and_duplicate_ids(self):
        self.assertEqual(score_retrieval(["a", "a"], ["a", "b"]),
                         {"recall": 0.5, "any_hit": 1, "all_hit": 0})
        with self.assertRaises(ValueError):
            score_retrieval(["a"], [])

    def test_recency_uses_dates_not_input_order(self):
        history = [{"date": "2025/01/02 (Thu) 00:00", "messages": []},
                   {"date": "2025/01/01 (Wed) 00:00", "messages": []}]
        self.assertEqual(rank_visible("", history, "recency"), [0, 1])


if __name__ == "__main__":
    unittest.main()
