"""Frozen complete-run analysis for independent user validation."""
import json
from pathlib import Path
import numpy as np
from confirmation_common import ROOT, CONDITIONS, MODELS, history_only, shuffled_history, save
from coat_baselines import load_archive, predictions
from coat_memory_reader import digest, parse_predictions


def metrics(pred, truth):
    pred=np.asarray(pred,dtype=float);truth=np.asarray(truth,dtype=float)
    if pred.shape!=truth.shape or not len(truth):raise ValueError('Prediction/target shape')
    error=pred-truth
    a,b=np.triu_indices(len(truth),1);different=truth[a]!=truth[b]
    delta=(pred[a]-pred[b])*np.sign(truth[a]-truth[b])
    concordance=np.where(delta>0,1.,np.where(delta<0,0.,.5))
    return {'mae':float(np.abs(error).mean()),'mse':float(np.square(error).mean()),
            'signed_error':float(error.mean()),'targets':len(truth),
            'level_mse':float(error.mean()**2),'centered_mse':float(np.mean((error-error.mean())**2)),
            'pairwise_accuracy':float(concordance[different].mean()) if different.any() else None}


def bootstrap(values):
    values=np.asarray(values,dtype=float);rng=np.random.default_rng(20260920)
    if not len(values):return None
    means=values[rng.integers(0,len(values),size=(10000,len(values)))].mean(axis=1)
    alpha=.05/10
    return {'users':len(values),'mean':float(values.mean()),
            'interval_95':np.quantile(means,[.025,.975]).tolist(),
            'family_adjusted_interval':np.quantile(means,[alpha/2,1-alpha/2]).tolist(),
            'positive_users':int((values>0).sum()),'negative_users':int((values<0).sum()),
            'zero_users':int((values==0).sum()),'replicates':10000,'seed':20260920}


