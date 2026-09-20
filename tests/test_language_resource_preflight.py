from pathlib import Path
import sys
import unittest
import json
import tempfile
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from run_language_resource_preflight import select_cases,bm25_selection,summary_text,reader_valid,native_export_complete,install_request_audit,MODEL


class ResourcePreflightTests(unittest.TestCase):
    def test_selection_uses_only_development_input_lengths(self):
        cases=[str(i) for i in range(60)]
        prep={'groups':{'development':cases,'reserved_confirmation':['never']},
              'token_counts':{c:{'qwen':{'full_history_reader':int(c)}} for c in cases}}
        self.assertEqual(select_cases(prep),['0','30','59'])

    def test_bm25_favors_matching_text_not_rating(self):
        instance={'history':[{'product':{'title':'Plain','features':[]},
                             'review':t,'rating':r} for t,r in [('piano keys',1),('guitar strings',5),('drum sticks',2)]],
                  'targets':[{'product':{'title':'Piano','features':[]}}]}
        self.assertEqual(bm25_selection(instance,1),[0])
        for item in instance['history']: item['rating']='FORBIDDEN'
        self.assertEqual(bm25_selection(instance,1),[0])

    def test_bm25_ties_are_deterministic(self):
        instance={'history':[{'product':{'title':'same','features':[]},'review':'same'} for _ in range(12)],
                  'targets':[{'product':{'title':'unmatched','features':[]}}]}
        self.assertEqual(bm25_selection(instance),[0,1,2,3])

    def test_summary_format_and_termination(self):
        def raw(content,finish='stop'):
            return {'response':{'choices':[{'finish_reason':finish,'message':{'content':content}}]}}
        self.assertEqual(summary_text(raw('{"profile":"Some evidence"}')),'Some evidence')
        for value in (raw('{"profile":"Some evidence"}','length'),raw('{"profile":""}'),
                      raw('{"profile":"x","extra":1}'),raw('No JSON'),{}):
            self.assertIsNone(summary_text(value))


    def test_malformed_completions_count_as_invalid(self):
        for response in ({}, {'choices':[]}, {'choices':[None]},
                         {'choices':[{'finish_reason':'stop','message':{'content':None}}]}):
            raw={'response':response}
            self.assertIsNone(summary_text(raw))
            self.assertFalse(reader_valid(raw))
        raw={'response':{'choices':[{'finish_reason':'stop','message':{'content':'[1, 3.5, 5]'}}]}}
        self.assertTrue(reader_valid(raw))

    def test_summary_rejects_over_budget_without_truncation(self):
        def raw(n):
            return {'response':{'choices':[{'finish_reason':'stop',
                'message':{'content':json.dumps({'profile':' '.join(['word']*n)})}}]}}
        self.assertIsNotNone(summary_text(raw(400)))
        self.assertIsNone(summary_text(raw(401)))

    def test_export_rejects_duplicate_or_missing_memory(self):
        added={'results':[{'id':'a'},{'id':'b'}]}
        stored={'results':[{'id':'a','memory':'one'},{'id':'b','memory':'two'}]}
        self.assertTrue(native_export_complete(added,stored))
        stored['results'].append(stored['results'][0])
        self.assertFalse(native_export_complete(added,stored))
        self.assertFalse(native_export_complete(added,{'results':[{'id':'a'},{'id':'b'}]}))

    def test_request_budget_blocks_before_transport(self):
        calls=[]
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:calls.append(kw))))
        with tempfile.TemporaryDirectory() as folder:
            install_request_audit(client,Path(folder),counter=lambda _: {'prompt_tokens':16300})
            with self.assertRaisesRegex(ValueError,'resource allowance'):
                client.chat.completions.create(model=str(MODEL),temperature=0,top_p=1,max_tokens=256,messages=[])
            record=json.loads(next(Path(folder).glob('*.json')).read_text())
            self.assertFalse(record['transport_attempted'])
            self.assertEqual(record['status'],'error')
            self.assertEqual(calls,[])

    def test_failed_transport_attempt_is_retained(self):
        def failed(**kwargs):raise ConnectionError('fixture')
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=failed)))
        with tempfile.TemporaryDirectory() as folder:
            install_request_audit(client,Path(folder),counter=lambda _: {'prompt_tokens':10})
            with self.assertRaises(ConnectionError):
                client.chat.completions.create(model=str(MODEL),temperature=0,top_p=1,max_tokens=256,messages=[])
            record=json.loads(next(Path(folder).glob('*.json')).read_text())
            self.assertTrue(record['transport_attempted'])
            self.assertEqual(record['status'],'error')


if __name__=='__main__':unittest.main()
