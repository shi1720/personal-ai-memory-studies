# Pilot 004: extraction-component and reader gate

Protocol frozen before generation. This is a small exploratory component test,
not a Mem0 end-to-end reproduction or an independent confirmatory study.

## Purpose and scope

Determine whether a native user-fact extraction prompt loses information needed
for aggregate personalization when the same reader can answer from full history.
Use the exact USER_MEMORY_EXTRACTION_PROMPT from pinned Mem0 commit
`a39a802bbc93e85b820078cd3c4dbaf53af25dbe`, rendering its date as 2026-09-19.
Load the string via a restricted AST reader, without importing upstream code.
The native interface returns an unrestricted list of facts. No six-event cap is
imposed. Updates, vector retrieval, embeddings and product infrastructure are
outside this test. Never call the result a measured failure rate of Mem0.

Compare native extraction with the same prompt plus an explicit instruction to
retain exact activity outcome counts. This is a task-specific prompting control,
not a proposed novel algorithm. Both have a 1,536-output-token ceiling; save
truncation and parsing failure, with no retry. Full source journals fit in context.

## Fresh data

Construct twelve new fictional journals with seeds 41000-41011. Each records
24 dated visits, twelve per activity. The four outcome-count pairs are (9,6),
(3,6), (6,9), and (6,6). For each pair, construct three independent journals:
plain, incidental detail on three positive events, and incidental detail on
three negative events. Detail-assignment sign is therefore crossed with count
pair, but each rendering uses a different random journal. Do not describe this
as a paired rendering intervention. Balance named activities by fixed rotation.
These are new development examples, not twelve real users or a representative
population. Outcomes are generated programmatically, not by an LLM.

Each journal has two fixed questions: which activity has the higher empirical
positive-outcome fraction, and whether a specified dated visit was enjoyed.
Randomize answer-option letters before inference. Include an insufficient-
evidence choice in both tasks. The event question also has an explicit mixed-
feelings distractor. Save source-truth labels separately from inference inputs.
A count ledger contains only per-activity positive/negative/total counts and no
visit-level detail. It can solve the rate question but not identify the dated
visit outcome. This deliberately exposes its capability limit.

## Models and execution

Use the pinned Qwen3 4B and Phi-4 four-bit models, with native system/user roles.
Run each model sequentially on the same cases. Each model is its own extractor
and reader; no cross-model experiment or model-size causal inference is claimed.
Temperature zero, seed zero, 4,096 maximum input tokens, no truncation of input.
The writer sees only the source journal, not the downstream questions or gold.

For each journal/model, generate native facts and count-aware facts first.
Then answer both questions under four contexts: full journal, native facts,
count-aware facts, and exact ledger. Reader output ceiling: 256 tokens. Ask for
a brief evidence-based reason followed by an answer letter in JSON. Explicitly
instruct readers to abstain when memories do not support the requested fact;
generic likes/dislikes alone do not establish a frequency ranking.

This schedules at most 120 generations per model, 240 total. If a writer fails
to return a facts list, retain the failure and mark its two dependent reader
cases blocked; do not feed a malformed summary or silently skip the denominator.
All other cases continue. Save rendered prompts, raw outputs, timings, token
counts, finish reasons, parsed facts/answers and source-context hashes. Accept
bare JSON or one sole Markdown JSON fence, consistently for both models and
both stages. Do not repair JSON or extract it from additional prose. For the
reader require exactly the keys reason and answer, both strings, with an allowed
letter. Pin all input, code, protocol, prompt and model files in run manifests.

## Analysis and gate

Report writer validity, truncation, fact count and stored UTF-8 bytes; context
and prompt token counts; reader validity; correct, wrong and abstained counts
out of every planned case. Report coverage and error conditional on answered
valid cases separately. Wrong answer is not synonymous with a false memory.

For each compressed context, count paired losses where full history answers
correctly but compressed memory is wrong, abstains, invalid or blocked. Also
report reverse gains. Separate rate and event questions and all renderings.
The full-history reader is a control, not an oracle. Inspect every extracted
summary in this small pilot for explicit numerical/comparative claims and dated
facts using the source journal. Unstated quantities are omissions, not falsehoods.
Qualitative inspection is exploratory, not independent human annotation.

If the count-aware prompting control closes the rate gap, reject a claim that a
new general memory algorithm is needed to solve this task. If full-history
readers fail extensively, the pilot cannot isolate memory effects in those
cases. Do not extrapolate the diagnostic to real users, frontier models, deployed
systems or acceptance chances. A positive result motivates native pipeline and
realistic-data work; it does not by itself establish novelty.
