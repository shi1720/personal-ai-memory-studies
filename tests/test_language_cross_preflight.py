from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from language_cross_runtime import Runtime
from language_model_pins import model_path
from run_language_cross_preflight import native_valid,native_text,diagnostic_evidence,handoff,response_bijection,validate_handoff_state


class CrossRuntimeTests(unittest.TestCase):
    def request(self,model='phi',budget=256):
        return dict(model=str(model_path(model)),messages=[{'role':'user','content':'fixture'}],temperature=0,top_p=1,max_tokens=budget)

    def client(self,call):
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=call)))

    def test_wrong_model_cannot_reach_transport(self):
        calls=[]
        with tempfile.TemporaryDirectory() as folder:
            run=Runtime('phi',folder,27,counter=lambda m,q:{'model':m,'prompt_tokens':10})
            client=run.instrument(self.client(lambda **kw:calls.append(kw)))
            with self.assertRaisesRegex(ValueError,'Wrong model'):
                client.chat.completions.create(**self.request('qwen'))
            row=json.loads(next(run.audit.glob('*.json')).read_text())
            self.assertFalse(row['transport_attempted']);self.assertEqual(calls,[])

    def test_cap_and_budget_rejections_are_not_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Runtime('phi',folder,1,counter=lambda m,q:{'model':m,'prompt_tokens':16384})
            client=run.instrument(self.client(lambda **kw:self.fail('Transport must not run')))
            with self.assertRaisesRegex(ValueError,'resource allowance'):client.chat.completions.create(**self.request())
            with self.assertRaisesRegex(RuntimeError,'ceiling'):client.chat.completions.create(**self.request())
            self.assertEqual(len(list(run.audit.glob('*.json'))),1)

    def test_failed_transport_is_recorded_once_and_cached(self):
        calls=[]
        def fail(**kwargs):calls.append(kwargs);raise TimeoutError('fixture')
        with tempfile.TemporaryDirectory() as folder:
            run=Runtime('phi',folder,27,counter=lambda m,q:{'model':m,'prompt_tokens':10})
            client=run.instrument(self.client(fail));path=Path(folder)/'result.json'
            first=run.request(client,path,[],256);second=run.request(client,path,[],256)
            self.assertEqual(first,second);self.assertEqual(len(calls),1)
            row=json.loads(next(run.audit.glob('*.json')).read_text())
            self.assertTrue(row['transport_attempted']);self.assertEqual(row['status'],'error')
            with self.assertRaisesRegex(ValueError,'not identical'):run.request(client,path,[{'role':'user','content':'changed'}],256)

    def test_interrupted_request_cannot_regenerate(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Runtime('phi',folder,27);path=Path(folder)/'result.json';path.with_suffix('.started').write_text('started')
            with self.assertRaises(FileExistsError):run.request(self.client(lambda **kw:self.fail('No transport')),path,[],256)

    def test_wrong_tokenizer_is_rejected_before_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            run=Runtime('phi',folder,27,counter=lambda m,q:{'model':'qwen','prompt_tokens':10})
            client=run.instrument(self.client(lambda **kw:self.fail('No transport')))
            with self.assertRaisesRegex(ValueError,'wrong model'):client.chat.completions.create(**self.request())

    def native(self):
        return {'status':'completed','export_complete':True,
                'add':{'results':[{'id':'a','memory':'earlier evidence'}]},
                'stored':{'results':[{'id':'a','memory':'earlier evidence'}]},
                'traces':[{'response':{'choices':[{'finish_reason':'stop'}]}}]}

    def test_changed_export_text_or_nonstop_is_invalid(self):
        raw=self.native();self.assertTrue(native_valid(raw))
        raw['stored']['results'][0]['memory']='different';self.assertFalse(native_valid(raw))
        self.assertEqual(native_text(raw),'No stored memories are available.')
        self.assertTrue(diagnostic_evidence('native_phi',{'phi':(raw,{})}))
        raw=self.native();raw['traces'][0]['response']['choices'][0]['finish_reason']='length'
        self.assertFalse(native_valid(raw))

    def test_handoff_rejects_modified_phi_writer(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);run=root/'run';(run/'case'/'phi').mkdir(parents=True)
            (run/'manifest.json').write_text('{}')
            for name in ('native-writer.json','summary-writer.json'):(run/'case'/'phi'/name).write_text('{}')
            with patch('run_language_cross_preflight.ROOT',root),patch('run_language_cross_preflight.RUN',run):
                handoff({'cases':['case']},create=True)
                handoff({'cases':['case']})
                (run/'case'/'phi'/'native-writer.json').write_text('{"changed":true}')
                with self.assertRaisesRegex(ValueError,'handoff changed'):handoff({'cases':['case']})


    def test_response_bijection_rejects_duplicates_and_changed_content(self):
        rows=[{'id':'a','sha256':'first','model':'phi'},{'id':'b','sha256':'second','model':'phi'}]
        self.assertTrue(response_bijection(rows,list(reversed(rows)),2))
        self.assertFalse(response_bijection(rows,[rows[0],rows[0]],2))
        altered=[dict(rows[0]),dict(rows[1])];altered[1]['sha256']='changed'
        self.assertFalse(response_bijection(rows,altered,2))
        self.assertFalse(response_bijection(rows,[rows[0],None],2))

    def test_wrong_response_model_is_retained_as_failure(self):
        response=SimpleNamespace(model_dump=lambda **kw:{'id':'fixture','model':str(model_path('qwen'))})
        with tempfile.TemporaryDirectory() as folder:
            run=Runtime('phi',folder,27,counter=lambda m,q:{'model':m,'prompt_tokens':10})
            client=run.instrument(self.client(lambda **kw:response))
            with self.assertRaisesRegex(ValueError,'wrong model identity'):client.chat.completions.create(**self.request())
            row=json.loads(next(run.audit.glob('*.json')).read_text())
            self.assertEqual(row['status'],'error');self.assertTrue(row['transport_attempted'])
            self.assertEqual(row['response']['id'],'fixture')

    def test_reports_cannot_bypass_handoff(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);run=root/'run';(run/'case'/'phi').mkdir(parents=True)
            (run/'manifest.json').write_text('{}')
            for name in ('native-writer.json','summary-writer.json'):(run/'case'/'phi'/name).write_text('{}')
            with patch('run_language_cross_preflight.ROOT',root),patch('run_language_cross_preflight.RUN',run):
                validate_handoff_state({'cases':['case']})
                (run/'case'/'qwen').mkdir();(run/'case'/'qwen'/'native_phi.json').write_text('{}')
                with self.assertRaisesRegex(ValueError,'required'):validate_handoff_state({'cases':['case']})
                handoff({'cases':['case']},create=True)
                validate_handoff_state({'cases':['case']})
                (run/'case'/'phi'/'summary-writer.json').write_text('{"changed":true}')
                with self.assertRaisesRegex(ValueError,'changed'):validate_handoff_state({'cases':['case']})


if __name__=='__main__':unittest.main()
