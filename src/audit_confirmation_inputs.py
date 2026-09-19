"""Descriptive checks of evaluation inputs, without prediction scoring.

This auxiliary audit was added after the public protocol freeze, while accuracy
remained uninspected. It changes no inference or primary analysis decision.
"""
import json
from pathlib import Path
import numpy as np
from confirmation_common import ROOT,shuffled_history,save
from coat_memory_reader import load_data,digest
from movie_validation_data import load


def summary(train,users):
    records=[]
    for user in users:
        h=train[user];p=shuffled_history(h,user);mask=h>0
        assert np.array_equal(h>0,p>0)
        assert np.array_equal(np.sort(h[mask]),np.sort(p[mask]))
        assert h[mask].mean()==p[mask].mean()
        assert np.median(h[mask])==np.median(p[mask])
        records.append({'user_row':user,'history_items':int(mask.sum()),
            'distinct_rating_values':int(len(np.unique(h[mask]))),'changed_assignments':int(np.count_nonzero(h!=p))})
    changed=[r['changed_assignments'] for r in records]
    return {'users':len(users),'constant_histories':sum(r['distinct_rating_values']==1 for r in records),
      'unchanged_permutations':sum(v==0 for v in changed),'mean_changed_assignments':float(np.mean(changed)),
      'minimum_changed_assignments':min(changed),'maximum_changed_assignments':max(changed),'records':records}


def main():
    ctrain,ctest,_,_=load_data();cusers=json.loads((ROOT/'results/coat-user-split.json').read_text())['users']['reserved_evaluation']
    mtrain,mtest,_,_,msplit,_=load();musers=msplit['evaluation']
    report={'scope':'post-freeze auxiliary input audit, no model predictions or accuracy inspected',
        'coat':summary(ctrain,cusers),'movielens':summary(mtrain,musers),'source_sha256':digest(Path(__file__))}
    assert all(r['history_items']==24 for d in ['coat','movielens'] for r in report[d]['records'])
    assert not np.any((mtrain>0)&(mtest>0))
    report['coat']['new_targets']=int(((ctest[cusers]>0)&(ctrain[cusers]==0)).sum())
    report['movielens']['new_targets']=int((mtest[musers]>0).sum())
    save(ROOT/'results/confirmation-input-audit.json',report)
    print(json.dumps({d:{k:v for k,v in report[d].items() if k!='records'} for d in ['coat','movielens']},indent=2))


if __name__=='__main__':main()
