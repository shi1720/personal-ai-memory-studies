# Native extracted memory versus full observed history

Development study, fixed after fitting-user output preflight and before any
LLM predictions on the 30 development users. This is a falsification screen,
not a new algorithm or confirmatory test. It extends the frozen Coat split.

## Question

Does replacing a user's complete observed rating history with native extracted
memories materially change a fixed reader's predictions for new items? The
primary contrast is native-memory MAE minus full-history MAE, paired by user.
Positive values mean greater prediction error with extracted memory. Also
compare no-history reading and established numerical personalization baselines.
A memory-related difference must be distinguished from a weak general reader.

## Data and information boundaries

Use all 30 development users in the exact frozen split order. The 60 fitting
users have already supplied population parameters. The 200 reserved users
remain unscored. There are 438 development new-item targets. Include every one;
known-item overlaps are excluded from this study. Feature and ordering rules
are those in coat-development-protocol.md. Neither writer nor reader receives
target ratings. The evaluator accesses only development labels for scoring.
Public 2016 data may have appeared in model training.

## Writer and contexts

Use the complete native Mem0 2.1.0 pinned code with local Qwen3-4B Instruct 2507
4-bit, native additive extraction, BGE dense embeddings, BM25, spaCy, local
Qdrant and SQLite. Each user receives a fresh store, one add call containing all
24 structured rating records, no custom extraction instructions, temperature
zero and a 2048-output-token maximum. These are serialized records, not an
invented conversation. Capture native runtime dates. Disable telemetry and
client retries. Record failures and truncations without repair.

The three contexts are no personal history, complete observed history, and all
native stored memory texts. Sort native texts lexicographically for repeatable
presentation, and request up to 1,000 records rather than the API's default 20.
Verify stored count against the add result in the fresh store. No retrieval
subset or memory-size constraint is imposed. This isolates extraction and
representation; it is not an evaluation of retrieval ranking or a published
Mem0 benchmark reproduction. Native storage has already been validated, but
predictive reading is our explicitly specified adapter.

An empty or failed writer yields an explicitly empty native context and remains
in the operational comparison. Report these events separately. An interrupted
writer with an uncommitted trace may not be silently regenerated. Reader
failures remain invalid, with coverage reported. No label-dependent retry.

## Reader and scoring

Use the exact reader instruction and parser in coat_memory_reader.py, validated
on three fitting users. Same Qwen model, temperature zero, top_p one, maximum
256 output tokens. One generation predicts all new-item targets for one user,
in ascending item order. Context order rotates by user position to distribute
cache/order effects. No target-dependent output prompt or fine-tuning.

For completed, parse-valid responses, compute per-user MAE and MSE; average MAE
across users and take the square root of average MSE. Report coverage first.
The primary paired difference includes only users valid in both memory and
full-history conditions and states the excluded users. Also report all-user
operational results with invalid-reader predictions replaced by the already
fixed population-feature predictions. This fallback is an explicit secondary
metric, not a repaired LLM answer.

Use a paired user bootstrap (10,000 replicates, seed 20260919) for an exploratory
95% percentile interval on the primary difference. Give individual errors and
wins/ties/losses. Numerical references are previously development-selected, so
comparisons to their winning settings are descriptive. No main-paper claim can
be based on development selection alone.

## Resources and limits

Record all 30 writer attempts and 90 scheduled reader calls, finish reasons,
actual prompt/output tokens, cache counts, wall times, native memory counts and
UTF-8 text bytes. Report writing and reading separately. These bytes exclude
databases, vectors, original-message history and entity links; do not call them
total storage savings. Timing uses a warmed local runtime, not a production
latency guarantee. Raw third-party records and generated traces stay in ignored
data/ with hashes. No raw ratings are added to the public artifact by default.

This screen has one small quantized model, one product-rating domain and batch
queries. It cannot establish frontier-model behavior, longitudinal preferences,
causal effects or novelty. If the full reader fails to exploit information that
simple attribute regression uses, inspect that failure before attributing it
solely to memory. A successful screen still needs substantive prior-work
differentiation, stronger models, other domains and independent evaluation.
