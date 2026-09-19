import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from extraction_answer_sensitivity import parse_option_answer


class ExactOptionSensitivityTests(unittest.TestCase):
    def test_bare_and_exact_option_are_consistent(self):
        options = {'A': 'swimming', 'B': 'cycling'}
        for answer in ['A', 'A. swimming']:
            import json
            self.assertEqual(parse_option_answer(json.dumps({'reason':'counted', 'answer':answer}), options), {'reason':'counted', 'answer':'A'})

    def test_no_semantic_or_schema_repairs(self):
        import json
        options = {'A': 'swimming', 'B': 'cycling'}
        for answer in ['A. cycling', 'a. swimming', 'A. Swimming', 'A. swimming because I prefer it', 'The answer is A', 'A.swimming']:
            self.assertIsNone(parse_option_answer(json.dumps({'reason':'counted', 'answer':answer}), options))
        self.assertIsNone(parse_option_answer('{"answer":"A. swimming"}', options))
        self.assertIsNone(parse_option_answer('{"reason":"counted","answer":"A. swimming","extra":1}', options))


if __name__ == '__main__':
    unittest.main()
