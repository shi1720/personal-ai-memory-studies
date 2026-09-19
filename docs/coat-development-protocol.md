# Coat: development baselines before a memory study

2026-09-19. Fixed before fitting models or calculating predictive scores.
This is a feasibility study with established baselines, not a new method.

## Question and sampling unit

Does the available rating history provide useful prediction signal beyond a
population model, when already-rated items are separated from new items?
This checks whether Coat can support a meaningful personal-memory experiment.
It does not test an LLM, causal preference identification or long-term drift.

One user is the unit. The archive and integrity audit are already pinned.
Its overall counts, means and overlap were inspected before this protocol.
No individual user prediction or method comparison has been calculated yet.

Rank the 290 zero-based user row indices by SHA256 of
`coat-memory-development-v1:user:{index}`. Assign the first 60 to population
fitting, the next 30 to development, and the remaining 200 to reserved
evaluation. Do not stratify or select users using ratings. Save the exact row
lists and hashes before model fitting. Reserved evaluation ratings are not used
to fit models, tune hyperparameters or calculate scores in this development run.
The data have previously been public, so this is not a contamination-free claim.

## Inputs and targets

The author's self-selected matrix supplies each user's 24-item history. The
random-item matrix supplies observed targets, not exact latent preferences.
For each target, mark whether the same user-item rating occurs in the history.
Primary scores use only new-item targets. Report known-item scores separately,
alongside an exact-history lookup diagnostic. Do not pool them as if they all
measured prediction of unseen preferences.

Use item category and color indicators as supplied in the archive, including
the product's menswear/womenswear category. Exclude the front-page promotion
indicators from preference features. Do not use user demographic attributes.
Add an intercept. Item IDs are array addresses, not predictive features.
There are no timestamps; item order is not asserted to be chronology.

## Established controls

Population mean uses the fitting users' observed random-item ratings. A
population item-feature ridge regressor uses the same fitting targets, with
penalty 10 on feature coefficients and no intercept penalty. This is one fixed
initial baseline, not a tuned state-of-the-art recommender.

User-mean adaptation adds a shrunken average history residual to the population
feature model. Attribute adaptation instead fits a ridge residual model to the
user's history. Test the following fixed history weights for attribute adaptation:

1. Uniform weights.
2. Estimated exposure weights: inverse smoothed item observation frequency,
   capped at 20. Frequencies use only the fitting users' self-selected masks,
   with Beta(1,1) smoothing. They are simple estimated item propensities, not
   known causal probabilities or a reproduction of CALMRec.
3. Positive-outcome gate: 0.9 for ratings 4-5 and 0.1 otherwise.
4. Estimated exposure weights multiplied by that positive-outcome gate.

Normalize each user's history weights to mean one before fitting. This prevents
a constant gate from changing the effective ridge penalty. For user-mean and
each attribute variant, consider penalties 0.1, 1, 10 and 100. Retain every
development result, not only the winner. Rank penalties by user-macro new-item
MAE, breaking exact ties in favor of the larger penalty. Clip predictions to
the valid rating interval [1,5]. No subsequent gate, cap or feature tuning is
part of this protocol.

## Analysis and limits

Primary metric is the mean of per-user MAE on new items. Secondary metric is
the square root of mean per-user MSE. Report target and user counts and every
development user's errors, keeping users with no eligible target explicit.
For the selected variants, pair errors by user. Development-selected differences
are descriptive; do not present them as confirmatory significance tests.

The exact-cache diagnostic returns a known history rating if available and
otherwise the population feature prediction. Its zero known-item error is by
construction and is not a learned capability or a memory-budget advantage.
Storage, inference cost and stronger collaborative baselines must be assessed
before any full study. This run does not establish a novel algorithm, equal
memory budgets, causal effects or superiority over published methods.

If these controls reveal useful prediction signal, a subsequent protocol must
specify the actual memory method and fair competing systems before opening the
reserved evaluation results. If no meaningful new contribution emerges, leave
the reserved set untouched rather than retrofitting a paper to this pilot.
