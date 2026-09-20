# Language-rich memory study: fixed development evaluation

Prepared 20 September 2026 before development accuracy inspection. This is a
development protocol, not held-out confirmation or evidence of a new memory
algorithm. The completed Coat/MovieLens manuscript remains unchanged.

## Purpose and population

Evaluate whether the proposed crossed writer-reader design is operationally
feasible and sufficiently precise before accessing reserved confirmation
outcomes. Use exactly the 60 development users from the frozen input preparation
report, in its recorded hash order. Each supplies twelve earlier reviews and
three later observed product ratings. Retain the preparation's chronological,
catalog, minimum-language and token-budget rules without further selection.
Do not open the 200 reserved confirmation inputs or their outcome fields.

These are selected reviewers in Amazon Reviews 2023 Musical Instruments, not a
random sample of shoppers. Catalog information is a retrospective snapshot.
Inference cannot establish point-in-time deployment performance, conversational
understanding, intrinsic taste or causal effects on people. Model pretraining
overlap with this public corpus is unknown.

## Prerequisite and unchanged settings

Require the completed cross-writer/cross-reader resource preflight to pass its
frozen engineering rule, including the 54-call audit. Verify all its hashes.
Reuse those exact outputs for its three development users; never regenerate
them to obtain more favorable or uniform outputs. All other 57 users are new
development inference. No development outcome has been used to select the
three engineering cases or the present configuration.

Use the same pinned Qwen and Phi model conversions, native Mem0 path and
configuration, history serializer, summary instruction, reader prompt, parsers,
BM25 selection and evidence serialization as the cross preflight. Writers see
only earlier history. Both readers consume the same four stored representations.
Every native store is isolated by user and writer. Preserve all valid native
entries. The task-summary limit remains 400 whitespace-delimited words.

Use temperature zero, top-p one, 2,048 output tokens per writer and 256 per
reader. Count the complete actual request with the pinned model tokenizer;
prompt plus allowance must not exceed 16,384 tokens. Retain timeout 360 seconds,
zero client retries, loopback transport and one model server at a time. Preserve
native date fields as actually generated, rather than editing saved prompts.
Preflight reuse and later execution dates are recorded and are a design limit.

## Seven reader conditions and sequential stages

The seven conditions are no history, full history, Qwen-native memory,
Qwen task summary, Phi-native memory, Phi task summary, and BM25 history. BM25
selects four complete earlier records using the combined three-target catalog
query and presents them chronologically. This query-conditioned retrieval is
different from target-independent writing. No condition silently truncates
history or repairs generated text.

| Stage | Work for each of 57 new users | Maximum new generation attempts |
| --- | --- | ---: |
| qwen_base | Two Qwen writes and five Qwen reads excluding Phi evidence | 399 |
| phi | Two Phi writes and all seven Phi reads | 513 |
| qwen_cross | Two Qwen reads of the Phi representations | 114 |

There are 1,026 new planned calls plus 54 retained preflight calls, totaling
240 writes and 840 reads. All actual transport attempts, including native calls
which fail before callbacks, count toward stage limits. Unexpected generations,
wrong model identity or broken provenance block confirmation eligibility.
Record condition order in the runner and lock it with the code hash before new
inference. Do not choose order based on accuracy or validity.

## Persistence, failures and completion

Before new inference, freeze source dependencies, environment/model manifests,
prepared inputs, protocol, precision settings and reused-output hashes in a new
run manifest. Publish that implementation and protocol before starting. Retain
raw request/response files, per-cell attempt ledgers, model identity, exact token
counts, termination reason and elapsed time. Verify handoff hashes between
stages. Completed records are immutable, including errors. Resume only skips
verified completed records; ambiguous interrupted attempts require inspection
and cannot trigger automatic regeneration. No hidden retries are permitted.

Completion means every planned cell is accounted for under the frozen attempt
policy and every saved output has auditable provenance. Completion does not
mean all predictions or writers succeeded. Report missing, blocked, transport,
format, token-limit and writer-export failures separately. A protocol deviation
is not repaired by calling the original experiment successful.

After an invalid writer, retain the fixed sentinel-evidence read as a diagnostic
where the runner calls it. It does not become a valid realization of that memory
condition. For primary operational accuracy, use exactly [3, 3, 3] whenever a
required writer is invalid or the reader response is invalid. No-history, full
history and BM25 require only reader validity. A valid reader must finish normally
and pass the frozen three-number parser; a native writer must have a nonempty,
complete ID-and-text-matched export and normal generation termination; a summary
must pass the frozen JSON, nonempty and word-count checks. Common-valid paired
sensitivity requires valid complete pipelines on both sides of a contrast.

## Outcome boundary and analysis

Only after all three development stages complete and their raw-file hashes and
manifest have been verified may development labels be materialized. Use exact
development row mappings from the frozen source mapping and verified source
archive. Verify user, distinct product identities, chronology and prepared
catalog/history correspondence before reading selected target ratings. Access
rating fields only for these 180 development target rows. Parsing the archive
to locate rows is disclosed; reserved target rating fields are neither selected,
materialized nor used. Labels and source identities remain private.

Report all 60 users for every operational condition. Compute per-user MAE as
the mean absolute error over that user's three targets, then average users.
Compute RMSE as the square root of the mean squared error over equally weighted
users and their three targets. Report validity and resources separately.
History mean, history median and constant three are fixed numerical baselines.
These are development results, not independent confirmation.

As a secondary descriptive diagnostic, compute concordance on target pairs
with unequal observed ratings: one for correct order, zero for reversed order,
and one half for an exact prediction tie. Average pairs within each eligible
user, then users; report the number of eligible users. Users with three equal
target ratings have no ordering score but remain in every accuracy metric.
With only three targets this is a sparse diagnostic, not another primary test.

The eight predeclared differences are native minus full history and native minus
same-writer task summary for every pair of two writers and two readers. Positive
values mean the native pipeline has greater error. Keep the full family even if
results are unfavorable. No significance, mean, sign or favorable-effect
criterion determines whether a contrast is retained.

Apply the fixed `language_precision_planning.plan_precision` calculation to
the eight arrays of 60 paired user-MAE differences. Its 20,000-resample,
fixed-seed upper empirical SD quantile projects eight-test adjusted normal
half-widths at the already reserved 200 users. The resolution criterion is 0.10
MAE for every contrast. It is approximate planning, not a power or coverage
guarantee. See `docs/language-precision-planning.md` for complete settings and
limitations. A failed gate remains NO_GO; do not relax it after seeing accuracy.

## Decision after development

Before reserved inference, publish the complete development results, failures,
precision decision and an independent implementation review. Confirmation
requires both engineering integrity and the prospective precision GO. Any
change of hypothesis, settings or scientific aim requires an explicit prospective
amendment; it cannot relabel development as confirmation. Passing this stage
does not establish acceptance-level novelty, universal reliability or usefulness
outside the stated prediction task.
