"""Complete-case accounting for every planned extraction and reader case."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
from extraction_pilot_data import parse_facts,parse_answer
ROOT=Path(__file__).resolve().parents[1]
CONTEXTS=['full','native','count_aware','ledger']

def classify(row,truth):
    if row['status']=='blocked_writer':return 'blocked_writer'
    if row['status']=='invalid':return 'invalid'
    answer=row['parsed_answer']['answer']
    if answer==truth['abstain']:return 'abstained'
    return 'correct' if answer==truth['answer'] else 'wrong'

def aggregate(rows):
    counts={k:sum(r['outcome']==k for r in rows) for k in ['correct','wrong','abstained','invalid','blocked_writer']}
    n=len(rows);answered=counts['correct']+counts['wrong']
    return {'planned':n,**counts,'answer_coverage':answered/n if n else None,
            'source_truth_accuracy':counts['correct']/n if n else None,
            'error_given_answered':counts['wrong']/answered if answered else None}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',required=True,choices=['qwen','phi']);args=parser.parse_args()
    prefix=ROOT/'results'/f'pilot-004-{args.model}'
    manifest=json.loads(Path(str(prefix)+'-manifest.json').read_text())
    for p,digest in manifest['hashes'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=digest:raise ValueError('Changed dependency: '+p)
    inputs={j['id']:j for j in json.loads((ROOT/'results/pilot-004-inputs.json').read_text())}
    gold={j['id']:j for j in json.loads((ROOT/'results/pilot-004-gold.json').read_text())}
    trace_path=Path(str(prefix)+'-predictions.jsonl')
    trace=[json.loads(line) for line in trace_path.read_text().splitlines()]
    keys=[(r['journal'],r['stage'],r['context'],r.get('question_kind','')) for r in trace]
    expected={(j,'writer',c,'') for j in inputs for c in ['native','count_aware']}
    expected|={(j,'reader',c,q['kind']) for j,item in inputs.items() for c in CONTEXTS for q in item['queries']}
    if len(keys)!=120 or set(keys)!=expected:raise ValueError('Complete unique trace required')
    readers=[];writers=[]
    for r in trace:
        if r['status']!='blocked_writer':
            if hashlib.sha256(r['prompt'].encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('Prompt hash mismatch')
            if r['prompt_tokens']>4096 or r['generation_tokens']>(1536 if r['stage']=='writer' else 256):raise ValueError('Budget exceeded')
        if r['stage']=='writer':
            facts=parse_facts(r['text'])
            if facts!=r['facts'] or (facts is not None)!=(r['status']=='valid'):raise ValueError('Writer parsing mismatch')
            writers.append({'journal':r['journal'],'context':r['context'],'valid':facts is not None,
                            'truncated':r['finish_reason']=='length','fact_count':len(facts) if facts is not None else None,
                            'stored_bytes':len(json.dumps({'facts':facts},ensure_ascii=False).encode()) if facts is not None else None,
                            'facts':facts})
        else:
            question=next(q for q in inputs[r['journal']]['queries'] if q['kind']==r['question_kind'])
            truth=next(t for t in gold[r['journal']]['answers'] if t['kind']==r['question_kind'])
            if r['status']!='blocked_writer':
                parsed=parse_answer(r['text'],set(question['options']))
                if parsed!=r['parsed_answer'] or (parsed is not None)!=(r['status']=='valid'):raise ValueError('Reader parsing mismatch')
                if hashlib.sha256(r['evidence'].encode()).hexdigest()!=r['evidence_sha256']:raise ValueError('Evidence hash mismatch')
            else:
                parent=next(w for w in trace if w['journal']==r['journal'] and w['stage']=='writer' and w['context']==r['context'])
                if parent['status']!='invalid':raise ValueError('Unexpected blocked reader')
            readers.append({'journal':r['journal'],'context':r['context'],'kind':r['question_kind'],
                            'rendering':inputs[r['journal']]['rendering'],'outcome':classify(r,truth),
                            'evidence_tokens':r.get('evidence_tokens'),'evidence_bytes':r.get('evidence_bytes'),
                            'prompt_tokens':r.get('prompt_tokens'),'truncated':r.get('finish_reason')=='length'})
    summaries={};paired={};writer_summaries={}
    for context in CONTEXTS:
        summaries[context]={}
        for kind in ['rate','event']:
            rows=[r for r in readers if r['context']==context and r['kind']==kind]
            summaries[context][kind]=aggregate(rows)
            summaries[context][kind]['by_rendering']={v:aggregate([r for r in rows if r['rendering']==v]) for v in ['plain','positive_detail','negative_detail']}
        generated=[r for r in readers if r['context']==context and r['evidence_tokens'] is not None]
        summaries[context]['mean_evidence_tokens']=statistics.mean(r['evidence_tokens'] for r in generated) if generated else None
        summaries[context]['mean_prompt_tokens']=statistics.mean(r['prompt_tokens'] for r in generated) if generated else None
    for context in ['native','count_aware']:
        rows=[w for w in writers if w['context']==context];valid=[w for w in rows if w['valid']]
        writer_summaries[context]={'planned':len(rows),'valid':len(valid),'truncated':sum(w['truncated'] for w in rows),
            'mean_fact_count':statistics.mean(w['fact_count'] for w in valid) if valid else None,
            'mean_stored_bytes':statistics.mean(w['stored_bytes'] for w in valid) if valid else None}
    for context in CONTEXTS[1:]:
        paired[context]={}
        for kind in ['rate','event']:
            records=[]
            for jid in inputs:
                base=next(r for r in readers if r['journal']==jid and r['context']=='full' and r['kind']==kind)
                new=next(r for r in readers if r['journal']==jid and r['context']==context and r['kind']==kind)
                records.append({'journal':jid,'full':base['outcome'],'compressed':new['outcome']})
            paired[context][kind]={'full_correct':sum(r['full']=='correct' for r in records),
                'retained_correct':sum(r['full']=='correct' and r['compressed']=='correct' for r in records),
                'losses':{o:sum(r['full']=='correct' and r['compressed']==o for r in records) for o in ['wrong','abstained','invalid','blocked_writer']},
                'reverse_gains':sum(r['full']!='correct' and r['compressed']=='correct' for r in records),'pairs':records}
    out={'status':'exploratory native-prompt component test; not deployed-system evaluation',
         'model':args.model,'planned_cases':120,'actual_generations':sum(r['status']!='blocked_writer' for r in trace),
         'generation_seconds':sum(r.get('generation_seconds',0) for r in trace),
         'reader_truncations':sum(r['truncated'] for r in readers),'writer_summaries':writer_summaries,
         'summaries':summaries,'paired':paired,'reader_measurements':readers,'writer_inspection':writers,
         'hashes':{'trace':hashlib.sha256(trace_path.read_bytes()).hexdigest(),
                   'gold':hashlib.sha256((ROOT/'results/pilot-004-gold.json').read_bytes()).hexdigest(),
                   'analysis':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
    Path(str(prefix)+'-analysis.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'writers':writer_summaries,'summaries':summaries,'paired':{c:{k:{t:v for t,v in r.items() if t!='pairs'} for k,r in b.items()} for c,b in paired.items()}},indent=2))
if __name__=='__main__':main()
