import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from analyze_coat_memory_development import paired_bootstrap

class AnalysisTests(unittest.TestCase):
    def test_zero_effect_is_zero_not_artificial_significance(self):
        r=paired_bootstrap([0,0,0])
        self.assertEqual(r['percentile_95'],[0.,0.]);self.assertEqual(r['equal'],3)
        self.assertEqual(r['memory_better'],0);self.assertEqual(r['memory_worse'],0)
    def test_direction_and_unit(self):
        r=paired_bootstrap([-1,-1,-1])
        self.assertEqual(r['users'],3);self.assertEqual(r['memory_better'],3)
        self.assertEqual(r['percentile_95'],[-1.,-1.]);self.assertEqual(r['mean'],-1.)
        self.assertIsNone(paired_bootstrap([]))
    def test_reproducible_user_resampling(self):
        self.assertEqual(paired_bootstrap([-.2,0,.3]),paired_bootstrap([-.2,0,.3]))

if __name__=='__main__':unittest.main()
