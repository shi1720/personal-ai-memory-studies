import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from coat_memory_reader import targets,records,messages

class BoundaryTests(unittest.TestCase):
    def test_changing_target_ratings_cannot_change_prompt(self):
        h=np.array([1.,0.,0.]);a=np.array([0.,1.,5.]);b=np.array([0.,5.,1.])
        f=np.array([[1,0],[0,1],[1,1]]);names=['color:black','type:rain']
        context=str(records(h,f,names))
        self.assertEqual(messages(context,targets(h,a>0,f,names)),messages(context,targets(h,b>0,f,names)))
    def test_no_demographics_or_promotion_in_features(self):
        h=np.array([5,1]);f=np.array([[1,1],[0,1]])
        r=records(h,f,['color:black','onfrontpage:yes'])
        self.assertNotIn('onfrontpage',str(r))
        self.assertEqual(len(r),2)

if __name__=='__main__':unittest.main()
