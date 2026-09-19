"""Native Mem0 write path on three fitting histories; no target ratings read."""
import hashlib
import io
import json
import os
from pathlib import Path
import time
import zipfile
import numpy as np
from mem0_native_preflight import ROOT, MODEL, verify_files, digest

RUN = ROOT/'data/coat-native-resource-preflight-v1'
OUT = ROOT/'results/coat-native-resource-preflight.json'

def histories():
    archive=ROOT/'data/coat/coat.zip'
    assert digest(archive)=='6073d0b515ed1f6e830e4fead66dc76ad7991a7553eaa58e228b234a9d19daed'
    split=json.loads((ROOT/'results/coat-user-split.json').read_text())
    with zipfile.ZipFile(archive) as z:
        train=np.loadtxt(io.BytesIO(z.read('coat/train.ascii')))
        features=np.loadtxt(io.BytesIO(z.read('coat/user_item_features/item_features.ascii')))
        names=z.read('coat/user_item_features/item_features_map.txt').decode().splitlines()
    for user in split['users']['fitting'][:3]:
        records=[]
        for item in np.flatnonzero(train[user]):
            attributes=[name for name, value in zip(names,features[item]) if value and not name.startswith('onfrontpage:')]
            records.append({'item':f'coat-{item:03d}','attributes':attributes,'rating':int(train[user,item])})
        assert len(records)==24
        message='These are this user\'s structured coat ratings from a study, on a scale of 1 to 5. They are ordered by item ID, not time. No demographic information is supplied.\n'+json.dumps(records)
        yield user,message


def main():
    if RUN.exists() or OUT.exists():
        raise RuntimeError('Refusing to overwrite resource preflight')
    RUN.mkdir(parents=True)
    for key in ['OPENROUTER_API_KEY','OPENAI_API_KEY','OPENAI_BASE_URL']:
        os.environ.pop(key,None)
    os.environ.update(MEM0_TELEMETRY='false',MEM0_DIR=str(RUN/'mem0'),HF_HUB_OFFLINE='1',
                      FASTEMBED_CACHE_PATH=str(ROOT/'models/fastembed-cache'))
    from mem0 import Memory
    from mem0.utils.spacy_models import get_nlp_full,get_nlp_lemma
    assert get_nlp_full() is not None and get_nlp_lemma() is not None
    verify_files()
    config=json.loads((ROOT/'results/mem0-native-complete-preflight.json').read_text())['config']
    config['vector_store']['config']['path']=str(RUN/'qdrant')
    config['vector_store']['config']['collection_name']='coat_resources'
    config['history_db_path']=str(RUN/'history.db')
    config['llm']['config']['api_key']='local-placeholder'
    traces=[]
    def callback(llm,response,params):
        traces.append({'params':params,'response':response.model_dump(mode='json')})
    config['llm']['config']['response_callback']=callback
    memory=Memory.from_config(config)
    assert memory.vector_store._get_bm25_encoder() is not None
    report={'scope':'three fitting users; resource preflight only; no target ratings loaded',
            'protocol_sha256':digest(ROOT/'docs/coat-native-resource-preflight.md'),
            'code_sha256':digest(Path(__file__)),'users':[]}
    try:
        for user,message in histories():
            traces.clear();start=time.perf_counter()
            raw={'user_row':user,'input':message}
            try:
                raw['add']=memory.add([{'role':'user','content':message}],user_id=f'coat-{user}')
                raw['stored']=memory.get_all(filters={'user_id':f'coat-{user}'})
                status='completed'
            except Exception as e:
                status='error';raw['error']=f'{type(e).__name__}: {e}'
            raw['llm_traces']=list(traces)
            seconds=time.perf_counter()-start
            path=RUN/f'user-{user}.json';path.write_text(json.dumps(raw,indent=2)+'\n')
            texts=[m['memory'] for m in raw.get('stored',{}).get('results',[])]
            row={'user_row':user,'status':status,'seconds':seconds,'stored_memories':len(texts),
                 'stored_utf8_bytes':sum(len(t.encode()) for t in texts),'raw_trace_sha256':digest(path),
                 'generations':[{'finish_reason':t['response']['choices'][0]['finish_reason'],
                    'usage':t['response']['usage']} for t in traces]}
            report['users'].append(row);OUT.write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(row),flush=True)
    finally:
        memory.close();memory.vector_store.client.close()

if __name__=='__main__':
    main()
