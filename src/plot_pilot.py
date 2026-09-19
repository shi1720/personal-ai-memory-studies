"""Make a descriptive figure from measured pilot outputs, without inference."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((ROOT / "results/pilot-001-retrieval.json").read_text())
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), gridspec_kw={"width_ratios": [1, 1.3]})
    for method, label, color in [("bm25", "BM25", "#355b9d"), ("recency", "Newest sessions first", "#8d969e")]:
        ks = [1, 3, 5, 10]
        ys = [100 * result["summary"][method][str(k)]["all_hit"] for k in ks]
        axes[0].plot(ks, ys, marker="o", color=color, label=label, linewidth=2)
    axes[0].set(xlabel="Number of retrieved sessions", ylabel="All required sessions found (%)",
                title="Evidence coverage across retrieval depths", ylim=(0, 100), xticks=[1, 3, 5, 10])
    axes[0].legend(frameon=False, loc="upper left")
    types = sorted({row["question_type"] for row in result["rows"]})
    groups = [[r for r in result["rows"] if r["question_type"] == t] for t in types]
    vals = [100 * sum(r["methods"]["bm25"]["scores"]["5"]["all_hit"] for r in rs) / len(rs) for rs in groups]
    labels = [f"{t.replace('single-session-', 'Single: ').replace('-', ' ')}  (n={len(rs)})" for t, rs in zip(types, groups)]
    bars = axes[1].barh(labels, vals, color="#355b9d", height=0.6)
    axes[1].bar_label(bars, fmt="%.1f%%", padding=5, fontsize=9)
    axes[1].set(xlabel="All required sessions found in top five (%)", title="BM25 coverage by question type", xlim=(0, 112))
    axes[1].set_xticks([0, 25, 50, 75, 100])
    axes[1].invert_yaxis()
    for ax in axes:
        ax.set_axisbelow(True)
        ax.grid(axis="y" if ax is axes[0] else "x", color="#e5e8eb", linewidth=0.6)
    fig.suptitle("LongMemEval-S: exploratory retrieval baseline", fontsize=16, fontweight="bold", x=0.05, ha="left")
    fig.text(0.05, 0.02, "470 answerable questions. Retrieval coverage is not answer accuracy. No new method or inferential claim.", fontsize=9, color="#555555")
    fig.tight_layout(rect=(0, 0.065, 1, 0.93), w_pad=2)
    out = ROOT / "results/figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "pilot-001-retrieval.png", dpi=180, facecolor="white")
    plt.close(fig)
    print(out / "pilot-001-retrieval.png")


if __name__ == "__main__":
    main()
