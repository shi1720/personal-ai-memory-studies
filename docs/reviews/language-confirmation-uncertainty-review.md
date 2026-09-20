# Prospective confirmation uncertainty: bounded review

20 September 2026. Internal independent AI code and statistical-design review, using source inspection and invented arrays only. No private histories, target labels, development outcomes, reserved inputs, inference, or completed-paper analyses were accessed or modified.

## Verdict

No remaining substantive defect found in the reviewed numerical component. It implements the prospective eight-contrast specification after the output-contract correction below. This is not approval of a complete confirmation experiment or evidence of empirical coverage, independent laboratory replication, or publication readiness.

Reviewed `docs/language-confirmation-uncertainty.md`, `src/language_confirmation_uncertainty.py`, and its tests, with the provisional confirmation-design review and fixed precision-planning specification as context.

## Findings

* The estimand is consistently native minus comparator user-MAE, with all three targets averaged within each user. Positive values mean greater native-pipeline error. The resampling unit is 200 users, not 600 target ratings.
* One PCG64 index stream is shared across all eight contrast columns. Canonical column ordering and preserved user ordering are correct. Paired dependence is retained without treating writer-reader cells as independent replications or generating an unplanned interaction test.
* The ordinary and adjusted percentile levels are correct. An eight-member family at alpha 0.05 gives two adjusted tails of 0.003125. The document appropriately conditions the Bonferroni interpretation on approximate marginal coverage and does not claim an exact finite-sample guarantee.
* The specified seed, 200,000 resamples, batch size, interpolation, family, sample size, and direction tolerance are fixed before outcome access. No result-dependent interval or favorable-contrast selection is exposed. The precision-planning gate remains separate from effect direction and final uncertainty.
* Validation rejects incomplete families, incorrect dimensions or lengths, booleans, nonnumeric or nonfinite inputs, and values outside [-4, 4]. Input values are copied before calculation. No data-loading or inference path appears in the module.
* The initial implementation attached directional conclusions to ordinary intervals and used different label names from the specification. The author corrected this before final review: there is now one per-contrast direction, derived exclusively from adjusted endpoints, with the prescribed labels. Ordinary intervals contain only numeric endpoints. Centered summation preserves constant inputs at the tolerance boundary. I inspected the correction and reran the tests.

## Synthetic verification

All 10 isolated tests passed independently in 4.644 seconds. Checks include a separate frequency-weighted calculation with manually interpolated quantiles for all eight contrasts, shared-index affine relationships, mapping-order determinism, no mutation, constants and strict tolerance boundaries, malformed inputs, and rejection of runtime overrides. These validate implementation behavior on constructed inputs, not statistical coverage on the study population.

Command:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python3 -m unittest discover -s tests -p test_language_confirmation_uncertainty.py -v
```

## Remaining integration obligations

Numeric arrays cannot certify user identities, their common ordering, label provenance, complete inference, or correct whole-pipeline constant-3 fallback. The eventual scorer and independent verifier must establish these before calling the function. Failed responses must not remove users. Constant empirical differences can produce degenerate intervals without establishing zero population variance. Zero-containing intervals do not establish equivalence, and the direction tolerance is not a meaningful-effect threshold. The specification already states these boundaries.

Reviewed SHA256 values:

```text
41073544b2dcb61088b6a8a98567afa33ce2acf5fa4cec1187dc8bfeed7dff7a  docs/language-confirmation-uncertainty.md
b58e7ec3e5c3e2cc5dd1083816a93e924eb5fa763c06615596927a2bd0e1ca34  src/language_confirmation_uncertainty.py
64992b7e973329b3d703d5e98fb41e89cc6e5c174729fcbf8340ac6e694a4dc4  tests/test_language_confirmation_uncertainty.py
```
