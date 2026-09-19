# What does a gated personal memory estimate?

2026-09-19. Exact estimand audit and a real-data feasibility check. No new
estimator, model-training result or conference-readiness claim.

## Why this is narrower than exposure-aware memory

[CALMRec](https://arxiv.org/html/2607.23647v1) already separates exposure from
preference and uses propensity weighting. Its Proposition 1 states the ordinary
importance-weighting identity. Its subsequent consistency statement refers to
the long-term memory update, which also includes a learned gate informed by
current evidence and delayed outcomes. The distinction examined here is whether
that gated update targets the same mean as the ungated identity.

The primary formulation, update and proposition were inspected, along with the
limitations and reproducibility statement. A matching implementation was not
located through the paper's visible links, exact-name web searches or GitHub
repository search. That is a search result, not a claim that no repository
exists. The check below implements only the stated scalar recursion at decay
one. It does not reproduce the paper's trained system or dispute its reported
utility improvements. A utility-weighted representation can be intentional;
its target must simply be stated accordingly.

## Conditional target and the gate

Fix a history H. Let action A have known logging probability mu(A|H), and let
pi0 be the declared reference policy. Let X be bounded observed evidence,
with consistency, positivity and conditional ignorability. With unclipped
w = pi0(A|H)/mu(A|H), the familiar identity is

    E_mu[w X | H] = E_pi0[X | H] = T.

Now consider a nonnegative gate g with positive reference expectation. In a
stationary independent setting with finite moments and no decay, the gated
self-normalized average converges to

    T_g = E_mu[w g X | H] / E_mu[w g | H]
        = E_pi0[g X | H] / E_pi0[g | H].

Consequently,

    T_g - T = Cov_pi0(g, X | H) / E_pi0[g | H].

This is elementary algebra. Exposure weighting removes the logging factor;
it does not remove the gate. A constant gate cancels. An action-dependent gate
can change the target even without looking at the outcome. Outcome-dependent
gating is another sufficient mechanism. Conditional independence of the gate
and evidence would eliminate this covariance, but it is an extra condition.

This calculation does not cover arbitrary adaptive gates by assuming an
unjustified law of large numbers. The concrete counterexample below uses a
fixed gate and independent bounded outcomes, so those complications are absent.
It also deliberately sets decay to one: a forgetting estimator has a different
time-dependent target and is not silently treated as an ordinary sample mean.

## Exact check, with a positive control

Two actions have success probabilities 4/5 and 1/5. The logging policy assigns
them probabilities 4/5 and 1/5, while the reference policy is uniform. The
observed mean is 17/25 = 0.68; the reference mean is 1/2 = 0.50.

| Gate | Exposure-corrected gated target | Difference from reference |
| --- | ---: | ---: |
| Constant 1/2 | 0.50 | 0.00 |
| 0.9 for action A, 0.1 for B | 0.74 | 0.24 |
| 0.9 for success, 0.1 for failure | 0.90 | 0.40 |

The outcome gate is realizable by a sigmoid affine in binary X. No clipping,
estimated propensity error, zero-support outcome or hidden confounder is needed.
The ungated propensity identity remains correct in all cases.

The code enumerates the four action-outcome cells with exact rational
arithmetic. A 100-event cycle realizes the population proportions exactly, and
the scalar online recursion equals the derived ratio. Permutations and ten
repetitions preserve that ratio. These are constructed arithmetic checks, not
observations of people or measurements of an LLM's memory behavior.

Four tests cover the propensity identity under sixteen policy combinations,
the two shifted targets and covariance identity, sequence accounting, and
invalid support. The machine-readable result records the exact fractions and
code hash in `results/gated-memory-estimand.json`.

## A real-data resource, with limits

The [author release](https://www.cs.cornell.edu/~schnabts/mnar/) for
[Recommendations as Treatments](https://proceedings.mlr.press/v48/schnabel16.html)
provides Coat ratings and learned propensity estimates. The primary paper's
Section 6.5 describes an elicited shopping study. The release links CC BY-NC
4.0. The archive was downloaded for research, hashed and left under ignored
`data/`; it is not bundled with our code.

Direct archive validation finds 290 users and 300 items. Every user has 24
self-selected and 16 random-item ratings. There are 6,960 and 4,640 observed
ratings respectively, with means 2.6115 and 2.2289. Importantly, **366 user-item
cells occur in both matrices, all with identical ratings**. A future memory
study must distinguish recall of these known ratings from prediction of unseen
items. Treating all test cells as unseen would be incorrect for that purpose.

The release's propensities are learned estimates, not known randomization
probabilities. Sparse random-item ratings are not exact individual latent
preferences. The matrices contain no timestamps or conversational histories.
This dataset can ground a limited preference-prediction experiment, but cannot
by itself validate a longitudinal assistant or causal preference recovery.
The audit excludes demographic features and does not fit or evaluate a model.

## Research decision

The broad exposure-aware-memory idea remains closed as a novelty claim. The
gate check identifies a specific estimand condition, not a new debiasing method.
Keeping an ungated statistical record alongside a task-weighted representation,
or correcting known stochastic inclusion probabilities, are existing statistical
solutions and required baselines rather than inventions to rename.

A follow-up must show a meaningful practical problem in an authentic memory
pipeline, state whether the desired quantity is behavioral frequency, utility-
weighted evidence or prediction, and establish a substantive improvement over
those controls. First separate genuine source errors, intentional weighting,
selection bias and downstream prediction. Do not infer a deployed-system failure
from this arithmetic example or advertise the result as an ICML contribution.

## Reproduce

```sh
python3 -m unittest discover -s tests -p 'test_gated_memory_estimand.py' -v
python3 src/gated_memory_estimand.py
python3 src/audit_coat.py
```

The first two commands use Python's standard library. The dataset audit uses
NumPy and downloads only the pinned author archive if it is not already present.
