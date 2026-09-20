# Prospective confirmation scoring component

Prepared on 20 September 2026 during development inference, before development
target ratings or reserved confirmation inputs were accessed. This is a pure
calculation component with invented-array tests. It is not an empirical result,
a completed confirmation protocol, or permission to start reserved inference.

## Fixed numerical contract

`src/language_confirmation_metrics.py` exposes `score_confirmation(cases,
targets, histories, cells)`. It accepts exactly 200 distinct nonempty string
case identifiers in a fixed common order, exactly three target ratings and
twelve historical ratings per user, and all fourteen reader-condition cells
per user. Ratings and valid predictions must be finite real nonboolean numbers
in [1, 5]. Cell validity must be a boolean, not a numeric proxy.

The fourteen model systems cross two readers with seven evidence conditions:
no history, full history, Qwen native memory, Qwen task summary, Phi native
memory, Phi task summary, and BM25-selected history. History mean, history
median and constant three give three additional descriptive references. All
17 systems retain all 200 users, producing 3,400 user-system metric records.

The caller must independently establish complete inference, split membership,
source and label hashes, output parsing, and validity of both the required
writer and reader. The scorer cannot establish these from arrays. In particular,
a valid sentinel-evidence reader after an invalid writer is still an invalid
whole pipeline. Every invalid pipeline receives [3, 3, 3] for primary accuracy,
even if its supplied diagnostic predictions would be accurate. No response is
repaired or removed from the all-user calculation.

Point metrics deliberately reuse the frozen development metric definitions:
per-user MAE, MSE, signed error and unequal-target-pair concordance, followed by
equal-user averaging. RMSE is the square root of mean user MSE, not the mean
of user RMSE. Exact prediction ties receive half credit; users with no unequal
target pairs remain in accuracy calculations and are excluded only from
concordance. Report their eligibility count. Shared code preserves definitions
but is not itself an independent numerical check.

## Contrasts and uncertainty

The primary family is exactly eight native-minus-comparator paired user-MAE
contrasts: native versus full history and native versus the same writer's
summary, for every writer-reader combination. All arrays preserve the supplied
common user order. Positive values mean greater error under native memory.

The separately specified `bootstrap_confirmation` component supplies 200,000
joint paired-user resamples, seed 20260924, ordinary 95% and Bonferroni-adjusted
99.375% percentile intervals. See
[`language-confirmation-uncertainty.md`](language-confirmation-uncertainty.md)
for the exact random stream, interpolation, direction rule and limitations.
The scorer checks agreement between the point and bootstrap-input means.
It does not run development precision planning or offer an option to change
the sample size, family, fallback or uncertainty settings.

Each contrast also reports the number of users with valid pipelines on both
sides and their paired mean difference. This common-valid sensitivity is
descriptive only: no extra interval, p-value or significance label. It cannot
replace the all-user result. An empty common-valid subset yields count zero
and a null mean, not a zero effect. Different subsets can represent different
populations and are not automatically comparable across configurations.

## Evidence and use boundary

Tests cover complete-grid accounting, hand-calculated error and concordance,
invalid-writer fallback despite valid diagnostic predictions, writer-reader
indexing, numerical references, user ordering, rejected malformed inputs and
unchanged caller data. The uncertainty module has separate numerical tests.
All fixtures are invented. No reported test value is a research finding.

The output's `calculation_complete` flag means the supplied arrays were fully
processed. It intentionally does not claim the inference experiment completed.
Actual use requires development integrity and the frozen precision gate to
pass, a complete reviewed and publicly frozen confirmation protocol, verified
reserved inference, gated label materialization and a separate result verifier.
Those integration steps are not provided by this module.
