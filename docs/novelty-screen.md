# Novelty screening, 2026-09-19

This is a working screen, not an exhaustive systematic review. An overlap finding
is a reason to narrow or abandon a claim, not a claim that a field is solved.
Evidence levels and unresolved primary-source leads are in `screening.json`.

| Candidate claim | Closest work | Decision |
| --- | --- | --- |
| Temporal lifegraph with evolving user beliefs | TSM; DCPM | Reject as standalone novelty. |
| Clarification detects genuine preference drift | PAHF; CAPTURE lead | Too close; no method selected. |
| Provenance avoids counting repeated evidence as independent support | CAMA; origin-bound authority | Reject generic corroboration claim. |
| Asynchronous memory needs transactional commit and cascading repair | MemTX; DCPM | Reject generic transaction proposal. |
| Consolidation can make useful memories harmful | Zhang et al., revised August 2026 | Established failure, not our discovery. |
| Preserve sources so a compressed memory remains correctable | Reclaim evaluation repository | Direct overlap lead; inspect before proposing. |
| Adaptive minimal personalized context | ENOUGH | Reject broad selection/stopping claim. |
| Evaluate personal agents under changes in user state | Qian et al. temporal interventions | Existing framing. Any contribution needs a new technical result or substantial validated study. |
| Reduce calibration calls by batching or adaptive evaluation | BB-CRC; Active Testing; PPAT; BARGAIN | Reject this broad novelty claim. Exact full-reference recovery failed Pilot 002: limited strict-risk savings and near-total abstention. |
| Query uncertain rows until a threshold is determined | Stochastic Score Classification | Established query-evaluation principle. A simple interval certificate is insufficient for the requested contribution. |

## Remaining questions, not novelty claims

1. **Revision-sensitive compression.** Can a representation preserve the ability
   to recompute decisions after changes under a strict storage budget? Compare
   source retention, replay, dependency tracking and task-aware compression.
   Kill if the only result is that retaining evidence beats discarding it, or
   if published correction-sensitive compression already supplies the method.
2. **Evidence sensitivity of personal-memory evaluation.** Can a matched
   intervention distinguish dependence on user evidence from generic response
   quality? Existing causal and personalization benchmarks must be audited first.
   Kill if a prior protocol already measures the same estimand, unless there is
   a substantial generalizable new result supported across datasets and models.
3. **Reliability under memory lifecycle shifts.** Can a calibrated policy retain
   its reliability after memory is revised or compacted? Compare ordinary
   recalibration, selective prediction and online risk-control methods. Kill if
   standard calibration or retraining achieves the same cost-reliability curve.

   More specific subquestion for the next screen: after a retrieval index changes,
   can valid calibration results be reused for unaffected queries, with conservative
   bounds for unresolved queries, at substantially lower cost than full recalibration?
   Dynamic conformal inference, selective prediction, incremental computation and
   retrieval cache invalidation are required comparisons. Merely caching unchanged
   prompts is not a sufficient contribution. Any guarantee must state whether the
   memory update is independent of calibration labels and test queries. Adaptive
   user feedback can violate that condition; it must not be hidden in the theorem.

No candidate has passed the selection gates yet. Do not give the manuscript a
novel-method title or write a results section before the evidence exists.

## Closed feasibility gate

Pilot 002 is complete. The current unrestricted-interval candidate is rejected
as the main contribution. See `pilot-002-results.md` for complete measurements.
All outputs and the negative decision are preserved.

The next broad candidate, exposure-aware preference memory, has a direct overlap
with CALMRec (arXiv 2607.23647, primary methods inspected). It is also rejected as
a standalone novelty claim. Any narrower retention-selection study must compare
with classical survey sampling and avoid claiming importance weighting as new.

## Initial audit

Inspect benchmark construction, evidence fields, history overlap, valid sampling
units, scoring conventions and licensing. Never feed evidence labels, answers or
question-specific identifiers to a purported ordinary retrieval baseline.
Establish data integrity before interpreting performance differences.


## Retention audit gate

Pilot 003 is complete across three local model families. It exposes sensitivity
to instructions and presentation, but does not support a universal positivity
bias or failure of proportional-retention prompting. See `pilot-003-results.md`.
Generic content-biased retention is established prior work; a new sampling
method has not been demonstrated. Native memory-interface and downstream-reader
tests are the next practical-validity gate, not a claim of conference readiness.

Pilot 004's first-model test is now complete: the unrestricted exported prompt
retains all correct source outcomes in the small journal set, with some added
contradictions; larger-budget reader accuracy matches full history. The second
model remains in progress. Source tracing also found that the exported prompt
is not on Mem0's active extraction path at the pinned revision. This test cannot
be used to pass a native-pipeline external-validity gate. The correction is
recorded separately from immutable experimental manifests.

AgingBench already offers stage interventions for write, retrieval and
utilization failures. CICL already studies decision-sensitive memory utility.
These are additional overlap constraints, not claims that either system has
been reproduced. Any next candidate still needs a precise unaddressed result.

Pilot 004 is now complete across both models and both budgets, with separate
strict and exact-option analyses. Its unmodified exported prompt shows no net
frequency-answer degradation in either model. The forced-selection direction
is not being promoted to the main contribution. Source inaccuracies remain
documented, but do not by themselves establish a new memory method or a failure
of the active pipeline. See `pilot-004-results.md` for the completed gate.

## Observed-history personalization overlap

MemoryCD (2603.25973) directly evaluates memory methods on rating prediction
from real user histories. MAP (2505.03824) already uses structured rating tables
and relevant-history retrieval. Primary task/method sections were inspected;
reading depths are recorded in screening.json. Thus, neither replacing synthetic
journals with ratings nor adding a structured recommendation memory is enough
for the requested contribution. The ongoing Coat development run is a controlled
feasibility screen, not a claim to introduce this task. Randomly elicited Coat
targets differ from self-selected review histories, but that sampling distinction
and propensity methods are themselves established by Schnabel et al. (2016).
