# Pilot 004: completed exported-prompt component study

## Decision

Do not promote the forced-selection hypothesis to the main paper contribution.
On this small development set, an unrestricted exported extraction prompt does
not produce an overall frequency-answer loss relative to full history. Qwen
preserves all correct event outcomes, sometimes alongside added contradictions.
Phi represents them differently and makes source errors, but its frequency
answer score is slightly higher than full history. The observations do not
support the proposed general selective-retention failure mechanism.

The study also fails a source-path external-validity requirement. The tested
prompt exists in the pinned Mem0 source but is not the prompt used by that
revision's active extraction pipeline. The source correction is part of this
report, not an optional caveat. No product performance claim is justified.

## Completed scope

Two pinned community four-bit models, Qwen3 4B and Phi-4, process the same twelve
fictional journals. Each journal has 24 dated visits, a frequency comparison and
a dated-event question. The original protocol uses two writers and four reader
contexts: full journal, unmodified exported prompt, count-aware prompt, and an
exact oracle count ledger. The ledger intentionally lacks dated outcomes.

All 336 scheduled records are accounted for. There are 327 actual generations:
234 in the original runs and 93 in the post hoc frequency-budget runs. Nine
records mark readers blocked by three invalid Phi writers, six in the original
phase and three in the budget phase. This is twelve development journals, not
336 independent users. Total measured generation time is 2,943.25 seconds,
excluding downloads, loading, hashing, preprocessing and analysis.

The 768-token frequency sensitivity reuses exact original prompts after a
256-token ceiling truncated 22 Qwen readers. Phi has no truncated original
responses. Increasing its ceiling changes none of its completed responses.
All writers use the original 1,536-token allowance and none is truncated.

## Frequency answers at the larger budget

Entries are correct / wrong / abstained / invalid / blocked, out of twelve.
“Exact-option” is a separately labelled post hoc parser accepting a bare letter
or exactly the displayed letter and option. It repairs neither JSON nor wording.
It recovers six Phi answers and no Qwen answers; the original scores remain.

| Model / parsing | Full journal | Exported prompt | Count-aware prompt | Oracle ledger |
| :--- | :--- | :--- | :--- | :--- |
| Qwen, strict or exact-option | 9/3/0/0/0 | 9/3/0/0/0 | 9/3/0/0/0 | 12/0/0/0/0 |
| Phi, strict | 8/3/0/1/0 | 9/2/0/1/0 | 4/3/0/2/3 | 10/0/0/2/0 |
| Phi, exact-option | 9/3/0/0/0 | 10/2/0/0/0 | 6/3/0/0/3 | 12/0/0/0/0 |

Using exact-option parsing, Qwen's exported memory loses one full-history-correct
answer and gains one elsewhere. Phi's retains all nine full-history-correct
answers and gains one. These small paired results do not demonstrate a useful
new method, statistical equivalence, or a population-level benefit.

Dated-event answers distinguish capabilities. Qwen gets all twelve right with
full and either extracted context. Phi gets twelve with full history, eleven
with the exported prompt, and three with count-aware memory; the latter has six
abstentions and three blocked cases. Both ledgers abstain on all twelve event
questions, appropriately. The one wrong exported-memory event answer invents a
contradiction despite the correct negative event being present in the evidence.

## Source accuracy differs from final-answer accuracy

Qwen retains all 24 correct source outcomes in every summary, but adds false
dated assertions in two summaries. Its count-aware instruction never produces
explicit numerical count triples. Phi's exported-prompt summaries have false
dated assertions in five of twelve cases. All nine valid Phi count-aware
summaries contain incorrect numerical counts: 30 of 54 explicit count claims
are false. Three further writers add invalid-schema numerical fields; those
outputs remain blocked, even though their facts lists preserve correct events.

The source audits use post hoc literal grammars plus model-assisted inspection
of residual prose. They are not independent human annotations. Claim counts
include dependent assertions from the same journal and must not be treated as
independent samples. Correct activity rankings can coexist with wrong counts.

## Interpretation and limitations

The fixed six-event interface in Pilot 003 influenced its findings. This follow-up
shows why that result cannot simply be generalized to unrestricted extraction.
It also demonstrates how insufficient answer space and strict option syntax can
distort an apparent comparison. These are diagnostic controls, not discoveries
that memory compression, arithmetic or output formatting can fail.

The journals are formulaic, short, fully observed and selected for development.
The study excludes active Mem0 request construction, provider schema enforcement,
native updates, embeddings, retrieval, realistic multi-session workloads and
frontier models. A query-aware oracle ledger is not a fair general-purpose
memory replacement. The post hoc budget and format analyses are not confirmatory.

Prior work already covers content-selective retention, aggregate reasoning,
structured queries, preference-versus-recall evaluation and component diagnosis.
Relevant inspected sources include
[Oolong](https://arxiv.org/html/2511.02817v1),
[S-RAG](https://arxiv.org/html/2511.08505v1),
[FinPerMA](https://arxiv.org/html/2608.04095v1), and
[AgingBench](https://arxiv.org/html/2605.26302v1).
Their existence does not settle every narrower question, but it rules out those
broad framings as our standalone novelty claim.

## Artifact map and next gate

- Original frozen protocol: `pilot-004.md`.
- Source-path correction: `pilot-004-source-correction.md`.
- Post hoc changes: `pilot-004-reader-budget-sensitivity.md` and
  `pilot-004-answer-format-sensitivity.md`.
- Model-specific results and source inspections: `pilot-004-qwen-*` and
  `pilot-004-phi-*` reports.
- Exact requests, outputs and source hashes: JSONL traces and manifests in
  `results/`; both strict and sensitivity analyses are retained.
- Figures: `results/figures/pilot-004-extraction.png` and
  `results/figures/pilot-004-extraction-answer-format.png`.

Do not scale this rejected hypothesis or present these development controls as
the requested ICML paper. The next candidate must identify a substantive result
beyond known selection, aggregation or component-attribution methods, verify its
actual execution path, and pass a fresh feasibility test before a confirmatory
study. No new candidate is yet selected. The full research objective remains
unfinished; no manuscript, public research repository or submission is claimed.
