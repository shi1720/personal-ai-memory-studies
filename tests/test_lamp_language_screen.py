import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from lamp_language_screen import read_prefix, target_text, text_hash, audit


class Tokenizer:
    def encode(self, text, **kwargs):
        return text.split()


class LanguageScreenTests(unittest.TestCase):
    def test_partial_utf8_and_commas_across_chunks(self):
        source = json.dumps([{'x': 'café'}, {'x': 2}, {'x': 3}], ensure_ascii=False).encode()
        for chunk in range(1, 12):
            rows, size, _ = read_prefix(io.BytesIO(source), count=2, chunk_size=chunk)
            self.assertEqual(rows, [{'x': 'café'}, {'x': 2}])
            self.assertLessEqual(size, len(source))

    def test_incomplete_or_malformed_stream_rejected(self):
        for data in (b'{}', b'[{} {}]', b'[{}', b'[1,2]', b'[]'):
            with self.assertRaises(ValueError):
                read_prefix(io.BytesIO(data), count=2, chunk_size=2)

    def test_limit_is_enforced(self):
        with self.assertRaises(ValueError):
            read_prefix(io.BytesIO(b'[{"x":"long string"}]'), count=1, limit=10)

    def test_target_uses_first_marker_and_normalization(self):
        self.assertEqual(target_text({'input': 'Rate review: some review: more'}), 'some review: more')
        self.assertEqual(text_hash('Good  BOOK'), text_hash(' good book '))
        self.assertNotEqual(text_hash('good book'), text_hash('not good book'))
        with self.assertRaises(ValueError):
            target_text({'input': 'Unknown task'})

    def test_overlap_and_conflicts_are_reported_without_text(self):
        rows = [
            {'id':'a', 'input':'Rate review: SAME', 'profile':[{'text':'same', 'score':'5'}]},
            {'id':'b', 'input':'Rate review: Three stars', 'profile':[{'text':'SAME', 'score':'1'}]},
        ]
        result = audit(rows, Tokenizer())
        self.assertEqual(result['pairs_sharing_normalized_history_text'], 1)
        self.assertEqual(result['history_texts_with_conflicting_ratings_across_sample'], 1)
        self.assertEqual(result['targets_exactly_in_own_history'], 1)
        self.assertEqual(result['targets_exactly_in_other_histories'], 1)
        self.assertEqual(result['targets_with_star_expression'], 1)
        self.assertNotIn('Three stars', json.dumps(result))
        self.assertFalse(result['independent_user_identity_established'])

    def test_bad_ratings_and_duplicate_ids_rejected(self):
        row = {'id':'a', 'input':'Rate review: text', 'profile':[{'text':'history', 'score':'6'}]}
        with self.assertRaises(ValueError):
            audit([row], Tokenizer())
        row['profile'][0]['score'] = '1'
        with self.assertRaises(ValueError):
            audit([row, row], Tokenizer())


if __name__ == '__main__':
    unittest.main()
