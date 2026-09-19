from fractions import Fraction as F
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gated_memory_estimand import GATES, audit, exact_cycle, population, sequential_update


class GatedMemoryTests(unittest.TestCase):
    def test_propensity_identity_and_constant_gate(self):
        for mu in [F(1,10), F(1,2), F(4,5), F(9,10)]:
            for reference in [F(0), F(1,4), F(1,2), F(1)]:
                result = audit(population(mu, reference), GATES['constant'])
                self.assertEqual(result['target_mean'], result['ungated_propensity_mean'])
                self.assertEqual(result['gated_ratio'], result['target_mean'])

    def test_gate_changes_target_and_covariance_identity(self):
        expected = {'constant': F(1,2), 'action_dependent': F(37,50), 'outcome_dependent': F(9,10)}
        for name, gate in GATES.items():
            result = audit(population(), gate)
            self.assertEqual(result['gated_ratio'], expected[name])
            self.assertEqual(result['bias'], result['covariance_identity'])
            self.assertEqual(result['observed_mean'], F(17,25))

    def test_recursion_permutation_and_repetition(self):
        for gate in GATES.values():
            events = exact_cycle(population(), gate)
            baseline = sequential_update(events)
            random.Random(29).shuffle(events)
            self.assertEqual(sequential_update(events), baseline)
            repeated = sequential_update(events*10)
            self.assertEqual(repeated[0], baseline[0])
            self.assertEqual(repeated[1], 10*baseline[1])

    def test_invalid_or_empty_support_rejected(self):
        with self.assertRaises(ValueError):
            population(F(0))
        with self.assertRaises(ValueError):
            audit(population(), lambda r: 0)
        with self.assertRaises(ValueError):
            audit(population(), lambda r: 2)
        with self.assertRaises(ValueError):
            sequential_update([])
        with self.assertRaises(ValueError):
            exact_cycle(population(), GATES['constant'], size=1)


if __name__ == '__main__':
    unittest.main()
