"""Paired user-level analysis of the frozen, complete development experiment."""
import json
from pathlib import Path
import numpy as np
from coat_memory_reader import ROOT,CONTEXTS,digest,load_data,parse_predictions,targets
from coat_baselines import predictions


def paired_bootstrap(differences,seed=20260919,replicates=10000):
    values=np.asarray(differences,dtype=float)
    if not len(values):return None
    rng=np.random.default_rng(seed)
    samples=values[rng.integers(0,len(values),size=(replicates,len(values)))].mean(axis=1)
    return {'users':len(values),'mean':float(values.mean()),
        'percentile_95':np.quantile(samples,[.025,.975]).tolist(),
        'memory_better':int((values<0).sum()),'equal':int((values==0).sum()),'memory_worse':int((values>0).sum()),
        'seed':seed,'replicates':replicates}


def main():
    path=ROOT/'results/coat-memory-development-traces.json'
    run=json.loads(path.read_text())
    if not run.get('complete'):raise RuntimeError('Wait for complete experiment; do not analyze partial scores')
    for p,h in run['hashes'].items():assert digest(ROOT/p)==h,p
    split=json.loads((ROOT/'results/coat-user-split.json').read_text())['users']
    users=split['development']
    assert len(run['writers'])==30 and len(run['readers'])==90
    assert {(r['user_row'],r['context']) for r in run['readers']}=={(u,c) for u in users for c in CONTEXTS}
    assert [r['user_row'] for r in run['writers']]==users
    train,test,features,names=load_data()
    # The saved numerical population model used only fitting users.
    base=json.loads((ROOT/'results/coat-development-baselines.json').read_text())
    population={k:np.array(v) if isinstance(v,list) else v for k,v in base['population_model'].items()}
    from coat_baselines import load_archive
    _,_,numeric_features,_=load_archive()
    rows=[]
    for r in run['readers']:
        user=r['user_row'];context=r['context']
        rawpath=ROOT/f'data/coat-memory-development-v1/user-{user}/reader-{context}.json'
        assert digest(rawpath)==r['raw_sha256']
        raw=json.loads(rawpath.read_text());response=raw.get('response')
        mask=(test[user]>0)&(train[user]==0)
        y=test[user,mask];assert len(y)==r['targets']
        pred=None
        if response and response['choices'][0]['finish_reason']=='stop':
            pred=parse_predictions(response['choices'][0]['message']['content'],len(y))
        assert (pred is not None)==r['parsed']
        fallback=predictions(train[user],numeric_features,population,'population_features')[mask]
        effective=np.array(pred) if pred is not None else fallback
        row={'user_row':user,'context':context,'targets':len(y),'valid':pred is not None,
             'operational_mae':float(np.abs(effective-y).mean()),'operational_mse':float(((effective-y)**2).mean())}
        row['mae']=row['operational_mae'] if pred is not None else None
        row['mse']=row['operational_mse'] if pred is not None else None
        rows.append(row)
    lookup={(r['user_row'],r['context']):r for r in rows}
    paired=[];excluded=[]
    for user in users:
        m=lookup[(user,'native_memory')];f=lookup[(user,'full_history')]
        if m['valid'] and f['valid']:paired.append({'user_row':user,'delta_mae':m['mae']-f['mae']})
        else:excluded.append(user)
    summary={}
    for context in CONTEXTS:
        all_rows=[r for r in rows if r['context']==context]
        valid=[r for r in all_rows if r['valid']]
        summary[context]={'valid_users':len(valid),'valid_targets':sum(r['targets'] for r in valid),
            'scheduled_users':len(all_rows),'scheduled_targets':sum(r['targets'] for r in all_rows),
            'macro_mae':float(np.mean([r['mae'] for r in valid])) if valid else None,
            'macro_rmse':float(np.sqrt(np.mean([r['mse'] for r in valid]))) if valid else None,
            'operational_macro_mae':float(np.mean([r['operational_mae'] for r in all_rows])),
            'operational_macro_rmse':float(np.sqrt(np.mean([r['operational_mse'] for r in all_rows])))}
    for writer in run['writers']:
        assert digest(ROOT/f"data/coat-memory-development-v1/user-{writer['user_row']}/writer.json")==writer['raw_sha256']
    def usage_sum(generations):
        return {key:sum((g.get('usage') or {}).get(key,0) for g in generations) for key in ['prompt_tokens','completion_tokens','total_tokens']}
    resources={'writers':{'calls_with_response':sum(len(w['generations']) for w in run['writers']),
        'attempted_users':len(run['writers']),'errors':sum(w['status']!='completed' for w in run['writers']),
        'length_stops':sum(g['finish_reason']=='length' for w in run['writers'] for g in w['generations']),
        'seconds':sum(w['seconds'] for w in run['writers']),
        'tokens':usage_sum([g for w in run['writers'] for g in w['generations']]),
        'memory_count_total':sum(w['memory_count'] for w in run['writers']),
        'stored_text_bytes':sum(w['utf8_text_bytes'] for w in run['writers'])},'readers':{}}
    for context in CONTEXTS:
        calls=[r for r in run['readers'] if r['context']==context]
        resources['readers'][context]={'calls':len(calls),'seconds':sum(r['seconds'] for r in calls),'tokens':usage_sum(calls),
            'invalid':sum(not r['parsed'] for r in calls),'length_stops':sum(r['finish_reason']=='length' for r in calls)}
    numerical=[]
    for variant in ['population_mean','population_features','user_mean','uniform']:
        penalty=base['selected_penalties'][variant]['penalty'] if variant in base['selected_penalties'] else None
        b=next(b for b in base['results'] if b['variant']==variant and b['penalty']==penalty)
        numerical.append({'variant':variant,'penalty':penalty,**b['summaries']['new']})
    report={'scope':'exploratory development; no held-out score; no new method claim',
        'hashes':{'results/coat-memory-development-traces.json':digest(path),'src/analyze_coat_memory_development.py':digest(Path(__file__))},
        'summaries':summary,'primary_paired':paired_bootstrap([p['delta_mae'] for p in paired]),
        'excluded_paired_users':excluded,'paired_users':paired,'users':rows,
        'numerical_references':numerical,'resources':resources}
    (ROOT/'results/coat-memory-development-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'summaries':summary,'primary':report['primary_paired'],'resources':resources},indent=2))

if __name__=='__main__':main()
