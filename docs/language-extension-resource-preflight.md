# Language-rich extension: first resource preflight

This is a development-only engineering run, not a confirmation experiment or an
accuracy test. It uses no target ratings. Source archives are parsed only during
input preparation; this runner reads the prepared development inputs and never
opens the raw archive, source-row mapping, reserved inputs or a label file.

Choose three of the 60 development cases by Qwen full-history reader token
length: shortest, median (index 30 in ascending order), and longest, breaking
ties by case hash. This intentionally exercises input-size range rather than
estimating population performance. All three remain development data forever.

For each, run the pinned native Mem0 extraction pipeline and a fixed task-matched
summary baseline using the local pinned Qwen3-4B-Instruct-2507 conversion. Both
writers receive only the earlier history and have temperature zero, top-p one,
and a 2,048-token generation allowance. Native extraction retains the actual
upstream prompt and pipeline; the task summary uses a separately recorded
instruction for a compact review-based profile. These are existing baseline
ideas, not proposed novel algorithms.

The same Qwen reader predicts three ratings under five evidence conditions:
no history, all 12 historical reviews, complete exported native memory, the
task-matched summary, and four raw history records selected with standard BM25
against the combined target catalog query. BM25 uses k1=1.5 and b=0.75, positive
Robertson-style IDF, lowercase alphanumeric tokens, and deterministic ties. It
ranks earlier review plus catalog text, not historical rating values. Selected
records are presented in chronological order. This is joint-query retrieval
for the three-target batch, not a per-target top-four experiment.

Reader output allowance is 256 tokens. The parser accepts exactly three finite
numbers between one and five, optionally enclosed in a JSON code fence. No
retry, answer repair or accuracy-dependent choice is allowed. Every request,
response, finish reason, elapsed time and token usage is retained locally.
Native stores are isolated per case. Interrupted attempts are marked and not
silently regenerated. Complete exports must match the inserted memory IDs.

There are at most **21 model calls**: six writer calls and fifteen reader calls.
The transport wrapper logs attempted calls even if native extraction fails before
its response callback. It blocks request 22, retaining any unexpected native calls
in the log rather than silently exceeding the engineering allowance. No provider API or paid service is used. The server is bound to loopback,
with one prompt slot, one decode slot and a one-entry prompt cache. Transport
timeout is 360 seconds per client request. Any failure remains in the record.

Inspect generation validity, native export completeness, nonempty stores,
response termination, actual native request token counts, wall time and memory
lengths. Require every preflight reader response to parse and every native
export to be complete and nonempty before treating this configuration as a
working prototype. Three cases cannot establish a 95% population reliability
rate. A larger development run, another reader family, a precision assessment,
and a separate public freeze remain necessary before confirmation inference.

Before every transport attempt, count the complete actual chat prompt with the
pinned Qwen tokenizer in the model-serving environment. Verify every expected
tokenizer/config file and record Transformers and tokenizers versions. The full
prompt plus output allowance must not exceed 16,384 tokens. This is an engineering
resource cap, not a claim about the model's maximum supported context. Persist
attempt markers before transport, including errors; the client performs no
automatic retries. The final gate requires server-reported prompt counts to match
the independently counted template and every native generation to stop normally.
The task-summary parser enforces the prompted maximum of 400 whitespace-delimited
words. A longer summary is invalid, not truncated or regenerated. Native writer
wall time is separate from request timings; a multi-call write must not duplicate
its total wall time as the duration of every call.


The 400-word summary constraint and native generation allowance do not match
output lengths. Treat them as two specified pipelines, not equal-size memory
representations. Request wall times include the tokenizer precheck; native wall
time also includes store setup and embeddings. These engineering timings are not
isolated server latency or a model-speed benchmark.
