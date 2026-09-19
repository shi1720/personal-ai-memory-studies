"""Post hoc audit of literal dated-event claims, with unparsed facts explicit.

This deliberately limited parser does not judge arbitrary prose or infer omitted
claims. Its grammar was developed after viewing Qwen's initial outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]

def literal_claims(fact):
    single=re.match(r'Attended (?:a )?(\w+) session on [Dd]ay (\d+)(?: and|,)? (did not enjoy|enjoyed)(?: it)?(?=$|[.,])',fact)
    if single:
        a,d,outcome=single.groups()
        return [{'activity':a,'day':int(d),'positive':outcome=='enjoyed'}],fact[single.end():].strip()
    dated=re.match(r'(?:V\d+ \| )?Day (\d+): Attended a (\w+) session(?: and|,)? (did not enjoy|enjoyed)(?: it| the session)?(?=$|[.,])',fact)
    if dated:
        d,a,outcome=dated.groups()
        return [{'activity':a,'day':int(d),'positive':outcome=='enjoyed'}],fact[dated.end():].strip()
    group=re.fullmatch(r'(Did not enjoy|Enjoyed) (\w+) sessions? on days: ([\d, ]+)',fact)
    if group:
        outcome,a,days=group.groups()
        return [{'activity':a,'day':int(d.strip()),'positive':outcome=='Enjoyed'} for d in days.split(',')],''
    attendance=re.fullmatch(r'Attended (\w+) sessions on days: ([\d, ]+)',fact)
    if attendance:
        a,days=attendance.groups()
        return [{'activity':a,'day':int(d.strip()),'positive':None} for d in days.split(',')],''
    return [],fact

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True,choices=['qwen','phi']);args=p.parse_args()
    path=ROOT/'results'/f'pilot-004-{args.model}-predictions.jsonl'
    trace=[json.loads(l) for l in path.read_text().splitlines()]
    if len(trace)!=120:raise ValueError('Complete initial run required')
    gold={j['id']:j for j in json.loads((ROOT/'results/pilot-004-gold.json').read_text())}
    records=[]
    for row in trace:
        if row['stage']!='writer':continue
        source={e['day']:e for e in gold[row['journal']]['events']}
        claims=[];unparsed=[];correct_days=set()
        for index,fact in enumerate(row['facts'] or []):
            parsed,residual=literal_claims(fact)
            if residual:unparsed.append({'fact_index':index,'residual_text':residual,'entire_fact_unparsed':not parsed})
            for claim in parsed:
                target=source.get(claim['day'])
                valid=target is not None and target['activity']==claim['activity'] and (claim['positive'] is None or target['positive']==claim['positive'])
                claims.append({'fact_index':index,**claim,'matches_source':valid,'source_event':target if not valid else None})
                if valid and claim['positive'] is not None:correct_days.add(claim['day'])
        records.append({'journal':row['journal'],'context':row['context'],'writer_status':row['status'],
                        'fact_count':len(row['facts']) if row['facts'] is not None else None,
                        'parsed_literal_claims':len(claims),'mismatched_literal_claims':sum(not c['matches_source'] for c in claims),
                        'distinct_source_days_with_matching_outcome':len(correct_days),
                        'claims':claims,'unparsed_residuals':unparsed})
    out={'status':'post hoc limited-grammar diagnostic, not a full semantic judge or independent human annotation',
         'model':args.model,'records':records,'hashes':{'trace':hashlib.sha256(path.read_bytes()).hexdigest(),
          'gold':hashlib.sha256((ROOT/'results/pilot-004-gold.json').read_bytes()).hexdigest(),
          'code':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
    (ROOT/'results'/f'pilot-004-{args.model}-claim-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    for r in records:
        print(r['journal'],r['context'],'claims',r['parsed_literal_claims'],'mismatches',r['mismatched_literal_claims'],
              'days covered',r['distinct_source_days_with_matching_outcome'],'unparsed facts',sum(x['entire_fact_unparsed'] for x in r['unparsed_residuals']))
if __name__=='__main__':main()
