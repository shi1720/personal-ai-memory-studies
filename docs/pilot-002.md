# Pilot 002: recalibration after memory availability changes

Recorded before inference on these examples. Exploratory, not a confirmatory
study or evidence of performance on the official PersonaMem-v2 leaderboard.

## Data and split

Use only the upstream text validation CSV from PersonaMem-v2, revision
`ed956dea41521fc4499acbc63f966e0fd3c053ba`. Its primary dataset card declares
CC BY 4.0. Cite Jiang et al., PersonaMem-v2, arXiv:2512.06688. Do not assume a
third-party repository's MIT statement applies to this pinned dataset.

Choose 128 distinct personas by a fixed SHA-256 ordering with salt
`partial-recalibration-pilot-002`. Within each persona choose one query by a
fixed hash of its query text. The first 64 personas are calibration, the next 64
evaluation. This entire pilot is development data for any eventual main study.
The official benchmark split is not used. Group-disjointness is asserted.

## Reader and memory

Pinned local Qwen3-4B-Instruct-2507, MLX community 4-bit conversion. Use next-token
probabilities of A/B/C/D after a fixed multiple-choice prompt. Normalize over
those four labels, choose the highest, and record its normalized probability
and the total unnormalized probability mass of all four labels. This is a
constrained-choice reader, not ordinary unconstrained answer generation.

Shuffle the four choices deterministically per example. The answer key is only
used by the scorer. Exclude persona summaries, oracle snippets, gold preference
fields and all initial system messages from retrieval. Index chronological
user-assistant blocks with the existing BM25 implementation. Retrieve using only
the question text, not options or the answer key.

Cap each block at 512 tokenizer tokens, then greedily pack ranked blocks within
a 3,072-token TOTAL rendered prompt budget. Skip a block that will not fit.
Do not silently truncate the question or choices; reject oversize examples.
The exact chunking, prompt and retrieval code hashes go in the run manifest.

The baseline memory has all conversation blocks. The changed memory removes
blocks independently by a deterministic hash threshold of 0.25. This is memory
availability loss, not a claim that a user's preferences changed. Gold answer
semantics remain fixed. Deletion never consults evidence labels. An unchanged
exact rendered prompt permits reuse because the model/configuration and answer
key also remain fixed. Report changed-prompt frequency.

## Policies and analysis

Thresholds: 0, then 0.25 through 1.0 in increments of 0.05, then 1.01 for guaranteed
abstention. Alpha values: 0.05, 0.10, 0.20, 0.30. Report all, without choosing the
best after seeing results.

Infrastructure correction before the full run: two initial diagnostic examples
exposed bfloat16 logsumexp rounding, including a label probability mass above one.
Their outputs and code are preserved under `results/invalid/`. Cast final logits
to float32 before logsumexp and recompute both examples in the full run. This does
not change the selected examples, choices, prompts or model weights.

Compare full new calibration; stale old calibration; exact caching plus all
changed rows; conservative partial evaluation in fixed and randomized orders.
No learned selection policy is claimed in this pilot. For exact recovery, stop
when the lower and upper reference-policy indices agree. Also show budgeted
policies at 0, 25, 50, 75 and 100 percent of changed calibration rows.

All new outputs are computed to make the full reference available. Partial
schedules are therefore OFFLINE TRACE REPLAY; their avoided-call counts are
counterfactual accounting, not wall-clock speedups. A later live experiment is
required before any actual latency-saving claim.

Report calibration/test always-answer accuracy, policy threshold, marginal
shipped-error frequency, answer coverage, conditional error among answered
queries, exact-reference recovery and recomputation counts. A 64-persona test
slice cannot validate a distribution-free theorem empirically or establish
deployment safety. Public personas are simulated, not consenting real users.

## Kill criterion

If exact caching achieves essentially the same savings, or partial evaluation
needs nearly every changed row to recover the full policy, record a negative
feasibility result. Do not compensate by reporting only more-abstaining policies.
