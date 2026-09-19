# Pilot 003: completed retention audit

Research owner: Shivam Gupta. Status: exploratory development result, not a
submission-ready paper or a demonstrated new memory method.

## Finding

Individually accurate retained events can give an inaccurate aggregate picture
of the source journal. However, the pilot does not support a universal positive
retention bias, a model-independent failure of representative prompting, or a
claim that a new algorithm is necessary. Effects vary substantially by model,
instruction and rendering. This narrows the research direction rather than
establishing an ICML-level contribution.

## Execution and provenance

Twelve fictional journals contain 24 recorded visits each: 12 visits to each of
two activities, with empirical positive-outcome rates 0.75 and 0.50. Each writer
retains six event IDs. No user behavior was simulated by an LLM and no private
user data was used. All valid IDs point to unchanged source events.

There were 336 actual generation calls: 48 original Qwen cases, 72 Qwen controls,
108 Mistral cases and 108 Phi-4 cases. Twelve Qwen control prompts exactly repeat
original prompts and produce identical outputs. There are 324 unique
model-journal-condition combinations but only twelve journal construction units.
This is not a 324-user study. The models are community four-bit conversions of
Qwen3 4B Instruct 2507, Mistral 7B Instruct v0.3 and Microsoft Phi-4.

Measured generation sections total 929.65 seconds, excluding downloads, model
loading, file hashing and preprocessing. This is descriptive local runtime,
not a cross-model efficiency benchmark. Mistral uses a single-user-message
adapter because its native default template does not support a system role.
Model identity, templates and role placement are therefore confounded in
cross-model comparisons. All runs use temperature zero and the same fixed
output-token ceiling; no malformed output was regenerated or repaired.

## Serialization results

| Model | Actual calls | Strict bare-JSON valid | Fence-only recovery | Still invalid |
| :--- | ---: | ---: | ---: | ---: |
| Qwen3 4B | 120 | 120 | 0 | 0 |
| Mistral 7B | 108 | 99 | 0 | 9 |
| Phi-4 | 108 | 0 | 108 | 0 |

The primary analysis enforces the frozen bare-JSON protocol. Phi-4 encloses all
its arrays in Markdown code fences. A separately documented post hoc sensitivity
analysis accepts only a single fenced array, then applies the unchanged
six-distinct-known-ID validator. It recovers all 108 Phi-4 selections. It does
not recover Mistral's extra prose or invalid identifier. Treating every Phi-4
format failure as a semantic memory failure would be misleading.

## Aggregate fidelity after fence-only recovery

The entries below are mean absolute error / mean signed error, on a probability
scale. The sensitivity analysis does not change Qwen or Mistral selections.
Phi-4 values are post hoc, not primary strict-format results.

| Condition | Qwen3 4B | Mistral 7B | Phi-4 |
| :--- | ---: | ---: | ---: |
| Important, plain | .375 / +.375 | .353 / +.047 | .330 / +.253 |
| Important, detailed | .427 / +.427 | .378 / +.358 | .408 / +.346 |
| Representative, plain | .340 / +.340 | .241 / -.074 | .257 / -.069 |
| Representative, detailed | .385 / +.385 | .337 / +.267 | .240 / +.059 |
| Important, liked/disliked | .365 / +.365 | .297 / -.001 | .332 / +.256 |
| Archive, enjoy/not enjoy | .375 / +.375 | .322 / +.170 | .326 / +.167 |
| Archive, liked/disliked | .354 / +.354 | .299 / -.028 | .332 / +.256 |
| Proportional, enjoy/not enjoy | .384 / -.287 | .455 / -.370 | .236 / -.208 |
| Proportional, liked/disliked | .388 / -.297 | .411 / -.336 | .257 / -.215 |

Errors average over represented activities in valid selections, then journals.
They exclude missing activities and invalid outputs. They are not directly
comparable when those denominators differ. The accompanying figures and JSON
report every invalid and missing count. No significance test or population
estimate is claimed. These are properties of selected event sets, not answers
from a downstream assistant.

Uniform sampling at the same six-record budget has mean available-activity MAE
0.2111 and signed error -0.0024 over 1,000 draws per journal, with 153 missing
activity slots in 24,000. Those draws are Monte Carlo repetitions, not users.
A four-count ledger solves the two fixed frequency queries exactly but cannot
answer individual-event questions. A task-specific six-event quota can also
preserve both rates exactly. These are known statistical controls, not proposed
innovations or universal equal-capability baselines.

## What survived, and what did not

- Qwen's important/plain writer retains 72 positive events out of 72 selected.
  Mistral retains 51/72 and Phi-4 66/72. Qwen's extreme result is not universal.
- Adding incidental detail to selected positive events raises their mean recall
  under the important writer in all three models: +.347 Qwen, +.472 Mistral and
  +.278 Phi-4, on the same twelve paired journals. Length and distinctiveness
  change together, so this is not an isolated causal salience estimate.
- The representative writer does not show the same rendering effect everywhere.
  Phi-4's designated-event recall decreases by .042; among its eight pairs with
  both activities represented in both conditions, MAE decreases by .010.
  Therefore the claim that detail consistently harms representative retention
  is rejected.
- The proportional instruction yields negative signed bias in every model. It
  improves Phi-4's mean MAE relative to important/plain (.330 to .236 with
  negation wording), but does not do so for Qwen or Mistral. The prompt explicitly
  highlights negative evidence, so overcorrection is one plausible explanation,
  not an established mechanism.
- Qwen's important-writer MAE increase under detailed rendering disappears on
  its seven complete-activity pairs. Its larger all-row MAE partly reflects
  changed missingness. Reporting only the pooled error would conceal this.

## Research decision

Do not write a paper claiming a new positivity-bias discovery or a universal
failure of LLM memory selection from this pilot. Prior work already studies
content-dependent retention, affective memory distributions and response-aware
selection. See `retention-closest-work.md` for precise scope and primary sources.

The next gate is practical validity: test native memory extraction and a
subsequent reader against full history, on fresh controlled journals with
independently balanced detail and outcome. Separate missing evidence, incorrect
facts, reader errors and abstention. A prompt-component test is not an end-to-end
reproduction of a deployed product. The design memo is
`retention-next-study-design.md`; it has not yet been executed or frozen.

The larger goal remains an original, technically substantive and reproducible
paper. Current evidence is useful for selecting that contribution, but novelty,
external validity and conference readiness are unresolved.

## Artifacts

- Protocols: `pilot-003.md`, `pilot-003-controls.md`, `pilot-003-replication.md`.
- Syntax amendment: `pilot-003-format-sensitivity.md`.
- All rendered prompts and raw outputs: `../results/pilot-003*-predictions.jsonl`.
- Strict analyses and paired sensitivity: `../results/pilot-003*-analysis.json`
  and `../results/pilot-003-format-sensitivity.json`.
- Figures: `../results/figures/pilot-003-retention.png` and
  `../results/figures/pilot-003-retention-sensitivity.png`.
- Reproduction commands: `../README.md`. All 38 measurement tests pass.
