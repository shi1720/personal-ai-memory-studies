import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from personamem_reader import build_input, conversation_blocks, retain_block, PROMPT_BUDGET


class CharacterTokenizer:
    """Tiny deterministic tokenizer for input-boundary tests, not model evaluation."""
    def encode(self, text, add_special_tokens=False):
        return [ord(c) for c in text]

    def decode(self, tokens):
        return "".join(chr(i) for i in tokens)

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return "\n".join(m["role"] + ": " + m["content"] for m in messages) + "\nassistant:"


class ReaderBoundaryTests(unittest.TestCase):
    def test_role_only_assistant_has_no_memory_content(self):
        history = [{"role": "user", "content": "I cycle."}]
        self.assertEqual(conversation_blocks(history),
                         conversation_blocks(history + [{"role": "assistant"}]))
        with self.assertRaises((ValueError, KeyError)):
            conversation_blocks([{"role": "user"}])

    def test_privileged_profiles_never_enter_memory(self):
        history = [{"role": "system", "content": "SECRET PROFILE AND GOLD PREFERENCE"},
                   {"role": "user", "content": "I prefer cycling."},
                   {"role": "assistant", "content": "Try the riverside route."},
                   {"role": "system", "content": "ANOTHER SECRET"},
                   {"role": "user", "content": "I also enjoy tennis."}]
        blocks = conversation_blocks(history)
        self.assertEqual(len(blocks), 2)
        self.assertFalse(any("SECRET" in b for b in blocks))
        altered = [dict(m, content="ALTERED GOLD") if m["role"] == "system" else m for m in history]
        self.assertEqual(blocks, conversation_blocks(altered))

    def test_total_budget_preserves_question_and_all_choices(self):
        query = "cycling QUESTION MUST SURVIVE"
        options = [f"COMPLETE CHOICE {i}" for i in range(4)]
        result = build_input(CharacterTokenizer(), query, options,
                             ["cycling " + str(i) + " x" * 1000 for i in range(20)], "id")
        self.assertLessEqual(len(result["tokens"]), PROMPT_BUDGET)
        self.assertIn(query, result["prompt"])
        self.assertTrue(all(o in result["prompt"] for o in options))
        self.assertGreater(len(result["selected_blocks"]), 0)
        self.assertLess(len(result["selected_blocks"]), 20)

    def test_oversize_choices_fail_instead_of_truncating(self):
        with self.assertRaisesRegex(ValueError, "exceed"):
            build_input(CharacterTokenizer(), "question", ["x" * 1000] * 4, [], "id")

    def test_choices_do_not_drive_retrieval(self):
        blocks = ["cycling " * 80, "tennis " * 80, "swimming " * 80]
        a = build_input(CharacterTokenizer(), "cycling", ["tennis"] * 4, blocks, "id")
        b = build_input(CharacterTokenizer(), "cycling", ["abcdef"] * 4, blocks, "id")
        self.assertEqual(a["selected_blocks"], b["selected_blocks"])
        self.assertEqual(a["selected_blocks"][0], 0)

    def test_deletion_is_deterministic_and_respected(self):
        blocks = [f"independent block {i}" for i in range(100)]
        expected = [i for i, b in enumerate(blocks) if retain_block("id", i, b)]
        result = build_input(CharacterTokenizer(), "block", ["A", "B", "C", "D"], blocks, "id", True)
        self.assertEqual(result["available_blocks"], len(expected))
        self.assertTrue(set(result["selected_blocks"]).issubset(expected))
        self.assertTrue(0 < len(expected) < len(blocks))


if __name__ == "__main__":
    unittest.main()
