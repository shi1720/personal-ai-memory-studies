"""Plot completed runs only, with missingness and failure counts visible."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
labels = ['Important / plain', 'Important / detailed', 'Representative / plain',
          'Representative / detailed', 'Important / liked-disliked',
          'Archive / enjoy-not enjoy', 'Archive / liked-disliked',
          'Proportional / enjoy-not enjoy', 'Proportional / liked-disliked']
conditions = ['important_plain', 'important_detailed', 'representative_plain',
              'representative_detailed', 'important_antonym', 'archive_negation',
              'archive_antonym', 'proportional_negation', 'proportional_antonym']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sensitivity', action='store_true')
    args = parser.parse_args()
    initial = json.loads((ROOT / 'results/pilot-003-analysis.json').read_text())['summaries']
    controls = json.loads((ROOT / 'results/pilot-003-controls-analysis.json').read_text())['summaries']
    qwen = {c: initial[c] if c in initial else controls[c] for c in conditions}
    series = [('Qwen3 4B', qwen, '#245c83')]
    for name, label, color in [('mistral', 'Mistral 7B', '#bd662b'), ('phi', 'Phi-4', '#37806b')]:
        path = ROOT / 'results' / f'pilot-003-{name}-analysis.json'
        if path.exists():
            data = json.loads(path.read_text())
            if data['actual_calls'] != 108:
                raise ValueError('Incomplete run')
            series.append((label, data['summaries'], color))
    if args.sensitivity:
        sensitivity = json.loads((ROOT / 'results/pilot-003-format-sensitivity.json').read_text())['models']
        series = [(label, sensitivity[key]['summaries'], color) for key, label, color in
                  [('qwen', 'Qwen3 4B', '#245c83'), ('mistral', 'Mistral 7B', '#bd662b'), ('phi', 'Phi-4', '#37806b')]]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})
    fig, axes = plt.subplots(1, 3, figsize=(15, 7.6), gridspec_kw={'width_ratios': [1, 1, .84]})
    y = np.arange(len(conditions)); offsets = np.linspace(-.22, .22, len(series))
    for (name, data, color), offset in zip(series, offsets):
        axes[0].scatter([data[c]['mean_journal_mae_available'] for c in conditions], y + offset, label=name, c=color, s=38)
        axes[1].scatter([data[c]['mean_journal_signed_bias_available'] for c in conditions], y + offset, c=color, s=38)
    for ax in axes[:2]:
        ax.set_ylim(len(conditions)-.45, -.65)
        ax.set_yticks(y)
        ax.grid(axis='x', color='#dedede', linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[['top', 'right']].set_visible(False)
    axes[0].set_yticklabels(labels)
    axes[1].set_yticklabels([])
    axes[0].set_xlim(0, .52)
    axes[1].set_xlim(-.52, .52)
    axes[0].set_xlabel('Mean absolute error')
    axes[1].set_xlabel('Mean signed error')
    axes[0].set_title('Aggregate fidelity', loc='left', fontweight='bold')
    axes[1].set_title('Bias can change direction', loc='left', fontweight='bold')
    axes[1].axvline(0, color='#555', linewidth=.8)
    axes[0].axvline(initial['uniform_sample']['mean_journal_mae_available'], linestyle='--', color='#777', linewidth=1, label='Uniform sampling')
    fig.legend(*axes[0].get_legend_handles_labels(), loc='lower left', bbox_to_anchor=(.02, .075), ncol=4, frameon=False)
    ax = axes[2]
    ax.set_xlim(0, len(series));ax.set_ylim(len(conditions)-.45, -.65);ax.axis('off')
    ax.set_title('Invalid / missing activity', loc='left', fontweight='bold')
    for col, (name, data, color) in enumerate(series):
        ax.text(col+.45, -.55, name, ha='center', color=color, fontsize=9, fontweight='bold')
        for row, condition in enumerate(conditions):
            s = data[condition]
            missing = f"{s['missing_activities']}/{s['activity_slots_in_valid_cases']}" if s['activity_slots_in_valid_cases'] else "n/a"
            ax.text(col+.45, row, f"{s['invalid_cases']}/12 | {missing}", ha='center', va='center', fontsize=9)
    fig.suptitle('Truthful selected events can distort an aggregate history', x=.02, ha='left', fontsize=17, fontweight='bold')
    subtitle = 'Exploratory audit: 12 fictional journals, six retained events, community 4-bit models. '
    subtitle += 'POST HOC: fence-only syntax recovery.' if args.sensitivity else 'Strict bare-JSON protocol.'
    fig.text(.02, .918, subtitle, fontsize=10, color='#444')
    fig.text(.02, .025, 'Errors average over represented activities in valid outputs only. Missingness and format failures must be read alongside the dots.\nUniform reference: 1,000 draws per journal, not additional users. Model templates differ. No confidence intervals or population claim.', fontsize=9, color='#444', linespacing=1.5)
    fig.subplots_adjust(left=.24, right=.985, bottom=.19, top=.84, wspace=.16)
    path = ROOT / 'results/figures' / ('pilot-003-retention-sensitivity.png' if args.sensitivity else 'pilot-003-retention.png')
    fig.savefig(path, dpi=180)
    print(path)
if __name__ == '__main__':
    main()
