"""Published-result validation must reject corrupted summaries and intervals."""
import copy
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from verify_published_results import interval, verify


class PublishedResultsChecks(unittest.TestCase):
    def test_bootstrap_reconstruction_and_corruption(self):
        values = [-.5, .2, .3, .9]
        rng = np.random.default_rng(20260920)
        means = np.array(values)[rng.integers(0, 4, (10000, 4))].mean(axis=1)
        record = {'users': 4, 'replicates': 10000, 'seed': 20260920,
                  'mean': .225, 'positive_users': 3, 'negative_users': 1, 'zero_users': 0,
                  'interval_95': np.quantile(means, [.025, .975]).tolist(),
                  'family_adjusted_interval': np.quantile(means, [.0025, .9975]).tolist()}
        interval(values, record)
        record['family_adjusted_interval'][1] -= .01
        with self.assertRaises(AssertionError):
            interval(values, record)

    def test_aggregation_and_duplicate_or_damaged_records(self):
        rows = [{'user_row': u, 'system': 'constant', 'valid': True, 'targets': 16,
                 'mae': .5, 'mse': .25, 'signed_error': .5, 'level_mse': .25,
                 'centered_mse': 0., 'pairwise_accuracy': .5} for u in range(200)]
        aggregate = {'mae': .5, 'rmse': .5, 'signed_error': .5, 'level_mse': .25,
                     'centered_mse': 0., 'pairwise_accuracy': .5}
        report = {'users': rows, 'summaries': {'constant': {'users': 200, 'targets': 3200,
                  'valid_users': 200, 'valid_targets': 3200,
                  'operational': aggregate, 'valid_only': dict(aggregate)}},
                  'primary_contrasts': {}}
        self.assertEqual(verify(report, 0)['status'], 'passed')
        broken = copy.deepcopy(report)
        broken['users'][0]['centered_mse'] = .1
        with self.assertRaises(AssertionError):
            verify(broken, 0)
        broken = copy.deepcopy(report)
        broken['users'][0]['user_row'] = 1
        with self.assertRaises(AssertionError):
            verify(broken, 0)
        broken = copy.deepcopy(report)
        broken['summaries']['constant']['operational']['mae'] = .45
        with self.assertRaises(AssertionError):
            verify(broken, 0)


if __name__ == '__main__':
    unittest.main()
