"""Show completed component-test runs with failures and abstentions retained."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
CONTEXTS=['full','native','count_aware','ledger']
LABELS=['Full journal','Exported prompt','Count-aware prompt','Exact count ledger']
COLORS={'correct':'#277d73','wrong':'#b54848','abstained':'#8190a3','invalid':'#d6a347','blocked_writer':'#8b67a4'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--answer-format-sensitivity',action='store_true')
    args=parser.parse_args()
    format_runs={}
    if args.answer_format_sensitivity:
        for phase in ['initial','budget']:
            format_runs[phase]=json.loads((ROOT/'results'/f'pilot-004-answer-format-{phase}.json').read_text())['models']
    models=[]
    for key,label in [('qwen','Qwen3 4B'),('phi','Phi-4')]:
        a=ROOT/'results'/f'pilot-004-{key}-analysis.json';b=ROOT/'results'/f'pilot-004-{key}-budget-analysis.json'
        if a.exists() and b.exists():
            original=json.loads(a.read_text());budget=json.loads(b.read_text())
            if args.answer_format_sensitivity:
                original['summaries']=format_runs['initial'][key]['summaries']
                budget['summaries']={c:s['rate'] for c,s in format_runs['budget'][key]['summaries'].items()}
            models.append((label,original,budget))
    if not models:raise ValueError('No complete initial-plus-budget model analysis')
    fig,axes=plt.subplots(len(models),3,figsize=(15,3.4*len(models)+2.4),squeeze=False,sharex=True,sharey=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    for row,(label,original,budget) in enumerate(models):
        panels=[('Frequency question\nOriginal: 256 output tokens',{c:original['summaries'][c]['rate'] for c in CONTEXTS}),
                ('Frequency question\nBudget check: 768 output tokens',budget['summaries']),
                ('Dated-event question\nOriginal: 256 output tokens',{c:original['summaries'][c]['event'] for c in CONTEXTS})]
        for col,(title,summaries) in enumerate(panels):
            ax=axes[row,col];y=np.arange(4);left=np.zeros(4)
            for outcome,color in COLORS.items():
                counts=np.array([summaries[c][outcome] for c in CONTEXTS]);ax.barh(y,counts,left=left,color=color,label=outcome.replace('_',' '),height=.64)
                for pos,count,offset in zip(y,counts,left):
                    if count:ax.text(offset+count/2,pos,str(count),ha='center',va='center',color='white' if outcome in ['correct','wrong','blocked_writer'] else '#14202b',fontweight='bold',fontsize=10)
                left+=counts
            if not np.all(left==12):raise ValueError('Every planned case must be counted')
            ax.set_xlim(0,12);ax.set_xticks([0,3,6,9,12]);ax.set_xlabel('Cases out of 12');ax.set_yticks(y);ax.set_yticklabels(LABELS)
            ax.set_ylim(3.6,-.7);ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
            ax.set_title((label+'\n' if col==0 else '')+title,fontsize=11,fontweight='bold',loc='left',pad=14)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower left',bbox_to_anchor=(.02,.087),ncol=5,frameon=False)
    fig.suptitle('Memory extraction: '+('exact-option format sensitivity' if args.answer_format_sensitivity else 'strict protocol results'),x=.02,ha='left',fontsize=17,fontweight='bold')
    fig.text(.02,.92,'12 fictional journals. Exported prompt component test, not Mem0\'s active extraction path or a deployed-system study.',fontsize=10,color='#444')
    note=' The exact-option answer parser is also post hoc.' if args.answer_format_sensitivity else ''
    fig.text(.02,.025,'All planned cases remain in the denominator. Abstention is separate from a wrong answer. The count ledger omits dated events by design.\nThe higher-budget run is post hoc and reuses original prompts.'+note+' Model outputs are not independent users.',fontsize=9,color='#444',linespacing=1.5)
    fig.subplots_adjust(left=.17,right=.98,top=.78 if len(models)==1 else .81,bottom=.25 if len(models)==1 else .19,wspace=.16,hspace=.6)
    name='pilot-004-extraction'+('-answer-format' if args.answer_format_sensitivity else '')+'.png'
    path=ROOT/'results/figures'/name;fig.savefig(path,dpi=180);print(path)
if __name__=='__main__':main()
