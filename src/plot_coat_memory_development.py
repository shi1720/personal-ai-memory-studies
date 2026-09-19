"""Render only completed, hash-validated empirical results."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from coat_memory_reader import ROOT,digest


def main():
    data=json.loads((ROOT/'results/coat-memory-development-analysis.json').read_text())
    for p,h in data['hashes'].items():assert digest(ROOT/p)==h,p
    fig,axes=plt.subplots(1,2,figsize=(12,5.4))
    labels=['LLM: no history','LLM: full history','LLM: native memories']
    values=[data['summaries'][c]['macro_mae'] for c in ['no_history','full_history','native_memory']]
    colors=['#898d95','#3466a4','#98508e']
    for key,label,color in [('population_features','Population features','#707070'),('uniform','Attribute regression','#288276')]:
        row=next(r for r in data['numerical_references'] if r['variant']==key)
        labels.append(label);values.append(row['macro_mae']);colors.append(color)
    axes[0].barh(range(len(labels)),values,color=colors,height=.56)
    axes[0].set_yticks(range(len(labels)),labels);axes[0].invert_yaxis()
    axes[0].set_xlabel('User-macro MAE on new items (lower is better)')
    axes[0].set_xlim(0,max(values)*1.19)
    for i,v in enumerate(values):axes[0].text(v+.025,i,f'{v:.3f}',va='center',fontsize=9)
    axes[0].set_title('Prediction error with each information source',fontsize=11,weight='bold',pad=14)
    ds=[r['delta_mae'] for r in data['paired_users']]
    axes[1].bar(range(1,len(ds)+1),ds,color=['#b56642' if d>0 else '#288276' for d in ds],width=.7)
    axes[1].axhline(0,color='#333333',lw=.8)
    axes[1].set_xlabel('User position in paired development subset')
    axes[1].set_ylabel('MAE: native memory minus full history')
    axes[1].set_title('Memory effect varies across users',fontsize=11,weight='bold',pad=14)
    p=data['primary_paired']
    if p:
        lo,hi=p['percentile_95']
        axes[1].text(.5,-.22,f"Mean difference {p['mean']:+.3f}; exploratory 95% interval [{lo:+.3f}, {hi:+.3f}]\nPositive values mean greater error with extracted memory.",
            transform=axes[1].transAxes,ha='center',va='top',fontsize=9,linespacing=1.5)
    for ax in axes:
        ax.spines[['top','right']].set_visible(False);ax.set_axisbelow(True)
    axes[0].grid(axis='x',color='#e3e5e8',linewidth=.6)
    axes[1].grid(axis='y',color='#e3e5e8',linewidth=.6)
    fig.suptitle('Native memory and preference prediction',fontsize=16,weight='bold',y=.97)
    coverage='; '.join(f"{c.replace('_',' ')} {v['valid_users']}/30 valid" for c,v in data['summaries'].items())
    fig.text(.5,.90,coverage,ha='center',fontsize=9)
    fig.text(.5,.035,'Development only. One local 4-bit model; 438 scheduled targets. Bars use available valid users.\nNumerical penalties selected on development data; the paired comparison uses 29 common users.',ha='center',fontsize=9,linespacing=1.5)
    fig.subplots_adjust(left=.165,right=.975,top=.79,bottom=.28,wspace=.40)
    fig.savefig(ROOT/'results/figures/coat-memory-development.png',dpi=180,facecolor='white')
    fig.savefig(ROOT/'results/figures/coat-memory-development.pdf',facecolor='white',
        metadata={'Title':'Native memory and preference prediction',
                  'Author':'Shivam Gupta',
                  'Subject':'Exploratory development study, not confirmatory evidence'})
    plt.close(fig)

if __name__=='__main__':main()
