"""Synthetic fixtures only: prove development label boundaries fail closed."""
import copy
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from language_development_labels import (ARMS, CUTOFF, project_window_identities,
    project_development_labels, verify_catalog, verify_inference_gate, write_once,
    DEVELOPMENT_INPUTS, development_input_hashes)


class NoRating(dict):
    def __getitem__(self, key):
        if key == 'rating':
            raise AssertionError('Unauthorized rating access')
        return super().__getitem__(key)


class NoAccess(dict):
    def __getitem__(self, key):
        raise AssertionError('Nondevelopment source row was accessed')


def fixture():
    rows = []
    products = []
    history = []
    targets = []
    for i in range(15):
        time = CUTOFF + ((i - 12) * 1000 if i < 12 else (i - 11) * 1000)
        source = {'user_id': 'development-user', 'parent_asin': 'product-' + str(i),
                  'timestamp': time, 'rating': (i % 5) + 1}
        rows.append((i, source))
        product = {'title': 'Product ' + str(i), 'features': ['Feature']}
        products.append({'parent_asin': source['parent_asin'], **product})
        if i < 12:
            history.append({'review_date_utc': datetime.fromtimestamp(time / 1000, timezone.utc).isoformat(),
                            'product': product})
        else:
            targets.append({'target': i - 11, 'product': product})
    mapping = {'case': {'group': 'development', 'user_id': 'development-user',
                        'history_rows': list(range(12)), 'target_rows': [12, 13, 14]}}
    inputs = {'case': {'history': history, 'targets': targets}}
    return rows, mapping, inputs, products


