# Working technical note: partial recalibration after memory changes

Author of this working analysis: Shivam Gupta.

Status: candidate method and correctness argument. Novelty and empirical utility
are unestablished. This is not a completed conference paper.

## Problem and scope

A frozen reader uses a mutable personal-memory context. A memory update changes
some prompts and therefore can change both predictions and confidence scores.
Reusing old calibration losses for changed prompts is generally unsound. Fully
recomputing them is correct under the usual calibration assumptions but may be
expensive. Exact caching avoids calls for unchanged inputs; our candidate must
offer something beyond that baseline.

Fix an ordered policy grid t_1 < ... < t_m, where larger indices mean more
abstention. A reader produces a label a_i and scalar confidence c_i on example i.
Define the shipped-error loss

    L_i(j) = 1[a_i != y_i] * 1[c_i >= t_j].

The final policy always abstains, so L_i(m)=0. Each row is bounded in [0,1] and
non-increasing in j. This controls the marginal frequency of wrong answers that
are sent, NOT the error rate conditional on sending an answer. Always report
answer coverage and conditional error separately to expose vacuous solutions.

Let L_i'(j) be the loss under the updated memory. A valid cache certificate
identifies cases with unchanged *complete* inference and scoring inputs: exact
rendered prompt, model and tokenizer revisions, decoding randomness/configuration,
label semantics, and scoring code. Matching a retrieved document ID is insufficient.
Changed answer labels invalidate cached scores even if the prompt is unchanged.

## Full reference and partial bounds

