"""Separate numerical cross-check. Imports no project data, parser, or metric code.

Reconstructs primary inputs directly from licensed local archives and frozen
split metadata; compares an augmented least-squares implementation with the
study's normal-equation ridge fit. This is a second implementation, not a
claim of external peer review or independently collected data.
"""
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import zipfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def read(path):return json.loads((ROOT/path).read_text())


def measurements(pred,truth,tolerance=0.):
    assert len(pred)==len(truth)>0
    differences=[float(p)-float(t) for p,t in zip(pred,truth)]
    mean=sum(differences)/len(differences)
    pairs=[]
    for i,j in itertools.combinations(range(len(truth)),2):
        if truth[i]!=truth[j]:
            pairs.append(.5 if abs(pred[i]-pred[j])<=tolerance else float((pred[i]>pred[j])==(truth[i]>truth[j])))
    return {'mae':sum(abs(v) for v in differences)/len(differences),
      'mse':sum(v*v for v in differences)/len(differences),'signed_error':mean,
      'level_mse':mean*mean,'centered_mse':sum((v-mean)**2 for v in differences)/len(differences),
      'targets':len(differences),'pairwise_accuracy':sum(pairs)/len(pairs) if pairs else None}


def parse(raw,count):
    try:
        choice=raw['response']['choices'][0]
        if choice['finish_reason']!='stop':return None
        text=choice['message']['content'].strip()
        if text.startswith('```json\n') and text.endswith('\n```'):text=text[8:-4]
        elif text.startswith('```\n') and text.endswith('\n```'):text=text[4:-4]
        arr=json.loads(text)
        if type(arr)!=list or len(arr)!=count:return None
        if not all(type(v) in [int,float] and math.isfinite(v) and 1<=v<=5 for v in arr):return None
        return arr
    except (KeyError,TypeError,ValueError,IndexError):return None


def load_coat():
    with zipfile.ZipFile(ROOT/'data/coat/coat.zip') as z:
        h=np.loadtxt(io.BytesIO(z.read('coat/train.ascii')))
        t=np.loadtxt(io.BytesIO(z.read('coat/test.ascii')))
        f=np.loadtxt(io.BytesIO(z.read('coat/user_item_features/item_features.ascii')))
        names=z.read('coat/user_item_features/item_features_map.txt').decode().splitlines()
    x=np.column_stack((np.ones(f.shape[0]),f[:,[i for i,n in enumerate(names) if not n.startswith('onfrontpage:')]]))
    return h,t,x,read('results/coat-user-split.json')['users']['reserved_evaluation'],['intercept']+[n for n in names if not n.startswith('onfrontpage:')]


def load_movie():
    with zipfile.ZipFile(ROOT/'data/movielens/ml-100k.zip') as z:
        rows=np.loadtxt(io.BytesIO(z.read('ml-100k/u.data')),dtype=int)
        item_lines=z.read('ml-100k/u.item').decode('latin-1').splitlines()
        genres=z.read('ml-100k/u.genre').decode().splitlines()
    x=np.ones((1683,20));x[:,1:]=0
    for line in item_lines:
        a=line.split('|');x[int(a[0]),1:]=list(map(int,a[-19:]))
    users=read('results/movie-user-split.json')['users']['evaluation'];h=np.zeros((944,1683));t=np.zeros_like(h)
    for u in users:
        events=sorted(rows[rows[:,0]==u],key=lambda a:hashlib.sha256(('movie-memory-validation-v1:pair:%d:%d'%(u,a[1])).encode()).hexdigest())
        for a in events[:24]:h[u,a[1]]=a[2]
        for a in events[24:40]:t[u,a[1]]=a[2]
    names=['intercept']+[None]*19
    for line in genres:
        if line:
            name,index=line.split('|');names[int(index)+1]='genre:'+name
    return h,t,x,users,names


