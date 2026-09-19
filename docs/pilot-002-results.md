# Pilot 002: result and stopping decision

Shivam Gupta. Development study completed 2026-09-19.

## Decision

Stop the current unrestricted-interval partial-recalibration method as a candidate
for the paper's main contribution. Its correctness is supported, but this pilot
shows neither useful selective prediction nor a compelling computational saving
at strict risk targets. No ICML-level novelty or readiness claim is warranted.

The negative result is retained. It does not prove that all partial, approximate,
or prediction-powered recalibration methods fail, nor that memory is useless.

## Completed experiment

The frozen protocol used 128 distinct PersonaMem-v2 personas, split 64/64 into
calibration and evaluation development groups. A pinned community-quantized
Qwen3-4B-Instruct-2507 reader answered shuffled four-option questions with a
3,072-token total prompt limit. A deterministic mask removed approximately 25%
of conversation blocks before retrieval. This models memory availability loss,
not a change in the user's underlying preferences. Labels remained fixed.

The full run made 256 reader calls. Recorded reader time sums to 1,370.11 seconds
(22.84 minutes), excluding model loading and input preparation. This is not total
wall time or a measured partial-run speedup. All prompts changed, so exact input
caching saved zero calls. Outputs, code identities and data/model checksums were
validated before analysis.

The run had one schema interruption. A role-only assistant record contained no
text. The exact repair and proof that completed prompts were unchanged are in
`pilot-002-amendment.md`. All 128 originally selected examples were retained.
Earlier low-precision normalization diagnostics are separately archived and were
not included in the analysis.

## Measured outcomes

| Quantity | Calibration, n=64 | Evaluation, n=64 |
| --- | ---: | ---: |
| Original correct answers | 18 | 22 |
| Changed-memory correct answers | 17 | 22 |
| Changed predicted options | 12 | 10 |
| Correct to wrong | 4 | 4 |
| Wrong to correct | 3 | 4 |

Changed-memory evaluation accuracy without abstention was 22/64, or 34.375%.
This is a custom short-context, constrained-choice pilot. It is not an official
benchmark score or a reproduction of the model's published performance. No
no-memory or stronger-reader ablation has been run, so this result does not
establish a benefit from memory or identify the cause of poor answer quality.

| Marginal risk target | Exact-cache baseline calls | Fixed-order exact recovery | Random-order mean, range | Oracle minimum |
| --- | ---: | ---: | ---: | ---: |
| 0.05 | 64 | 62 | 62, 62-62 | 62 |
| 0.10 | 64 | 59 | 59, 59-59 | 59 |
| 0.20 | 64 | 52 | 52, 52-52 | 52 |
| 0.30 | 64 | 46 | 46.14, 46-48 | 46 |

Random-order results cover 100 permutations of the same calibration table. The
ranges are not confidence intervals or independent experimental replications.
The oracle uses all hidden new outputs to compute the smallest possible
certificate. It cannot be used as an online acquisition algorithm.

At alpha=0.05, saving 2/64 calls is a 3.125% counterfactual call reduction. At
alpha=0.10, it is 5/64, or 7.8125%. These are offline trace-replay counts.

All four full recalibration settings chose confidence threshold 1.0. They
accepted zero calibration answers and one evaluation answer. That evaluation
answer was wrong. Thus coverage was 1.5625%, marginal wrong-and-answered risk
was 1.5625%, and conditional error among answered queries was 100% (one query).
This small conditional-error count is descriptive, not a population estimate.
Low marginal risk here came from near-total abstention, not reliable answers.

Stale calibration selected the same threshold and evaluation behavior at every
alpha. This pilot therefore does not demonstrate a benefit of recalibration over
stale reuse. Stale reuse remains generally uncertified after input changes; the
absence of a failure in this slice is not proof of its safety.

## Theory and grid diagnostic

For n rows and integer CRC loss budget K, certifying a non-final policy with
uninformative unknown losses requires n-K known zero-loss rows. This predicts
minimum counts of 62, 59, 52 and 46 here. The measured fixed-order counts meet
these limits. Altering the query order cannot break this information barrier.

The separate grid-resolution note derives the oracle certificate formula,
proves that a singleton loss boundary requires every uncached row, and shows
that nested grid refinement cannot reduce the minimum exact certificate size.
These are elementary decision-certificate arguments. Their novelty has not been
established, and they are not being presented as a new general calibration theory.

A post-protocol replay refined the fixed grid from 18 to 483 policies. Every
setting still chose threshold 1.0, with unchanged coverage and oracle cost. The
boundary crossing count fell from 29 to 19, but did not reach one. Thus the
real-model trace does not empirically instantiate the singleton-boundary case.
That result has exhaustive small-instance checks, not a claimed real-data effect.

## Verification and limitations

Thirty tests passed, including exhaustive binary monotone tables, cache subsets,
certificate costs and grid refinements. Every replayed conservative policy
satisfied the pointwise dominance check, and every full-budget schedule recovered
the reference policy. Dataset identities, labels, model files, code dependencies,
probability normalization, token budgets and exact-cache matches were checked.

This is one quantized model, one small synthetic-persona development slice, one
availability mask, and a restricted response protocol. There is no independent
confirmatory study, user-level guarantee, human-subjects evaluation, live partial
latency measurement, or comparison with strong published memory systems.
Population CRC guarantees additionally require the full reference's statistical
assumptions; the deterministic dominance check alone does not establish them.

## Research implication

Do not enlarge this experiment simply to obtain more rows for a weak method.
A future recalibration direction needs a concrete information source that yields
tighter valid bounds, or a clearly stated probabilistic/approximate target with
comparison against existing methods. Generic proxy-assisted risk estimation is
already covered by close prior work. An alternative memory research question
must pass its own novelty and baseline checks before a full study begins.

## Artifacts

- `results/pilot-002-predictions.jsonl`: all 128 paired predictions.
- `results/pilot-002-run-manifest.json`: model-run dependency hashes.
- `results/pilot-002-analysis.json`: full baseline and replay measurements.
- `results/pilot-002-grid-resolution.json`: post-protocol grid diagnostic.
- `results/figures/pilot-002-recalibration.png`: plot from the recorded analysis.
- `docs/closest-work-comparison.md`: current overlap assessment.
