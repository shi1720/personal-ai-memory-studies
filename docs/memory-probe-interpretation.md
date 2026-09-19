# Interpreting a memory-only confidence probe

2026-09-19. Development analysis, not a manuscript or a novel method.

## What the mathematical check establishes

A fixed memory-only response channel satisfies conditional independence of
response and latent state given its inputs. This is an elementary property,
not a new impossibility theorem about all memory evaluation. It does not imply
that response entropy cannot be a useful empirical predictor.

In particular, consider a response space equal to the state space and a reader
whose distribution is exactly the true posterior over states given memory.
Its response entropy equals state uncertainty even though their conditional
mutual information is zero. The added posterior-sampling positive control uses
the same finite example: it returns the retained bit exactly and samples a fair
bit on erasure. State and response entropies both equal zero in the retained
regime and one bit in the erased regime. This exact control was added after the
inference protocol was frozen; it changes neither prompts nor empirical scoring.

The ranking reversal, deterministic tie and posterior-sampling control together
show that calibration assumptions matter. A zero conditional-information term
does not by itself imply a bad metric. Nor does an unrestricted counterexample
invalidate the empirical effects of a trained reward that also uses outcomes.
Natural-language token entropy additionally measures verbalization choices and
is not automatically entropy over semantically distinct task states.

## Why this screen cannot establish a selection advantage

The candidate memories reuse two different writing procedures on twelve
fictional journals. They are not exchangeable samples from one writer. The
downstream outcomes and limited-grammar audits were known before the probe run,
so this is development work rather than independent validation.
Qwen's two writer outputs are exactly identical lists of facts for extract-00
and extract-01. Repeated calls on these inputs are accounting checks, not
additional independent evidence.

Under the previously fixed exact-option scoring, Qwen's two writer candidates
have identical correctness on every journal. Phi has only two valid pairs with
different correctness, extract-05 and extract-10. The unmodified exported-prompt
candidate is correct in both, and the count-aware candidate is wrong. Three
other Phi pairs contain an invalid writer and cannot enter a complete-pair
comparison. Thus even perfect selection cannot beat the always-exported-prompt
baseline on these observed candidate pairs. Confidence might avoid or incur a
loss here, but this is not a well-powered test of general selection quality.

Strict-format results remain separately reported because syntax failures change
the apparent correctness pattern. The first-32-token diagnostic is not a silent
replacement for the main completed-response score. Its actual generation cost
is the full recorded call cost, not a hypothetical early-stopping cost.

## Existing baselines are substantive

[QAFactEval](https://aclanthology.org/2022.naacl-main.187/) already checks
summary-derived questions against the source, accounts for unanswerability,
filters problematic questions and combines QA with entailment. Primary PDF
Sections 3.1-3.3 were read; no baseline implementation was executed.

[QuestEval](https://aclanthology.org/2021.emnlp-main.529/) combines QA-based
precision and recall, including question weighting. It explicitly distinguishes
answerability confidence from factual correctness. Primary PDF Sections 3-4 and
the displayed experimental setup were read; no baseline was executed.

Replacing a memory-only confidence score with a source comparison is therefore
not, by itself, a new contribution. A substantive follow-up would need a precise
unresolved reliability or cost question, faithfully implemented comparisons,
fresh histories, enough pairs with meaningful quality differences, and useful
evidence beyond familiar confidence failures. This screen is not a reproduction
of trained MMPO, nor evidence that its reported results are false.
