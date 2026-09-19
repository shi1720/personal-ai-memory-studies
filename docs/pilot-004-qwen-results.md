# Pilot 004: completed first-model gate

Qwen3 4B, community four-bit conversion. The second-model study is separate
and was not complete when this report was written. All twelve journals are
fictional development examples, not independent samples of real users.

**Source correction:** this tests an upstream-exported prompt, not the active
extraction prompt at the pinned Mem0 revision. See
`pilot-004-source-correction.md`. Historical condition names below are retained
to match the raw data; they do not identify a native product run.

## Decision

This first-model test does not support scaling the selective-retention claim.
The unmodified exported prompt preserves the correct dated outcome for every source event.
It occasionally adds contradictory claims, but its downstream frequency score
matches full history after increasing the reader's output budget. The earlier
forced six-event selection result does not transfer to this unrestricted
extraction interface.

This is an extraction-prompt component test. It excludes Mem0's native updates,
embeddings, retrieval and backend. It cannot establish deployed-system failure
rates or a new memory algorithm.

## Execution

The frozen original protocol scheduled 120 generations: 24 writers and 96 readers.
All completed. Both writer conditions produced valid facts lists in all twelve
journals, without truncation. Native extraction averaged 23 facts and 1,337.58
stored UTF-8 bytes; count-aware extraction averaged 25.5 facts and 1,524.75 bytes.
These are observed operating points, not equal storage budgets.

The original 256-token reader allowance truncated 22 frequency responses.
The separately documented post hoc sensitivity reran **all 48 frequency cases**
with 768 output tokens, retaining exactly the original prompts and extracted
memories. All 48 completed with valid JSON and no truncation. Responses that
originally ended normally did not change. The original outputs remain intact.

Measured generation time was 661.91 seconds for the original run and 491.98
seconds for the sensitivity. Loading, hashing, preprocessing and analysis time
are excluded. The 168 calls are not 168 independent experimental units.

## Results

Each table entry is a count out of twelve. C = correct; W = wrong;
A = abstained; I = invalid. No reader was blocked by an invalid writer.

| Context | Frequency, original C/W/A/I | Frequency, larger budget C/W/A/I | Dated event C/W/A/I |
| :--- | :--- | :--- | :--- |
| Full journal | 1/0/0/11 | 9/3/0/0 | 12/0/0/0 |
| Native extraction | 3/2/0/7 | 9/3/0/0 | 12/0/0/0 |
| Count-aware extraction | 7/2/0/3 | 9/3/0/0 | 12/0/0/0 |
| Exact count ledger | 12/0/0/0 | 12/0/0/0 | 0/0/12/0 |

At the larger budget, both extracted contexts retain eight of the nine answers
that full history gets right. Each loses one such answer and gains one answer
where full history is wrong. Equality of total accuracy does not mean equality
case by case. The ledger supplies correct frequency evidence, but deliberately
contains no dated-event information; its twelve event abstentions are appropriate.
It is an oracle representation control, not a demonstrated extraction method.

All three wrong full-history frequency answers concern equal-rate journals.
The native and count-aware conditions get one of these equal-rate cases right
and instead fail extract-06. This small development result motivates inspecting
reader aggregation, not claiming a statistically established subgroup effect.

## Source fidelity

The post hoc literal-claim audit and model-assisted inspection find all 24
correct source outcomes represented in every extracted summary. They also find
additional false claims in two outputs: eighteen in extract-03's count-aware
summary and four in extract-05's native summary. These are contradictions added
to retained evidence, not simple selective omission. See the separate source
inspection report for the exact comparisons and parser limitations.

No output supplies explicit total/enjoyed/not-enjoyed count triples, even under
the count-aware instruction. The comparison therefore tests the effect of that
instruction as actually followed; it does not test an accurate learned counting
representation. Generic numerical aggregation and structured-query solutions
are established prior work, including Oolong and S-RAG.

## Limits and next decision

The output-budget change was chosen after early truncation was observed. It is
not preregistered confirmation. The original protocol and post hoc sensitivity
must both be reported. The formulaic journal grammar and small sample restrict
external validity. This run does not test natural preference change, arbitrary
user questions, long histories, repeated memory updates or frontier models.

Complete the already specified Phi-4 check. If the same practical-validity gate
fails, archive the forced-selection direction rather than enlarging a synthetic
benchmark around an unsupported failure mechanism. A manuscript needs a new
substantive contribution and stronger evidence; these controls alone do not
meet the requested ICML standard.

## Reproduction artifacts

- `results/pilot-004-qwen-analysis.json`: original scores and costs.
- `results/pilot-004-qwen-budget-analysis.json`: all higher-budget comparisons.
- `results/pilot-004-qwen-claim-audit.json`: literal claims checked against source.
- `docs/pilot-004-qwen-source-inspection.md`: bounded qualitative inspection.
- `results/figures/pilot-004-extraction.png`: all completed model comparisons.
- Both manifests and JSONL traces preserve exact prompts and raw outputs.

Prior-work links: [Oolong](https://arxiv.org/html/2511.02817v1),
[S-RAG](https://arxiv.org/html/2511.08505v1).
