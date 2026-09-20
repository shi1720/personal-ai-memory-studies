# Independent implementation review of development scoring

This is an internal AI implementation review requested by the author. It is not external peer review, a new experiment, or validation of the truth of source labels. No real input archives, prepared cases, target labels, or model outputs were opened for this review.

## Reviewed scope

- `src/language_development_metrics.py` and its eight synthetic tests.
- `docs/language-development-protocol.md`.
- `src/language_precision_planning.py` and `docs/language-precision-planning.md`.
- The relevant validity fields in the newly written development runner, solely to check the scoring API boundary.

The eight scoring tests pass. A separate NumPy calculation on 60 invented users also agrees with the pure scorer for operational MAE and RMSE across all fourteen model conditions, all eight paired contrast arrays, and all common-valid subsets. The invented run constructs the full precision family. It is a test fixture, not a reported accuracy result.

## Mathematical findings

**No mathematical error found in the reviewed pure scoring implementation.**

1. User MAE is the mean of three absolute target errors. Aggregation averages users. Since every user has exactly three targets, this agrees with the pooled target mean while preserving the intended user-unit interpretation.
2. RMSE is the square root of average user MSE, not an average of user RMSE values. The test fixture explicitly distinguishes these quantities.
3. Pairwise concordance compares only unequal-rated target pairs. Prediction ties receive half credit, and all-equal target users receive no ordering score. Eligible users are averaged equally rather than allowing users with three unequal pairs to outweigh users with two. With three targets, this is necessarily a sparse, secondary diagnostic.
4. Invalid whole-pipeline cells are replaced with exactly `[3, 3, 3]` even if a numeric prediction vector is present. All users remain in operational summaries. Valid cells must contain finite, bounded, nonboolean numbers.
5. All eight native-minus-full and native-minus-same-writer-summary contrasts have the intended signs and writer-reader identities. Pairing follows one frozen case order across systems.
6. Common-valid means select the same users on both sides of each contrast and return `None` for an empty subset. These conditional summaries should remain descriptive; they do not eliminate validity-dependent selection.
7. The pure function deliberately supports small synthetic cohorts but calls the fixed precision planner only for exactly 60 cases. The real adapter must enforce the exact prepared 60-case set before calling it, as the label gate already does.
8. The precision planner consumes all eight arrays, uses paired user differences, and implements the prescribed adjusted normal half-width projection from an upper empirical bootstrap SD quantile. Neither the effect sign nor mean selects a contrast or a GO. The documentation correctly distinguishes this calculation from guaranteed interval coverage, statistical power, or scientific success.

## Concrete integration issue found

At review time, the runner's reader report contains two different meanings of validity:

- `reader_valid`: the reader stopped normally and passed the array parser.
- `pipeline_valid`: the reader is valid and every required writer is valid.
- The generic runner alias `valid` currently means `reader_valid`.

The pure scoring function's cell field `valid` instead requires whole-pipeline validity. Forwarding a runner row unchanged would therefore score a well-formatted sentinel-evidence answer after an invalid writer as a valid memory prediction. That would violate the protocol.

**Resolved in the analysis adapter.** `src/analyze_language_development.py` reparses native stores, summary outputs and reader responses, computes the conjunction itself, cross-checks the reported reader/pipeline flags, and passes only whole-pipeline validity to the pure scorer. The integration fixture supplies an invalid writer and a valid nonconstant reader response; operational scoring still uses `[3, 3, 3]`. Additional fixtures reject parseable token-limited outputs, untruthful validity flags, and missing or duplicate cells. All five adapter tests pass. This resolves the observed scoring hazard without changing the operational policy.

## Clarifications recommended before freezing the analysis adapter

1. **Resolved:** the protocol now defines secondary concordance, prediction ties, equal-target exclusions and ordering-eligible user counts. This documents existing behavior without introducing another primary hypothesis.
2. The adapter verifies the complete case grid and hashed provenance and recomputes writer/reader validity. The label materializer establishes source target order and the private artifact is bound to the exact completed inference report. These properties remain responsibilities of the surrounding adapter and provenance gates, not the pure numeric scorer. **Completed follow-up:** the adapter also compares `required_writer_valid` and `diagnostic_fallback_evidence` to recomputed writer validity, in addition to reader validity, pipeline validity and constant-fallback flags.
3. Preserve the fixed interpretation of precision GO. Uniform fallback can have low or zero estimated contrast dispersion and therefore pass a precision gate. That is mathematically consistent with the declared operational estimand, but does not certify useful generation or acceptable failure rates. Report writer/reader validity separately and do not describe precision GO as proof of operational quality. Any additional success-rate threshold would need an explicit prospective protocol decision rather than being added after observing outcomes.
4. The three reused resource-preflight users are legitimate members of the declared development set, not a separate validation set. Keep the generation-date and engineering-case-selection disclosure. Do not reuse these users as reserved confirmation evidence.

## Separate label-boundary correction

The original label materializer hashed every preparation input file, which would open reserved and donor input bytes despite never reading their rating fields. The root reviewer identified this stricter protocol issue. The materializer now selects only development-input and source-mapping hashes for verification and output provenance. A synthetic mapping fixture raises if a reserved or donor input digest is accessed. It also requires the label and scoring module hashes in the frozen inference manifest, alongside the protocol and precision-planning source. All seven label-boundary tests pass after that change. No real source archive was executed.

## Review outcome

The pure metrics and fixed planning calculation are internally consistent with the development design. The writer-versus-reader validity issue is resolved and tested. The final runner's writer/model aliases, path aliases, development case order, raw-file hashes and three stage-status fields match the label gate's contract.

A final manifest inspection found a separate pre-execution integration blocker: the runner dependency list initially omitted `src/language_development_labels.py`, `src/language_development_metrics.py` and `src/analyze_language_development.py`, whereas the label and scoring gates require those files to be pinned. **Resolved before execution:** direct follow-up source inspection confirms all three entries are now included. The runner also removed its ambiguous generic `valid` alias, retaining explicit `reader_valid` and `pipeline_valid` fields. No target labels or analysis were executed to identify or verify these corrections.

This review supports implementation readiness of the scoring boundary with the corrected dependency pins. It does not establish empirical findings, independent confirmation, conference-level novelty, or acceptance.
