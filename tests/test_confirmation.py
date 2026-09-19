import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from confirmation_common import shuffled_history,history_only
from analyze_confirmation import metrics,bootstrap


class ConfirmationTests(unittest.TestCase):
    def test_permutation_preserves_marginal_and_item_support(self):
        h=np.array([1.,0.,2.,5.,4.,3.,0.,1.,5.])
        a=shuffled_history(h,17)
        np.testing.assert_array_equal(a!=0,h!=0)
        np.testing.assert_array_equal(np.sort(a),np.sort(h))
        np.testing.assert_array_equal(a,shuffled_history(h,17))
        self.assertFalse(np.array_equal(a,h))

    def test_statistical_reader_uses_no_other_user_information(self):
        x=np.column_stack([np.ones(4),[0,0,1,1]])
        a=history_only(np.array([1.,0.,5.,0.]),x,'history_ridge',1.)
        self.assertLess(a[1],a[3]);self.assertTrue(np.all((1<=a)&(a<=5)))

    def test_pairwise_ties_and_equal_targets(self):
        self.assertEqual(metrics([3,3],[1,5])['pairwise_accuracy'],.5)
        self.assertEqual(metrics([1,5],[1,5])['pairwise_accuracy'],1.)
        self.assertEqual(metrics([5,1],[1,5])['pairwise_accuracy'],0.)
        self.assertIsNone(metrics([1,5],[3,3])['pairwise_accuracy'])

    def test_bootstrap_adjustment_does_not_narrow_interval(self):
        r=bootstrap([-.5,.2,1.,-.3,.6])
        self.assertLessEqual(r['family_adjusted_interval'][0],r['interval_95'][0])
        self.assertGreaterEqual(r['family_adjusted_interval'][1],r['interval_95'][1])
        self.assertEqual(bootstrap([0,0,0])['family_adjusted_interval'],[0.,0.])


if __name__=='__main__':unittest.main()
