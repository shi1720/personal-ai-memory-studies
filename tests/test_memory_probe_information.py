import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from memory_probe_information import analyze, conditional_mutual_information, entropy, example


class MemoryProbeInformationTests(unittest.TestCase):
    def test_entropy_known_values_and_invalid_inputs(self):
        self.assertEqual(entropy([1, 0]), 0)
        self.assertEqual(entropy([0.5, 0.5]), 1)
        with self.assertRaises(ValueError):
            entropy([0.5])
        with self.assertRaises(ValueError):
            entropy([-0.5, 1.5])

    def test_conditional_independence_over_channel_grid(self):
        for noise in (0, 0.1, 0.5, 0.9, 1):
            for bias in (0, 0.01, 0.5, 0.99, 1):
                joint = example(noise, bias)
                self.assertAlmostEqual(sum(joint.values()), 1)
                self.assertAlmostEqual(conditional_mutual_information(joint, (0,), (3,), (2,)), 0)

    def test_rank_reversal_and_positive_unconditional_relevance(self):
        result = analyze(example())
        self.assertGreater(result['state_response_mutual_information_bits'], 0)
        good = result['regimes']['retained']
        bad = result['regimes']['erased']
        self.assertAlmostEqual(good['state_entropy_given_memory_bits'], 0)
        self.assertAlmostEqual(bad['state_entropy_given_memory_bits'], 1)
        self.assertAlmostEqual(good['response_error_probability'], 0.1)
        self.assertAlmostEqual(bad['response_error_probability'], 0.5)
        self.assertGreater(good['response_entropy_given_memory_bits'], bad['response_entropy_given_memory_bits'])

    def test_deterministic_reader_ties_despite_different_information(self):
        result = analyze(example(0, 0))['regimes']
        for regime in result.values():
            self.assertAlmostEqual(regime['response_entropy_given_memory_bits'], 0)
        self.assertNotEqual(result['retained']['state_entropy_given_memory_bits'], result['erased']['state_entropy_given_memory_bits'])

    def test_state_access_control_breaks_independence(self):
        # A genuine observation of S beyond M makes the conditional term nonzero.
        joint = {(0, '?', 0): 0.5, (1, '?', 1): 0.5}
        self.assertAlmostEqual(conditional_mutual_information(joint, (0,), (2,), (1,)), 1)

    def test_posterior_sampling_entropy_matches_despite_zero_conditional_information(self):
        # Distributional calibration can validate entropy without a nonzero CMI.
        result = analyze(example(0, .5))
        self.assertAlmostEqual(result['state_response_conditional_mutual_information_given_memory_bits'], 0)
        for regime in result['regimes'].values():
            self.assertAlmostEqual(regime['state_entropy_given_memory_bits'], regime['response_entropy_given_memory_bits'])


if __name__ == '__main__':
    unittest.main()
