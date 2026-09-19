"""Plot every frozen development setting, with per-user paired diagnostics."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((ROOT/'results/coat-development-baselines.json').read_text())
    for path, digest in result['hashes'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise ValueError('Changed dependency: '+path)
    rows = result['results']
    styles = {'user_mean': ('User mean', '#757575'), 'uniform': ('Uniform history', '#287d83'),
              'exposure': ('Estimated exposure', '#3359a5'), 'positive': ('Positive gate', '#bc5c2a'),
              'exposure_positive': ('Exposure + positive gate', '#9b4c8f')}
    fig, axes = plt.subplots(1,2,figsize=(12,5.6))
    for method, (label, color) in styles.items():
        settings = [r for r in rows if r['variant'] == method]
        axes[0].plot([r['penalty'] for r in settings], [r['summaries']['new']['macro_mae'] for r in settings],
                     marker='o', color=color, label=label, linewidth=1.7, markersize=4)
    population = next(r for r in rows if r['variant']=='population_features')
    axes[0].axhline(population['summaries']['new']['macro_mae'], color='#333333', linestyle='--',
                   linewidth=1.2, label='Population features')
    axes[0].set_xscale('log')
    axes[0].set_xlabel('Ridge penalty')
    axes[0].set_ylabel('User-macro MAE on new items')
    axes[0].set_title('All development settings', fontsize=12, weight='bold')
    axes[0].legend(fontsize=8, frameon=False, loc='upper left', bbox_to_anchor=(0, -.20), ncol=2)
    uniform = next(r for r in rows if r['variant']=='uniform' and r['penalty']==1.)
    gated = next(r for r in rows if r['variant']=='positive' and r['penalty']==1.)
    u = {r['user_row']:r for r in uniform['users']}
    g = {r['user_row']:r for r in gated['users']}
    deltas = [g[k]['new']['mae']-u[k]['new']['mae'] for k in u]
    axes[1].bar(range(1,len(deltas)+1), deltas, color=['#bc5c2a' if d>=0 else '#287d83' for d in deltas], width=.75)
    axes[1].axhline(0,color='#333333',linewidth=.9)
    axes[1].set_title('Gate effect for each development user', fontsize=12, weight='bold')
    axes[1].set_xlabel('User position in frozen development split')
    axes[1].set_ylabel('MAE: positive gate minus uniform history')
    axes[1].text(.5,-.20,'Same penalty (1) for both methods.\nPositive values mean the gate increases error.',
                 transform=axes[1].transAxes, ha='center', va='top', fontsize=9, linespacing=1.6)
    for ax in axes:
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y', color='#e5e7eb', linewidth=.6)
        ax.set_axisbelow(True)
    fig.suptitle('Observed ratings support a real personalization test', fontsize=16,weight='bold', y=.985)
    fig.text(.5,.925,'30 development users, 438 new-item targets. Established baselines; 200 reserved users remain unscored.',
             ha='center',fontsize=10)
    fig.subplots_adjust(left=.07,right=.975,top=.82,bottom=.26,wspace=.30)
    fig.savefig(ROOT/'results/figures/coat-development.png', dpi=180,facecolor='white')
    plt.close(fig)


if __name__=='__main__':
    main()
