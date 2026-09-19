import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from independent_result_check import measurements,numerical,parse,validate_prompt
import json

class IndependentCalculationTests(unittest.TestCase):
    def test_hand_computed_loss(self):
        r=measurements([2,5],[1,3])
        self.assertEqual(r['mae'],1.5);self.assertEqual(r['mse'],2.5)
        self.assertEqual(r['level_mse'],2.25);self.assertEqual(r['centered_mse'],.25)
        self.assertEqual(r['pairwise_accuracy'],1.)

    def test_prompt_audit_detects_leaked_target_label(self):
        history=np.array([0.,5.,0.]);target=np.array([0.,5.,2.]);features=np.array([[1.,0.],[1.,1.],[1.,0.]])
        query=[{'item':'coat-002','attributes':[]}]
        def raw(q):return {'messages':[{'role':'system','content':'unused'},
          {'role':'user','content':'Personal evidence:\nNo personal history is available.\n\nTarget coats in output order:\n'+json.dumps(q)+'\n\nReturn 1 ratings as one JSON array.'}]}
        validate_prompt('coat',1,'no_history',raw(query),history,target,features,['intercept','color:red'])
        query[0]['rating']=2
        with self.assertRaises(AssertionError):validate_prompt('coat',1,'no_history',raw(query),history,target,features,['intercept','color:red'])

    def test_augmented_fit_with_intercept_only(self):
        p=numerical(np.array([1.,3.,0.]),np.ones((3,1)),'history_ridge',2,1)
        np.testing.assert_allclose(p,[2.5]*3)

    def test_strict_parser_rejects_booleans_nan_wrong_shape(self):
        def r(s):return {'response':{'choices':[{'finish_reason':'stop','message':{'content':s}}]}}
        for s in ['[true,3]','[NaN,3]','[2]','[0,3]']:self.assertIsNone(parse(r(s),2))
        self.assertEqual(parse(r('```json\n[1,5]\n```'),2),[1,5])

if __name__=='__main__':unittest.main()
