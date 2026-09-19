# Alternative-direction screen

2026-09-19. No new candidate is selected or claimed novel.

A possible question is whether persistent assistant memory mistakes user behavior
caused by the assistant's own earlier recommendations for independently expressed
preferences. This is distinct from simply repeating an assistant's generated
text as a remembered user statement. For example, a user tries a recommended
activity because it was the only offered option, then the system stores that
choice as strong evidence of an intrinsic preference and narrows future options.

The broad phenomenon is established in performative prediction, recommendation
feedback loops and personalization-sycophancy discussions. Primary sources added
to the screening matrix include Eilat and Rosenfeld (ICML 2023), Wang et al.
(arXiv 2601.05184), and Tolety et al.'s 2025 position paper. Only abstracts have
been read for this branch; no novelty conclusion follows.

A viable gap would need a precise intervention and identification target, such as
recovering a stable preference under logged exposure policies with known support,
and a demonstrated failure not resolved by standard propensity weighting,
contextual bandits or explicit source provenance. The commercial application
would be a personal or enterprise assistant whose choices do not become
self-confirming evidence. Human preferences need not be stable, so a simulation
must not be described as proof of real users' intrinsic preferences.

Before any implementation: inspect the closest methods, formalize what is
observable, and test whether a simple propensity-aware baseline solves the whole
problem. Do not introduce an LLM wrapper around a known causal estimator and
call it a new algorithm. A carefully validated empirical failure might be a
contribution, but it requires stronger evidence than a generated toy example.

## Pilot 003: retention distributions, current assessment

A custom writer can retain only true events while corrupting the empirical
frequency of experiences. Qwen3 and Mistral development runs show different
signed biases, so a universal positivity narrative is already unsupported.
Representation and instruction sensitivity remain measurable. All three model checks are complete under `pilot-003-replication.md`; they reuse
the same development data. Results are in `pilot-003-results.md`.

This alone is not a strong ICML contribution. Content-biased transmission through
LLM summaries was studied by Acerbi and Stubbersfield (PNAS 2023). RUMS already
optimizes query-conditioned memory selection through response entropy. DAM-LLM
already stores and updates affective confidence distributions. Classical
sampling, stratification and count ledgers predate all of these systems.
The distinction under investigation is aggregate-history fidelity under
query-agnostic retention, not a discovery that summaries can be selective.

Before scaling a custom benchmark, test whether the effect survives an authentic
memory extraction interface and affects downstream personalization relative to
full history. The inspected pinned Mem0 extraction prompt asks for likes AND
dislikes and has no six-event cap. It must not be represented by our custom
selection prompt. A prompt-component test must be called that, not an end-to-end
Mem0 reproduction; a full reproduction additionally requires retrieval, updates,
embedding configuration and the native memory pipeline. Any follow-up must
separate factual misstatement, omitted evidence, missing count information and
reader arithmetic errors. Missing information is not necessarily a false claim.

Follow-up implemented in Pilot 004: new fixed fictional journals with balanced
positive/negative base rates and independently assigned incidental detail;
full-history versus extracted-memory readers on objective frequency rankings;
separate event-recall and aggregate queries. Cheap rate-preserving summaries
and sampling controls are mandatory. No new method or acceptance claim is
justified until this external-validity gate and a narrower contribution succeed.
Both model checks are complete and do not show net frequency-answer degradation
for the unmodified exported prompt under the larger reader budget. Source-path
inspection also showed that this is not the pinned revision's active extraction
prompt. The completed report and source correction are in the Pilot 004 records.

## Memory-confidence follow-up: completed development check

The frozen 69-call probe and analytic controls are documented in
`memory-probe-results.md` and `memory-probe-interpretation.md`. The completed-
response comparison has no eligible candidate pairs under the fixed budget.
The predeclared prefix diagnostic matches the fixed baseline, with essentially
no candidate discrimination available in Qwen and only two correctness-
discordant Phi pairs after exact-option scoring. Source-audit examples show
both favorable and unfavorable selections.

Do not treat a low-entropy hallucination or an elementary conditional-
independence identity as a new main-conference contribution. The posterior-
sampling positive control also shows that entropy can faithfully represent
uncertainty under the right calibration assumptions. No trained MMPO baseline
has been reproduced, and its empirical results are not refuted here.

Before additional inference on this branch, identify a substantive unresolved
question and a dataset with enough meaningful candidate variation. Run a
separate preflight for response length, then freeze the actual comparison.
Increasing the budget on these same twelve journals alone cannot establish
a general selection benefit. Source-conditioned QA verification already has
substantive baselines in QAFactEval and QuestEval.

## Gate target versus reference target

`gated-memory-estimand.md` documents a narrower exact check: even with known
propensities, a normalized gated memory estimates a gate-weighted quantity unless
the reference covariance of gate and evidence is zero. This is elementary
selection algebra, not new importance weighting. It does not dispute a gate's
possible utility or reproduce CALMRec's implementation. A matching implementation
was not located in the bounded source/repository search.

The author-hosted Coat archive is now pinned and audited as a possible observed-
behavior resource. Its 366 identical overlapping user-item cells must be separated
from unseen-item predictions; learned propensity estimates cannot be described
as known randomized logging probabilities. An established-baseline development
study has since completed; see coat-development-results.md. The native memory
pipeline is now validated with local inference, NLP and keyword retrieval.
A three-fitting-user resource preflight precedes any memory accuracy study.
Do not reuse the broad exposure-aware-memory proposal as if it were new.

## Cross-model portability screen

A generic memory migration proposal is not selected. The primary study at
https://arxiv.org/html/2609.05339v1 already separates writers and readers,
compares inherited stores at a fixed reader, and diagnoses writing versus
retrieval losses. Rosetta Memory (https://arxiv.org/html/2606.07711v1) already
trains model-conditioned read/write adapters. A change of personal-history
dataset would not establish methodological novelty. Neither paper has been
reproduced here. The abstract-only learned-table transfer lead is separately
labelled in the screening record.

The running Coat study remains an external-validity development check, not
a portability experiment. Its results must be evaluated before any further
model calls or expansion of this branch.

## User-specific benefit and memory utilization

A wrong-user-history control would help distinguish personalization from generic
context benefit, but it is not itself a contribution. CAPA already uses shuffled
histories (https://arxiv.org/html/2607.26611v1), and the developer-skills study
compares generic and other-user skills (https://arxiv.org/html/2608.10319v1).
Paired recall and behavior testing is also explicit in Know It, Act on It
(https://arxiv.org/html/2607.29433v1). A study must add more than these existing
controls or rename their motivation. These sources constrain future claims;
they do not invalidate our still-useful development diagnostics.

## Native observed-history development decision

The complete 30-user Coat experiment does not pass an extraction-harm gate.
The 29-user paired MAE difference is +0.0949, with exploratory 95% interval
[-0.0624, +0.2488]. Full-history reading also underperforms conventional
regression descriptively. The branch needs a substantive mechanism or method
before further scaling; no reserved-user scoring is justified simply to seek
a positive result. See coat-memory-development-results.md for coverage and
the one invalid full-history output.
