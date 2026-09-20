from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from analyze_language_development import checked_cells
from language_development_metrics import ARMS, READERS, score_development


def response(content):
    return {'status': 'completed', 'response': {'choices': [
        {'finish_reason': 'stop', 'message': {'content': content}}]}}


def fixture():
    native = {'status': 'completed', 'add': {'results': [{'id': 'x', 'memory': 'An earlier preference'}]},
              'stored': {'results': [{'id': 'x', 'memory': 'An earlier preference'}]},
              'traces': [response('{}')]}
    files, writers, readers = {}, [], []
    for writer in READERS:
        files['native/' + writer] = deepcopy(native)
        files['summary/' + writer] = response('{"profile":"Earlier preferences and ratings."}')
        writers.append({'case_id': 'a', 'writer': writer,
                        'native_path': 'native/' + writer, 'summary_path': 'summary/' + writer})
    for reader in READERS:
        for arm in ARMS:
            path = reader + '/' + arm
            files[path] = response('[1,3,5]')
            readers.append({'case_id': 'a', 'reader': reader, 'arm': arm, 'raw_path': path,
                            'reader_valid': True, 'pipeline_valid': True,
                            'required_writer_valid': True, 'diagnostic_fallback_evidence': False,
                            'operational_constant3_required': False})
    return {'cases': ['a'], 'writers': writers, 'readers': readers}, files


class DevelopmentAdapterTests(unittest.TestCase):
    def test_reparses_both_writer_and_reader(self):
        report, files = fixture()
        cells = checked_cells(report, files.__getitem__)
        self.assertEqual(len(cells), 14)
        self.assertTrue(all(value['a']['valid'] for value in cells.values()))

    def test_invalid_writer_valid_sentinel_read_gets_operational_fallback(self):
        report, files = fixture()
        files['native/phi']['stored']['results'] = []
        for row in report['readers']:
            if row['arm'] == 'native_phi':
                row.update(pipeline_valid=False, operational_constant3_required=True,
                           required_writer_valid=False, diagnostic_fallback_evidence=True)
        cells = checked_cells(report, files.__getitem__)
        self.assertFalse(cells[('qwen', 'native_phi')]['a']['valid'])
        scored = score_development(['a'], {'a': [1, 3, 5]}, {'a': [3] * 12}, cells)
        self.assertAlmostEqual(scored['systems']['qwen/native_phi']['summary']['mae'], 4 / 3)
        self.assertEqual(scored['systems']['qwen/full_history']['summary']['mae'], 0)

    def test_invalid_reader_never_uses_parseable_truncated_response(self):
        report, files = fixture()
        files['phi/full_history']['response']['choices'][0]['finish_reason'] = 'length'
        for row in report['readers']:
            if (row['reader'], row['arm']) == ('phi', 'full_history'):
                row.update(reader_valid=False, pipeline_valid=False, operational_constant3_required=True)
        cells = checked_cells(report, files.__getitem__)
        self.assertFalse(cells[('phi', 'full_history')]['a']['valid'])
        self.assertIsNone(cells[('phi', 'full_history')]['a']['predictions'])

    def test_untruthful_validity_flags_are_rejected(self):
        report, files = fixture()
        files['native/phi']['status'] = 'error'
        with self.assertRaises(ValueError):
            checked_cells(report, files.__getitem__)

    def test_duplicate_and_missing_grids_rejected(self):
        for key, duplicate in (('writers', True), ('writers', False), ('readers', True), ('readers', False)):
            report, files = fixture()
            if duplicate: report[key].append(report[key][0])
            else: report[key].pop()
            with self.subTest(key=key, duplicate=duplicate), self.assertRaises(ValueError):
                checked_cells(report, files.__getitem__)


if __name__ == '__main__':
    unittest.main()