def numerical(history,x,variant,penalty,user,solver="augmented"):
    ids=np.flatnonzero(history);y=history[ids].copy()
    if variant=='history_mean':return np.repeat(sum(y)/len(y),len(history))
    if variant=='history_median':return np.repeat(np.median(y),len(history))
    if variant=='constant_3':return np.repeat(3.,len(history))
    if variant=='shuffled_history_ridge':
        seed=int.from_bytes(hashlib.sha256(f'coat-association-control-v1:{user}'.encode()).digest()[:8],'little')
        y=np.random.default_rng(seed).permutation(y)
    if solver=='normal':
        coef=np.linalg.solve(x[ids].T@x[ids]+np.eye(x.shape[1])*penalty,x[ids].T@(y-3.))
        return np.clip(3.+x@coef,1,5)
    xx=np.vstack((x[ids],np.eye(x.shape[1])*math.sqrt(penalty)))
    yy=np.concatenate((y-3,np.zeros(x.shape[1])))
    coef=np.linalg.lstsq(xx,yy,rcond=None)[0]
    return np.clip(3+x@coef,1,5)


def validate_prompt(domain,user,context,raw,history,target,x,names):
    def rows(ids,ratings=None):
        out=[]
        for item in ids:
            label=f'coat-{item:03d}' if domain=='coat' else f'movie-{item:04d}'
            r={'item':label,'attributes':[name for name,active in zip(names[1:],x[item,1:]) if active]}
            if ratings is not None:r['rating']=int(ratings[item])
            out.append(r)
        return out
    message=raw['messages'][1]['content']
    split=message.split('\n\nTarget '+('coats' if domain=='coat' else 'movies')+' in output order:\n')
    assert len(split)==2,(domain,user,context,'target boundary')
    evidence=split[0].removeprefix('Personal evidence:\n')
    queries=json.loads(split[1].split('\n\nReturn ')[0])
    ids=np.flatnonzero((target>0)&(history==0));assert queries==rows(ids),(domain,user,context,'target metadata')
    if context=='no_history':assert evidence=='No personal history is available.'
    elif context=='native_memory':
        writer=read(f'data/confirmation-v1/evaluation/user-{user}/writer.json')
        assert json.loads(writer['input'].split('\n',1)[1])==rows(np.flatnonzero(history),history),'writer history mismatch'
        texts=sorted(r['memory'] for r in writer.get('stored',{}).get('results',[]))
        expected='\n'.join(texts) if texts else 'No stored personal memories are available.'
        assert evidence==expected,'native evidence differs from complete recorded store'
    else:
        ratings=history.copy()
        if context=='shuffled_history':
            ids=np.flatnonzero(history)
            seed=int.from_bytes(hashlib.sha256(f'coat-association-control-v1:{user}'.encode()).digest()[:8],'little')
            ratings[ids]=np.random.default_rng(seed).permutation(ratings[ids])
        assert json.loads(evidence.split('\n',1)[1])==rows(np.flatnonzero(history),ratings),(domain,user,context,'history differs')