For n calibration examples, the full CRC reference selects the smallest j with

    (sum_i L_i'(j) + 1) / (n+1) <= alpha.

If no such j exists, use the known zero-loss always-abstain policy. This is an
application of conformal risk control [1], not a new calibration theorem.

Maintain lower and upper loss bounds l_i(j) <= L_i'(j) <= u_i(j). Reused or
recomputed rows are exact. Otherwise use [0,1], except for the known zero final
column. Select j_U using the upper losses in the same CRC expression. Define
j_L analogously using lower losses.

**Dominance lemma.** For every realized calibration sample and every valid bound
matrix, j_L <= j_full <= j_U. Consequently, for every test example and any
non-increasing test loss, L_test(j_U) <= L_test(j_full). The statement remains true
when rows are recomputed in an adaptive order or evaluation stops adaptively.

**Proof.** For every column, the lower corrected empirical loss is no larger than
the exact corrected empirical loss, which is no larger than the upper corrected
empirical loss. Every upper-feasible index is therefore exact-feasible; every
exact-feasible index is lower-feasible. Taking the minimum feasible index gives
the sandwich. The common final fallback preserves the order. Monotonicity of the
test loss proves pointwise dominance. The argument holds for each realized valid
bound matrix and thus for any sequence of bound-tightening operations. QED.

If j_L=j_U, the partial procedure recovers exactly the full-reference policy
without requiring the remaining rows. This is a deterministic certificate, not
a probability statement about the correctness of the unevaluated predictions.

Under the assumptions of the full CRC theorem, taking expectations transfers
its marginal risk guarantee to j_U. The dominance argument itself does not need
exchangeability; the population-risk interpretation does. This distinction is
essential. We claim no calibration validity under arbitrary adaptive memory
updates that depend on calibration labels or test outcomes.

## Candidate computation policy

Start with exact cached rows and conservative intervals for the remainder. At
each step, compare j_L and j_U. Recompute a row whose interval is open at j_L,
then update both thresholds. Stop when they agree, a compute budget is reached,
or a predeclared policy is certified. Under a budget, return j_U.

The initial implementation uses deterministic ties. Other orders, including
random selection and prediction of the likelihood of a changed error, must be
compared. A learned ordering would use development data only. Recomputing one
reader output resolves its entire policy-loss row.

## Why this might fail as a research direction

- The dominance lemma is elementary. It must not be presented as a major new
  theorem. Prior work on partial calibration, safe screening, active testing and
  lazy evaluation may already imply the entire method.
- If changed prompts are rare, exact caching may capture nearly all savings.
- If thresholds lie near the empirical boundary, the certificate may need nearly
  every changed row. A positive result on only hand-picked changes is inadequate.
- Conservative bounds may save computation only by abstaining much more often.
- Certifying marginal shipped-error risk can mask poor selective accuracy.
- Small datasets or dependent persona queries do not justify user-level coverage.
- Quantized local models are a pilot resource, not a substitute for model diversity.

## A computation barrier for uninformative intervals

This is an elementary certificate-complexity observation, not an established
novel contribution. Let losses be binary and let
`K = floor(alpha * (n+1) - 1) >= 0`. For any policy other than the forced-zero
final policy, an unevaluated row has upper loss one. If `z` rows are known to
have zero loss at that policy, its worst-case total loss is `n-z`. Therefore
certifying its feasibility requires at least `n-K` known zero-loss rows.

If a cache contains `c0` such zeros and `c1` ones, at least
`max(0, n-K-c0)` additional rows must be evaluated. Compared with recomputing all
`n-c0-c1` uncached rows, at most `K-c1` calls can be avoided when this expression
is nonnegative. The bound applies to an exact certificate that uses no additional
restriction on unknown rows. It does not apply to a probabilistic certificate,
tighter valid stability bounds, or returning the always-abstain policy.

The same requirement follows by indistinguishability: if fewer zeros have been
observed, completing all unknown rows as ones at the chosen non-final policy
produces a compatible monotone loss table where that policy is infeasible.
Thus no adaptively chosen ordering can evade the barrier in this information
model. This is not an impossibility result for all risk-control methods.

For an interior exact-reference policy `j`, one also needs at least `K+1` known
ones at `j-1` to rule out its immediate predecessor. Monotonicity then rules out
all earlier policies. These two conditions are necessary and sufficient. For
an *oracle diagnostic* with access to all new rows, let `a` be the remaining
zero witnesses needed at `j`, `b` the remaining one witnesses needed at `j-1`,
and `d` the number of uncached rows with `(L(j-1), L(j)) = (1,0)`. The smallest
certificate uses `max(a, b, a+b-d)` additional rows. A row of type `(1,0)` can
meet both requirements; the other two types meet at most one. This proves the
lower bound, and selecting up to `min(a,b,d)` dual witnesses followed by the
remaining single witnesses achieves it. Endpoints omit the absent constraint.
The oracle is not an implementable acquisition baseline and its cost must be
labelled accordingly.

With 64 calibration rows and no cache, the first bound alone requires 62, 59,
52, and 46 evaluations at alpha 0.05, 0.10, 0.20, and 0.30 respectively for any
non-final certificate. These are algebraic predictions, not measured results.

## Required experiment

Use public personalized-response tasks with objective answer labels. Separate
personas across development, calibration and held-out evaluation. Replay explicit
memory availability changes with fixed labels. Evaluate native preference changes
separately, because their label semantics can change too. Keep masks independent
of labels. Benchmark full recalibration, stale reuse, exact caching, conservative
partial random order, and the candidate ordering at equal reader budgets.

Measure risk, answer coverage, conditional error, exact-policy recovery, actual
reader calls and token/latency cost. Reuse fully computed new rows only as an
offline oracle when replaying partial schedules, and label that experiment as
offline trace replay. A live partial run must confirm the claimed avoided calls.

## Primary sources and closest work

[1] Angelopoulos et al. Conformal Risk Control. ICLR 2024; arXiv:2208.02814.
https://arxiv.org/abs/2208.02814

[2] Kang et al. C-RAG: Certified Generation Risks for Retrieval-Augmented Language
Models. ICML 2024. https://arxiv.org/abs/2402.03181

[3] Opoku and Banahene. ToolChain-CRC: Conformal Risk Control for Agentic AI Under
Retrieval and Tool-Use Drift. Preprint. https://arxiv.org/abs/2606.18467

[4] Kotte. When Can Conformal Risk Control Certify LLM Outputs? Bounds,
Impossibility, and Adaptation for Structured Generation. Preprint, v2.
https://arxiv.org/abs/2606.29054

[5] Liang, Zhou and Sesia. Conformal Inference is (almost) Free for Neural Networks
Trained with Early Stopping. ICML 2023.
https://proceedings.mlr.press/v202/liang23i.html

Reading status: [1] v4 sections 1.1 and 2.1, theorem and proof inspected; [3]
sections 3-5 and reproducibility statements inspected; [4] section 2 inspected.
Other references have only an abstract-level screen. Full closest-method review
remains necessary. No absence of overlap is inferred from a search term failing
to appear. On the finite policy grid, the CRC argument can be applied directly
to the ordered indices; no continuity of the confidence distribution is assumed.
