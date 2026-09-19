# MemoryCD rating and temporal-support audit

Exploratory dataset audit, written before downloading or examining the released
user records. This runs independently of the frozen Coat model experiment and
does not alter its protocol. It is not a new memory method or a reproduction of
paper scores. Scope: the released 323-user cross-domain subset only.

Pin the author dataset WZDavid/MemoryCD at
14b934ce3f76f96b6c3c2efa173525f0da62952e and the public harness at
4cee5ebbf8a1ac4c933bde147006217e04678370. Retain raw records under ignored data/;
publish code, hashes and aggregate results without user identifiers or reviews.
Follow the noncommercial academic-use scope stated by the primary paper and
original Amazon data release. The repository code's MIT license does not
replace underlying data terms. No commercial deployment or private-data use.

## Why this audit

A low rating error may result from a concentrated rating distribution without
requiring detailed personal memory. That is a hypothesis, not a discovered
flaw. Independently, the public cross-domain loader uses all source-domain
interactions without filtering against each target timestamp. This is suitable
for retrospective transfer, but prospective assistance requires a cutoff.
Measure support for both interpretations before claiming temporal leakage.

## Fixed calculations

1. Validate unique user IDs, numeric finite ratings in [1,5], numeric finite
   timestamps, per-domain counts and missing fields. Fail rather than silently
   repair invalid records. Do not inspect or infer identities.
2. Use the harness's four domains and single-domain split: stable timestamp
   sort, final three interactions as targets, preceding history as memory;
   include all users with at least four interactions. Report target rating
   histograms and ties across the history/target timestamp boundary.
3. Report all five fixed constant-rating predictors, plus each user's history
   mean and history median. No test-selected constant is labelled a trained
   model. No item metadata, product-average rating or target review is needed.
   Compute per-user MAE and MSE, then user-macro MAE and sqrt(mean MSE).
   These baselines use no language model and are established, not proposed here.
4. For the cross-domain Home_and_Kitchen task, require three target interactions
   and at least one source interaction from the other three domains. For each
   of the last three targets, count source events strictly later than it,
   equal-time events, and strictly earlier events. Report per-target and user
   aggregates, including users with no prior source evidence. Do not infer
   availability from timestamp alone: this is a timestamp-order audit.
5. Compare the same simple source-history mean and median under the release's
   unrestricted source history and under a strictly earlier per-target cutoff.
   For empty earlier histories report exclusion and, separately, a fixed 3.0
   fallback. Give coverage explicitly. This is a retrospective diagnostic of
   support, not a causal estimate of future-information benefit.

No significance testing, inferential novelty, human-satisfaction claim or
comparison against paper tables is authorized by this audit alone. The released
cross-domain sample need not equal the paper's single-domain cohorts. Do not
compare numbers across unmatched cohorts as if they were paired runs. User
history statistics do not condition on product attributes; they are controls,
not the strongest recommender baseline. If concentrated ratings alone explain
low error, a full memory benchmark needs an additional informative task or
stronger evaluation contrast. That conclusion must follow the data.
