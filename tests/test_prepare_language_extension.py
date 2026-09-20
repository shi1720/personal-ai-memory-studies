import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from prepare_language_extension import partition, project_record, language_reason, write_once, case_id, token_counts


class PreparationTests(unittest.TestCase):
    def test_partitions_are_disjoint_order_independent_and_sized(self):
        users = [str(i) for i in range(333)]
        groups = partition(users)
        self.assertEqual(groups, partition(users[::-1]))
        self.assertEqual({k:len(v) for k,v in groups.items()},
                         {'development':60, 'reserved_confirmation':200, 'donors':73})
        flat = [u for group in groups.values() for u in group]
        self.assertEqual(len(set(flat)),333)
        self.assertEqual(set(flat),set(users))
        self.assertEqual(len(case_id('u')),64)

    def test_insufficient_or_duplicate_users_rejected(self):
        for users in ([str(i) for i in range(319)], ['same'] * 320):
            with self.assertRaises(ValueError):
                partition(users)

    def test_target_projection_does_not_access_target_outcomes(self):
        class Guarded(dict):
            def __getitem__(self, key):
                if key in ('rating','text','title'):
                    raise AssertionError('Forbidden target field accessed')
                return super().__getitem__(key)
        source = Guarded(user_id='u',parent_asin='i',timestamp=1640995200001)
        self.assertEqual(project_record(source, False), dict(source))

    def test_history_projection_preserves_verbatim_text_and_rating(self):
        source = dict(user_id='u',parent_asin='i',timestamp=1640995100000,
                      text='  Original\ntext! ',rating=2,average_rating='forbidden')
        got = project_record(source, True)
        self.assertEqual(got['text'], source['text'])
        self.assertEqual(got['rating'], 2)
        self.assertNotIn('average_rating', got)

    def test_language_checks_never_consult_ratings(self):
        history = [{'text':('word ' * 20) + str(i), 'rating':'UNREAD'} for i in range(12)]
        self.assertIsNone(language_reason(history))
        history[1]['text'] = history[0]['text'].upper()
        self.assertEqual(language_reason(history),'duplicate_history_text')
        history[1]['text'] = 'too short'
        self.assertEqual(language_reason(history),'review_under_5_words')
        history = [{'text':'five words in this text'} for _ in range(12)]
        self.assertEqual(language_reason(history),'history_under_240_words')

    def test_immutable_prepared_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nested/output.json'
            first = write_once(path, {'unicode':'café','rows':[1,2]})
            self.assertEqual(first,write_once(path, {'rows':[1,2],'unicode':'café'}))
            with self.assertRaises(ValueError):
                write_once(path, {'rows':[1,3]})
            self.assertEqual(json.loads(path.read_text())['rows'],[1,2])

    def test_chat_token_counts_require_flat_ids_not_mapping_length(self):
        class Tokenizer:
            def encode(self, text, **kwargs):
                return [1] * 20
            def apply_chat_template(self, query, **kwargs):
                if kwargs.get('return_dict') is False:
                    return [1] * 100
                return {'input_ids':[1]*100, 'attention_mask':[1]*100}
        instance = {'history':[], 'targets':[]}
        counts = token_counts(instance, {'test':Tokenizer()})
        self.assertEqual(counts['test']['full_history_reader'],100)
        class BadTokenizer(Tokenizer):
            def apply_chat_template(self, query, **kwargs):
                return {'input_ids':[1]*100, 'attention_mask':[1]*100}
        with self.assertRaises(ValueError):
            token_counts(instance, {'test':BadTokenizer()})


if __name__ == '__main__':
    unittest.main()
