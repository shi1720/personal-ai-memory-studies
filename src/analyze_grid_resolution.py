"""Post-protocol, full-information grid-resolution diagnostic on complete traces."""
import hashlib
import json
from pathlib import Path
from analyze_personamem_pilot import ALPHAS, metrics
from certificate_cost import oracle_certificate_cost
from partial_calibration import shipped_loss_row

ROOT=Path(__file__).resolve().parents[1]

def main():
    trace_path=ROOT/'results/pilot-002-predictions.jsonl'
    trace=[json.loads(s) for s in trace_path.read_text().splitlines()]
    original=json.loads((ROOT/'results/pilot-002-analysis.json').read_text())
    trace_hash=hashlib.sha256(trace_path.read_bytes()).hexdigest()
    if trace_hash!=original['trace_sha256'] or len(trace)!=128:
        raise ValueError('Complete, previously validated trace required')
    cal=[r for r in trace if r['split']=='calibration']
    evaluation=[r for r in trace if r['split']=='evaluation']
    cached=[i for i,r in enumerate(cal) if r['changed']['reused_original']]
    results=[]
    previous={}
    for refinement in range(6):
        denominator=20*2**refinement
        thresholds=[0.0]+[i/denominator for i in range(denominator//4,denominator+1)]+[1.01]
        losses=[shipped_loss_row(r['changed']['correct'],r['changed']['confidence'],thresholds) for r in cal]
        for alpha in ALPHAS:
            cost=oracle_certificate_cost(losses,alpha,cached)
            j=cost['policy']
            crossings=sum(r[j-1]-r[j] for r in losses) if j>0 else None
            if alpha in previous:
                assert cost['calls']>=previous[alpha]
            previous[alpha]=cost['calls']
            if 0<j<len(thresholds)-1 and crossings==1:
                assert cost['calls']==len(cal)-len(cached)
            results.append({'alpha':alpha,'step':1/denominator,'grid_size':len(thresholds),
                'full_threshold':thresholds[j], 'policy_index':j,
                'is_final_abstention':j==len(thresholds)-1,
                'boundary_crossing_rows':crossings,'oracle_additional_calls':cost['calls'],
                'calibration':metrics(cal,thresholds[j]),'evaluation':metrics(evaluation,thresholds[j])})
    output={'status':'post-protocol exploratory oracle diagnostic, not an online strategy',
        'trace_sha256':trace_hash,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'note_sha256':hashlib.sha256((ROOT/'docs/grid-resolution-note.md').read_bytes()).hexdigest(),
        'rows':results}
    (ROOT/'results/pilot-002-grid-resolution.json').write_text(json.dumps(output,indent=2)+'\n')
    for r in results:
        print(f"alpha={r['alpha']:.2f} grid={r['grid_size']:3} threshold={r['full_threshold']:.7f} "
              f"crossings={r['boundary_crossing_rows']} oracle_calls={r['oracle_additional_calls']} "
              f"coverage={r['evaluation']['coverage']:.3f}")

if __name__=='__main__':main()