def main():
    for model in MODELS:
        other=json.loads((ROOT/f'results/movie-validation-evaluation-{model}.json').read_text())
        assert other['complete'],'Do not score before both datasets are complete'
    lock=json.loads((ROOT/'results/confirmation-lock.json').read_text())
    for path,want in lock['hashes'].items():assert digest(ROOT/path)==want,path
    runs={m:json.loads((ROOT/f'results/confirmation-evaluation-{m}.json').read_text()) for m in MODELS}
    for m,r in runs.items():assert r['complete'],f'{m}: do not inspect partial scores'
    split=json.loads((ROOT/'results/coat-user-split.json').read_text())['users']
    users=split['reserved_evaluation'];assert len(users)==200
    train,test,x,names=load_archive()
    selection=json.loads((ROOT/'results/confirmation-baseline-selection.json').read_text())
    penalty=selection['selected_history_ridge_penalty']
    numeric=json.loads((ROOT/'results/coat-development-baselines.json').read_text())
    population={k:np.array(v) if isinstance(v,list) else v for k,v in numeric['population_model'].items()}
    rows=[]
    for u in users:
        mask=(test[u]>0)&(train[u]==0);truth=test[u,mask]
        for variant in ['history_mean','history_median','history_ridge']:
            pred=history_only(train[u],x,variant,penalty)
            rows.append({'user_row':u,'system':variant,'valid':True,**metrics(pred[mask],truth)})
        pred=history_only(shuffled_history(train[u],u),x,'history_ridge',penalty)
        rows.append({'user_row':u,'system':'shuffled_history_ridge','valid':True,**metrics(pred[mask],truth)})
        for variant in ['population_mean','population_features','user_mean','uniform']:
            strength=numeric['selected_penalties'][variant]['penalty'] if variant in numeric['selected_penalties'] else None
            pred=predictions(train[u],x,population,variant,strength)
            rows.append({'user_row':u,'system':variant,'valid':True,**metrics(pred[mask],truth)})
    for model,run in runs.items():
        assert run['hashes']==lock['hashes']
        assert run['users']==users
        assert len(run['writers'])==200 and len(run['readers'])==800
        assert {(r['user_row'],r['context']) for r in run['readers']}=={(u,c) for u in users for c in CONDITIONS}
        for w in run['writers']:
            assert digest(ROOT/f"data/confirmation-v1/evaluation/user-{w['user_row']}/writer.json")==w['raw_sha256']
        for r in run['readers']:
            u=r['user_row'];c=r['context'];path=ROOT/f'data/confirmation-v1/evaluation/user-{u}/{model}-{c}.json'
            assert digest(path)==r['raw_sha256']
            raw=json.loads(path.read_text());response=raw.get('response');mask=(test[u]>0)&(train[u]==0);truth=test[u,mask]
            pred=parse_predictions(response['choices'][0]['message']['content'],len(truth)) if response and response['choices'][0]['finish_reason']=='stop' else None
            assert (pred is not None)==r['valid'];assert len(truth)==r['targets']
            operational=np.asarray(pred) if pred is not None else np.full(len(truth),3.)
            rows.append({'user_row':u,'system':model+'_'+c,'valid':pred is not None,**metrics(operational,truth)})
    lookup={(r['user_row'],r['system']):r for r in rows}
    summaries={}
    for system in sorted({r['system'] for r in rows}):
        a=[r for r in rows if r['system']==system];v=[r for r in a if r['valid']]
        summary={'users':len(a),'targets':sum(r['targets'] for r in a),'valid_users':len(v),'valid_targets':sum(r['targets'] for r in v)}
        for prefix,records in [('operational',a),('valid_only',v)]:
            summary[prefix]={'mae':float(np.mean([r['mae'] for r in records])) if records else None,
                'rmse':float(np.sqrt(np.mean([r['mse'] for r in records]))) if records else None,
                'signed_error':float(np.mean([r['signed_error'] for r in records])) if records else None,
                'level_mse':float(np.mean([r['level_mse'] for r in records])) if records else None,
                'centered_mse':float(np.mean([r['centered_mse'] for r in records])) if records else None,
                'pairwise_accuracy':float(np.mean([r['pairwise_accuracy'] for r in records if r['pairwise_accuracy'] is not None])) if any(r['pairwise_accuracy'] is not None for r in records) else None}
        summaries[system]=summary
    contrasts={}
    for model in MODELS:
        pairs={'extraction':(model+'_native_memory',model+'_full_history'),
               'association':(model+'_shuffled_history',model+'_full_history'),
               'numerical_reader':(model+'_full_history','history_ridge')}
        for label,(a,b) in pairs.items():
            differences=[lookup[(u,a)]['mae']-lookup[(u,b)]['mae'] for u in users]
            eligible=[u for u in users if lookup[(u,a)]['valid'] and lookup[(u,b)]['valid']]
            contrasts[model+'_'+label]={'left':a,'right':b,'operational':bootstrap(differences),
                 'common_valid':bootstrap([lookup[(u,a)]['mae']-lookup[(u,b)]['mae'] for u in eligible]),
                 'excluded_common_valid':[u for u in users if u not in eligible]}
    def usage(calls):
        return {key:sum((r.get('usage') or {}).get(key,0) for r in calls) for key in ['prompt_tokens','completion_tokens','total_tokens']}
    resources={'writer':{'calls_with_response':sum(len(w['generations']) for w in runs['qwen']['writers']),
        'tokens':usage([g for w in runs['qwen']['writers'] for g in w['generations']]),
        'errors':sum(w['status']!='completed' for w in runs['qwen']['writers']),
        'memory_entries':sum(w['memory_count'] for w in runs['qwen']['writers']),
        'memory_text_bytes':sum(w['text_bytes'] for w in runs['qwen']['writers'])},'readers':{}}
    for m,run in runs.items():
        resources['readers'][m]={c:{'calls':len([r for r in run['readers'] if r['context']==c]),
            'tokens':usage([r for r in run['readers'] if r['context']==c]),
            'invalid':sum(not r['valid'] for r in run['readers'] if r['context']==c)} for c in CONDITIONS}
    result={'scope':'fixed independent-user evaluation; one Coat domain, two quantized readers, one native writer',
        'users':rows,'summaries':summaries,'primary_contrasts':contrasts,'resources':resources,
        'hashes':{n:digest(ROOT/n) for n in ['results/confirmation-lock.json','results/confirmation-evaluation-qwen.json','results/confirmation-evaluation-phi.json','src/analyze_confirmation.py']}}
    save(ROOT/'results/confirmation-analysis.json',result)
    print(json.dumps({'summaries':summaries,'contrasts':contrasts,'resources':resources},indent=2))


if __name__=='__main__':main()
