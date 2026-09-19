"""Frozen, resumable 48-call custom memory-writer pilot."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time
import mlx.core as mx
from mlx_lm import load,stream_generate
from mlx_lm.sample_utils import make_sampler
from retention_pilot_data import messages,parse_selection

ROOT=Path(__file__).resolve().parents[1]

def sha(p):
    digest=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def main():
    journals=json.loads((ROOT/'results/pilot-003-journals.json').read_text())
    if len(journals)!=12:raise ValueError('Complete fixed population required')
    model_manifest=json.loads((ROOT/'references/local-model-manifest.json').read_text())
    directory=ROOT/'models/qwen3-4b-instruct-2507-4bit'
    for record in model_manifest['files']:
        if sha(directory/record['name'])!=record['sha256']:raise ValueError('Changed model file')
    dependencies=['src/run_retention_pilot.py','src/retention_pilot_data.py','docs/pilot-003.md',
                  'results/pilot-003-journals.json','references/local-model-manifest.json']
    manifest={'status':'exploratory custom selection prompts; not a published-method reproduction',
              'hashes':{p:sha(ROOT/p) for p in dependencies},'temperature':0,'max_output_tokens':160,
              'max_prompt_tokens':4096,'seed':0,'expected_calls':48,
              'versions':{p:importlib.metadata.version(p) for p in ['mlx','mlx-lm','transformers']}}
    mp=ROOT/'results/pilot-003-run-manifest.json'
    if mp.exists() and json.loads(mp.read_text())!=manifest:raise ValueError('Run identity changed')
    mp.write_text(json.dumps(manifest,indent=2)+'\n')
    output=ROOT/'results/pilot-003-predictions.jsonl'
    completed=set()
    if output.exists():
        for line in output.read_text().splitlines():
            row=json.loads(line);key=(row['journal'],row['writer'],row['detailed'])
            if key in completed:raise ValueError('Duplicate completed case')
            completed.add(key)
    model,tokenizer=load(str(directory),tokenizer_config={'trust_remote_code':False})
    for journal in journals:
        for writer in ['important','representative']:
            for detailed in [False,True]:
                key=(journal['id'],writer,detailed)
                if key in completed:continue
                prompt=tokenizer.apply_chat_template(messages(journal,writer,detailed),tokenize=False,add_generation_prompt=True)
                tokens=tokenizer.encode(prompt,add_special_tokens=False)
                if len(tokens)>4096:raise ValueError('Prompt budget exceeded')
                mx.random.seed(0);start=time.perf_counter();parts=[];last=None
                for response in stream_generate(model,tokenizer,tokens,max_tokens=160,sampler=make_sampler(temp=0.0)):
                    parts.append(response.text);last=response
                elapsed=time.perf_counter()-start
                if last is None:raise RuntimeError('No generation response')
                text=''.join(parts)
                selection=parse_selection(text,{e['id'] for e in journal['events']})
                row={'journal':journal['id'],'writer':writer,'detailed':detailed,
                     'prompt':prompt,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                     'text':text,'selection':selection,'valid':selection is not None,
                     'prompt_tokens':last.prompt_tokens,'generation_tokens':last.generation_tokens,
                     'finish_reason':last.finish_reason,'reader_seconds':elapsed}
                with output.open('a') as f:
                    f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
                completed.add(key);mx.clear_cache()
                print(f'Completed {len(completed)}/48 {key} valid={selection is not None}',flush=True)

if __name__=='__main__':main()
