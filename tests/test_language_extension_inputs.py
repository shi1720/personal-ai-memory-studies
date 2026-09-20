import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from language_extension_inputs import build_inputs, catalog_input, writer_history, reader_query

CUTOFF = 1640995200000


def fixture():
    history = [{'user_id':'private-user', 'parent_asin':f'h{i}',
                'timestamp':CUTOFF - 100 + i, 'text':f'A complete earlier review {i}.',
                'rating':i % 5 + 1} for i in range(12)]
    targets = [{'user_id':'private-user', 'parent_asin':f't{i}',
                'timestamp':CUTOFF + 100 + i,
                'text':'TARGET_TEXT_CANARY', 'rating':'TARGET_LABEL_CANARY',
                'title':'TARGET_REVIEW_TITLE_CANARY'} for i in range(3)]
    metadata = {r['parent_asin']:{'title':'CATALOG_' + r['parent_asin'],
        'features':['catalog feature'], 'average_rating':'AGGREGATE_CANARY',
        'rating_number':'COUNT_CANARY', 'price':'PRICE_CANARY',
        'description':['UNAPPROVED_DESCRIPTION_CANARY'], 'images':['IMAGE_CANARY']}
        for r in history + targets}
    return history, targets, metadata


class LanguageInputTests(unittest.TestCase):
    def test_hidden_fields_and_target_labels_never_reach_inputs(self):
        history, targets, metadata = fixture()
        instance = build_inputs(history, targets, metadata, CUTOFF)
        text = json.dumps(instance)
        self.assertNotIn('CANARY', text)
        self.assertNotIn('private-user', text)
        self.assertIn('A complete earlier review 0.', text)
        self.assertEqual(instance['history'][0]['rating'], 1)
        self.assertNotIn('rating', instance['targets'][0])

    def test_writer_is_query_independent_reader_receives_catalog_only(self):
        history, targets, metadata = fixture()
        instance = build_inputs(history, targets, metadata, CUTOFF)
        evidence = writer_history(instance)
        self.assertNotIn('CATALOG_t', evidence)
        query = json.dumps(reader_query(instance, evidence))
        self.assertIn('CATALOG_t0', query)
        self.assertNotIn('CANARY', query)
        targets[0]['rating'] = -999999
        targets[0]['text'] = 'ANOTHER_FUTURE_CANARY'
        changed = build_inputs(history, targets, metadata, CUTOFF)
        self.assertEqual(instance, changed)

    def test_chronology_and_identity_fail_closed(self):
        history, targets, metadata = fixture()
        for field, value in [('user_id','other-user'), ('user_id',''), ('timestamp',CUTOFF), ('timestamp',True),
                             ('timestamp',1640995200),
                             ('parent_asin','h0')]:
            modified = copy.deepcopy(targets)
            modified[0][field] = value
            with self.assertRaises(ValueError):
                build_inputs(history, modified, metadata, CUTOFF)
        with self.assertRaises(ValueError):
            build_inputs(history[::-1], targets, metadata, CUTOFF)

    def test_no_silent_history_truncation_or_duplicate_text(self):
        history, targets, metadata = fixture()
        history[0]['text'] = 'Extremely long original prose. ' * 50000
        instance = build_inputs(history, targets, metadata, CUTOFF)
        self.assertEqual(instance['history'][0]['review'], history[0]['text'])
        history[1]['text'] = history[0]['text'].upper()
        with self.assertRaises(ValueError):
            build_inputs(history, targets, metadata, CUTOFF)

    def test_catalog_and_history_rating_validation(self):
        for bad in ({'title':''}, {'title':'x','features':'not a list'}):
            with self.assertRaises(ValueError):
                catalog_input(bad)
        history, targets, metadata = fixture()
        for value in (True, float('nan'), 2.5, 7, '4'):
            history[0]['rating'] = value
            with self.assertRaises(ValueError):
                build_inputs(history, targets, metadata, CUTOFF)


if __name__ == '__main__':
    unittest.main()
