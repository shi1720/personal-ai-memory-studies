"""Plot measured full-trace results only. Never fills missing measurements."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((ROOT / "results/pilot-002-analysis.json").read_text())
    policies = result["policies"]
    x = np.arange(len(policies))
    labels = [f"{p['alpha']:.2f}" for p in policies]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "axes.titleweight": "bold"})
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.5), constrained_layout=True)
    ax = axes[0, 0]
    ax.bar(x-.25, [p["fixed_exact_calls"] for p in policies], .25, label="Fixed order", color="#325E9A")
    means = [p["random_exact_calls"]["mean"] for p in policies]
    errors = [[m-p["random_exact_calls"]["min"] for m,p in zip(means,policies)],
              [p["random_exact_calls"]["max"]-m for m,p in zip(means,policies)]]
    ax.bar(x, means, .25, yerr=errors, capsize=3, label="Random order: mean, min/max", color="#70A8AB")
    ax.bar(x+.25, [p["oracle_certificate_diagnostic"]["calls"] for p in policies], .25,
           label="Oracle minimum (not deployable)", color="#CACAD4")
    ax.axhline(result["exact_cache_baseline_new_calls"], color="#9C4B30", linestyle="--",
               label="Exact caching baseline")
    ax.set(title="A. Calls to recover the full-reference policy", ylabel="New calibration reader calls",
           ylim=(0, 69), xticks=x, xticklabels=labels, xlabel="Target marginal risk alpha")
    ax.legend(fontsize=8, loc="lower right")
    for ax, metric, title, ylabel in [
        (axes[0,1], "coverage", "B. Evaluation answer coverage", "Answered queries (%)"),
        (axes[1,0], "shipped_error_rate", "C. Evaluation marginal shipped errors", "Wrong and answered / all queries (%)")]:
        ax.bar(x-.17, [100*p["full_evaluation"][metric] for p in policies], .34,
               label="Full recalibration", color="#325E9A")
        ax.bar(x+.17, [100*p["stale_evaluation"][metric] for p in policies], .34,
               label="Stale calibration", color="#BC7853")
        if metric == "shipped_error_rate":
            ax.scatter(x, [100*p["alpha"] for p in policies], marker="_", s=240,
                       color="#25252C", label="Risk target")
        ax.set(title=title, ylabel=ylabel, xticks=x, xticklabels=labels,
               xlabel="Target marginal risk alpha", ylim=(0, 105 if metric == "coverage" else 40))
        ax.legend(fontsize=8)
        if metric == "coverage":
            counts = {(p["full_evaluation"]["accepted"], p["full_evaluation"]["n"],
                       p["full_evaluation"]["shipped_errors"]) for p in policies}
            if len(counts) == 1:
                accepted, total, errors = counts.pop()
                ax.text(.5, .62, f"Every setting answered {accepted} of {total} queries.\n"
                        f"Incorrect answers among those sent: {errors}.",
                        transform=ax.transAxes, ha="center", va="center", fontsize=12,
                        color="#5C3330", bbox=dict(facecolor="#F7EFEB", edgecolor="none", pad=12))
    ax = axes[1,1]
    for p, color in zip(policies, ["#325E9A", "#70A8AB", "#BC7853", "#8263A0"]):
        fractions = [0, .25, .5, .75, 1.0]
        values = []
        for f in fractions:
            cases = [s for s in p["schedules"] if s["seed"] is not None and s["budget_fraction"] == f]
            values.append(100*np.mean([s["evaluation"]["coverage"] for s in cases]))
        ax.plot([100*f for f in fractions], values, marker="o", color=color, label=f"alpha {p['alpha']:.2f}")
    ax.set(title="D. Coverage when recalibration stops early", xlabel="Budget / changed calibration rows (%)",
           ylabel="Evaluation answer coverage (%)", ylim=(0, 105), xlim=(-3, 103))
    ax.legend(fontsize=8)
    fig.suptitle("Partial recalibration after memory availability loss\n"
                 "Exploratory PersonaMem-v2 slice: 64 calibration and 64 evaluation personas", fontsize=14)
    fig.supxlabel("Offline replay of recorded predictions. Call counts are not measured speedups.\n"
                  "Random-order ranges describe 100 orderings of one fixed table, not statistical confidence intervals.", fontsize=9)
    output = ROOT / "results/figures/pilot-002-recalibration.png"
    fig.savefig(output, dpi=180)
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