class DevelopmentLabelChecks(unittest.TestCase):
    def test_dependency_selection_does_not_access_reserved_input_hashes(self):
        class OnlyDevelopmentHashes(dict):
            def __getitem__(self, key):
                if key not in DEVELOPMENT_INPUTS:
                    raise AssertionError('Reserved or donor input dependency accessed')
                return super().__getitem__(key)
        values = OnlyDevelopmentHashes({name: 'a' * 64 for name in DEVELOPMENT_INPUTS})
        values['data/language-extension-v1/reserved_confirmation-inputs.json'] = 'b' * 64
        values['data/language-extension-v1/donors-inputs.json'] = 'c' * 64
        self.assertEqual(set(development_input_hashes(values)), set(DEVELOPMENT_INPUTS))
        with self.assertRaises(ValueError):
            development_input_hashes({DEVELOPMENT_INPUTS[0]: 'a' * 64})

    def test_two_pass_projection_never_reads_unselected_ratings(self):
        rows, mapping, inputs, products = fixture()
        first = [(row, NoRating(record)) for row, record in rows] + [(999, NoAccess())]
        windows = project_window_identities(first, mapping, inputs)
        verify_catalog(products, windows, inputs)
        second = [(row, record if row >= 12 else NoRating(record)) for row, record in rows]
        second.insert(0, (999, NoAccess()))
        # Physical stream order must not override frozen target order.
        result = project_development_labels(list(reversed(second)), windows)
        self.assertEqual(result['case']['target_rows'], [12, 13, 14])
        self.assertEqual(result['case']['target_ratings'], [3, 4, 5])

    def test_window_rejects_missing_duplicate_wrong_user_and_dates(self):
        rows, mapping, inputs, _ = fixture()
        for damaged in [rows[:-1], rows + [rows[0]]]:
            with self.assertRaises(ValueError):
                project_window_identities(damaged, mapping, inputs)
        for key, value in [('user_id', 'reserved-user'), ('timestamp', CUTOFF),
                           ('timestamp', CUTOFF + 1), ('parent_asin', 'product-0')]:
            damaged = copy.deepcopy(rows)
            index = 12 if key != 'timestamp' or value == CUTOFF else 0
            damaged[index][1][key] = value
            with self.assertRaises(ValueError):
                project_window_identities(damaged, mapping, inputs)
        bad = copy.deepcopy(mapping)
        bad['case']['target_rows'][1] = 12
        with self.assertRaises(ValueError):
            project_window_identities(rows, bad, inputs)
        bad = copy.deepcopy(mapping)
        bad['case']['group'] = 'reserved_confirmation'
        with self.assertRaises(ValueError):
            project_window_identities(rows, bad, inputs)

    def test_second_pass_checks_identity_before_rating_access(self):
        rows, mapping, inputs, _ = fixture()
        windows = project_window_identities(rows, mapping, inputs)
        for key, value in [('user_id', 'reserved-user'), ('parent_asin', 'different-product'),
                           ('timestamp', CUTOFF + 9999)]:
            changed = copy.deepcopy(rows)
            changed[12][1][key] = value
            changed[12] = (12, NoRating(changed[12][1]))
            with self.assertRaises(ValueError):
                project_development_labels(changed, windows)
        for damaged in (rows[:-1], rows + [rows[-1]]):
            with self.assertRaises(ValueError):
                project_development_labels(damaged, windows)
        for value in (True, float('nan'), 6, 2.5):
            changed = copy.deepcopy(rows)
            changed[12][1]['rating'] = value
            with self.assertRaises(ValueError):
                project_development_labels(changed, windows)

    def test_catalog_requires_exact_prepared_product(self):
        rows, mapping, inputs, products = fixture()
        windows = project_window_identities(rows, mapping, inputs)
        for damaged in (products[:-1], products + [products[0]]):
            with self.assertRaises(ValueError):
                verify_catalog(damaged, windows, inputs)
        changed = copy.deepcopy(products)
        changed[14]['title'] = 'Another title'
        with self.assertRaises(ValueError):
            verify_catalog(changed, windows, inputs)

    def test_complete_grid_gate_rejects_partial_or_duplicate_records(self):
        cases = ['case-' + str(i) for i in range(60)]
        hashes = {}
        readers, writers = [], []
        for case in cases:
            for model in ('qwen', 'phi'):
                writer = {'case_id': case, 'model': model}
                for kind in ('native', 'summary'):
                    path = case + '/' + model + '/' + kind + '.json'
                    hashes[path] = 'a' * 64
                    writer.update({kind + '_file': path, kind + '_sha256': hashes[path]})
                writers.append(writer)
                for arm in ARMS:
                    path = case + '/' + model + '/reader-' + arm + '.json'
                    hashes[path] = 'b' * 64
                    readers.append({'case_id': case, 'reader': model, 'arm': arm,
                                    'file': path, 'raw_sha256': hashes[path]})
        report = {'phase': 'development', 'complete': True, 'cases': cases,
                  'stage_status': {s: 'completed' for s in ('qwen_base', 'phi', 'qwen_cross')},
                  'raw_file_hashes': hashes, 'readers': readers, 'writers': writers}
        manifest = {'cases': cases}
        verify_inference_gate(report, manifest, cases, hashes)
        for key, value in [('complete', False), ('phase', 'reserved_confirmation'),
                           ('cases', list(reversed(cases))), ('readers', readers[:-1]),
                           ('writers', writers + [writers[0]])]:
            altered = dict(report)
            altered[key] = value
            with self.assertRaises(ValueError):
                verify_inference_gate(altered, manifest, cases, hashes)
        altered = copy.deepcopy(report)
        altered['stage_status']['qwen_cross'] = 'incomplete'
        with self.assertRaises(ValueError):
            verify_inference_gate(altered, manifest, cases, hashes)

    def test_label_artifact_cannot_be_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'labels.json'
            first = write_once(path, {'fixture': [1, 2, 3]})
            self.assertEqual(first, write_once(path, {'fixture': [1, 2, 3]}))
            with self.assertRaises(ValueError):
                write_once(path, {'fixture': [3, 2, 1]})


if __name__ == '__main__':
    unittest.main()
