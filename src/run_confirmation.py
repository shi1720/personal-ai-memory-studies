"""Independent user evaluation: native Qwen writer, two separately served readers.

Does not calculate accuracy. Only fitting users are permitted in preflight mode.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import time
from confirmation_common import *
from coat_memory_reader import load_data, digest
from mem0_native_preflight import verify_files
from run_coat_memory_development import run_writer, history_message

DEPENDENCIES = ['docs/confirmation-protocol.md','src/confirmation_common.py',
    'src/run_confirmation.py','src/analyze_confirmation.py','src/coat_memory_reader.py',
    'src/run_coat_memory_development.py','src/coat_baselines.py',
    'results/coat-user-split.json','results/confirmation-baseline-selection.json',
    'results/mem0-native-complete-preflight.json','references/mem0-native-complete-environment.txt',
    'references/local-model-manifest.json','references/phi-model-manifest.json']


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',choices=MODELS,required=True)
    p.add_argument('--preflight',action='store_true');a=p.parse_args()
    for k in ['OPENAI_API_KEY','OPENROUTER_API_KEY','OPENAI_BASE_URL']:os.environ.pop(k,None)
    os.environ.update(MEM0_TELEMETRY='false',HF_HUB_OFFLINE='1',
        MEM0_DIR=str(ROOT/'data/confirmation-runtime'),FASTEMBED_CACHE_PATH=str(ROOT/'models/fastembed-cache'))
    from openai import OpenAI
    if a.model=='qwen':
        from mem0.utils.spacy_models import get_nlp_full,get_nlp_lemma
        assert get_nlp_full() is not None and get_nlp_lemma() is not None
        verify_files()
    else:
        for f in json.loads((ROOT/'references/phi-model-manifest.json').read_text())['files']:
            assert digest(ROOT/'models'/MODELS['phi']/f['name'])==f['sha256']
    train,test,features,names=load_data()
    split=json.loads((ROOT/'results/coat-user-split.json').read_text())['users']
    users=split['fitting'][:3] if a.preflight else split['reserved_evaluation']
    suffix='preflight' if a.preflight else 'evaluation'
    run=ROOT/f'data/confirmation-v1/{suffix}';out=ROOT/f'results/confirmation-{suffix}-{a.model}.json'
    manifest={'scope':suffix,'model':a.model,'users':users,'concurrency':1,
              'hashes':{n:digest(ROOT/n) for n in DEPENDENCIES}}
    if not a.preflight:
        lock=json.loads((ROOT/'results/confirmation-lock.json').read_text())
        assert manifest['hashes']==lock['hashes'],'Independent protocol changed after freeze'
        for model in MODELS:
            pre=json.loads((ROOT/f'results/confirmation-{model}-preflight.json').read_text())
            assert pre['valid']>=11 and pre['total']==12
        native=json.loads((ROOT/'results/confirmation-preflight-qwen.json').read_text())
        assert native['complete'] and len(native['writers'])==3
        assert all(w['status']=='completed' for w in native['writers'])
    path=run/f'manifest-{a.model}.json'
    if path.exists():assert json.loads(path.read_text())==manifest,'Cannot silently resume changed protocol'
    else:save(path,manifest)
    def worker(position,user):
        rawdir=run/f'user-{user}';rawdir.mkdir(parents=True,exist_ok=True)
        history=history_message(records(train[user],features,names))
        if a.model=='qwen':writer=run_writer(user,history,rawdir)
        else:
            writer=json.loads((rawdir/'writer.json').read_text())
            assert writer['input']==history
        texts=[x['memory'] for x in writer.get('stored',{}).get('results',[])]
        w={'user_row':user,'status':writer['status'],'memory_count':len(texts),
           'text_bytes':sum(len(t.encode()) for t in texts),'seconds':writer['seconds'],
           'raw_sha256':digest(rawdir/'writer.json'),
           'generations':[{'usage':t['response']['usage'],'finish_reason':t['response']['choices'][0]['finish_reason']} for t in writer['traces']]}
        target_records=targets(train[user],test[user]>0,features,names)
        contexts=evidence_for(user,train[user],features,names,texts)
        order=CONDITIONS[position%4:]+CONDITIONS[:position%4]
        client=OpenAI(api_key='local-placeholder',base_url='http://127.0.0.1:8317/v1',max_retries=0,timeout=300)
        rows=[]
        try:
            for context in order:
                path=rawdir/f'{a.model}-{context}.json';prompt=messages(contexts[context],target_records)
                if path.exists():
                    raw=json.loads(path.read_text());assert raw['messages']==prompt
                else:
                    raw={'user_row':user,'model':a.model,'context':context,'messages':prompt};start=time.perf_counter()
                    try:
                        response=client.chat.completions.create(model=str(ROOT/'models'/MODELS[a.model]),
                            messages=prompt,temperature=0,top_p=1,max_tokens=256)
                        raw['response']=response.model_dump(mode='json');raw['status']='completed'
                    except Exception as e:
                        raw['status']='error';raw['error']=f'{type(e).__name__}: {e}'
                    raw['seconds']=time.perf_counter()-start;save(path,raw)
                response=raw.get('response');finish=response['choices'][0]['finish_reason'] if response else None
                pred=parse_predictions(response['choices'][0]['message']['content'],len(target_records)) if response and finish=='stop' else None
                rows.append({'user_row':user,'context':context,'status':raw['status'],'valid':pred is not None,
                    'targets':len(target_records),'finish_reason':finish,'seconds':raw['seconds'],
                    'usage':response.get('usage') if response else None,'raw_sha256':digest(path)})
        finally:client.close()
        return w,rows
    results={}
    with ThreadPoolExecutor(max_workers=1) as pool:
        futures=[pool.submit(worker,i,u) for i,u in enumerate(users)]
        for f in as_completed(futures):
            w,readers=f.result();results[w['user_row']]=(w,readers)
            ordered=[results[u] for u in users if u in results]
            report={**manifest,'writers':[r[0] for r in ordered],
                    'readers':[row for r in ordered for row in r[1]],'complete':False}
            save(out,report)
            print(f"{len(results)}/{len(users)} {a.model}: user {w['user_row']}; writer {w['status']}; valid readers {sum(r['valid'] for r in readers)}/4",flush=True)
    assert len(report['readers'])==4*len(users)
    report['complete']=True;save(out,report)


if __name__=='__main__':main()
