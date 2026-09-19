"""Select a history-only ridge penalty using development users, never test users."""
import json
from pathlib import Path
import numpy as np
from confirmation_common import ROOT, history_only, save
from coat_baselines import load_archive
from coat_memory_reader import digest


def main():
    train,test,x,_=load_archive()
    users=json.loads((ROOT/'results/coat-user-split.json').read_text())['users']['development']
    results=[]
    for penalty in [.1,1.,10.,100.]:
        losses=[]
        for u in users:
            mask=(test[u]>0)&(train[u]==0)
            pred=history_only(train[u],x,'history_ridge',penalty)
            losses.append(float(np.abs(pred[mask]-test[u,mask]).mean()))
        results.append({'penalty':penalty,'macro_mae':float(np.mean(losses))})
    chosen=min(results,key=lambda r:(r['macro_mae'],-r['penalty']))['penalty']
    report={'scope':'development selection only; no reserved-user scores',
            'selected_history_ridge_penalty':chosen,'results':results,
            'users':users,'hashes':{n:digest(ROOT/n) for n in ['src/confirmation_common.py','src/select_confirmation_baselines.py','results/coat-user-split.json']}}
    save(ROOT/'results/confirmation-baseline-selection.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
