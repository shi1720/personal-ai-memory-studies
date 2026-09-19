import copy
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from analyze_memory_probe import selection_pair, validate_score


class ProbeAnalysisTests(unittest.TestCase):
    def row(self):
        return {'status': 'complete', 'prompt': 'p', 'prompt_sha256': hashlib.sha256(b'p').hexdigest(),
                'generation_tokens': 3, 'finish_reason': 'stop',
                'token_records': [{'id': 1, 'eos': False, 'entropy_nats': 1., 'nll_nats': .5},
                                  {'id': 2, 'eos': False, 'entropy_nats': 3., 'nll_nats': .6},
                                  {'id': 0, 'eos': True, 'entropy_nats': 9., 'nll_nats': .7}],
                'primary_entropy_nats': 2., 'first_32_entropy_nats': None}

    def test_eos_excluded_and_tampering_rejected(self):
        row = self.row()
        validate_score(row)
        for key, value in [('primary_entropy_nats', 13/3), ('generation_tokens', 2),
                           ('prompt', 'changed'), ('first_32_entropy_nats', 2.)]:
            bad = copy.deepcopy(row)
            bad[key] = value
            with self.assertRaises(ValueError):
                validate_score(bad)

    def test_truncation_preserves_prefix_only(self):
        row = self.row()
        row.update(status='unscored', finish_reason='length', generation_tokens=256,
                   token_records=[dict(row['token_records'][0]) for _ in range(256)],
                   primary_entropy_nats=None, first_32_entropy_nats=1.)
        validate_score(row)
        row['primary_entropy_nats'] = 1.
        with self.assertRaises(ValueError):
            validate_score(row)

    def test_pair_selection_ties_and_missingness(self):
        a = {'journal': 'j', 'score': .2, 'outcome': 'correct'}
        b = {'journal': 'j', 'score': .2, 'outcome': 'wrong'}
        tie = selection_pair(a, b, 'score', 'outcome')
        self.assertEqual(tie['selected_correct'], .5)
        self.assertEqual(tie['always_native_correct'], 1)
        self.assertEqual(tie['uniform_expected_correct'], .5)
        self.assertTrue(tie['candidate_correctness_differs'])
        b['score'] = .1
        self.assertEqual(selection_pair(a, b, 'score', 'outcome')['selected_correct'], 0)
        b['score'] = None
        self.assertIsNone(selection_pair(a, b, 'score', 'outcome'))

    def test_blocked_generation_is_rejected(self):
        validate_score({'status': 'blocked_writer'})
        with self.assertRaises(ValueError):
            validate_score({'status': 'blocked_writer', 'text': 'invented'})


if __name__ == '__main__':
    unittest.main()
