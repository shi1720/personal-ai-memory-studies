"""Per-journal diagnostic, generated only from the validated probe analysis."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((ROOT / 'results/memory-probe-analysis.json').read_text())
    for path, digest in result['hashes'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Analysis dependency changed: ' + path)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.8), sharey=True)
    for ax, model, title in zip(axes, ['qwen', 'phi'], ['Qwen3 4B', 'Phi-4 14B']):
        measured = result['models'][model]['measurements']
        lookup = {(r['journal'], r['context']): r for r in measured}
        for i in range(12):
            journal = f'extract-{i:02d}'
            a, b = [lookup[(journal, c)] for c in ['native', 'count_aware']]
            score = 'first_32_entropy_nats'
            if a[score] is not None and b[score] is not None:
                ax.plot([a[score], b[score]], [i-.12, i+.12], color='#b7bdc7', lw=1, zorder=1)
            for row, offset, color, shape in [(a, -.12, '#295b93', 'o'), (b, .12, '#ad5c27', 's')]:
                if row[score] is None:
                    ax.text(.985, i+offset, 'blocked' if row['status'] == 'blocked_writer' else 'unscored',
                            transform=ax.get_yaxis_transform(), ha='right', va='center', fontsize=8, color=color)
                    continue
                correct = row['format_outcome'] == 'correct'
                ax.scatter(row[score], i+offset, s=62, marker=shape,
                           facecolor=color if correct else 'white', edgecolor=color, linewidth=1.5, zorder=3)
        comparison = result['models'][model]['comparisons']['first_32_entropy_nats']['format_outcome']
        ax.set_title(title + ' (4-bit)', fontsize=13, pad=14, weight='bold')
        ax.set_xlabel('Mean entropy of first 32 response tokens (nats)', fontsize=10, labelpad=10)
        ax.set_ylim(11.8, -.8)
        ax.set_xlim(left=0)
        ax.set_yticks(range(12))
        ax.set_yticklabels([f'{i:02d}' for i in range(12)])
        ax.grid(axis='x', color='#e5e7eb', linewidth=.6)
        ax.spines[['top', 'right']].set_visible(False)
        n = comparison['eligible_journals']
        ax.text(.5, -.16, f"Eligible pairs: {n}/12  |  Correct: entropy selection {comparison['selected_correct']:g}/{n}\n"
                f"Always exported prompt {comparison['always_native_correct']:g}/{n}; uniform expectation {comparison['uniform_expected_correct']:g}/{n}",
                transform=ax.transAxes, ha='center', va='top', fontsize=9, linespacing=1.6)
    axes[0].set_ylabel('Fictional development journal', fontsize=10)
    legend = [Line2D([], [], marker='o', color='#295b93', linestyle='none', label='Exported prompt'),
              Line2D([], [], marker='s', color='#ad5c27', linestyle='none', label='Count-aware addendum'),
              Line2D([], [], marker='o', color='#333333', linestyle='none', label='Filled: correct downstream answer'),
              Line2D([], [], marker='o', color='#333333', markerfacecolor='white', linestyle='none', label='Open: wrong downstream answer')]
    fig.suptitle('Does lower probe entropy choose a better memory?', fontsize=17, weight='bold', y=.98)
    fig.text(.5, .932, 'Exploratory prefix diagnostic, including truncated responses. Exact-option downstream scoring.', ha='center', fontsize=10)
    fig.legend(handles=legend, loc='lower center', ncol=2, fontsize=9, frameon=False, bbox_to_anchor=(.5, .0))
    fig.subplots_adjust(top=.855, bottom=.245, wspace=.15, left=.075, right=.975)
    output = ROOT / 'results/figures/memory-probe-prefix.png'
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
