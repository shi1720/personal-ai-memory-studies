"""Frozen native-write and fixed-reader comparison on development users only."""
import json
import os
from pathlib import Path
import time
from coat_memory_reader import ROOT,CONTEXTS,digest,load_data,records,targets,messages,parse_predictions
from mem0_native_preflight import MODEL,verify_files

RUN=ROOT/'data/coat-memory-development-v1'
OUT=ROOT/'results/coat-memory-development-traces.json'
DEPENDENCIES=['src/run_coat_memory_development.py','src/coat_memory_reader.py',
    'docs/coat-memory-development-protocol.md','results/coat-user-split.json',
    'results/mem0-native-complete-preflight.json','references/mem0-native-complete-environment.txt']


def save(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)


def history_message(rows):
    return ('These are this user\'s structured coat ratings from a study, on a scale of 1 to 5. '
            'They are ordered by item ID, not time. No demographic information is supplied.\n'+json.dumps(rows))


def run_writer(user,history,rawdir):
    from mem0 import Memory
    path=rawdir/'writer.json'
    if path.exists():return json.loads(path.read_text())
    if (rawdir/'qdrant').exists():raise RuntimeError('Writer interrupted without trace; do not silently repeat')
    traces=[]
    def callback(llm,response,params):traces.append({'params':params,'response':response.model_dump(mode='json')})
    cfg=json.loads((ROOT/'results/mem0-native-complete-preflight.json').read_text())['config']
    cfg['llm']['config'].update(api_key='local-placeholder',response_callback=callback)
    cfg['vector_store']['config'].update(path=str(rawdir/'qdrant'),collection_name='coat_development')
    cfg['history_db_path']=str(rawdir/'history.db')
    memory=Memory.from_config(cfg)
    memory.llm.client=memory.llm.client.with_options(max_retries=0,timeout=180)
    assert memory.vector_store._get_bm25_encoder() is not None
    raw={'user_row':user,'input':history};start=time.perf_counter()
    try:
        raw['add']=memory.add([{'role':'user','content':history}],user_id=f'coat-{user}')
        raw['stored']=memory.get_all(filters={'user_id':f'coat-{user}'},top_k=1000)
        assert len(raw['stored']['results'])==len(raw['add']['results']), 'Incomplete store listing'
        raw['status']='completed'
    except Exception as e:
        raw['status']='error';raw['error']=f'{type(e).__name__}: {e}'
    finally:
        raw['seconds']=time.perf_counter()-start;raw['traces']=traces
        save(path,raw);memory.close();memory.vector_store.client.close()
    return raw


def main():
    for k in ['OPENROUTER_API_KEY','OPENAI_API_KEY','OPENAI_BASE_URL']:os.environ.pop(k,None)
    os.environ.update(MEM0_TELEMETRY='false',MEM0_DIR=str(RUN/'mem0'),HF_HUB_OFFLINE='1',
        FASTEMBED_CACHE_PATH=str(ROOT/'models/fastembed-cache'))
    RUN.mkdir(parents=True,exist_ok=True)
    from mem0.utils.spacy_models import get_nlp_full,get_nlp_lemma
    from openai import OpenAI
    assert get_nlp_full() is not None and get_nlp_lemma() is not None
    verify_files()
    client=OpenAI(api_key='local-placeholder',base_url='http://127.0.0.1:8317/v1',max_retries=0,timeout=180)
    manifest={'scope':'30 development users only; held-out set unscored',
        'hashes':{p:digest(ROOT/p) for p in DEPENDENCIES}}
    if (RUN/'manifest.json').exists():assert json.loads((RUN/'manifest.json').read_text())==manifest
    else:save(RUN/'manifest.json',manifest)
    train,test,features,names=load_data()
    users=json.loads((ROOT/'results/coat-user-split.json').read_text())['users']['development']
    assert len(users)==30
    report=dict(manifest,writers=[],readers=[])
    for position,user in enumerate(users):
        rawdir=RUN/f'user-{user}';rawdir.mkdir(exist_ok=True)
        history=history_message(records(train[user],features,names))
        writer=run_writer(user,history,rawdir)
        assert writer['input']==history
        texts=sorted(x['memory'] for x in writer.get('stored',{}).get('results',[]))
        report['writers'].append({'user_row':user,'status':writer['status'],'seconds':writer['seconds'],
            'memory_count':len(texts),'utf8_text_bytes':sum(len(t.encode()) for t in texts),
            'raw_sha256':digest(rawdir/'writer.json'),
            'generations':[{'finish_reason':t['response']['choices'][0]['finish_reason'],'usage':t['response']['usage']} for t in writer['traces']]})
        save(OUT,report)
        evidence={'no_history':'No personal history is available.','full_history':history,
                  'native_memory':'\n'.join(texts) if texts else 'No stored personal memories are available.'}
        target_records=targets(train[user],test[user]>0,features,names)
        order=CONTEXTS[position%3:]+CONTEXTS[:position%3]
        for context in order:
            path=rawdir/f'reader-{context}.json'
            prompt=messages(evidence[context],target_records)
            if path.exists():
                raw=json.loads(path.read_text());assert raw['messages']==prompt
            else:
                raw={'user_row':user,'context':context,'messages':prompt};start=time.perf_counter()
                try:
                    response=client.chat.completions.create(model=str(MODEL),messages=prompt,
                        temperature=0,top_p=1,max_tokens=256)
                    raw['response']=response.model_dump(mode='json');raw['status']='completed'
                except Exception as e:
                    raw['status']='error';raw['error']=f'{type(e).__name__}: {e}'
                raw['seconds']=time.perf_counter()-start;save(path,raw)
            response=raw.get('response');parsed=None
            finish=response['choices'][0]['finish_reason'] if response else None
            if response and finish=='stop':
                parsed=parse_predictions(response['choices'][0]['message']['content'],len(target_records))
            report['readers'].append({'user_row':user,'context':context,'status':raw['status'],'finish_reason':finish,
                'parsed':parsed is not None,'targets':len(target_records),'seconds':raw['seconds'],
                'usage':response.get('usage') if response else None,'raw_sha256':digest(path)})
            save(OUT,report)
        print(f"{position+1}/30 user {user}: writer {writer['status']}, {len(texts)} memories; three readers recorded",flush=True)
    assert sum(r['targets'] for r in report['readers'] if r['context']=='full_history')==438
    report['complete']=True;save(OUT,report)

if __name__=='__main__':main()
