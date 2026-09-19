"""Pinned, resumable native-prompt component test with paired reader controls."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time
import mlx.core as mx
from mlx_lm import load,stream_generate
from mlx_lm.sample_utils import make_sampler
from extraction_pilot_data import writer_messages,reader_messages,parse_facts,parse_answer
from run_retention_pilot import sha
ROOT=Path(__file__).resolve().parents[1]
MODELS={'qwen':('qwen3-4b-instruct-2507-4bit','local-model-manifest.json'),
        'phi':('phi-4-4bit','phi-model-manifest.json')}
CONTEXTS=['full','native','count_aware','ledger']

def key(row):return (row['journal'],row['stage'],row['context'],row.get('question_kind',''))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',required=True,choices=MODELS);args=parser.parse_args()
    directory_name,manifest_name=MODELS[args.model];directory=ROOT/'models'/directory_name
    for r in json.loads((ROOT/'references'/manifest_name).read_text())['files']:
        if sha(directory/r['name'])!=r['sha256']:raise ValueError('Changed model')
    inputs=json.loads((ROOT/'results/pilot-004-inputs.json').read_text())
    if len(inputs)!=12:raise ValueError('Unexpected population')
    upstream_prompt=(ROOT/'results/pilot-004-extraction-prompt.txt').read_text()
    dependencies=['src/run_extraction_pilot.py','src/extraction_pilot_data.py','src/run_retention_pilot.py',
                  'docs/pilot-004.md','results/pilot-004-inputs.json','results/pilot-004-extraction-prompt.txt',
                  'references/mem0-prompt-screen.json','references/'+manifest_name]
    manifest={'status':'exploratory prompt-component test; not end-to-end Mem0',
              'model':args.model,'temperature':0,'seed':0,'max_prompt_tokens':4096,
              'max_writer_tokens':1536,'max_reader_tokens':256,'planned_writer_cases':24,
              'planned_reader_cases':96,'hashes':{p:sha(ROOT/p) for p in dependencies},
              'versions':{p:importlib.metadata.version(p) for p in ['mlx','mlx-lm','transformers']}}
    prefix=ROOT/'results'/f'pilot-004-{args.model}'
    mp=Path(str(prefix)+'-manifest.json')
    if mp.exists() and json.loads(mp.read_text())!=manifest:raise ValueError('Run identity changed')
    mp.write_text(json.dumps(manifest,indent=2)+'\n')
    output=Path(str(prefix)+'-predictions.jsonl');completed={}
    if output.exists():
        for line in output.read_text().splitlines():
            row=json.loads(line);k=key(row)
            if k in completed:raise ValueError('Duplicate case')
            completed[k]=row
    expected={(j['id'],'writer',c,'') for j in inputs for c in ['native','count_aware']}
    expected|={(j['id'],'reader',c,q['kind']) for j in inputs for c in CONTEXTS for q in j['queries']}
    if len(expected)!=120 or not set(completed)<=expected:raise ValueError('Unexpected cases')
    model,tok=load(str(directory),tokenizer_config={'trust_remote_code':False})

    def generate(ms,max_tokens):
        prompt=tok.apply_chat_template(ms,tokenize=False,add_generation_prompt=True)
        tokens=tok.encode(prompt,add_special_tokens=False)
        if len(tokens)>4096:raise ValueError('Prompt exceeds budget')
        mx.random.seed(0);start=time.perf_counter();parts=[];last=None
        for response in stream_generate(model,tok,tokens,max_tokens=max_tokens,sampler=make_sampler(temp=0.0)):
            parts.append(response.text);last=response
        if last is None:raise RuntimeError('No generation')
        row={'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
             'text':''.join(parts),'prompt_tokens':last.prompt_tokens,'generation_tokens':last.generation_tokens,
             'finish_reason':last.finish_reason,'generation_seconds':time.perf_counter()-start}
        mx.clear_cache();return row

    def save(row):
        if key(row) in completed:raise ValueError('Duplicate write')
        row['model']=args.model
        with output.open('a') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
        completed[key(row)]=row
        print(f"Completed {len(completed)}/120 {key(row)} status={row['status']}",flush=True)

    for journal in inputs:
        for context in ['native','count_aware']:
            k=(journal['id'],'writer',context,'')
            if k in completed:continue
            row=generate(writer_messages(upstream_prompt,journal['journal_text'],context=='count_aware'),1536)
            facts=parse_facts(row['text'])
            row.update(journal=journal['id'],stage='writer',context=context,facts=facts,
                       status='valid' if facts is not None else 'invalid')
            save(row)
        for context in CONTEXTS:
            if context=='full':evidence=journal['journal_text']
            elif context=='ledger':evidence=journal['ledger']
            else:
                writer=completed[(journal['id'],'writer',context,'')]
                if parse_facts(writer['text'])!=writer['facts']:raise ValueError('Saved writer parsing mismatch')
                evidence=json.dumps({'facts':writer['facts']},ensure_ascii=False) if writer['facts'] is not None else None
            for query in journal['queries']:
                k=(journal['id'],'reader',context,query['kind'])
                if k in completed:continue
                if evidence is None:
                    save({'journal':journal['id'],'stage':'reader','context':context,'question_kind':query['kind'],
                          'status':'blocked_writer','reason':'Invalid extraction output; no reader generation performed'})
                    continue
                row=generate(reader_messages(evidence,query['question'],query['options']),256)
                answer=parse_answer(row['text'],set(query['options']))
                row.update(journal=journal['id'],stage='reader',context=context,question_kind=query['kind'],
                           parsed_answer=answer,status='valid' if answer is not None else 'invalid',
                           evidence=evidence,evidence_sha256=hashlib.sha256(evidence.encode()).hexdigest(),
                           evidence_bytes=len(evidence.encode()),evidence_tokens=len(tok.encode(evidence,add_special_tokens=False)))
                save(row)
if __name__=='__main__':main()
