"""Emit typesetting inputs from completed measured results, with no invented values."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper'

def load(name):return json.loads((ROOT/'results'/name).read_text())
def f(x):return '--' if x is None else f'{x:.3f}'
def escape(s):return s.replace('_',r'\_')


def system_label(key):
    numerical={'history_mean':'History mean','history_median':'History median',
      'history_ridge':'History-only ridge','shuffled_history_ridge':'Ridge / permuted',
      'constant_3':'Scale midpoint', 'population_mean':'Population mean',
      'population_features':'Population features','user_mean':'Pop. + user offset',
      'uniform':'Pop. + residual ridge'}
    if key in numerical:return numerical[key]
    for model in ['qwen','phi']:
        if key.startswith(model+'_'):
            context=key[len(model)+1:]
            return model.capitalize()+' / '+{'no_history':'none','full_history':'full',
                'shuffled_history':'permuted','native_memory':'memory'}[context]
    return escape(key)


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
    aux=load('confirmation-auxiliary-report.json')
    systems=[('constant_3','Scale midpoint'),('shuffled_history_ridge','Ridge / permuted'),('history_mean','History mean'),('history_median','History median'),('history_ridge','History-only ridge'),
             ('qwen_no_history','Qwen / no history'),('qwen_full_history','Qwen / full history'),('qwen_shuffled_history','Qwen / permuted history'),('qwen_native_memory','Qwen / native memory'),
             ('phi_no_history','Phi / no history'),('phi_full_history','Phi / full history'),('phi_shuffled_history','Phi / permuted history'),('phi_native_memory','Phi / native memory')]
    rows=[]
    for key,label in systems:
        row=[label]
        for domain in reports:
            s=reports[domain]['summaries'].get(key)
            if domain=='Coat' and key=='constant_3':
                s={'operational':{'mae':aux['coat_midpoint_reference']['mae']},'valid_users':200}
            row.extend([f(s['operational']['mae']),f"{s['valid_users']}/200"] if s else ['--','--'])
        rows.append(row)
    (PAPER/'main-results-table.tex').write_text(table(['System / evidence','Coat MAE','Valid','MovieLens MAE','Valid'],rows,
       'Operational user-macro MAE and valid-output coverage. Invalid reader arrays use the predeclared constant-3 fallback. Numerical methods always produce valid predictions. Native memory is evaluated on Coat only. Lower MAE is better. The Coat midpoint row is an auxiliary descriptive reference; ridge permutation is a frozen secondary control.',
       'tab:main-results','lrrrr')+'\n')
    supplement=[]
    for domain,r in reports.items():
        rows=[]
        for system,s in r['summaries'].items():
            a=s['operational'];v=s['valid_only'];rows.append([system_label(system),f(a['mae']),f(a['rmse']),f(a['signed_error']),f(a['pairwise_accuracy']),f(v['mae']),f"{s['valid_users']}/200"])
        supplement.append(table(['System','MAE','RMSE','Signed error','Pairwise','Valid-only MAE','Valid'],rows,
            domain+' complete metric summary. Pairwise concordance averages eligible users; ties receive half credit. All primary operational summaries include every user. Valid-only subsets can differ.' + (' Population and Pop. rows use additional fitting-user data; their equations are in Appendix~\\ref{app:population}.' if domain=='Coat' else ''),
            'tab:metrics-'+domain.lower(),'lrrrrrr'))
        rows=[]
        for key,c in r['primary_contrasts'].items():
            a=c['operational'];v=c['common_valid'];ci=a['family_adjusted_interval'];vci=v['interval_95'] if v else [None,None]
            model,contrast=key.split('_',1)
            label=model.capitalize()+' / '+{'extraction':'extraction','association':'association','numerical_reader':'numerical reader'}[contrast]
            rows.append([label,f(a['mean']),f'[{f(ci[0])}, {f(ci[1])}]',f(v['mean']) if v else '--',f'[{f(vci[0])}, {f(vci[1])}]',str(v['users']) if v else '0'])
        supplement.append(table(['Contrast','All users','Adjusted interval','Common valid','95\\% interval','Users'],rows,
          domain+' predeclared primary contrasts and paired common-valid sensitivity. The all-user intervals use alpha 0.005 for the family of ten comparisons; the descriptive common-valid intervals shown here are ordinary 95\\% intervals. Positive effects follow the definitions in the main text.',
          'tab:contrasts-'+domain.lower(),'lrrrrr'))
    supplement.append(r'\subsection{Construction and Reading Resources}'+ '\n' + r'Table~\ref{tab:resources} separates native construction from reading costs. Counts exclude development and fitting-user preflights; prompt totals include the target list and shared instructions.')
    rows=[];writer=reports['Coat']['resources']['writer']
    rows.append(['Coat','Qwen','Native writing',str(writer['calls_with_response']),format(writer['tokens']['prompt_tokens'],','),format(writer['tokens']['completion_tokens'],',')])
    for domain,r in reports.items():
        rr=r['resources']['readers'] if domain=='Coat' else r['resources']
        for model,contexts in rr.items():
            for context,entry in contexts.items():rows.append([domain,model.capitalize(),system_label(model+'_'+context).split(' / ',1)[1],str(entry['calls']),format(entry['tokens']['prompt_tokens'],','),format(entry['tokens']['completion_tokens'],',')])
    supplement.append(table(['Domain','Model','Stage / evidence','Calls','Prompt tokens','Output tokens'],rows,
      'Recorded model usage, excluding separately reported preflights and development. Native writing counts responses recorded by the native provider callback; reader calls count attempted condition calls. Token totals do not measure full storage or commercial cost.',
      'tab:resources','lllrrr'))
    aux=load('confirmation-auxiliary-report.json')
    supplement.append(r'\subsection{Output Reliability}'+ '\n' + r'Table~\ref{tab:format-failures} partitions every invalid reader response into disjoint categories. Table~\ref{tab:precision} reports the separate numerical near-tie sensitivity; it does not alter the primary MAE analysis.')
    rows=[]
    for domain,models in aux['reader_resource_crosscheck'].items():
        label='Coat' if domain=='coat' else 'MovieLens'
        report=reports[label]
        for model,contexts in models.items():
            for context,entry in contexts.items():
                invalid=200-report['summaries'][model+'_'+context]['valid_users']
                non_stop=sum(n for reason,n in entry['finish_reasons'].items() if reason!='stop')
                transport=entry['transport_errors']
                contract=invalid-non_stop-transport
                assert contract>=0
                rows.append([label,model.capitalize(),system_label(model+'_'+context).split(' / ',1)[1],
                    str(invalid),str(non_stop),str(transport),str(contract)])
    supplement.append(table(['Domain','Reader','Evidence','Invalid','Non-stop','Transport','Contract'],rows,
      'Output failures out of 200 attempts per row. Non-stop counts responses whose generation did not end normally, including token-limit termination. Transport counts attempts without a model response. Contract counts normally stopped responses that fail the exact-array parser. Categories are disjoint and sum to Invalid. All are retained through the constant-3 fallback.',
      'tab:format-failures','lllrrrr'))
    rows=[]
    for domain,systems in aux['numerical_tie_sensitivity'].items():
        for system,r in systems.items():
            rows.append([{'coat':'Coat','movie':'MovieLens'}[domain],system_label(system),str(r['eligible_users']),format(r['strict_normal_mean'],'.6f'),format(r['strict_augmented_mean'],'.6f'),format(r['near_tie_mean'],'.6f'),str(r['users_with_strict_solver_disagreement'])])
    supplement.append(table(['Domain','System','Users','Normal','Augmented','Near-tie','Disagreements'],rows,
      'Post-freeze numerical precision sensitivity, specified before accuracy inspection. Columns show mean pairwise concordance from the original normal-equation solve, augmented least squares, and a common tie tolerance of 1e-10. Disagreements count users whose strict concordance differs between solvers. Primary MAE comparisons are unchanged.',
      'tab:precision','llrrrrr'))
    (PAPER/'supplementary-tables.tex').write_text('\n\n'.join(supplement)+'\n')
    print('Generated tables for',targets,'Coat and 3200 MovieLens targets')


if __name__=='__main__':main()
