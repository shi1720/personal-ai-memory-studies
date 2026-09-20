# Prospective uncertainty calculation for the language-rich extension

Specified on 20 September 2026 while development inference was running, before
development target ratings or reserved confirmation data were accessed. This
document fixes a numerical component, not a completed confirmation protocol or
an authorization to start reserved inference. The completed rating-prediction
paper and its frozen analyses remain unchanged.

## Estimand and input contract

The primary unit is a user. For each of the eight previously selected
writer-reader comparisons, compute the native pipeline's absolute prediction
error averaged over that user's three targets, minus the comparator's error
averaged over the same targets. Positive differences mean higher error for the
native pipeline. The comparator is either full history or the task-matched
summary from the same writer. Both Qwen and Phi are writers and readers.

Each contrast has exactly 200 paired differences in [-4, 4]. All eight arrays
must use the same frozen user order. Booleans, nonfinite values, unknown or
missing contrasts, and incorrect lengths are rejected before calculation.
The caller must establish user identity, complete inference, label provenance,
and correct whole-pipeline constant-3 fallback. A numerical function cannot
verify those facts from arrays alone. Invalid responses do not remove users.

The function uses no dataset, model, network, file, or random system state.
Its input contains only the complete supplied primary family. It exposes no
runtime override for sample size, family, seed, or interval level.

## Fixed paired-user bootstrap

Use 200,000 resamples of 200 users with replacement. A single NumPy PCG64
generator with seed 20260924 draws integer user indices. Each resample uses
the same indices for all eight contrasts, retaining their paired dependence.
Draw in batches of 1,000 without changing the random stream. Contrast columns
use lexicographically sorted canonical names; mapping insertion order has no
effect. Input user order is preserved, never sorted by observed error.
For numerical stability, subtract each contrast's first value before averaging
each resample and add it back afterward. This preserves a constant input
exactly, including at the direction-label tolerance. The reported observed
mean uses a compensated sum divided by 200.

For each contrast, report the mean of its 200 observed differences and the
linear-interpolated percentiles of its resampled means:

- Ordinary 95% interval: quantiles 0.025 and 0.975.
- Eight-comparison Bonferroni-adjusted 99.375% interval: quantiles 0.003125 and
  0.996875, corresponding to alpha 0.05 divided across eight comparisons.

Report all eight, including unfavorable, inconclusive, and degenerate results.
The adjusted intervals are the primary uncertainty summaries. Resampling the
600 ratings independently would change the sampling unit and is not allowed.
Do not average writer-reader cells into a new primary effect or interpret an
unplanned difference between contrasts as a confirmatory interaction.

For a descriptive direction label, use the adjusted interval only. Label
`native_higher_error` if its lower endpoint exceeds 1e-12 and
`native_lower_error` if its upper endpoint is below -1e-12. Otherwise label it
`inconclusive`. The numerical tolerance only protects against floating-point
noise around zero; it is not a practical-effect threshold. Preserve unrounded
endpoints in the machine-readable output. Neither the direction label nor a
zero-containing interval establishes equivalence or practical importance.

## Interpretation and limitations

These are approximate nonparametric percentile-bootstrap intervals. The
Bonferroni construction would control the family error if each marginal
interval attained its nominal coverage; this implementation does not prove
that finite-sample coverage. Shared indices preserve observed dependence but
do not make the coverage claim exact. Monte Carlo error remains, including at
the adjusted tail quantiles. The chosen resample count is fixed before results.

The sampling interpretation concerns comparable selected reviewers, subject to
the cohort's observational and selection limitations. Reviewers may not be
independent in the real world; resampling cannot remove that limitation,
catalog-timing uncertainty, or model pretraining contamination. A constant
observed difference produces a degenerate empirical interval, not proof that
the population variance is zero. Report validity and failures alongside error.

Common-valid sensitivities, if retained in the eventual full protocol, remain
descriptive and separate. They cannot replace all-user primary estimates or
change the eight-member family. This component intentionally does not select
or score a common-valid subset.

## Gates before use

All development stages must finish before development labels are materialized.
Primary development analysis and its separate computational verifier must
agree. Engineering integrity and the already frozen precision-planning gate
must both pass before any reserved inference. A NO_GO cannot be changed by
altering thresholds, dropping contrasts, or enlarging the fixed reserved sample
after observing development results.

The eventual full confirmation protocol must freeze source and input hashes,
model pins, all prompts, output parsing, fallback, ordering, transport handling,
analysis integration, and this module before the first reserved prediction.
This document and invented-array tests do not constitute empirical validation,
independent laboratory replication, peer review, or a conference-readiness
claim.
