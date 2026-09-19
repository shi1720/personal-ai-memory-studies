"""Post-freeze descriptive audits. Never changes the ten primary comparisons.

Added while accuracy was uninspected. Reports failures, input-token matching,
constant-3 reference performance and numerical near-tie sensitivity separately.
"""
from collections import Counter
import json
from pathlib import Path
import numpy as np
from confirmation_common import ROOT,save
from coat_memory_reader import digest
from independent_result_check import load_coat,measurements


def read(path):return json.loads((ROOT/path).read_text())


def main():
    runs={d:{m:read(f'results/{stem}-evaluation-{m}.json') for m in ['qwen','phi']}
        for d,stem in [('coat','confirmation'),('movielens','movie-validation')]}
    assert all(r['complete'] for rr in runs.values() for r in rr.values())
    check=read('results/independent-calculation-check.json');assert all(c['status']=='passed' for c in check['checks'])
    analysis={'coat':read('results/confirmation-analysis.json'),'movielens':read('results/movie-validation-analysis.json')}
    token_matching={};reader_resources={}
    for domain,models in runs.items():
        token_matching[domain]={};reader_resources[domain]={}
        for model,run in models.items():
            lookup={(r['user_row'],r['context']):r for r in run['readers']};deltas=[];missing=0
            for u in run['users']:
                a=lookup[(u,'full_history')].get('usage');b=lookup[(u,'shuffled_history')].get('usage')
                if a and b:deltas.append(a['prompt_tokens']-b['prompt_tokens'])
                else:missing+=1
            token_matching[domain][model]={'compared_users':len(deltas),'missing_usage_users':missing,
                'nonzero_prompt_token_differences':sum(v!=0 for v in deltas),'maximum_absolute_difference':max(map(abs,deltas)) if deltas else None}
            reader_resources[domain][model]={}
            for context in sorted({r['context'] for r in run['readers']}):
                records=[r for r in run['readers'] if r['context']==context]
                totals=Counter();finishes=Counter();transport_errors=0
                for r in records:
                    u=r['user_row'];path=f'data/confirmation-v1/evaluation/user-{u}/{model}-{context}.json' if domain=='coat' else f'data/movie-validation-v1/evaluation/{model}/{u}-{context}.json'
                    raw=read(path)
                    if raw.get('response'):
                        totals.update({k:raw['response']['usage'].get(k,0) for k in ['prompt_tokens','completion_tokens','total_tokens']})
                        finishes[raw['response']['choices'][0]['finish_reason']]+=1
                    else:transport_errors+=1
                expected=analysis[domain]['resources']['readers'][model][context]['tokens'] if domain=='coat' else analysis[domain]['resources'][model][context]['tokens']
                assert dict(totals)==expected,(domain,model,context,'token accounting')
                reader_resources[domain][model][context]={'attempts':len(records),'transport_errors':transport_errors,'finish_reasons':dict(finishes),'tokens':dict(totals)}
    writers=runs['coat']['qwen']['writers'];totals=Counter();finishes=Counter();counts=[];sizes=[];no_response=[];errors=[]
    for w in writers:
        raw=read(f'data/confirmation-v1/evaluation/user-{w["user_row"]}/writer.json')
        if not raw['traces']:no_response.append(w['user_row'])
        if raw['status']!='completed':errors.append(w['user_row'])
        for trace in raw['traces']:
            response=trace['response'];totals.update({k:response['usage'].get(k,0) for k in ['prompt_tokens','completion_tokens','total_tokens']})
            finishes[response['choices'][0]['finish_reason']]+=1
        memories=raw.get('stored',{}).get('results',[]);counts.append(len(memories));sizes.append(sum(len(r['memory'].encode()) for r in memories))
    expected=analysis['coat']['resources']['writer'];assert dict(totals)==expected['tokens']
    assert sum(counts)==expected['memory_entries'] and sum(sizes)==expected['memory_text_bytes']
    h,t,x,users,names=load_coat();midpoints=[]
    for u in users:
        truth=t[u,(t[u]>0)&(h[u]==0)];midpoints.append(measurements([3.]*len(truth),truth.tolist()))
    midpoint={'scope':'post-freeze descriptive scale-midpoint reference, not an additional primary contrast',
      'users':len(users),'targets':sum(r['targets'] for r in midpoints),'mae':float(np.mean([r['mae'] for r in midpoints])),
      'rmse':float(np.sqrt(np.mean([r['mse'] for r in midpoints])))}
    ties={}
    for domain in check['checks']:
        ties[domain['domain']]={}
        for system in ['history_ridge','shuffled_history_ridge']:
            all_rows=[r for r in domain['numerical_tie_sensitivity'] if r['system']==system]
            rows=[r for r in all_rows if r['near_tie_pairwise'] is not None]
            ties[domain['domain']][system]={'eligible_users':len(rows),
              'strict_normal_mean':float(np.mean([r['normal_exact_pairwise'] for r in rows])),
              'strict_augmented_mean':float(np.mean([r['augmented_exact_pairwise'] for r in rows])),
              'near_tie_mean':float(np.mean([r['near_tie_pairwise'] for r in rows])),
              'users_with_strict_solver_disagreement':sum(r['normal_exact_pairwise']!=r['augmented_exact_pairwise'] for r in rows),
              'maximum_prediction_difference':max(r['max_solver_prediction_difference'] for r in all_rows)}
    report={'scope':'post-freeze descriptive audits, added before accuracy inspection; primary analysis unchanged',
      'source_sha256':digest(Path(__file__)),'prompt_token_matching':token_matching,'reader_resource_crosscheck':reader_resources,
      'writer':{'scheduled_writes':len(writers),'recorded_responses':sum(finishes.values()),'finish_reasons':dict(finishes),
        'top_level_error_users':errors,'no_recorded_response_users':no_response,'empty_store_users':sum(v==0 for v in counts),
        'memory_entries':sum(counts),'text_bytes':sum(sizes),'median_text_bytes':float(np.median(sizes)),
        'minimum_memory_entries':min(counts),'maximum_memory_entries':max(counts),'tokens':dict(totals)},
      'coat_midpoint_reference':midpoint,'numerical_tie_sensitivity':ties,
      'pairwise_eligible_users':{d:sum(r['system']=='history_mean' and r['pairwise_accuracy'] is not None for r in report['users']) for d,report in analysis.items()}}
    save(ROOT/'results/confirmation-auxiliary-report.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
