"""Frozen complete-run analysis for the second independent domain."""
import json
import numpy as np
from confirmation_common import ROOT, MODELS, history_only, shuffled_history, save
from coat_memory_reader import digest, parse_predictions
from movie_validation_data import load
from run_movie_validation import CONDITIONS
from analyze_confirmation import metrics, bootstrap


def main():
    for m in MODELS:
        assert json.loads((ROOT/f'results/confirmation-evaluation-{m}.json').read_text())['complete'],'Complete both datasets before scoring'
    lock=json.loads((ROOT/'results/movie-validation-lock.json').read_text())
    for path,want in lock['hashes'].items():assert digest(ROOT/path)==want,path
    runs={m:json.loads((ROOT/f'results/movie-validation-evaluation-{m}.json').read_text()) for m in MODELS}
    for m,r in runs.items():assert r['complete'],f'{m}: do not inspect partial scores'
    train,test,features,names,split,_=load();users=split['evaluation'];assert len(users)==200
    x=np.column_stack([np.ones(len(features)),features])
    penalty=json.loads((ROOT/'results/movie-baseline-selection.json').read_text())['selected_history_ridge_penalty']
    rows=[]
    for u in users:
        mask=test[u]>0;truth=test[u,mask]
        for variant in ['history_mean','history_median','history_ridge']:
            pred=history_only(train[u],x,variant,penalty)
            rows.append({'user_row':u,'system':variant,'valid':True,**metrics(pred[mask],truth)})
        pred=history_only(shuffled_history(train[u],u),x,'history_ridge',penalty)
        rows.append({'user_row':u,'system':'shuffled_history_ridge','valid':True,**metrics(pred[mask],truth)})
        rows.append({'user_row':u,'system':'constant_3','valid':True,**metrics(np.full(len(truth),3.),truth)})
    for model,run in runs.items():
        assert run['hashes']==lock['hashes'] and run['users']==users
        assert len(run['readers'])==600
        assert {(r['user_row'],r['context']) for r in run['readers']}=={(u,c) for u in users for c in CONDITIONS}
        for r in run['readers']:
            u=r['user_row'];c=r['context'];path=ROOT/f'data/movie-validation-v1/evaluation/{model}/{u}-{c}.json'
            assert digest(path)==r['raw_sha256'];raw=json.loads(path.read_text());response=raw.get('response');truth=test[u,test[u]>0]
            pred=parse_predictions(response['choices'][0]['message']['content'],len(truth)) if response and response['choices'][0]['finish_reason']=='stop' else None
            assert (pred is not None)==r['valid'] and len(truth)==r['targets']
            rows.append({'user_row':u,'system':model+'_'+c,'valid':pred is not None,
                **metrics(np.array(pred) if pred is not None else np.full(len(truth),3.),truth)})
    summaries={}
    for system in sorted({r['system'] for r in rows}):
        a=[r for r in rows if r['system']==system];valid=[r for r in a if r['valid']]
        s={'users':len(a),'targets':sum(r['targets'] for r in a),'valid_users':len(valid),'valid_targets':sum(r['targets'] for r in valid)}
        for prefix,records in [('operational',a),('valid_only',valid)]:
            s[prefix]={k:float(np.mean([r[k] for r in records])) if records else None for k in ['mae','signed_error','level_mse','centered_mse']}
            s[prefix]['rmse']=float(np.sqrt(np.mean([r['mse'] for r in records]))) if records else None
            pairwise=[r['pairwise_accuracy'] for r in records if r['pairwise_accuracy'] is not None]
            s[prefix]['pairwise_accuracy']=float(np.mean(pairwise)) if pairwise else None
        summaries[system]=s
    lookup={(r['user_row'],r['system']):r for r in rows};contrasts={}
    for model in MODELS:
        pairs={'association':(model+'_shuffled_history',model+'_full_history'),'numerical_reader':(model+'_full_history','history_ridge')}
        for label,(a,b) in pairs.items():
            valid=[u for u in users if lookup[(u,a)]['valid'] and lookup[(u,b)]['valid']]
            contrasts[model+'_'+label]={'left':a,'right':b,'operational':bootstrap([lookup[(u,a)]['mae']-lookup[(u,b)]['mae'] for u in users]),
                'common_valid':bootstrap([lookup[(u,a)]['mae']-lookup[(u,b)]['mae'] for u in valid]),'excluded_common_valid':[u for u in users if u not in valid]}
    resources={m:{c:{'calls':200,'invalid':sum(not r['valid'] for r in run['readers'] if r['context']==c),
        'tokens':{k:sum((r.get('usage') or {}).get(k,0) for r in run['readers'] if r['context']==c) for k in ['prompt_tokens','completion_tokens','total_tokens']}}
        for c in CONDITIONS} for m,run in runs.items()}
    result={'scope':'independent MovieLens metadata-only observed-rating validation','users':rows,'summaries':summaries,
        'primary_contrasts':contrasts,'resources':resources,'hashes':{n:digest(ROOT/n) for n in ['results/movie-validation-lock.json','src/analyze_movie_validation.py',*[f'results/movie-validation-evaluation-{m}.json' for m in MODELS]]}}
    save(ROOT/'results/movie-validation-analysis.json',result)
    print(json.dumps({'summaries':summaries,'contrasts':contrasts,'resources':resources},indent=2))


if __name__=='__main__':main()
