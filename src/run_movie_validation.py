"""Frozen MovieLens observed-rating inference; never calculates accuracy."""
import argparse
import json
import time
from pathlib import Path
from confirmation_common import ROOT, MODELS, shuffled_history, save
from coat_memory_reader import SYSTEM, digest, parse_predictions
from movie_validation_data import load

CONDITIONS=['no_history','full_history','shuffled_history']
DEPENDENCIES=['docs/movie-validation-protocol.md','src/run_movie_validation.py',
 'src/analyze_movie_validation.py','src/movie_validation_data.py','src/confirmation_common.py',
 'src/analyze_confirmation.py','src/coat_memory_reader.py','src/coat_baselines.py',
 'references/movie-data-manifest.json','results/movie-user-split.json',
 'results/movie-baseline-selection.json','references/local-model-manifest.json','references/phi-model-manifest.json']


def records(ratings, features, names, include_rating=True):
    out=[]
    for i in (ratings>0).nonzero()[0]:
        r={'item':f'movie-{i:04d}','attributes':[n for n,v in zip(names,features[i]) if v]}
        if include_rating:r['rating']=int(ratings[i])
        out.append(r)
    return out


def messages(history, queries, features, names):
    evidence='No personal history is available.' if history is None else 'Structured observed movie ratings:\n'+json.dumps(records(history,features,names))
    return [{'role':'system','content':SYSTEM.replace('target coat','target movie')},
     {'role':'user','content':'Personal evidence:\n'+evidence+'\n\nTarget movies in output order:\n'+json.dumps(queries)+
      '\n\nReturn '+str(len(queries))+' ratings as one JSON array.'}]


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',choices=MODELS,required=True);p.add_argument('--preflight',action='store_true');a=p.parse_args()
    from openai import OpenAI
    for f in json.loads((ROOT/f'references/{"local" if a.model=="qwen" else "phi"}-model-manifest.json').read_text())['files']:
        assert digest(ROOT/'models'/MODELS[a.model]/f['name'])==f['sha256']
    train,test,features,names,split,_=load()
    assert split==json.loads((ROOT/'results/movie-user-split.json').read_text())['users']
    users=split['fitting'][:3] if a.preflight else split['evaluation']
    suffix='preflight' if a.preflight else 'evaluation'
    out=ROOT/f'results/movie-validation-{suffix}-{a.model}.json'
    manifest={'scope':suffix,'model':a.model,'users':users,'concurrency':1,'max_tokens':256,
      'hashes':{n:digest(ROOT/n) for n in DEPENDENCIES}}
    if not a.preflight:
        lock=json.loads((ROOT/'results/movie-validation-lock.json').read_text());assert manifest['hashes']==lock['hashes']
        pre=json.loads((ROOT/f'results/movie-validation-preflight-{a.model}.json').read_text())
        assert pre['complete'] and pre['valid']>=8 and len(pre['readers'])==9
    directory=ROOT/f'data/movie-validation-v1/{suffix}/{a.model}';directory.mkdir(parents=True,exist_ok=True)
    mp=directory/'manifest.json'
    if mp.exists():assert json.loads(mp.read_text())==manifest
    else:save(mp,manifest)
    client=OpenAI(api_key='local-placeholder',base_url='http://127.0.0.1:8317/v1',max_retries=0,timeout=300)
    rows=[]
    try:
        for index,user in enumerate(users):
            histories={'no_history':None,'full_history':train[user],'shuffled_history':shuffled_history(train[user],user)}
            queries=records(test[user],features,names,False)
            order=CONDITIONS[index%3:]+CONDITIONS[:index%3]
            for c in order:
                prompt=messages(histories[c],queries,features,names);path=directory/f'{user}-{c}.json'
                if path.exists():
                    raw=json.loads(path.read_text());assert raw['messages']==prompt
                else:
                    raw={'user_row':user,'model':a.model,'context':c,'messages':prompt};start=time.perf_counter()
                    try:
                        response=client.chat.completions.create(model=str(ROOT/'models'/MODELS[a.model]),messages=prompt,
                          temperature=0,top_p=1,max_tokens=256)
                        raw['response']=response.model_dump(mode='json');raw['status']='completed'
                    except Exception as e:
                        raw['status']='error';raw['error']=f'{type(e).__name__}: {e}'
                    raw['seconds']=time.perf_counter()-start;save(path,raw)
                response=raw.get('response');finish=response['choices'][0]['finish_reason'] if response else None
                pred=parse_predictions(response['choices'][0]['message']['content'],len(queries)) if response and finish=='stop' else None
                rows.append({'user_row':user,'context':c,'status':raw['status'],'valid':pred is not None,'targets':len(queries),
                    'finish_reason':finish,'seconds':raw['seconds'],'usage':response.get('usage') if response else None,'raw_sha256':digest(path)})
            report={**manifest,'readers':rows,'valid':sum(r['valid'] for r in rows),'complete':False};save(out,report)
            print(f'{index+1}/{len(users)} {a.model} MovieLens: user {user}, calls {len(rows)}, valid {report["valid"]}',flush=True)
    finally:client.close()
    report['complete']=True;save(out,report)
    if a.preflight and report['valid']<8:raise RuntimeError('Output-contract preflight failed; stop before evaluation')


if __name__=='__main__':main()
