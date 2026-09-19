import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from movie_validation_data import user_order
from run_movie_validation import records,messages
from analyze_confirmation import metrics


class MovieValidationTests(unittest.TestCase):
    def test_user_order_independent_of_input_order(self):
        self.assertEqual(user_order([1,4,3,2]),user_order([4,3,2,1]))

    def test_target_records_never_contain_ratings(self):
        ratings=np.array([0.,2.,5.]);features=np.array([[0,0],[1,0],[0,1]])
        query=records(ratings,features,['genre:A','genre:B'],False)
        changed=records(np.array([0.,5.,1.]),features,['genre:A','genre:B'],False)
        self.assertEqual(query,changed)
        self.assertTrue(all('rating' not in r for r in query))
        prompt=messages(None,query,features,['genre:A','genre:B'])
        self.assertNotIn('coat',str(prompt));self.assertIn('target movie',prompt[0]['content'])

    def test_mse_identity(self):
        r=metrics([1,4,3,5],[2,2,5,4])
        self.assertAlmostEqual(r['mse'],r['level_mse']+r['centered_mse'])
        s=metrics([2,5,4,6],[3,3,6,5])
        self.assertEqual(r['mse'],s['mse'])


if __name__=='__main__':unittest.main()
