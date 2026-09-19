import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from certificate_cost import oracle_certificate_cost, integer_loss_budget
from partial_calibration import PartialCalibration


class CertificateCostTests(unittest.TestCase):
    def test_closed_form_matches_exhaustive_minimum_certificate(self):
        patterns = [(0,0,0,0), (1,0,0,0), (1,1,0,0), (1,1,1,0)]
        for n in range(1, 5):
            for rows in itertools.product(patterns, repeat=n):
                for cache_mask in range(2**n):
                    cached = {i: rows[i] for i in range(n) if cache_mask >> i & 1}
                    missing = [i for i in range(n) if i not in cached]
                    for alpha in [0.1, 0.3, 0.5, 0.8]:
                        actual = None
                        for count in range(len(missing) + 1):
                            for subset in itertools.combinations(missing, count):
                                known = {**cached, **{i: rows[i] for i in subset}}
                                state = PartialCalibration(n, 4, alpha, known)
                                if state.bounds().exact:
                                    actual = count
                                    break
                            if actual is not None:
                                break
                        diagnostic = oracle_certificate_cost(rows, alpha, cached)
                        self.assertEqual(diagnostic["calls"], actual, (rows, cached, alpha))

    def test_pilot_strict_risk_budget(self):
        self.assertEqual([64 - integer_loss_budget(64, a) for a in [.05, .1, .2, .3]],
                         [62, 59, 52, 46])


if __name__ == "__main__":
    unittest.main()
