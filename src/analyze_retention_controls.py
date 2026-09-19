"""Post-result control analysis using the original measurement definitions."""
import hashlib
import json
from pathlib import Path
from retention_pilot_data import parse_selection
from analyze_retention_pilot import measure,summarize
ROOT=Path(__file__).resolve().parents[1]

def main():
    jp=ROOT/'results/pilot-003-journals.json'
    journals={j['id']:j for j in json.loads(jp.read_text())}
    path=ROOT/'results/pilot-003-controls-predictions.jsonl'
    rows=[json.loads(l) for l in path.read_text().splitlines()]
    expected={(j,w,t) for j in journals for w in ['important','archive','proportional'] for t in ['negation','antonym']}
    if len(rows)!=72 or {(r['journal'],r['writer'],r['wording']) for r in rows}!=expected:raise ValueError('Complete control trace required')
    manifest=json.loads((ROOT/'results/pilot-003-controls-manifest.json').read_text())
    for p,h in manifest['hashes'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('Changed dependency: '+p)
    original={r['journal']:r for r in [json.loads(l) for l in (ROOT/'results/pilot-003-predictions.jsonl').read_text().splitlines()] if r['writer']=='important' and not r['detailed']}
    measured=[];repeated=[]
    for r in rows:
        j=journals[r['journal']];selection=parse_selection(r['text'],{e['id'] for e in j['events']})
        if selection!=r['selection'] or r['valid']!=(selection is not None):raise ValueError('Parse mismatch')
        if hashlib.sha256(r['prompt'].encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('Prompt hash mismatch')
        if r['prompt_tokens']>4096 or r['generation_tokens']>160:raise ValueError('Budget violation')
        metrics=measure(j,selection) if selection is not None else None
        pos=sum(e['positive'] for e in j['events'] if selection and e['id'] in selection)
        measured.append({'journal':r['journal'],'writer':r['writer'],'wording':r['wording'],
                         'metrics':metrics,'positive_selected':pos if selection is not None else None})
        if r['writer']=='important' and r['wording']=='negation':
            old=original[r['journal']]
            repeated.append({'journal':r['journal'],'identical_prompt':r['prompt']==old['prompt'],
                             'identical_output':r['text']==old['text']})
    summaries={}
    for w in ['important','archive','proportional']:
        for t in ['negation','antonym']:
            subset=[r for r in measured if r['writer']==w and r['wording']==t]
            stat=summarize(subset)
            stat['positive_selected']=sum(r['positive_selected'] or 0 for r in subset)
            stat['total_selected']=6*stat['valid_cases']
            summaries[w+'_'+t]=stat
    out={'status':'post-result synthetic controls; no independent confirmation or new-method claim',
         'trace_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
         'analysis_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'dependency_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/analyze_retention_pilot.py','src/retention_pilot_data.py']},
         'reader_seconds':sum(r['reader_seconds'] for r in rows),'summaries':summaries,
         'repeat_checks':repeated,'measurements':measured}
    (ROOT/'results/pilot-003-controls-analysis.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'summaries':summaries,'repeat_checks':repeated},indent=2))
if __name__=='__main__':main()
