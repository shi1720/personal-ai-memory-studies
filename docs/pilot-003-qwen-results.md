# Pilot 003: first-model results and diagnostic controls

Status: completed exploratory audit. This does not establish a novel method,
a natural-user effect, or readiness for a major conference.

## What ran

The pinned Qwen3 4B four-bit model completed 48 initial selections and 72
follow-up control selections. All returned valid six-ID JSON arrays. Twelve
control prompts deliberately repeat initial prompts; their outputs are identical.
Thus there are 120 actual calls but 108 unique journal-condition prompts, not
120 independent observations. There are only twelve fictional development
journals. Each contains 15 positive and 9 negative recorded visits.

## Results

| Writer / rendering | Positive events retained | Available-activity MAE | Signed bias | Missing activities |
| :--- | ---: | ---: | ---: | ---: |
| Important / plain | 72 / 72 | 0.3750 | +0.3750 | 0 / 24 |
| Important / detailed | 72 / 72 | 0.4271 | +0.4271 | 5 / 24 |
| Representative / plain | 70 / 72 | 0.3403 | +0.3403 | 0 / 24 |
| Representative / detailed | 72 / 72 | 0.3854 | +0.3854 | 1 / 24 |
| Important / antonym wording | 72 / 72 | 0.3646 | +0.3646 | 1 / 24 |
| Archive / negation wording | 72 / 72 | 0.3750 | +0.3750 | 0 / 24 |
| Archive / antonym wording | 72 / 72 | 0.3542 | +0.3542 | 2 / 24 |
| Proportional / negation wording | 25 / 72 | 0.3840 | -0.2868 | 0 / 24 |
| Proportional / antonym wording | 22 / 72 | 0.3875 | -0.2972 | 0 / 24 |

MAE and signed bias compare the retained subset's within-activity positive
fraction with the full journal's empirical rate. They average over represented
activities within a journal, then journals. Missing activities are excluded from
that error average and reported explicitly, so rows with different missingness
are not directly interchangeable. None of these numbers measure a downstream
LLM's answer accuracy.

Uniform six-event sampling over 1,000 seeds per journal has mean available-activity
MAE 0.2111 and signed bias -0.0024, with 153 missing activity slots out of 24,000.
Its 12,000 draws are Monte Carlo repetitions on twelve journals, not additional
users. An exact four-count ledger preserves both prespecified rates but lacks
individual event recall. A task-specific six-event allocation can also preserve
these deliberately simple rates exactly: three positive and one negative event
from the 0.75 activity, plus one positive and one negative from the 0.50 activity.
Neither classical sampling nor this quota construction is a novel method.

## Interpretation and limits

The all-positive selection survives a switch from personal-assistant framing to
archive framing and from negation to antonym wording. It is therefore not
explained by those two wording changes alone in this model. An explicit
proportional-retention instruction reverses the sign of bias without improving
MAE. Its reminder that negative experiences matter could itself overprime
negative selection. No causal explanation or universal direction of bias is
established.

The detailed rendering changes length and incidental distinctiveness together.
Its paired increase in recall of the designated events is not an isolated
salience effect. All prompts are custom, journals are formulaic and short,
the writer is a small quantized model, and the downstream task is absent.
We cannot infer failure rates for deployed products, real people, or other
memory architectures. Additional model checks use the same development journals.

The precise surviving research question concerns the gap between accurate
individual events and accurate aggregate histories. Generic positivity bias,
query-aware memory selection, and representative sampling all have prior work.
A paper needs a substantive empirical or technical contribution beyond these
observations, realistic memory implementations and appropriate workload controls.
