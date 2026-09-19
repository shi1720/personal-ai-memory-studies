import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from data_audit import audit, components, model_history, validate_record


def example():
    return {"question_id": "q1", "question_type": "single-session-user",
            "question": "Which city?", "answer": "Paris", "question_date": "2025/01/02 (Thu) 00:00",
            "haystack_dates": ["2025/01/01 (Wed) 00:00"], "haystack_session_ids": ["answer_1"],
            "answer_session_ids": ["answer_1"], "haystack_sessions": [[
                {"role": "user", "content": "I live in Paris.", "has_answer": True}]]}


class AuditTests(unittest.TestCase):
    def test_model_view_is_invariant_to_gold_and_id_changes(self):
        original = example()
        changed = copy.deepcopy(original)
        changed.update(answer="SECRET", answer_session_ids=["HIDDEN"], question_id="ANOTHER")
        changed["haystack_session_ids"] = ["SECRET_ID"]
        changed["haystack_sessions"][0][0]["has_answer"] = False
        self.assertEqual(model_history(original), model_history(changed))

    def test_parallel_arrays_cannot_silently_truncate(self):
        record = example()
        record["haystack_dates"] = []
        self.assertIn("parallel session arrays have unequal lengths", validate_record(record))
        with self.assertRaises(ValueError):
            audit([record])

    def test_overlap_is_transitive(self):
        self.assertEqual(components(["a", "b", "c", "d"], [["a", "b"], ["b", "c"]]),
                         [["a", "b", "c"], ["d"]])

    def test_metadata_detector_is_not_a_performance_claim(self):
        result = audit([example()])
        self.assertEqual(result["forbidden_metadata_shortcut"]["micro_recall"], 1.0)
        self.assertIn("no LLM", result["status"])

    def test_overlap_strips_answer_labels(self):
        first = example()
        second = copy.deepcopy(first)
        second["question_id"] = "q2"
        del second["haystack_sessions"][0][0]["has_answer"]
        result = audit([first, second])
        self.assertEqual(result["evidence_overlap_component_sizes"], [2])

    def test_duplicate_question_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            audit([example(), example()])

    def test_repeated_session_ids_remain_distinct_positions(self):
        record = example()
        for key in ["haystack_dates", "haystack_session_ids", "haystack_sessions"]:
            record[key] = record[key] + copy.deepcopy(record[key])
        self.assertEqual(len(model_history(record)), 2)
        self.assertEqual(len(audit([record])["questions_with_duplicate_session_ids"]), 1)


if __name__ == "__main__":
    unittest.main()
