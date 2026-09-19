# Next study design: external-validity gate

Historical design memo, superseded by the frozen `pilot-004.md` protocol.
The Qwen component test and post hoc budget sensitivity are complete, with
results in `pilot-004-results.md`. Both specified model runs are now complete.
The proposals below document the rationale before execution, not a separate
unexecuted experiment.

Subsequent source tracing found that the exported prompt tested in Pilot 004
is not on the pinned revision's active extraction path. The original design
therefore did not establish native-pipeline validity. See the source correction.

## Decision to make

Does query-agnostic memory extraction lose aggregate information needed for
personalization even when individual facts remain plausible? The current
six-event selection pilot cannot answer this for a deployed memory system.
Do not scale the custom selector before assessing the interface mismatch.

## Proposed component test

Use the pinned Mem0 USER_MEMORY_EXTRACTION_PROMPT exactly, with its runtime date
fixed and documented. Parse the Python string as data without importing upstream
code. Preserve its native JSON facts interface and absence of an event cap.
Call this an isolated prompt-component test, not a Mem0 reproduction. Native
updates, retrieval, embeddings and backend behavior are outside its scope.

Use fresh fictional journals, not the twelve development journals. Balance
which activity is favored, low/high overall positive rates, equal rates,
activity names and presentation order. Independently assign incidental detail
to positive or negative events so base valence and detail are not confounded.
Keep all targets deterministic and do not use a model to simulate behavior.

Evaluate the same downstream reader with (a) full journal, (b) extracted facts,
and (c) exact count ledger. The ledger is an explicit task-specific design
control, not a universal memory baseline. Use objective activity-frequency
ranking questions with a separate insufficient-evidence option, plus event
queries that expose the ledger's capability limits. Freeze scoring, parsing,
output budgets, all seeds and model identities before any new generation.

## Essential distinctions

1. Full-history reader errors are not memory losses.
2. An accurate summary that omits counts need not make a false statement.
3. A reader that abstains on incomplete memory loses utility but does not
   hallucinate; report coverage and conditional error separately.
4. A memory may support a ranking without explicit counts through an accurate
   comparative statement. Do not require one surface form as truth.
5. Equal event counts are not equal token or byte budgets. Report both storage
   and inference cost; do not claim an efficiency win from changing capabilities.
6. Formulaic journals are an identification tool, not a population sample.
7. A successful task-specific count prompt would reject a broad claim that a
   new memory algorithm is necessary. Test it before developing one.

## Go / no-go criterion

Proceed to realistic traces and native pipelines only if retained-memory answers
systematically degrade where the same reader succeeds with full history, and
the loss is not explained entirely by the fixed output budget or malformed
serialization. Otherwise archive the finding as a development audit and do
not claim a new research method. Even a positive component test would not by
itself establish novelty or an ICML-level contribution.
