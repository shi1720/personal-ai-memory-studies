"""Pinned, reproducible MovieLens metadata-only observed-rating split."""
import hashlib
import io
import json
import re
from pathlib import Path
import urllib.request
import zipfile
import numpy as np
from confirmation_common import ROOT, save, history_only
from coat_memory_reader import digest

URL='https://files.grouplens.org/datasets/movielens/ml-100k.zip'


def user_order(ids):
    return sorted(ids,key=lambda u:hashlib.sha256(f'movie-memory-validation-v1:user:{u}'.encode()).hexdigest())


def load():
    manifest=json.loads((ROOT/'references/movie-data-manifest.json').read_text())
    archive=ROOT/'data/movielens/ml-100k.zip';assert digest(archive)==manifest['sha256']
    with zipfile.ZipFile(archive) as z:
        raw=np.loadtxt(io.BytesIO(z.read('ml-100k/u.data')),dtype=int)
        item_lines=z.read('ml-100k/u.item').decode('latin-1').splitlines()
        genre_lines=z.read('ml-100k/u.genre').decode().splitlines()
    assert raw.shape==(100000,4)
    assert len({(r[0],r[1]) for r in raw})==len(raw)
    assert np.all((raw[:,2]>=1)&(raw[:,2]<=5))
    features=np.zeros((1683,19),dtype=float)
    for line in item_lines:
        v=line.split('|');features[int(v[0])]=np.array(v[-19:],dtype=float)
    names=[None]*19
    for line in genre_lines:
        if line:
            name,i=line.split('|');names[int(i)]='genre:'+name
    train=np.zeros((944,1683));test=np.zeros_like(train)
    counts=np.bincount(raw[:,0],minlength=944)
    eligible=[int(u) for u in np.flatnonzero(counts>=40)]
    ordered=user_order(eligible);assert len(ordered)>=290
    split={'fitting':ordered[:60],'development':ordered[60:90],'evaluation':ordered[90:290]}
    for u in ordered[:290]:
        events=raw[raw[:,0]==u]
        events=sorted(events,key=lambda r:hashlib.sha256(f'movie-memory-validation-v1:pair:{u}:{r[1]}'.encode()).hexdigest())
        for row in events[:24]:train[u,row[1]]=row[2]
        for row in events[24:40]:test[u,row[1]]=row[2]
    return train,test,features,names,split,len(eligible)


def prepare():
    target=ROOT/'data/movielens/ml-100k.zip';target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():
        with urllib.request.urlopen(URL,timeout=60) as r:target.write_bytes(r.read())
    with urllib.request.urlopen(URL+'.md5',timeout=60) as r:publisher=r.read().decode().strip()
    matches=re.findall(r'(?i)\b[0-9a-f]{32}\b',publisher)
    assert len(matches)==1,publisher
    expected=matches[0].lower();actual=hashlib.md5(target.read_bytes()).hexdigest()
    assert expected==actual,(expected,actual)
    save(ROOT/'references/movie-data-manifest.json',{'source':URL,'sha256':digest(target),
         'publisher_md5':expected,'bytes':target.stat().st_size,
         'license':'GroupLens research-use terms; no redistribution; see official README',
         'citation':'Harper and Konstan (2015), doi:10.1145/2827872'})
    train,test,features,names,split,eligible=load()
    save(ROOT/'results/movie-user-split.json',{'users':split,'eligible_users':eligible,
        'history_per_user':24,'targets_per_user':16,'source_sha256':digest(target),
        'source_code_sha256':digest(Path(__file__)),'protocol_sha256':digest(ROOT/'docs/movie-validation-protocol.md')})
    x=np.column_stack([np.ones(len(features)),features]);results=[]
    for penalty in [.1,1.,10.,100.]:
        losses=[]
        for u in split['development']:
            mask=test[u]>0;pred=history_only(train[u],x,'history_ridge',penalty)
            losses.append(float(np.abs(pred[mask]-test[u,mask]).mean()))
        results.append({'penalty':penalty,'macro_mae':float(np.mean(losses))})
    chosen=min(results,key=lambda r:(r['macro_mae'],-r['penalty']))['penalty']
    save(ROOT/'results/movie-baseline-selection.json',{'scope':'development only; evaluation unscored',
        'selected_history_ridge_penalty':chosen,'results':results,'split_sha256':digest(ROOT/'results/movie-user-split.json')})
    print(json.dumps({'eligible':eligible,'split_sizes':{k:len(v) for k,v in split.items()},'penalty':chosen,'development':results},indent=2))


if __name__=='__main__':prepare()
