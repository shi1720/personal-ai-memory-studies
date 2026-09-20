"""Publication figures from completed, hash-checked recorded analyses."""
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/figures/confirmation'
COLORS={'qwen':'#246A90','phi':'#A24D25','numeric':'#4E6474'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,
 'axes.titlesize':9,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'ps.fonttype':42,
 'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#9CA5AD','axes.linewidth':.6})


def emit(fig,name):
    OUT.mkdir(parents=True,exist_ok=True)
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight')
    fig.savefig(OUT/(name+'.png'),dpi=220,bbox_inches='tight')
    plt.close(fig)


def diagram():
    fig,ax=plt.subplots(figsize=(7.0,2.65));ax.set_xlim(0,10);ax.set_ylim(.25,4.7);ax.axis('off')
    def box(x,y,w,h,text,color='#F1F5F7',edge='#B7C4CB',size=8):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.06,rounding_size=0.07',fc=color,ec=edge,lw=.8))
        if text:ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=size)
    def arrow(a,b,color='#677986'):
        ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,lw=.9,color=color))
    box(.1,1.75,1.65,1.4,'24 observed\nitem-rating pairs\n\nTarget outcomes\nwithheld',size=7.3)
    boxes=[('Full history',3.7,None),('Permuted ratings',2.65,'Same items and rating multiset'),('Native memory',1.6,'Coat only; fixed Qwen writer'),('No history',.55,None)]
    for text,y,sub in boxes:
        box(2.95,y,2.35,.8,'',color='#EAF2F6' if text!='Native memory' else '#F4EEE8')
        ax.text(4.125,y+(.52 if sub else .4),text,ha='center',va='center',fontsize=8)
        if sub:ax.text(4.125,y+.2,sub,ha='center',va='center',fontsize=5.8,color='#435662')
        arrow((1.84,2.45),(2.88,y+.4));arrow((5.37,y+.4),(6.25,2.45))
    box(6.3,1.75,1.3,1.4,'Fixed reader\n\nQwen or Phi',size=7.5)
    arrow((7.68,2.45),(8.14,2.45))
    box(8.2,1.75,1.65,1.4,'New target\npredictions\n\nSame output rule',size=7.3)
    emit(fig,'design')


def load():
    reports={d:json.loads((ROOT/'results'/f).read_text()) for d,f in [('Coat','confirmation-analysis.json'),('MovieLens','movie-validation-analysis.json')]}
    for r in reports.values():
        for path,h in r['hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
    check=json.loads((ROOT/'results/independent-calculation-check.json').read_text())
    assert all(r['status']=='passed' for r in check['checks'])
    for path,h in check['analysis_hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    return reports


def forest(reports):
    fig,axes=plt.subplots(1,3,figsize=(7.1,3.2),gridspec_kw={'width_ratios':[1,1,1]})
    definitions=[('extraction','Extraction\nNative minus full','Positive: extraction hurts'),('association','Association use\nPermuted minus full','Positive: assignments help'),('numerical_reader','Reader choice\nFull minus ridge','Positive: ridge helps')]
    for ax,(key,title,label) in zip(axes,definitions):
        entries=[]
        for d,r in reports.items():
            for m in COLORS:
                if m+'_'+key in r['primary_contrasts']:entries.append((d,m,r['primary_contrasts'][m+'_'+key]['operational']))
        for i,(d,m,c) in enumerate(entries):
            y=len(entries)-i-1;lo,hi=c['family_adjusted_interval'];l95,h95=c['interval_95']
            ax.plot([lo,hi],[y,y],color=COLORS[m],lw=1,alpha=.65)
            ax.plot([l95,h95],[y,y],color=COLORS[m],lw=3,solid_capstyle='butt')
            ax.scatter([c['mean']],[y],c=COLORS[m],s=23,zorder=3,edgecolors='white',linewidths=.4)
        ax.axvline(0,color='#7D858B',lw=.7,ls='--');ax.set_yticks(range(len(entries)))
        ax.set_yticklabels([d+' / '+m.capitalize() for d,m,_ in entries][::-1],fontsize=6.8)
        ax.set_title(title,pad=9);ax.set_xlabel('MAE difference\n'+label,fontsize=7)
        ax.set_ylim(-.5,len(entries)-.5);ax.grid(axis='x',color='#E8EDF0',lw=.5)
    fig.tight_layout(w_pad=1.1);emit(fig,'primary-contrasts')


def decomposition(reports):
    fig,axes=plt.subplots(1,2,figsize=(7,2.9),sharey=True)
    for ax,(domain,r) in zip(axes,reports.items()):
        systems=['qwen_no_history','qwen_full_history','qwen_shuffled_history']+(['qwen_native_memory'] if domain=='Coat' else [])+['phi_no_history','phi_full_history','phi_shuffled_history']+(['phi_native_memory'] if domain=='Coat' else [])+['history_mean','history_ridge']
        labels=[s.replace('qwen_','Q / ').replace('phi_','P / ').replace('no_history','none').replace('full_history','full').replace('shuffled_history','perm.').replace('native_memory','memory').replace('history_mean','mean').replace('history_ridge','ridge') for s in systems]
        levels=np.array([r['summaries'][s]['operational']['level_mse'] for s in systems]);centered=np.array([r['summaries'][s]['operational']['centered_mse'] for s in systems])
        ax.bar(range(len(systems)),levels,color='#7898B0',label='Squared mean error',width=.7)
        ax.bar(range(len(systems)),centered,bottom=levels,color='#D4DFE5',label='Centered residual MSE',width=.7)
        ax.set_title(domain);ax.set_xticks(range(len(systems)));ax.set_xticklabels(labels,rotation=55,ha='right',fontsize=6.8);ax.set_axisbelow(True);ax.grid(axis='y',color='#EDF0F2',lw=.6)
    axes[0].set_ylabel('User-macro MSE');axes[1].legend(loc='upper right',fontsize=6.5,frameon=False)
    fig.tight_layout();emit(fig,'error-decomposition')


def main():
    reports=load();diagram();forest(reports);decomposition(reports)
    (OUT/'manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'analysis_hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['results/confirmation-analysis.json','results/movie-validation-analysis.json']}},indent=2)+'\n')


if __name__=='__main__':main()
