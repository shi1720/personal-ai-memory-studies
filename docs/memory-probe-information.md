# What can a memory-only probe measure?

Research note, 2026-09-19. Elementary analysis and an exploratory transfer
protocol. No new theorem, empirical failure rate or publication-readiness claim.

## A precise channel distinction

Let S be a latent task state, H an observed history, M its compressed memory,
Q a fixed task probe, and Y the response. A fixed reader with no access to H,
tools, hidden state or case-specific weights generates Y from a kernel K(Y|M,Q).
Its fresh randomness is independent of S conditional on M,Q. Hence

    P(S,Y | M,Q) = P(S | M,Q) K(Y | M,Q)
    I(S;Y | M,Q) = 0.

This does not say Y is uninformative about S. Unconditional dependence can be
positive because M carries information from H. It says a probe cannot add
independent evidence beyond its inputs. If the reader also sees original
evidence or obtains a new observation, the conditional-independence premise
changes. Model priors can help interpret M but do not remove the stated Markov
property for a fixed kernel.

Consequently the valid chain-rule identity

    H(Y | M,Q) = H(Y | M,Q,S) + I(Y;S | M,Q)

has a zero second term under this implementation. A nonzero residual term would
require a different joint model, such as a state-dependent oracle response, and
an explicit bridge from that oracle to the implemented reader. Token entropy can
still be empirically predictive of memory quality; this identity alone does not
establish that relationship.

## Exact examples and their limits

The script `src/memory_probe_information.py` uses a fair binary state. Half the
time memory retains the state; otherwise it erases it. A fixed reader is 90%
accurate on the retained state, while on erasure it returns zero with probability
0.99 independently of the state. The low-entropy response is therefore the worse
one. Exact enumeration gives:

| Memory | State uncertainty given memory, bits | Response entropy, bits | Response error |
| --- | ---: | ---: | ---: |
| State retained | 0 | 0.468996 | 0.10 |
| State erased | 1 | 0.080793 | 0.50 |

Unconditional state-response mutual information is positive (0.168398 bits),
but the conditional term is zero up to floating-point precision. A second
example uses a deterministic reader: both response entropies are zero although
one memory retains the state and the other does not. Five tests check these
facts, a 25-channel parameter grid, and a positive control where a genuine
state observation makes conditional mutual information nonzero.

These are constructed mathematical counterexamples to an unrestricted ranking
claim. They are not measurements of an LLM, nor evidence that a particular
training algorithm fails. The conditional-independence identity is standard.

## Closest method and fair interpretation

[MMPO](https://arxiv.org/html/2605.30159v1) uses a progress-and-gap probe, computes
mean token entropy, and combines it with terminal reward. Its Appendix C gives
a conditional-information argument. Under the memory-only response channel
above, the residual term vanishes. Its extra response-stability assumptions
therefore require empirical support; relevance alone does not establish ranking.
The paper already warns about premature confidence, reports an inferior direct
answer probe, and states limitations. Our analysis does not refute its reported
training gains. Reading: Sections 2.2-2.3, displayed reward construction, 4.3,
Appendices B-C, E-F and limitations. No trained MMPO checkpoint was run.

[SafeCommit](https://arxiv.org/html/2608.04289v1) already frames action release
using plausible states and explicitly separates missing-state representation
error from calibration. Its controlled simulator is not claimed as a deployed
LLM evaluation. A generic act/probe/defer policy is not our contribution.
Reading: problem and certificate definitions, conditional guarantee, scope,
Section 5 and displayed appendix statements. Its repository README was read;
no code was executed. Observed revision: `146708eba8d6c768544330d20ed98047a3cc73dc`.

Source-dependent factual evaluation is also established. [QAFactEval](https://arxiv.org/abs/2112.08542)
and [QuestEval](https://arxiv.org/abs/2103.12693) are mandatory comparisons for
any proposal to judge a summary against its source. Only their primary abstracts
and repository descriptions have been read at this stage. Ordinary KL
distillation is not a new method either; [Latent Context Compilation](https://arxiv.org/abs/2602.21221)
is a related primary-abstract lead requiring a methods read.

## Bounded empirical screen, fixed before probe outputs

Rather than constructing another favorable synthetic task, reuse every valid
writer output from Pilot 004, whose source audits and downstream answers are
already public within this local research record. This is explicitly post hoc
development analysis, not independent confirmation. No claim of causal
identification or trained-method reproduction is planned.

For each model, score all 24 scheduled writer cases plus twelve full-history
controls. Invalid writers produce blocked placeholders, not repaired summaries.
Use the same base model family as the writer and the recorded frequency question
without its answer or choices. Ask the published progress-and-gap probe using
an otherwise fixed, locally specified wrapper. The probe is not told which
context type it receives. Qwen has 36 calls; Phi has 33 calls and three blocked
placeholders. There are 72 scheduled records and 69 actual calls in total.

Use full-vocabulary token entropy in nats along a greedy response, computed from
float32 logits before normalization. This is distinct from entropy of the greedy
decoding policy, which is degenerate. Exclude terminal EOS from the score. Save
each token's entropy and selected-token NLL, the complete prompt/output,
completion reason, timings, versions and dependency hashes. Do not equate this
mean with exact sequence entropy. Use a 256-token output limit and 4,096-token
input limit; reject oversized input without truncating it.

Primary score: mean over all non-EOS tokens of a completed response. Empty or
truncated outputs have no primary score. A predeclared length diagnostic uses
the first 32 non-EOS tokens when available, including truncated responses, with
its smaller comparison population stated. Do not silently rerun only failures
at a larger budget.

For the two valid writer candidates within a journal, compare the lower-entropy
choice with always using the unmodified exported-prompt output and with uniform
random selection's exact expected score. Resolve exact entropy ties equally.
Use both previously recorded strict and exact-option downstream results;
report missingness and selection cost. Separate the twelve journal units from
the multiple contexts, and show every pair rather than treating contexts as
independent users. Source-audit associations are descriptive because the audit
grammars differ by model. Full history is a diagnostic, not a zero-cost competitor.

This test can establish feasibility of a more substantial study only if there
is a useful, reproducible discrepancy. Even a positive result will need fresh
natural histories, more capable models, fidelity baselines, stronger statistical
power and a nontrivial corrective method before it supports the requested paper.

## Reproduce the analytic check

```sh
python3 -m unittest discover -s tests -p 'test_memory_probe_information.py' -v
python3 src/memory_probe_information.py
```
