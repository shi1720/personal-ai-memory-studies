# Internal review of prospective confirmation scoring

20 September 2026. AI internal code review and independent synthetic arithmetic
checks, not external peer review, observed-data validation, or a submission
readiness claim. No development or reserved targets, prepared inputs, saved
generations, or inference services were accessed.

## Verdict

No substantive numerical or protocol-integration blocker found in
`src/language_confirmation_metrics.py`. The pure scorer is suitable for inclusion
in the eventual frozen confirmation analysis, subject to the separate execution,
provenance, label-access, and whole-pipeline validity gates. This review does not
authorize reserved inference or establish that confirmation has been completed.

## Checks

- Exactly 200 distinct nonempty string IDs are required. Target and history
  mappings and all fourteen reader-condition mappings must cover precisely
  those IDs. Validation precedes bootstrap calculation.
- Three target ratings and twelve historical ratings per user are checked by
  the unchanged shared numerical validator. Invalid whole pipelines ignore any
  supplied diagnostic prediction and receive `[3, 3, 3]`; no user is removed
  from a primary contrast.
- Fourteen reader systems and the three numerical references produce 3,400
  user-system records. MAE and signed error average within users and then over
  users. RMSE is the square root of mean user MSE. Concordance averages within
  eligible users, with half credit for prediction ties, rather than pooling
  unequal-rating pairs across users.
- All eight native-minus-full and native-minus-same-writer-summary contrasts
  select the intended writer and reader axes. The supplied case sequence fixes
  pairing and bootstrap order; mapping insertion order does not affect results.
- The fixed confirmation uncertainty routine receives the complete eight
  all-user arrays. Its mean estimates are checked against the shared point
  scorer before interval integration. Development precision planning cannot
  run for this 200-user calculation. Only the adjusted interval supplies the
  direction label.
- Common-valid sensitivities report paired means and counts only. With no
  jointly valid pipelines, the mean is `None`, not zero; no interval or
  significance interpretation is added. They never replace all-user estimates.

## Independent invented-data tests

Added `tests/test_language_confirmation_metrics_independent.py`. Its reference
arithmetic uses `fractions.Fraction` and explicit comparisons, without importing
the primary point-metric functions. The fixture includes unequal numbers of
eligible target pairs, all-tied target users, mixed invalid pipelines,
deliberately unusable invalid-cell predictions, and an entirely invalid Phi
writer condition producing four empty common-valid comparisons.

The five tests independently check all 3,400 user-system metric rows, all
seventeen aggregate summaries, all eight paired arrays and their common-valid
counts/means, invariance to reversed mappings, absence of input mutation, and
rejection of a same-size mapping containing a substituted user identity. The
reference fixture produces a different pooled-pair concordance for some systems,
so it detects accidental replacement of user-macro weighting by pair weighting.

Results: all five added tests passed in 1.31 seconds; the eight existing scorer
tests separately passed in 0.70 seconds. Three complete production-sized joint
bootstrap calculations were performed across those suites, exclusively on
invented arrays. BLAS and OMP thread limits were set to one. The separate
uncertainty module already has its own independent frequency-weighted bootstrap
tests; this review checks its integration rather than claiming a new empirical
replication.

## Boundary to retain

The pure scorer necessarily trusts the caller's boolean `valid` as validity of
the entire writer-reader pipeline. Numeric predictions cannot establish writer
success, response provenance, split membership, target provenance, or completion
of inference. The docstring and output scope disclose this correctly. Those
properties must be re-established from immutable records by the future gated
adapter before any real confirmation analysis. No scorer or frozen source file
was modified during this review.
