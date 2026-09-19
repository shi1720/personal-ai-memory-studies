"""Specified baseline and timestamp audit, without LLM calls or raw-data export."""
from collections import Counter,defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import mean,median

ROOT=Path(__file__).resolve().parents[1]
DOMAINS=['Beauty_and_Personal_Care','Books','Electronics','Home_and_Kitchen']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def split_last_three(events):
    if len(events)<4:return None
    ordered=sorted(events,key=lambda e:e['timestamp'])
    return ordered[:-3],ordered[-3:]


def score(actual,predicted):
    assert actual and len(actual)==len(predicted)
    errors=[p-y for y,p in zip(actual,predicted)]
    return {'targets':len(actual),'mae':mean(abs(e) for e in errors),'mse':mean(e*e for e in errors)}


def aggregate(rows):
    if not rows:return {'users':0,'targets':0,'macro_mae':None,'macro_rmse':None}
    return {'users':len(rows),'targets':sum(x['targets'] for x in rows),
            'macro_mae':mean(x['mae'] for x in rows),'macro_rmse':math.sqrt(mean(x['mse'] for x in rows))}


def temporal_sources(source,timestamp):
    before=[e for e in source if e['timestamp']<timestamp]
    equal=sum(e['timestamp']==timestamp for e in source)
    after=sum(e['timestamp']>timestamp for e in source)
    assert len(before)+equal+after==len(source)
    return before,equal,after


def main():
    manifest=json.loads((ROOT/'references/memorycd-data-manifest.json').read_text())
    path=ROOT/'data/memorycd'/manifest['revision']/manifest['file']
    assert sha(path)==manifest['sha256']
    seen=set();domain_results={d:defaultdict(list) for d in DOMAINS}
    histograms={d:Counter() for d in DOMAINS};counts=Counter();ties=Counter()
    cross=defaultdict(list);cross_rows=[];empty_targets=0;any_empty_users=0;all_empty_users=0
    repeated_items=Counter();unknown_domains=Counter()
    with gzip.open(path,'rt') as f:
        for row,line in enumerate(f):
            record=json.loads(line);uid=record['user_id']
            assert uid and uid not in seen,'Missing or duplicate user ID';seen.add(uid)
            domains=record['interactions'];assert isinstance(domains,dict)
            for d,events in domains.items():
                if d not in DOMAINS:unknown_domains[d]+=len(events)
                assert isinstance(events,list)
                for e in events:
                    for field in ['rating','timestamp']:
                        v=e[field];assert isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v),(row,d,field)
                    assert 1<=e['rating']<=5 and e['parent_asin'],(row,d,'invalid rating or item')
                counts[d]+=len(events)
            for domain in DOMAINS:
                split=split_last_three(domains.get(domain,[]))
                if split is None:continue
                history,test=split;ys=[e['rating'] for e in test];hr=[e['rating'] for e in history]
                histograms[domain].update(ys)
                ties[domain]+=history[-1]['timestamp']==test[0]['timestamp']
                history_items={e['parent_asin'] for e in history}
                repeated_items[domain]+=sum(e['parent_asin'] in history_items for e in test)
                methods={f'constant_{v}':[v]*len(ys) for v in range(1,6)}
                methods.update(history_mean=[mean(hr)]*len(ys),history_median=[median(hr)]*len(ys))
                for method,pred in methods.items():domain_results[domain][method].append(dict(user_row=row,**score(ys,pred)))
            target=sorted(domains.get('Home_and_Kitchen',[]),key=lambda e:e['timestamp'])[-3:]
            source=[e for d in DOMAINS if d!='Home_and_Kitchen' for e in domains.get(d,[])]
            if len(target)<3 or not source:continue
            y=[e['rating'] for e in target];sr=[e['rating'] for e in source]
            for method,stat in [('source_mean',mean),('source_median',median)]:
                cross['unrestricted_'+method].append(dict(user_row=row,**score(y,[stat(sr)]*len(y))))
            future=[];prior=[];equal=[];prior_predictions={'mean':[],'median':[]};valid_y=[]
            for e in target:
                before,n_equal,after=temporal_sources(source,e['timestamp'])
                prior.append(len(before));equal.append(n_equal);future.append(after)
                if before:valid_y.append(e['rating'])
                else:empty_targets+=1
                for name,stat in [('mean',mean),('median',median)]:
                    prior_predictions[name].append(stat([x['rating'] for x in before]) if before else None)
            missing=sum(v is None for v in prior_predictions['mean'])
            any_empty_users+=missing>0;all_empty_users+=missing==3
            for name,pred in prior_predictions.items():
                if valid_y:cross['strict_prior_'+name+'_covered'].append(dict(user_row=row,**score(valid_y,[v for v in pred if v is not None])))
                cross['strict_prior_'+name+'_fallback3'].append(dict(user_row=row,**score(y,[v if v is not None else 3. for v in pred])))
            cross_rows.append({'user_row':row,'source_events':len(source),'future_counts':future,'equal_counts':equal,'prior_counts':prior})
    audit={'scope':'released cross-domain cohort; exploratory baseline/timestamp audit, not paper-score reproduction',
        'users':len(seen),'counts':dict(counts),'unrecognised_domains':dict(unknown_domains),
        'single_domain':{d:{'target_histogram':dict(histograms[d]),'history_target_boundary_tie_users':ties[d],
            'test_items_already_in_history':repeated_items[d],
            'baselines':{m:aggregate(v) for m,v in domain_results[d].items()}} for d in DOMAINS},
        'cross_domain':{'users':len(cross_rows),'targets':3*len(cross_rows),
            'targets_with_future_sources':sum(n>0 for r in cross_rows for n in r['future_counts']),
            'users_with_any_future_sources':sum(any(n>0 for n in r['future_counts']) for r in cross_rows),
            'mean_per_target_future_fraction':mean(n/r['source_events'] for r in cross_rows for n in r['future_counts']),
            'equal_time_target_source_pairs':sum(sum(r['equal_counts']) for r in cross_rows),
            'targets_with_no_strict_prior_source':empty_targets,'users_with_any_empty_prior':any_empty_users,
            'users_with_all_empty_prior':all_empty_users,
            'baselines':{m:aggregate(v) for m,v in cross.items()},'temporal_counts_by_user':cross_rows},
        'hashes':{p:sha(ROOT/p) for p in ['src/audit_memorycd_baselines.py','docs/memorycd-baseline-audit-protocol.md','references/memorycd-data-manifest.json']}}
    assert audit['users']==323,'Unexpected cohort size'
    (ROOT/'results/memorycd-baseline-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ['hashes','cross_domain']},indent=2))
    print(json.dumps({k:v for k,v in audit['cross_domain'].items() if k!='temporal_counts_by_user'},indent=2))

if __name__=='__main__':main()
