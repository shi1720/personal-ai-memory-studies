from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from language_development_metrics import ARMS, READERS, score_development, user_metrics


def fixture():
    cases = ['a', 'b']
    targets = {'a': [1, 3, 5], 'b': [2, 2, 2]}
    histories = {'a': [1] * 6 + [5] * 6, 'b': [2] * 12}
    cells = {(reader, arm): {case: {'valid': True, 'predictions': targets[case][:]}
                            for case in cases} for reader in READERS for arm in ARMS}
    return cases, targets, histories, cells


class DevelopmentMetricsTests(unittest.TestCase):
    def test_exact_predictions_and_sparse_ordering(self):
        result = score_development(*fixture())
        self.assertEqual(len(result['systems']), 17)
        self.assertEqual(len(result['contrasts']), 8)
        summary = result['systems']['qwen/full_history']['summary']
        self.assertEqual(summary['mae'], 0.)
        self.assertEqual(summary['rmse'], 0.)
        self.assertEqual(summary['ordering_eligible_users'], 1)
        self.assertEqual(summary['pairwise_concordance'], 1.)
        self.assertIsNone(result['precision_planning'])

    def test_invalid_writer_or_reader_forces_three_and_preserves_user(self):
        args = fixture()
        args[3][('qwen', 'native_phi')]['a'] = {'valid': False, 'predictions': [1, 3, 5]}
        result = score_development(*args)
        system = result['systems']['qwen/native_phi']
        self.assertEqual(system['summary']['users'], 2)
        self.assertEqual(system['summary']['valid_users'], 1)
        self.assertAlmostEqual(system['summary']['mae'], 2 / 3)
        self.assertAlmostEqual(system['summary']['rmse'], (4 / 3) ** .5)
        contrast = result['contrasts']['native_minus_full__writer_phi__reader_qwen']
        self.assertAlmostEqual(contrast['mean_difference'], 2 / 3)
        self.assertEqual(contrast['common_valid_users'], 1)
        self.assertEqual(contrast['common_valid_mean_difference'], 0.)

    def test_matched_summary_contrast_keeps_writer_identity(self):
        args = fixture()
        args[3][('phi', 'summary_qwen')]['a']['predictions'] = [5, 3, 1]
        result = score_development(*args)
        self.assertAlmostEqual(result['contrasts']['native_minus_matched_summary__writer_qwen__reader_phi']['mean_difference'], -4 / 3)
        self.assertEqual(result['contrasts']['native_minus_matched_summary__writer_phi__reader_phi']['mean_difference'], 0.)

    def test_baselines_and_rmse_are_not_mean_user_rmse(self):
        result = score_development(*fixture())
        summary = result['systems']['constant_3']['summary']
        self.assertAlmostEqual(summary['mae'], 7 / 6)
        self.assertAlmostEqual(summary['rmse'], (11 / 6) ** .5)
        self.assertAlmostEqual(result['systems']['history_mean']['summary']['mae'], 2 / 3)
        self.assertEqual(result['systems']['history_median'], result['systems']['history_mean'])

    def test_ties_and_reversed_order(self):
        self.assertEqual(user_metrics([3, 3, 3], [1, 3, 5])['pairwise_concordance'], .5)
        self.assertEqual(user_metrics([5, 3, 1], [1, 3, 5])['pairwise_concordance'], 0.)
        self.assertIsNone(user_metrics([1, 2, 3], [4, 4, 4])['pairwise_concordance'])

    def test_validity_and_rating_contracts_reject_malformed_cells(self):
        for bad in (True, float('nan'), float('inf'), 0, 6, '3'):
            args = fixture()
            args[3][('qwen', 'full_history')]['a']['predictions'][0] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                score_development(*args)
        args = fixture()
        args[3][('qwen', 'full_history')]['a']['valid'] = 1
        with self.assertRaises(ValueError):
            score_development(*args)

    def test_no_missing_duplicate_or_extra_users_or_conditions(self):
        for mutation in ('missing_arm', 'missing_user', 'extra_user', 'duplicate_case'):
            args = fixture()
            if mutation == 'missing_arm': del args[3][('qwen', 'full_history')]
            elif mutation == 'missing_user': del args[3][('qwen', 'full_history')]['a']
            elif mutation == 'extra_user': args[2]['c'] = [3] * 12
            else: args[0].append('a')
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                score_development(*args)

    def test_scoring_does_not_mutate_inputs(self):
        args = fixture()
        before = deepcopy(args)
        score_development(*args)
        self.assertEqual(args, before)


if __name__ == '__main__':
    unittest.main()
