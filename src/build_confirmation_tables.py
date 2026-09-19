"""Emit typesetting inputs from completed measured results, with no invented values."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper'

def load(name):return json.loads((ROOT/'results'/name).read_text())
def f(x):return '--' if x is None else f'{x:.3f}'
def escape(s):return s.replace('_',r'\_')


def table(header,rows,caption,label,columns):
    return '\n'.join([r'\begin{table*}[t]',r'\centering\small',r'\caption{'+caption+'}',r'\label{'+label+'}',
       r'\begin{tabular}{'+columns+'}',r'\toprule',' & '.join(header)+r'\\',r'\midrule',
       *[' & '.join(row)+r'\\' for row in rows],r'\bottomrule',r'\end{tabular}',r'\end{table*}'])


def main():
    reports={'Coat':load('confirmation-analysis.json'),'MovieLens':load('movie-validation-analysis.json')}
    check=load('independent-calculation-check.json');assert all(c['status']=='passed' for c in check['checks'])
    for n,h in check['analysis_hashes'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    for r in reports.values():
        for n,h in r['hashes'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    targets=reports['Coat']['summaries']['history_ridge']['targets']
    (PAPER/'results.tex').write_text(r'\newcommand{\CoatTargets}{'+format(targets,',')+'}\n')
    systems=[('history_mean','History mean'),('history_median','History median'),('history_ridge','History-only ridge'),
             ('qwen_no_history','Qwen / no history'),('qwen_full_history','Qwen / full history'),('qwen_shuffled_history','Qwen / permuted history'),('qwen_native_memory','Qwen / native memory'),
             ('phi_no_history','Phi / no history'),('phi_full_history','Phi / full history'),('phi_shuffled_history','Phi / permuted history'),('phi_native_memory','Phi / native memory')]
    rows=[]
    for key,label in systems:
        row=[label]
        for domain in reports:
            s=reports[domain]['summaries'].get(key)
            row.extend([f(s['operational']['mae']),f"{s['valid_users']}/200"] if s else ['--','--'])
        rows.append(row)
    (PAPER/'main-results-table.tex').write_text(table(['System / evidence','Coat MAE','Valid','MovieLens MAE','Valid'],rows,
       'Operational user-macro MAE and valid-output coverage. Invalid reader arrays use the predeclared constant-3 fallback. Numerical methods always produce valid predictions. Native memory is evaluated on Coat only. Lower MAE is better.',
       'tab:main-results','lrrrr')+'\n')
    supplement=[]
    for domain,r in reports.items():
        rows=[]
        for system,s in r['summaries'].items():
            a=s['operational'];v=s['valid_only'];rows.append([escape(system),f(a['mae']),f(a['rmse']),f(a['signed_error']),f(a['pairwise_accuracy']),f(v['mae']),f"{s['valid_users']}/200"])
        supplement.append(table(['System','MAE','RMSE','Signed error','Pairwise','Valid-only MAE','Valid'],rows,
            domain+' complete metric summary. Pairwise concordance averages eligible users; ties receive half credit. All primary operational summaries include every user. Valid-only subsets can differ. Population-assisted Coat systems have additional fitting-user data.',
            'tab:metrics-'+domain.lower(),'lrrrrrr'))
        rows=[]
        for key,c in r['primary_contrasts'].items():
            a=c['operational'];v=c['common_valid'];ci=a['family_adjusted_interval'];vci=v['interval_95'] if v else [None,None]
            rows.append([escape(key),f(a['mean']),f'[{f(ci[0])}, {f(ci[1])}]',f(v['mean']) if v else '--',f'[{f(vci[0])}, {f(vci[1])}]',str(v['users']) if v else '0'])
        supplement.append(table(['Contrast','All users','Adjusted interval','Common valid','95\\% interval','Users'],rows,
          domain+' predeclared primary contrasts and paired common-valid sensitivity. The all-user intervals use alpha 0.005 for the family of ten comparisons; the descriptive common-valid intervals shown here are ordinary 95\\% intervals. Positive effects follow the definitions in the main text.',
          'tab:contrasts-'+domain.lower(),'lrrrrr'))
    supplement.append(r'\subsection{Construction and Reading Resources}')
    rows=[];writer=reports['Coat']['resources']['writer']
    rows.append(['Coat','Qwen','Native writing',str(writer['calls_with_response']),format(writer['tokens']['prompt_tokens'],','),format(writer['tokens']['completion_tokens'],',')])
    for domain,r in reports.items():
        rr=r['resources']['readers'] if domain=='Coat' else r['resources']
        for model,contexts in rr.items():
            for context,entry in contexts.items():rows.append([domain,model.capitalize(),escape(context),str(entry['calls']),format(entry['tokens']['prompt_tokens'],','),format(entry['tokens']['completion_tokens'],',')])
    supplement.append(table(['Domain','Model','Stage / evidence','Calls','Prompt tokens','Output tokens'],rows,
      'Recorded model usage, excluding separately reported preflights and development. Native writing counts responses recorded by the native provider callback; reader calls count attempted condition calls. Token totals do not measure full storage or commercial cost.',
      'tab:resources','lllrrr'))
    (PAPER/'supplementary-tables.tex').write_text('\n\n'.join(supplement)+'\n')
    print('Generated tables for',targets,'Coat and 3200 MovieLens targets')


if __name__=='__main__':main()
