"""Output-contract and batching check on fitting users only; no accuracy scoring."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
from confirmation_common import *
from coat_memory_reader import load_data, digest


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model', choices=MODELS, required=True)
    args=parser.parse_args()
    from openai import OpenAI
    train, test, features, names = load_data()
    users=json.loads((ROOT/'results/coat-user-split.json').read_text())['users']['fitting'][:3]
    out=ROOT/f'data/confirmation-preflight-v1/{args.model}'
    model=ROOT/'models'/MODELS[args.model]
    work=[]
    for user in users:
        raw=json.loads((ROOT/f'data/coat-native-resource-preflight-v1/user-{user}.json').read_text())
        texts=[x['memory'] for x in raw['stored']['results']]
        contexts=evidence_for(user,train[user],features,names,texts)
        queries=targets(train[user],test[user]>0,features,names)
        for name,evidence in contexts.items():work.append((user,name,messages(evidence,queries),len(queries)))
    def run(job):
        user,context,prompt,n=job;path=out/f'{user}-{context}.json'
        if path.exists():
            raw=json.loads(path.read_text());assert raw['messages']==prompt
        else:
            client=OpenAI(api_key='local-placeholder',base_url='http://127.0.0.1:8317/v1',max_retries=0,timeout=300)
            start=time.perf_counter()
            response=client.chat.completions.create(model=str(model),messages=prompt,temperature=0,top_p=1,max_tokens=256)
            raw={'messages':prompt,'response':response.model_dump(mode='json'),'seconds':time.perf_counter()-start}
            save(path,raw);client.close()
        choice=raw['response']['choices'][0]
        return {'user_row':user,'context':context,'targets':n,'valid':choice['finish_reason']=='stop' and parse_predictions(choice['message']['content'],n) is not None,
                'finish_reason':choice['finish_reason'],'usage':raw['response']['usage'],'raw_sha256':digest(path)}
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(run,j) for j in work]):results.append(f.result())
    results.sort(key=lambda r:(r['user_row'],r['context']))
    report={'scope':'fitting-user format preflight only; no accuracy calculated','model':args.model,'concurrency':4,'max_tokens':256,'results':results,
        'valid':sum(r['valid'] for r in results),'total':len(results),'source_sha256':digest(Path(__file__))}
    save(ROOT/f'results/confirmation-{args.model}-preflight.json',report)
    print(json.dumps({'model':args.model,'valid':report['valid'],'total':len(results)}),flush=True)
    if report['valid']<11:raise RuntimeError('Output contract failed preflight; do not start independent evaluation')


if __name__=='__main__':main()
