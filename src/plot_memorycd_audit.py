"""Aggregate scientific figure for the completed MemoryCD audit."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_memorycd_baselines import ROOT,sha,DOMAINS


def main():
    r=json.loads((ROOT/'results/memorycd-baseline-audit.json').read_text())
    for p,h in r['hashes'].items():assert sha(ROOT/p)==h,p
    fig,axes=plt.subplots(1,2,figsize=(12,5.2))
    labels=['Personal care','Books','Electronics','Home & kitchen']
    colors=['#9bb6c7','#8b91c6','#479085']
    for j,(method,label) in enumerate([('constant_5','Always 5'),('history_mean','History mean'),('history_median','History median')]):
        vals=[r['single_domain'][d]['baselines'][method]['macro_mae'] for d in DOMAINS]
        axes[0].bar([x+(j-1)*.23 for x in range(4)],vals,width=.22,color=colors[j],label=label)
    axes[0].set_xticks(range(4),labels,rotation=15,ha='right');axes[0].set_ylim(0,1)
    axes[0].set_ylabel('User-macro MAE (lower is better)');axes[0].legend(frameon=False,fontsize=9)
    axes[0].set_title('Simple controls provide useful prediction',fontsize=12,weight='bold')
    c=r['cross_domain'];bs=c['baselines']
    for i,(name,label) in enumerate([('mean','Mean'),('median','Median')]):
        before=bs['unrestricted_source_'+name]['macro_mae'];after=bs['strict_prior_'+name+'_covered']['macro_mae']
        axes[1].plot([0,1],[before,after],marker='o',lw=1.7,color=colors[i+1],label=label)
        axes[1].text(-.05,before,f'{before:.4f}',ha='right',va='center',fontsize=10)
        axes[1].text(1.05,after,f'{after:.4f}',ha='left',va='center',fontsize=10)
    axes[1].set_xlim(-.4,1.4);axes[1].set_ylim(.50,.82)
    axes[1].set_xticks([0,1],['All source events','Strictly earlier events'])
    axes[1].set_ylabel('Cross-domain MAE');axes[1].legend(frameon=False,fontsize=9)
    axes[1].set_title('Timestamp cutoff barely changes these controls',fontsize=12,weight='bold')
    for ax in axes:
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#e5e7eb',lw=.6);ax.set_axisbelow(True)
    fig.suptitle('MemoryCD released-cohort audit',fontsize=16,weight='bold',y=.97)
    fig.text(.5,.89,'323 users; 969 targets per domain. No language model or target-dependent parameter fitting.',ha='center',fontsize=10)
    fig.text(.5,.055,'Exploratory audit of the released cross-domain cohort. These are not reproductions of the paper’s distinct single-domain cohorts.',ha='center',fontsize=9)
    fig.subplots_adjust(left=.07,right=.98,top=.77,bottom=.23,wspace=.30)
    fig.savefig(ROOT/'results/figures/memorycd-baseline-audit.png',dpi=180,facecolor='white');plt.close(fig)

if __name__=='__main__':main()
