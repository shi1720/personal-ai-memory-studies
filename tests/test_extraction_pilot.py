import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from extraction_pilot_data import generate,extract_upstream_prompt,parse_facts,parse_answer,writer_messages

class ExtractionPilotTests(unittest.TestCase):
    def test_population_targets_and_disjoint_seeds(self):
        inputs,gold=generate()
        self.assertEqual(len(inputs),12)
        self.assertEqual({g['seed'] for g in gold},set(range(41000,41012)))
        self.assertTrue(all(len(g['events'])==24 for g in gold))
        for g in gold:
            for activity,n in zip(g['activities'],g['counts']):
                events=[e for e in g['events'] if e['activity']==activity]
                self.assertEqual(len(events),12)
                self.assertEqual(sum(e['positive'] for e in events),n)
            self.assertEqual(len({e['id'] for e in g['events']}),24)
    def test_detail_sign_and_labels(self):
        inputs,gold=generate()
        for item,g in zip(inputs,gold):
            marked=[e for e in g['events'] if e['detail']]
            self.assertEqual(len(marked),0 if item['rendering']=='plain' else 3)
            if marked:self.assertTrue(all(e['positive']==(item['rendering']=='positive_detail') for e in marked))
            for q,a in zip(item['queries'],g['answers']):
                self.assertIn(a['answer'],q['options']);self.assertIn(a['abstain'],q['options'])
                self.assertNotEqual(a['answer'],a['abstain'])
    def test_writer_interface_does_not_receive_query(self):
        source='EVENT TEXT';ms=writer_messages('UPSTREAM PROMPT',source)
        self.assertEqual(ms[0]['content'],'UPSTREAM PROMPT')
        self.assertEqual(ms[1]['content'],'User: Here is my complete activity journal.\nEVENT TEXT')
    def test_restricted_ast_prompt_loading(self):
        source='USER_MEMORY_EXTRACTION_PROMPT = f"Hello {{json}} {datetime.now().strftime(\'%Y-%m-%d\')}"'
        self.assertEqual(extract_upstream_prompt(source),'Hello {json} 2026-09-19')
        with self.assertRaises(ValueError):extract_upstream_prompt('USER_MEMORY_EXTRACTION_PROMPT = f"{dangerous()}"')
    def test_json_schema_and_fence_policy(self):
        self.assertEqual(parse_facts('{"facts": []}'),[])
        self.assertEqual(parse_facts('```json\n{"facts": ["a"]}\n```'),['a'])
        for text in ['prefix {"facts": []}','{"facts": [1]}','{"facts": [""]}','{"facts": [], "extra": 1}']:
            self.assertIsNone(parse_facts(text))
        self.assertEqual(parse_answer('{"reason":"counted", "answer":"B"}',set('ABCD'))['answer'],'B')
        for text in ['{"answer":"B"}','{"reason":"a","answer":"X"}','{"reason":2,"answer":"A"}']:
            self.assertIsNone(parse_answer(text,set('ABCD')))

class ExtractionScoringTests(unittest.TestCase):
    def test_abstention_is_not_wrong_and_blocked_stays_in_denominator(self):
        from analyze_extraction_pilot import classify,aggregate
        truth={'answer':'A','abstain':'D'}
        rows=[]
        for status,letter in [('valid','A'),('valid','B'),('valid','D'),('invalid',None),('blocked_writer',None)]:
            row={'status':status,'parsed_answer':{'answer':letter}}
            rows.append({'outcome':classify(row,truth)})
        result=aggregate(rows)
        self.assertEqual(result['planned'],5)
        self.assertEqual(result['answer_coverage'],.4)
        self.assertEqual(result['error_given_answered'],.5)
        self.assertEqual(result['source_truth_accuracy'],.2)
        self.assertEqual(result['abstained'],1)
        self.assertEqual(result['blocked_writer'],1)
    def test_source_truth_independently_matches_input_text(self):
        import re
        inputs,gold=generate()
        for item,g in zip(inputs,gold):
            counts={a:[0,0] for a in g['activities']}
            outcomes={}
            for line in item['journal_text'].splitlines():
                day=int(re.search(r'Day (\d+):',line).group(1))
                act=re.search(r'attended a (\w+) session',line).group(1)
                positive='I enjoyed the session.' in line
                counts[act][0]+=positive;counts[act][1]+=1;outcomes[day]=positive
            rates={a:p/n for a,(p,n) in counts.items()}
            for q,t in zip(item['queries'],g['answers']):
                chosen=q['options'][t['answer']]
                if q['kind']=='rate':
                    if len(set(rates.values()))==1:self.assertTrue(chosen.startswith('Both activities'))
                    else:self.assertEqual(chosen,max(rates,key=rates.get))
                else:
                    day=int(re.search(r'Day (\d+)',q['question']).group(1))
                    self.assertEqual(chosen.startswith('Yes,'),outcomes[day])

if __name__=='__main__':unittest.main()