def check_domain(domain):
    report=read('results/'+('confirmation-analysis.json' if domain=='coat' else 'movie-validation-analysis.json'))
    history,test,x,users,names=load_coat() if domain=='coat' else load_movie()
    penalty=read('results/'+('confirmation' if domain=='coat' else 'movie')+'-baseline-selection.json')['selected_history_ridge_penalty']
    lookup={(r['user_row'],r['system']):r for r in report['users']}
    checked=0;largest=0.;audited={};tie_records=[]
    numeric=['history_mean','history_median','history_ridge','shuffled_history_ridge']+(['constant_3'] if domain=='movie' else [])
    for user in users:
        mask=(test[user]>0)&(history[user]==0);truth=test[user,mask].tolist()
        systems={k:(numerical(history[user],x,k,penalty,user)[mask].tolist(),True) for k in numeric}
        for model in ['qwen','phi']:
            for context in ['no_history','full_history','shuffled_history']+(['native_memory'] if domain=='coat' else []):
                path=f'data/confirmation-v1/evaluation/user-{user}/{model}-{context}.json' if domain=='coat' else f'data/movie-validation-v1/evaluation/{model}/{user}-{context}.json'
                raw=read(path)
                validate_prompt(domain,user,context,raw,history[user],test[user],x,names)
                if raw.get('response'):
                    expected='qwen3-4b-instruct-2507-4bit' if model=='qwen' else 'phi-4-4bit'
                    assert raw['response']['model'].endswith(expected),(domain,user,model,'served model')
                parsed=parse(raw,len(truth));systems[model+'_'+context]=(parsed if parsed is not None else [3.]*len(truth),parsed is not None)
        for system,(pred,valid) in systems.items():
            original=lookup[(user,system)];assert original['valid']==valid,(domain,user,system,'valid')
            calculated=measurements(pred,truth)
            if system in ['history_ridge','shuffled_history_ridge']:
                canonical=numerical(history[user],x,system,penalty,user,solver='normal')[mask].tolist()
                delta=max(abs(a-b) for a,b in zip(pred,canonical));assert delta<1e-10
                exact=measurements(canonical,truth)['pairwise_accuracy']
                robust=measurements(pred,truth,tolerance=1e-10)['pairwise_accuracy']
                robust_canonical=measurements(canonical,truth,tolerance=1e-10)['pairwise_accuracy']
                assert robust==robust_canonical,(domain,user,system,'near-tie robustness')
                tie_records.append({'user_row':user,'system':system,'max_solver_prediction_difference':delta,
                    'augmented_exact_pairwise':calculated['pairwise_accuracy'],'normal_exact_pairwise':exact,
                    'near_tie_pairwise':robust})
                # Only exact floating-point tie decisions require canonical arithmetic.
                # All continuous metrics and primary effects retain the independent fit.
                calculated['pairwise_accuracy']=exact
            audited[(user,system)]={**calculated,'valid':valid}
            for key,value in calculated.items():
                target=original[key]
                if value is None:assert target is None
                else:
                    delta=abs(value-target);largest=max(largest,delta)
                    assert delta<1e-10,(domain,user,system,key,value,target)
            checked+=1
    for key,contrast in report['primary_contrasts'].items():
        a,b=contrast['left'],contrast['right'];d=[audited[(u,a)]['mae']-audited[(u,b)]['mae'] for u in users]
        assert abs(sum(d)/len(d)-contrast['operational']['mean'])<1e-10
        rng=np.random.default_rng(20260920)
        # Draw all user indices as specified, but accumulate via explicit sums.
        indices=rng.integers(0,len(users),size=(10000,len(users)))
        means=np.array([sum(d[int(i)] for i in draw)/len(draw) for draw in indices])
        for name,q in [('interval_95',[.025,.975]),('family_adjusted_interval',[.0025,.9975])]:
            actual=np.quantile(means,q);expected=contrast['operational'][name]
            assert np.max(np.abs(actual-expected))<1e-10,(domain,key,name)
    return {'domain':domain,'user_system_records_checked':checked,'prompt_content_checks':len(users)*(8 if domain=='coat' else 6),'primary_contrasts_checked':len(report['primary_contrasts']),
      'maximum_metric_difference':largest,'tolerance':1e-10,'status':'passed',
      'numerical_tie_sensitivity':tie_records}


def main():
    # Analysis files can exist only after both inference grids complete; also check explicitly.
    for dataset in ['confirmation','movie-validation']:
        for model in ['qwen','phi']:assert read(f'results/{dataset}-evaluation-{model}.json')['complete']
    checks=[check_domain(d) for d in ['coat','movie']]
    report={'scope':'second implementation on the same recorded data, not external peer review',
      'checks':checks,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'analysis_hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['results/confirmation-analysis.json','results/movie-validation-analysis.json']}}
    (ROOT/'results/independent-calculation-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
