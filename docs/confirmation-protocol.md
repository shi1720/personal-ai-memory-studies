# Independent observed-preference validation

This protocol will be frozen publicly before any reserved-user inference or
accuracy analysis. It follows exploratory results on 30 development users.
The contribution under development is empirical: controlled evidence about
extraction, use of rating associations and conventional statistical readers.
Ridge regression, rating prediction, permutation controls and user-level
bootstrap are established tools, not newly invented algorithms.

## Independent sample and information

Use all 200 reserved users in the existing SHA-256 user split. No subgroup is
selected by accuracy. Each user has 24 observed ratings. Predict every positive
test cell not present in that user's observed history. Known-item overlap is
excluded. The source data have no usable within-user chronology, so this is
new-item prediction, not prospective longitudinal evaluation. Randomly elicited
targets distinguish this sample from self-selected review histories, but do
not identify a causal intrinsic-preference estimand. The 2016 archive is public
and may occur in pretraining. Do not generalize to all users or frontier models.

## Fixed conditions

The Qwen3-4B Instruct 2507 4-bit model writes native Mem0 2.1.0 memories using
the same pinned pipeline and defaults as the completed development experiment.
Use one fresh store and one complete structured-history add per user, maximum
2,048 output tokens. Query all stored memory texts; there is no retrieval cap
or imposed compression ratio. Native failures remain recorded and yield an
empty memory context. No hidden retries or label-dependent repairs.

Read with Qwen3-4B Instruct 2507 4-bit and Phi-4 4-bit, separately served using
their own native chat templates. Phi reads the Qwen-created store, allowing the
reader to vary while the memory remains fixed. This is not a test of Phi's
writing or a claim about all possible writer-reader pairs.

Each reader receives four conditions: no personal history, full observed
history, a within-user rating-permutation control, and all native memory texts.
The permutation preserves rated item IDs, item attributes and the exact rating
multiset; only rating-to-item assignment changes. Its seed is fixed by user ID
before evaluating targets. This tests reliance on those associations, not all
forms of personalization and not a causal change in the real person's taste.
Rating-level adaptation remains a legitimate personalization capability.

The reader instruction and parser are unchanged from the development study.
Each call predicts all of a user's new targets in ascending item order, with
temperature zero, top_p one and maximum 256 output tokens. Rotate condition
order by user position. A single user worker uses a model server with decode and prompt concurrency
one after the fitting-user concurrency-four preflight exceeded GPU memory. Concurrency is a throughput
setting, not a tested method; no isolated latency claim is planned.

Before freezing, require at least 11 of 12 correctly shaped outputs per model
on three fitting users, without calculating accuracy. Check native sequential
writing on those fitting users as well. A preflight failure must be fixed and
recorded before reserved-user inference begins. Do not retune after test access.

## Statistical controls

Primary numerical comparator: history-only ridge around fixed prior 3, using
the same 32-dimensional item attributes and each user's 24 observed outcomes.
All coefficients are penalized and predictions clipped to [1,5]. Select its
penalty from {0.1,1,10,100} by development MAE only, with larger penalty breaking
ties. No labels from other users train this comparator. It is an established
statistical baseline, not a proposed new memory architecture.

Also report history mean, history median, shuffled-history ridge and the
previously frozen population/prior-assisted numerical baselines. The latter
use fitting-user labels and must be identified as a different training regime.
They are supplementary, not part of an equal-information superiority claim.

## Outcomes and six fixed primary contrasts

All 200 users are the sampling units. Report valid-output coverage first.
The operational metric uses constant 3 for an invalid response, declared here
as a common system fallback. It is not a repaired model answer. Also report
valid-only summaries and paired common-valid sensitivity analyses. A material
change between these views must be disclosed, not hidden behind the fallback.

For each reader, compare user-macro MAE for: (1) native minus full history;
(2) permuted minus full history; and (3) full history minus history-only ridge.
Positive values mean extraction increases error, rating associations help,
or the statistical comparator has lower error, respectively. Report effect
sizes without requiring the hypotheses to be supported.

Use 10,000 paired-user bootstrap replicates, seed 20260920. Give ordinary 95%
intervals and ten-comparison-adjusted percentile intervals using alpha 0.05/10. The six
Coat and four MovieLens contrasts constitute one predeclared family.
These are approximate bootstrap intervals, not exact finite-sample guarantees.
No threshold, stopping rule or model is selected by the resulting intervals.
Do not inspect accuracy until both readers on both datasets and all native
writes are complete. See movie-validation-protocol.md for the second domain.

Secondary metrics are macro RMSE, mean signed error and within-user pairwise
concordance on unequal-rated target pairs. Prediction ties receive 0.5.
Pairwise summaries average eligible users, not correlated pairs as independent
observations. Do not market rating-error gains as gains in every preference task.

## Scope, resources and reporting

Planned model calls: 200 native writes and 1,600 reads, excluding separately
recorded fitting-user preflights. Log responses, finish reasons, prompt/output
tokens, cache information, per-call timing and all failures. Record memory-text
bytes separately from full storage. Generated raw records remain local because
source data and derived text have separate redistribution constraints.

The separate MemoryCD audit is already inspected exploratory material, not an
independent replication or a second confirmatory domain. Its baseline results
must not be numerically compared against a paper cohort with different users.
The manuscript must include the earlier failed pilots, direct prior-work
overlap, training-regime differences, format failures and scope limits.

Completion means reporting every predeclared outcome, including null or adverse
results, in a complete manuscript with code and figures. A conference-standard
format does not imply peer review, acceptance or a guaranteed venue outcome.

A secondary squared-error diagnostic splits each user's MSE into squared mean
prediction error and centered residual MSE. This is an exact descriptive
identity, not a new theorem or a calibration method. Target means are used
only for retrospective evaluation, never to construct predictions.
