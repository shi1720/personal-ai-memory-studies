"""Post-result diagnostic controls, never independent confirmation."""
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
from run_retention_pilot import sha
ROOT=Path(__file__).resolve().parents[1]

def make_messages(journal,writer,wording):
    ms=messages(journal,'important',False)
    if writer=='archive':
        ms[0]['content']=ms[0]['content'].replace('You manage episodic memory for a personal assistant.','You manage an archive of recorded events.')
    if writer=='proportional':
        ms[0]['content']='You manage episodic memory for a personal assistant. Select exactly six events. Preserve the relative frequency of positive and negative outcomes within each activity as closely as the six-event budget permits. Negative experiences are important evidence too. Consider the entire journal before choosing the subset. Return only a JSON array of exactly six distinct event IDs. Do not include explanations or any IDs not in the journal.'
    if wording=='antonym':
        ms[1]['content']=ms[1]['content'].replace('I did not enjoy the session.','I disliked the session.').replace('I enjoyed the session.','I liked the session.')
    return ms

def main():
    journals=json.loads((ROOT/'results/pilot-003-journals.json').read_text())
    deps=['src/run_retention_controls.py','src/retention_pilot_data.py','src/run_retention_pilot.py',
          'docs/pilot-003-controls.md','results/pilot-003-journals.json','references/local-model-manifest.json']
    manifest={'status':'post-result diagnostic; not independent confirmation','hashes':{p:sha(ROOT/p) for p in deps},
              'expected_calls':72,'temperature':0,'seed':0,'max_output_tokens':160,
              'versions':{p:importlib.metadata.version(p) for p in ['mlx','mlx-lm','transformers']}}
    mp=ROOT/'results/pilot-003-controls-manifest.json'
    if mp.exists() and json.loads(mp.read_text())!=manifest:raise ValueError('Changed run identity')
    mp.write_text(json.dumps(manifest,indent=2)+'\n')
    output=ROOT/'results/pilot-003-controls-predictions.jsonl';completed=set()
    if output.exists():
        for line in output.read_text().splitlines():
            r=json.loads(line);key=(r['journal'],r['writer'],r['wording'])
            if key in completed:raise ValueError('Duplicate case')
            completed.add(key)
    directory=ROOT/'models/qwen3-4b-instruct-2507-4bit'
    for r in json.loads((ROOT/'references/local-model-manifest.json').read_text())['files']:
        if sha(directory/r['name'])!=r['sha256']:raise ValueError('Changed model')
    model,tok=load(str(directory),tokenizer_config={'trust_remote_code':False})
    for j in journals:
        for writer in ['important','archive','proportional']:
            for wording in ['negation','antonym']:
                key=(j['id'],writer,wording)
                if key in completed:continue
                prompt=tok.apply_chat_template(make_messages(j,writer,wording),tokenize=False,add_generation_prompt=True)
                tokens=tok.encode(prompt,add_special_tokens=False)
                if len(tokens)>4096:raise ValueError('Input budget exceeded')
                mx.random.seed(0);start=time.perf_counter();parts=[];last=None
                for r in stream_generate(model,tok,tokens,max_tokens=160,sampler=make_sampler(temp=0.0)):
                    parts.append(r.text);last=r
                if last is None:raise RuntimeError('No response')
                text=''.join(parts);selection=parse_selection(text,{e['id'] for e in j['events']})
                row={'journal':j['id'],'writer':writer,'wording':wording,'prompt':prompt,
                     'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'text':text,'selection':selection,
                     'valid':selection is not None,'prompt_tokens':last.prompt_tokens,
                     'generation_tokens':last.generation_tokens,'finish_reason':last.finish_reason,
                     'reader_seconds':time.perf_counter()-start}
                with output.open('a') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
                completed.add(key);mx.clear_cache()
                print(f'Completed {len(completed)}/72 {key} valid={selection is not None}',flush=True)
if __name__=='__main__':main()
