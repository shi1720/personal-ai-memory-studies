import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from audit_memorycd_baselines import split_last_three,temporal_sources,score,aggregate

class AuditTests(unittest.TestCase):
    def test_last_three_separated_stably(self):
        data=[{'timestamp':t,'rating':r} for t,r in [(2,5),(1,1),(3,2),(3,3),(4,4)]]
        history,test=split_last_three(data)
        self.assertEqual([x['rating'] for x in history],[1,5])
        self.assertEqual([x['rating'] for x in test],[2,3,4])
        self.assertIsNone(split_last_three(data[:3]))
    def test_future_and_equal_excluded_from_strict_prior(self):
        before,equal,after=temporal_sources([{'timestamp':1},{'timestamp':2},{'timestamp':3}],2)
        self.assertEqual(before,[{'timestamp':1}]);self.assertEqual((equal,after),(1,1))
    def test_macro_users_not_events(self):
        r=aggregate([score([1],[2]),score([1,1,1],[1,1,1])])
        self.assertEqual(r['macro_mae'],.5);self.assertEqual(r['users'],2);self.assertEqual(r['targets'],4)
    def test_prediction_error_known(self):
        r=score([1,5],[3,3]);self.assertEqual(r['mae'],2);self.assertEqual(r['mse'],4)

if __name__=='__main__':unittest.main()
