import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from coat_memory_reader import parse_predictions,targets,records

class ReaderTests(unittest.TestCase):
    def test_no_silent_repair(self):
        for text in ['[1,6]','[true,2]','[1]','[1,2,3]','Here: [1,2]','[NaN,2]','[1,"2"]','{"x":[1,2]}']:
            self.assertIsNone(parse_predictions(text,2),text)
        self.assertEqual(parse_predictions('```json\n[1,2.5]\n```',2),[1.,2.5])
    def test_targets_remove_known_items_and_ratings(self):
        history=np.array([3.,0.,0.]);features=np.array([[1,1],[1,0],[0,1]])
        names=['color:black','onfrontpage:yes']
        actual=targets(history,np.array([True,True,False]),features,names)
        self.assertEqual(actual,[{'item':'coat-001','attributes':['color:black']}])
    def test_history_preserves_low_ratings_excludes_promotion(self):
        actual=records(np.array([1,5]),np.array([[1,1],[1,0]]),['color:black','onfrontpage:yes'])
        self.assertEqual([x['rating'] for x in actual],[1,5])
        self.assertTrue(all(x['attributes']==['color:black'] for x in actual))

if __name__=='__main__':unittest.main()
