# Resource reporting for the language-rich memory study

Prepared 20 September 2026 during development inference, before development
accuracy or reserved confirmation data were accessed. This specifies descriptive
reporting of existing logs. It changes no inference setting, primary contrast,
fallback rule, precision gate, or completed-paper result.

## Units and accounting

Separate memory construction from reading. Each native or task-summary writer
processes one user's twelve historical reviews. Each reader request jointly
predicts the three target ratings for one user. A reader request is therefore
not a single target rating. The four stored representations are each constructed
once per user and reused by both readers; do not count a writer twice because
two readers consume it.

Development contains 60 users, four construction cells per user and fourteen
reader cells per user. Distinguish 54 previously completed preflight cells from
1,026 newly planned cells. These are planned generation cells, not a reason to
assume the actual transport count. A native setup failure can occur before
transport; an invalid extraction can finish its model request normally. Use
the attempt ledgers and transport audit to count actual requests. Never infer
success from a raw record's `status: completed` alone.

For each writer model and construction method, report planned cells, recorded
cells, attempted transports, completed model responses, valid representations,
and failures. For each reader model and evidence condition, report recorded
cells, attempted transports, completed responses, valid readers and valid
whole pipelines. The last two can differ when a writer failed. Preserve the
fixed diagnostic reads after invalid writers in resource accounting even though
their predictions cannot replace the primary constant-3 fallback.

## Tokens

Report complete chat-template prompt counts from each pinned model tokenizer,
alongside server-reported prompt and completion usage. Check equality of the
two prompt counts on completed responses. Keep exact-count disagreement as an
integrity failure, not a value to average away. Report the maximum prompt plus
reserved output allowance separately from actual generated tokens. The former
checks the 16,384-token request ceiling; it is not actual consumption.

For each model and operation, report sums and mean, median, and maximum counts,
with the number of contributing observations. For missing server usage after
a failed transport, report it as unavailable. The known prompt count may still
be reported, but do not impute zero output tokens or describe a partial sum as
the complete consumption. Count each unique audited request once, including
failed requests where token usage is available.

Keep writer and reader model families separate because their tokenizers differ.
Token counts across these families are not an equal semantic information budget
or a monetary price comparison. No hosted API cost is inferred from local runs.

For memory size, report native entry counts and exported text word counts and
task-summary word counts, with validity denominators. Invalid or empty stores
must not be presented as successful compression. Any prompt-size comparison
between a memory condition and full history should report all-user operational
values and, separately, the subset with a valid writer. Label the subset as
descriptive; do not replace the all-user accuracy estimand with it.
The current per-condition subset summaries are not themselves paired savings:
full history has no required writer and therefore includes every user. Any
later paired prompt-size comparison must apply the same memory-valid user mask
to both the memory and full-history condition before calculating a difference.
Do not subtract aggregates from differently composed subsets.

## Elapsed time

Use the outer native-write duration for construction time. It includes store
setup, encoding, model-request instrumentation, extraction and export; it ends
before final cleanup in the current runtime. It excludes prior history
serialization and configuration-file loading. Summary and reader durations
include token-count subprocess work, local client/server communication and
generation, but exclude prior evidence loading, BM25 selection and prompt
construction. Describe these as instrumented request times, not complete
reader-pipeline or retrieval latency. Transport audit durations are nested
inside these operation times. Do not add nested durations together or call them
isolated model latency.

Report mean, median, maximum and total recorded operation seconds with counts,
separately by operation and model. Keep reused preflight timings identifiable.
Model loading, pauses between stages, verification and analysis time are not
contained in the per-operation totals. Any total wall-clock duration needs its
own measured start/end record and disclosure of pauses.

The machine serves one generation at a time, with the recorded cache settings.
An idle-sleep inhibitor was added partway through development and recorded in
the execution context. Local contention, cache effects,
instrumentation and sleep-clock behavior limit timing comparability. Do not
claim deployment throughput, concurrency performance, energy efficiency or a
production service-level guarantee from these sequential engineering timings.

## Commercial interpretation

A useful deployment decision jointly considers predictive error, failure rate,
construction overhead and repeated read cost. Smaller evidence is not a benefit
if it is empty because extraction failed, and a faster reader is not equivalent
to a more reliable complete pipeline. The full-history and matched-summary
comparisons keep these tradeoffs visible for the tested task.

The experiment evaluates one joint three-target request per user and condition.
It does not measure longitudinal memory maintenance, correction, deletion,
retrieval at scale, fresh future queries, cloud billing or customer outcomes.
Do not present a repeated-use break-even point, revenue benefit or cost saving
as an observed result. Those require a separate workload and deployment study.

## Release boundary

Create the final descriptive table only after all three development stages are
accounted for and their provenance checks pass. Attach the inference-manifest
and completed-report hashes. Publish aggregate measurements, settings, missing
usage counts and failure categories, without review text, target ratings, user
identifiers or private model traces. Partial engineering observations remain
clearly partial and cannot be relabeled as final accuracy results.

## Implementation

After all development stages are complete, run:

```sh
python3 src/summarize_language_development_resources.py
```

The command verifies completed inference provenance and all stage handoffs
before adapting raw records. It attributes every audited request to exactly
one planned cell, checks reused response identities, reparses writer and reader
validity, and rejects unassigned audits. The pure `summarize_resources` function
then checks the full 1,080-cell grid and aggregates by model, condition and
preflight/new provenance. The output is
`results/language-development-resources.json`, with input and source hashes.
It never opens the label artifact or computes accuracy. An existing differing
output is not overwritten. Tests use invented artifacts only; they do not
constitute a resource measurement from the live experiment.
