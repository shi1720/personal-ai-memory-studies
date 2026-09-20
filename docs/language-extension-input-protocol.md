# Review-history extension: input preparation rules

Recorded 20 September 2026 before inspecting the completed Musical Instruments
cohort report or generating any prediction.
This fixes a data-preparation screen, not an inference protocol or a claim of
public preregistration. The released paper and its original evaluation stay fixed.

## Eligibility and information boundary

Use the verified official Amazon Reviews 2023 Musical Instruments archives.
The input-only feasibility script first excludes the 323 previously audited
MemoryCD source user IDs, deduplicates parent products by first event, and uses
1 January 2022 UTC as a strict boundary. It selects the latest 12 first-time
product events before that date and the first three strictly after it. Missing
catalog titles or empty selected historical reviews reject a user; do not
backfill a different window until a desired result appears.

The second-stage preparation retains the 12 historical review texts verbatim.
It rejects normalized duplicate historical text, reviews with fewer than five
whitespace-delimited words, and histories with fewer than 240 words in total.
These analyst-chosen thresholds enforce substantive written evidence. They
select a more verbose reviewer population and do not establish language,
quality, representativeness, or human preference ground truth.

Only catalog title and feature strings are visible for a target. Target review
text, review title, rating, aggregate product ratings, rating counts, price,
descriptions and images are excluded by field selection. Target source records
are projected to user ID, parent item ID and timestamp before input construction.
No target-label file is produced during this phase. Parsing a source JSON object
is not the same as keeping its labels inaccessible on disk; the guarantee is
that target outcomes are not consulted or used in eligibility or inputs.

## Context budget and deterministic partition

Count tokens with the already pinned local Qwen and Phi tokenizers, without
loading weights or making model requests. Require the history payload to be at
most 6,144 tokens for each tokenizer and the actual full-history reader chat
template to be at most 12,288 tokens. Do not shorten source reviews to pass.
The writer payload limit reserves room for native instructions but does not
certify the complete Mem0 request length. The latter still needs an execution
preflight. Every arm's exact final token use and output allowance must be fixed
and checked before confirmation inference.

After eligibility, order users by SHA-256 of the fixed string
`review-history-extension-v1:` followed by the exact source user ID. Allocate
the first 60 to development, next 200 to reserved confirmation, and all remaining
eligible users to a disjoint history-only donor pool. Require at least 60 donors,
so fewer than 320 eligible users is a data-preparation NO-GO. This hash ordering
is deterministic sampling, not cryptographic concealment or proof of random
population sampling. No language-model outcome or target rating enters selection.

Development and confirmation inputs, private source-row mappings and donor
histories remain under ignored `data/`. Published preparation records contain
counts, pseudonymous case hashes, source hashes and token distributions. Donor
outputs contain earlier history only, not their future product records. These
records must be frozen publicly with the final protocol before confirmation
predictions are generated. A successful preparation screen does not authorize
accuracy inspection of reserved users during development.

## Outstanding gates

Development must establish native extraction completeness, realistic writer
budgets, reader validity and the dispersion needed for a precision target.
The inference protocol must specify the native and task-matched writers,
retrieval and statistical baselines, reader identities, all prompts, failure
rules, primary comparisons and uncertainty calculations. Any donor diagnostic
must maintain the global time boundary and state that it changes semantic and
product support, unlike the Coat rating-assignment control.

Observed reviews are selectively collected outcomes. Catalog text is a later
snapshot whose earlier availability is not certified. These limitations remain
even if all software checks pass. No result direction is required for proceeding
or for inclusion in the scientific record.
