"""Score separately the post hoc identical-prompt, higher-budget rate cases."""
import argparse
import hashlib
import json
from pathlib import Path
from extraction_pilot_data import parse_answer
from analyze_extraction_pilot import classify,aggregate
ROOT=Path(__file__).resolve().parents[1]
CONTEXTS=['full','native','count_aware','ledger']

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True,choices=['qwen','phi']);args=p.parse_args()
    prefix=ROOT/'results'/f'pilot-004-{args.model}-budget'
    manifest=json.loads(Path(str(prefix)+'-manifest.json').read_text())
    for path,digest in manifest['hashes'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Changed dependency')
    trace_path=Path(str(prefix)+'-predictions.jsonl')
    rows=[json.loads(l) for l in trace_path.read_text().splitlines()]
    original={(r['journal'],r['context']):r for r in [json.loads(l) for l in (ROOT/'results'/f'pilot-004-{args.model}-predictions.jsonl').read_text().splitlines()] if r['stage']=='reader' and r['question_kind']=='rate'}
    inputs={j['id']:j for j in json.loads((ROOT/'results/pilot-004-inputs.json').read_text())}
    gold={j['id']:next(a for a in j['answers'] if a['kind']=='rate') for j in json.loads((ROOT/'results/pilot-004-gold.json').read_text())}
    expected={(j,c) for j in inputs for c in CONTEXTS}
    if len(rows)!=48 or {(r['journal'],r['context']) for r in rows}!=expected:raise ValueError('Complete unique cases required')
    measured=[]
    for r in rows:
        o=original[(r['journal'],r['context'])]
        if r['status']=='blocked_writer':
            if o['status']!='blocked_writer':raise ValueError('Unexpected blocked row')
        else:
            if r['prompt']!=o['prompt'] or hashlib.sha256(r['prompt'].encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('Changed prompt')
            q=next(q for q in inputs[r['journal']]['queries'] if q['kind']=='rate')
            parsed=parse_answer(r['text'],set(q['options']))
            if parsed!=r['parsed_answer'] or (parsed is not None)!=(r['status']=='valid'):raise ValueError('Parsing mismatch')
            if r['generation_tokens']>768 or r['prompt_tokens']>4096:raise ValueError('Budget exceeded')
        measured.append({'journal':r['journal'],'context':r['context'],'outcome':classify(r,gold[r['journal']]),
                         'initial_outcome':classify(o,gold[r['journal']]),'truncated':r.get('finish_reason')=='length',
                         'initial_truncated':o.get('finish_reason')=='length',
                         'completed_response_changed':o.get('finish_reason')=='stop' and r.get('text')!=o.get('text')})
    summaries={c:aggregate([r for r in measured if r['context']==c]) for c in CONTEXTS}
    paired={}
    for c in CONTEXTS[1:]:
        pairs=[]
        for jid in inputs:
            full=next(r for r in measured if r['journal']==jid and r['context']=='full')
            mem=next(r for r in measured if r['journal']==jid and r['context']==c)
            pairs.append({'journal':jid,'full':full['outcome'],'compressed':mem['outcome']})
        paired[c]={'full_correct':sum(r['full']=='correct' for r in pairs),
                   'retained_correct':sum(r['full']=='correct' and r['compressed']=='correct' for r in pairs),
                   'losses':{o:sum(r['full']=='correct' and r['compressed']==o for r in pairs) for o in ['wrong','abstained','invalid','blocked_writer']},
                   'reverse_gains':sum(r['full']!='correct' and r['compressed']=='correct' for r in pairs),'pairs':pairs}
    out={'status':'post hoc identical-prompt output-budget sensitivity', 'model':args.model,
         'planned_cases':48,'actual_generations':sum(r['status']!='blocked_writer' for r in rows),
         'generation_seconds':sum(r.get('generation_seconds',0) for r in rows),
         'truncations':sum(r['truncated'] for r in measured),
         'completed_response_changes':sum(r['completed_response_changed'] for r in measured),
         'summaries':summaries,'paired':paired,'measurements':measured,
         'hashes':{'trace':hashlib.sha256(trace_path.read_bytes()).hexdigest(),
                   'analysis':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   'gold':hashlib.sha256((ROOT/'results/pilot-004-gold.json').read_bytes()).hexdigest()}}
    Path(str(prefix)+'-analysis.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'summaries':summaries,'truncations':out['truncations'],'completed_response_changes':out['completed_response_changes'],'paired':{c:{k:v for k,v in r.items() if k!='pairs'} for c,r in paired.items()}},indent=2))
if __name__=='__main__':main()
