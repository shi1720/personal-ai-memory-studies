"""Analyze the complete development-only retention audit, including failures."""
import hashlib
import json
from pathlib import Path
import random
import statistics
from retention_pilot_data import parse_selection
ROOT=Path(__file__).resolve().parents[1]

def measure(journal,selection):
    events=journal['events'];kept=[e for e in events if e['id'] in selection]
    detail_ids={e['id'] for e in events if e['detail']}
    rates=[]
    for activity in journal['activities']:
        all_events=[e for e in events if e['activity']==activity]
        subset=[e for e in kept if e['activity']==activity]
        target=sum(e['positive'] for e in all_events)/len(all_events)
        estimate=sum(e['positive'] for e in subset)/len(subset) if subset else None
        rates.append({'activity':activity,'target':target,'retained':len(subset),'estimate':estimate,
                      'error':estimate-target if estimate is not None else None})
    available=[r['error'] for r in rates if r['error'] is not None]
    if len(available)<2:rank='missing'
    else:
        a,b=[r['estimate'] for r in rates]
        rank='correct' if a>b else 'wrong' if a<b else 'tie'
    return {'rates':rates,'missing_activities':sum(r['estimate'] is None for r in rates),
            'mae_available':statistics.mean(abs(x) for x in available),
            'signed_bias_available':statistics.mean(available),
            'detail_event_recall':len(set(selection)&detail_ids)/len(detail_ids),'rank':rank}

def summarize(rows):
    valid=[r for r in rows if r.get('metrics') is not None]
    return {'cases':len(rows),'valid_cases':len(valid),'invalid_cases':len(rows)-len(valid),
            'missing_activities':sum(r['metrics']['missing_activities'] for r in valid),
            'activity_slots_in_valid_cases':2*len(valid),
            'mean_journal_mae_available':statistics.mean(r['metrics']['mae_available'] for r in valid) if valid else None,
            'mean_journal_signed_bias_available':statistics.mean(r['metrics']['signed_bias_available'] for r in valid) if valid else None,
            'mean_detail_event_recall':statistics.mean(r['metrics']['detail_event_recall'] for r in valid) if valid else None,
            'rank_counts':{name:sum(r['metrics']['rank']==name for r in valid) for name in ['correct','wrong','tie','missing']}}

def main():
    trace_path=ROOT/'results/pilot-003-predictions.jsonl'
    trace=[json.loads(line) for line in trace_path.read_text().splitlines()]
    journals={j['id']:j for j in json.loads((ROOT/'results/pilot-003-journals.json').read_text())}
    expected={(j,w,d) for j in journals for w in ['important','representative'] for d in [False,True]}
    keys=[(r['journal'],r['writer'],r['detailed']) for r in trace]
    if len(keys)!=48 or set(keys)!=expected:raise ValueError('Complete unique trace required')
    manifest=json.loads((ROOT/'results/pilot-003-run-manifest.json').read_text())
    for path,digest in manifest['hashes'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Changed dependency: '+path)
    measured=[]
    for row in trace:
        journal=journals[row['journal']]
        parsed=parse_selection(row['text'],{e['id'] for e in journal['events']})
        if parsed!=row['selection'] or row['valid']!=(parsed is not None):raise ValueError('Parsing inconsistency')
        if hashlib.sha256(row['prompt'].encode()).hexdigest()!=row['prompt_sha256']:raise ValueError('Prompt mismatch')
        if row['prompt_tokens']>4096 or row['generation_tokens']>160:raise ValueError('Budget violation')
        measured.append({'journal':row['journal'],'writer':row['writer'],'detailed':row['detailed'],
                         'metrics':measure(journal,parsed) if parsed is not None else None})
    summaries={}
    for writer in ['important','representative']:
        for detailed in [False,True]:
            summaries[f'{writer}_{"detailed" if detailed else "plain"}']=summarize([r for r in measured if r['writer']==writer and r['detailed']==detailed])
    random_rows=[]
    for j in journals.values():
        ids=[e['id'] for e in j['events']]
        for seed in range(1000):
            kept=random.Random(100000*j['seed']+seed).sample(ids,6)
            random_rows.append({'metrics':measure(j,kept)})
    summaries['uniform_sample']=summarize(random_rows)
    pairs={}
    for writer in ['important','representative']:
        effects=[]
        for j in journals:
            cases={r['detailed']:r['metrics'] for r in measured if r['writer']==writer and r['journal']==j}
            if cases[False] is None or cases[True] is None:continue
            effects.append({'journal':j,'mae_delta_detailed_minus_plain':cases[True]['mae_available']-cases[False]['mae_available'],
                            'detail_recall_delta':cases[True]['detail_event_recall']-cases[False]['detail_event_recall']})
        pairs[writer]={'valid_pairs':len(effects),'effects':effects,
            'mean_mae_delta':statistics.mean(x['mae_delta_detailed_minus_plain'] for x in effects) if effects else None,
            'mean_detail_recall_delta':statistics.mean(x['detail_recall_delta'] for x in effects) if effects else None}
    out={'status':'small synthetic development audit; no new estimator or natural-user effect claim',
         'trace_sha256':hashlib.sha256(trace_path.read_bytes()).hexdigest(),
         'analysis_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'actual_calls':len(trace),'reader_seconds':sum(r['reader_seconds'] for r in trace),
         'total_prompt_tokens':sum(r['prompt_tokens'] for r in trace),
         'total_generation_tokens':sum(r['generation_tokens'] for r in trace),
         'summaries':summaries,'paired_rendering_effects':pairs,'measurements':measured,
         'counter_ledger_control':{'stored_counts_per_journal':4,'mae':0,'activity_order_accuracy':1,
             'limitation':'Only solves the two prespecified rate queries; does not retain individual event evidence.'}}
    (ROOT/'results/pilot-003-analysis.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'summaries':summaries,'paired':pairs},indent=2))
if __name__=='__main__':main()
