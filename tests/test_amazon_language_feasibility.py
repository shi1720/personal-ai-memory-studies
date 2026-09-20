from pathlib import Path
import sys
import unittest
import tempfile
import hashlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from amazon_language_feasibility import event_projection, choose_window, validate_sources


def events():
    return [{'user':'u', 'item':str(i), 'timestamp':100+i, 'row':i,
             'text_characters':10} for i in range(15)]


class AmazonFeasibilityTests(unittest.TestCase):
    def test_projection_drops_outcomes_and_text(self):
        row = {'user_id':'u', 'parent_asin':'p', 'timestamp':1640995200000, 'text':' earlier ',
               'rating':'SECRET LABEL', 'title':'SECRET TITLE'}
        projection = event_projection(row, 0)
        self.assertEqual(projection['text_characters'], 7)
        self.assertNotIn('SECRET', str(projection))
        self.assertNotIn('earlier', str(projection))

    def test_fixed_window_uses_no_future_records_in_history(self):
        data = events()
        (past, future), reason = choose_window(data[::-1], {x['item'] for x in data})
        self.assertEqual(reason, 'eligible')
        self.assertEqual(len(past), 12)
        self.assertEqual(len(future), 3)
        self.assertLess(max(x['timestamp'] for x in past), min(x['timestamp'] for x in future))

    def test_repeated_product_uses_first_event(self):
        data = events()
        data.append({**data[0], 'timestamp':999, 'row':20})
        (past, future), _ = choose_window(data, {x['item'] for x in data})
        self.assertEqual(past[0]['timestamp'],100)
        self.assertNotIn('0', [x['item'] for x in future])

    def test_boundary_tie_is_rejected(self):
        data = events()
        data[12]['timestamp'] = data[11]['timestamp']
        selected, reason = choose_window(data, {x['item'] for x in data})
        self.assertIsNone(selected)
        self.assertEqual(reason, 'history_target_boundary_tie')

    def test_global_cutoff_excludes_equal_time_and_previously_seen_items(self):
        data = events()
        data[12]['timestamp'] = 112  # Equal to cutoff, excluded.
        data.append({'user':'u','item':'new','timestamp':116,'row':15,'text_characters':10})
        data.append({**data[0], 'timestamp':117, 'row':16})
        (past, future), reason = choose_window(data, {x['item'] for x in data}, cutoff=112)
        self.assertEqual(reason, 'eligible')
        self.assertTrue(all(x['timestamp'] < 112 for x in past))
        self.assertTrue(all(x['timestamp'] > 112 for x in future))
        self.assertNotIn('0', [x['item'] for x in future])
        self.assertNotIn('12', [x['item'] for x in future])
        self.assertEqual(choose_window(data, {x['item'] for x in data}, cutoff=1000)[1],
                         'fewer_than_12_prior_and_3_later_items')

    def test_missing_title_or_earlier_text_rejected(self):
        data = events()
        self.assertEqual(choose_window(data, {'0'})[1], 'missing_catalog_title')
        data[0]['text_characters'] = 0
        self.assertEqual(choose_window(data, {x['item'] for x in data})[1], 'empty_history_review')

    def test_too_few_items_and_bad_timestamp_rejected(self):
        data = events()[:14]
        self.assertEqual(choose_window(data, {x['item'] for x in data})[1], 'fewer_than_15_distinct_items')
        with self.assertRaises(ValueError):
            event_projection({'user_id':'u','parent_asin':'p','timestamp':True,'text':'x'},0)
        with self.assertRaises(ValueError):
            event_projection({'user_id':'u','parent_asin':'p','timestamp':1640995200,'text':'x'},0)

    def test_exact_sources_required_before_opening_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = []
            for prefix, folder in [('', 'review_categories'), ('meta_', 'meta_categories')]:
                filename = prefix + 'Digital_Music.jsonl.gz'
                path = root / 'data/amazon-language-extension' / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'fixture')
                sources.append({'file': str(path.relative_to(root)), 'bytes':7,
                    'sha256':hashlib.sha256(b'fixture').hexdigest(),
                    'source':'https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/' + folder + '/' + filename})
            validate_sources(sources, 'Digital_Music', root)
            for bad in ([], sources[:1], [sources[0], sources[0]],
                        [{**sources[0], 'source':'https://example.com/wrong'}, sources[1]],
                        [{**sources[0], 'bytes':8}, sources[1]],
                        [{**sources[0], 'file':'different.gz'}, sources[1]]):
                with self.assertRaises(ValueError):
                    validate_sources(bad, 'Digital_Music', root)


if __name__ == '__main__':
    unittest.main()
