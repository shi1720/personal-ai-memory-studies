# Pilot 003: retention as a sampling design

Exploratory protocol, recorded before model generation. This is a narrow
measurement pilot, not a new-method or conference-readiness claim.

## Question

When an LLM selects a small episodic memory, does that subset preserve the
frequency of recorded outcomes as well as it preserves notable events? A
truthful subset need not be a representative subset. The basic statistical
phenomenon and inverse-inclusion weighting are established survey-sampling
ideas. A publishable contribution would require a substantive new empirical
result or unresolved technical obstacle, not renaming those ideas.

## Controlled population

Create 12 fixed-seed fictional activity journals. Each contains 24 distinct
visits, 12 to each of two named activities. One activity has 9 positive outcomes,
the other 6; their empirical rates are exactly 0.75 and 0.50. Activity names,
which activity has the higher rate, dates and presentation order are balanced
or randomized before inference. Each record has an immutable event ID.

Each journal has two renderings with identical activity, date and binary
outcome. In the plain rendering, every event uses a short neutral sentence. In
the detailed rendering, six events receive an extra incidental environmental
detail, selected from the lower-rate activity's positive visits. This changes
length and distinctiveness together. It is deliberately NOT described as a
semantics-preserving paraphrase or a causal test of salience alone. The target
is the empirical positive-outcome rate; it does not depend on those details.
No LLM simulates user behavior and no real person is represented.

## Memory writers

Use the pinned Qwen3-4B-Instruct-2507 4-bit reader as a writer, at temperature
zero, maximum 160 output tokens. For each rendering, compare two explicit
custom prompts: important-event selection and representative-event selection.
Both must select exactly six original event IDs with no rewrites. Future
activity-rate queries are not supplied to the writer. This is 48 generation
calls. The prompts are not claimed to reproduce a published memory system.

Each result must be a JSON array of six distinct allowed IDs. Preserve malformed
outputs and count them as failures; do not retry or silently repair them. Save
rendered prompts, hashes, output text, token counts and timings. All inference
uses the full journal, with a hard 4,096-token prompt check. Pin code, protocol,
data and model identities. Never replace examples based on outcomes.

## Measurements and inexpensive baselines

For each retained subset, compute the unweighted positive-outcome fraction per
activity when that activity is represented. Report missing-activity rate,
absolute error, signed bias and activity-order accuracy, with ties explicit.
These are properties of the retained data, NOT the output of a downstream LLM.
Also measure recall of the six detailed events and their actual metadata.

Compare uniform sampling without replacement at the same six-event budget over
1,000 seeds. Include a query-specific exact counter ledger as an oracle design
control: four counts solve these two fixed queries exactly. Its event-recall
capacity differs, so it is not a universal equal-capability baseline. Record
that limitation rather than claim a new sampler beats sufficient statistics.
A later generic-memory study would need both episodic and aggregate workloads
and byte/token budgets, not only record counts.

The independent construction unit is a journal. Twelve journals are a pilot;
random reservoir seeds are not additional users. Report paired rendering effects
and individual cases without a confirmatory significance claim. All data are
development data. No broad personal-assistant conclusions follow from one small
model and synthetic journals.

## Gate

If the representative-selection prompt or simple count ledger resolves the
entire effect, reject a generic debiasing-method claim. If only the deliberately
lengthened rendering shows an effect, do not call it evidence of natural-world
bias. A larger study requires verified published memory implementations,
multiple model families, realistic traces, and a distinct contribution beyond
classical stratified sampling and explicit sufficient statistics.
