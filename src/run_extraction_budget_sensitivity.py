"""All-condition post hoc rate-reader budget check, exact same prompts."""
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
from extraction_pilot_data import reader_messages,parse_answer
from run_retention_pilot import sha
ROOT=Path(__file__).resolve().parents[1]
MODELS={'qwen':('qwen3-4b-instruct-2507-4bit','local-model-manifest.json'),'phi':('phi-4-4bit','phi-model-manifest.json')}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',required=True,choices=MODELS);args=parser.parse_args()
    folder,mm=MODELS[args.model];directory=ROOT/'models'/folder
    for r in json.loads((ROOT/'references'/mm).read_text())['files']:
        if sha(directory/r['name'])!=r['sha256']:raise ValueError('Changed model')
    original_path=ROOT/'results'/f'pilot-004-{args.model}-predictions.jsonl'
    original=[json.loads(l) for l in original_path.read_text().splitlines()]
    if len(original)!=120:raise ValueError('Complete initial run required')
    initial_manifest=json.loads((ROOT/'results'/f'pilot-004-{args.model}-manifest.json').read_text())
    for p,d in initial_manifest['hashes'].items():
        if sha(ROOT/p)!=d:raise ValueError('Changed initial dependency')
    original=[r for r in original if r['stage']=='reader' and r['question_kind']=='rate']
    inputs={j['id']:j for j in json.loads((ROOT/'results/pilot-004-inputs.json').read_text())}
    expected={(j,c) for j in inputs for c in ['full','native','count_aware','ledger']}
    if len(original)!=48 or {(r['journal'],r['context']) for r in original}!=expected:raise ValueError('Incomplete rate cases')
    deps=['src/run_extraction_budget_sensitivity.py','src/extraction_pilot_data.py','src/run_retention_pilot.py',
          'docs/pilot-004-reader-budget-sensitivity.md','results/pilot-004-inputs.json',
          f'results/pilot-004-{args.model}-predictions.jsonl',f'results/pilot-004-{args.model}-manifest.json','references/'+mm]
    manifest={'status':'post hoc output-budget sensitivity, not replacement of initial results',
              'model':args.model,'max_output_tokens':768,'max_prompt_tokens':4096,'temperature':0,'seed':0,
              'planned_cases':48,'hashes':{p:sha(ROOT/p) for p in deps},
              'versions':{p:importlib.metadata.version(p) for p in ['mlx','mlx-lm','transformers']}}
    prefix=ROOT/'results'/f'pilot-004-{args.model}-budget'
    mp=Path(str(prefix)+'-manifest.json')
    if mp.exists() and json.loads(mp.read_text())!=manifest:raise ValueError('Changed sensitivity identity')
    mp.write_text(json.dumps(manifest,indent=2)+'\n')
    output=Path(str(prefix)+'-predictions.jsonl');done=set()
    if output.exists():
        for line in output.read_text().splitlines():
            r=json.loads(line);k=(r['journal'],r['context'])
            if k in done:raise ValueError('Duplicate case')
            done.add(k)
    if not done<=expected:raise ValueError('Unexpected output cases')
    model,tok=load(str(directory),tokenizer_config={'trust_remote_code':False})
    for original_row in original:
        k=(original_row['journal'],original_row['context'])
        if k in done:continue
        row={'journal':k[0],'context':k[1],'model':args.model,'stage':'reader','question_kind':'rate'}
        if original_row['status']=='blocked_writer':row['status']='blocked_writer'
        else:
            query=next(q for q in inputs[k[0]]['queries'] if q['kind']=='rate')
            ms=reader_messages(original_row['evidence'],query['question'],query['options'])
            prompt=tok.apply_chat_template(ms,tokenize=False,add_generation_prompt=True)
            if prompt!=original_row['prompt']:raise ValueError('Prompt changed')
            tokens=tok.encode(prompt,add_special_tokens=False)
            if len(tokens)>4096:raise ValueError('Input budget exceeded')
            mx.random.seed(0);start=time.perf_counter();parts=[];last=None
            for r in stream_generate(model,tok,tokens,max_tokens=768,sampler=make_sampler(temp=0.0)):
                parts.append(r.text);last=r
            if last is None:raise RuntimeError('No generation')
            text=''.join(parts);parsed=parse_answer(text,set(query['options']))
            row.update(status='valid' if parsed is not None else 'invalid',text=text,parsed_answer=parsed,
                       prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                       original_prompt_sha256=original_row['prompt_sha256'],original_status=original_row['status'],
                       prompt_tokens=last.prompt_tokens,generation_tokens=last.generation_tokens,
                       finish_reason=last.finish_reason,generation_seconds=time.perf_counter()-start)
            mx.clear_cache()
        with output.open('a') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
        done.add(k);print(f"Completed {len(done)}/48 {k} status={row['status']}",flush=True)
if __name__=='__main__':main()
