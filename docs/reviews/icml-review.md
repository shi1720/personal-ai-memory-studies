# Simulated ICML main-track review

Review date: 20 September 2026. This is an internal AI-assisted technical review, not a review by ICML, an external researcher, or an acceptance prediction. No model API credentials were accessed. No manuscript, frozen protocol, or primary analysis was changed by this reviewer.

## Material assessed

The complete TeX manuscript, abstract, findings, discussion, appendix, main results table, completed-results report, release status, protocols, and numerical summaries in both final analysis JSON files. Primary-source abstracts for PerRecBench, Language-Based User Profiles for Recommendation, and Mem0 were checked. This review does not claim a complete literature search or a fresh execution of inference.

## Summary

The paper measures three interventions in a tightly scoped metadata-only rating task: historical rating permutation within users; replacement of full history with native Mem0-written text; and replacement of an LLM reader with history-only ridge regression. The held-out sample, public freeze, valid-output accounting, user-level uncertainty, and second implementation are strong reproducibility features. The Coat extraction result is supported in both readers; the MovieLens association result is correctly described as inconclusive after adjustment. The paper distinguishes pipeline effects from information loss and association use from uniquely individual taste.

The main-track weakness is contribution significance, not an identified numerical error. Permutation reliance and profile-versus-history evaluation are established. Combining these controls in one narrow experiment is useful, but two small quantized readers, one writer configuration, one extraction domain, short histories, and only categorical metadata leave substantial uncertainty about importance for current personal AI memory. Polishing presentation cannot itself establish a broad empirical contribution.

## Simulated scores

The following is an explicitly chosen internal rubric, not an assertion about an official current ICML score form. Overall scale: 1 clear reject, 2 reject, 3 weak reject, 4 borderline, 5 weak accept, 6 accept.

| Criterion | Score | Reason |
|---|---:|---|
| Technical soundness | 4/5 | Claims are unusually well bounded; paired design and primary analysis are appropriate for the declared estimand. One draw and finite model configurations restrict inference. |
| Originality | 2/5 | Application of established controls, rather than a new control principle, algorithm, or identification result. |
| Significance | 2/5 | Useful implementation audit; transfer beyond short metadata-only rating tasks is unestablished. |
| Clarity | 4/5 | Explicit contrasts, restrained conclusions, and comprehensive appendix. Some defensive repetition dilutes the central result. |
| Reproducibility | 4/5 | Detailed pins, protocols, and arithmetic checks. Raw traces are not released, and independent inference reproduction has not occurred. |
| Overall | 3/6 | Weak reject for ICML main track in its current evidential scope. Potentially suitable as a carefully positioned workshop or evaluation-focused submission after the fixes below. |
| Review confidence | 4/5 | High on manuscript and design assessment; no exhaustive novelty search or raw-inference replay. |

## Strengths

1. The held-out evaluation and public pre-inference freeze substantially reduce result-dependent model and analysis selection for the final study.
2. The permutation preserves the exact history rating multiset and metadata support. Token-length matching is audited rather than merely assumed.
3. The paper retains all malformed answers under a specified operational policy and shows common-valid sensitivities.
4. Ridge receives the same source information as the LLM, with fitting-user population models explicitly separated.
5. Null results, ordinary versus family-adjusted intervals, quantization, public-data contamination, and the absence of external replication are accurately disclosed.
6. The separate calculation implementation is a meaningful software check and is not misrepresented as independent scientific peer review.

## Fixable issues using existing evidence

### 1. Bring the numerical permutation probe into the main interpretation

The already-computed ridge results are highly informative and currently mostly buried in supplementary data:

| Dataset | Correct history MAE | Permuted history MAE | Descriptive difference |
|---|---:|---:|---:|
| Coat | 0.913851 | 1.128555 | +0.214704 |
| MovieLens | 0.845297 | 0.864664 | +0.019367 |

The sharp attenuation across datasets is also visible in this non-language reader. Add a short paragraph to the association subsection stating this. It makes the MovieLens boundary easier to interpret: limited recoverable genre-level signal is a plausible explanation, alongside reader behavior. This does not prove which explanation is correct. These differences should remain descriptive unless a new, explicitly post hoc analysis is added; do not silently enlarge the ten primary hypotheses.

Suggested prose: “The numerical probe shows a similar domain contrast: permuting history increases ridge MAE by 0.215 on Coat and 0.019 on MovieLens. These descriptive comparisons suggest that the weaker MovieLens association effect may partly reflect the supplied genre representation, rather than a limitation specific to language-model readers. They do not distinguish representation limitations from other dataset differences.”

### 2. Scope the extraction headline to the actual writer configuration

The abstract currently says “native Mem0 extraction increases” MAE. This is technically bounded later, but an abstract-only reader may attribute the finding to Mem0 generally. Prefer “the tested Qwen-written Mem0 configuration increases” or equivalent. The headline should retain that this is one pinned batch-ingestion configuration, with all stored texts read and retrieval bypassed.

### 3. Make the central contribution more compact

Keep a single clear statement that the contribution is an empirical diagnostic application, not a new permutation algorithm. Repeated caveats in introduction, related work, discussion, conclusion, and appendix consume space without adding a new boundary. Concentrate detailed scope conditions in a limitations paragraph, while preserving essential local qualifiers. Use the recovered space for one concrete result-driven diagnostic implication rather than more abstract claims about “understanding.”

### 4. Explain the model comparison completely

Name Phi-4's parameter scale in the methods alongside Qwen3-4B. State that results compare fixed quantized implementations and are not a scaling experiment. The latter is already in the appendix; a short main-text statement is useful.

### 5. Keep claims about outperforming baselines proportionate

Ridge is the predeclared primary comparator, not the strongest observed MAE baseline. MovieLens history median has MAE 0.817 versus ridge 0.845. The text correctly reports this, but the abstract's numerical-reader sentence could mention that simple history-statistic baselines are also competitive. Avoid a title, figure treatment, or abstract implying that ridge is the proposed solution.

### 6. Add the active extraction prompt or a reproducible source locator in the appendix

The reader instruction is readable in the PDF, while the active writer instruction is only described as native additive extraction. At minimum identify the active exported constant and exact source path at the pinned revision. If space permits, include its task-relevant instructions in an appendix block, clearly marking source quotation. This matters because applying a general conversational fact extractor to structured rating records is a major interpretation boundary. A reviewer should be able to inspect the operative representation assumption without reverse-engineering the code.

### 7. Make submission and preprint files genuinely different

The anonymous TeX currently still uses the preprint package option and calls itself a preparation artifact. A clean submission PDF should use the selected venue's current review mode and satisfy its line-number and anonymity requirements. Retain the named preprint separately. An anonymous paper is not by itself a fully anonymized artifact; remove or replace author-identifying supplemental repository links when the target venue requires it. This is a packaging fix, not evidence of scientific acceptance readiness.

## Evidence gaps that require new experiments

These cannot honestly be repaired by stronger wording or extra automated reviews.

1. **Memory-relevant task coverage.** A language-rich history and semantically meaningful downstream task, with both full-context and native-memory conditions, would test whether the observed extraction tradeoff extends beyond the current metadata-to-rating conversion. At present the extraction finding has no second-domain replication.
2. **Writer and implementation dependence.** A second writer model and a task-specific summarizer or an additional memory implementation would distinguish the current default extraction configuration from a broad memory-construction phenomenon. Crossed writers and readers would be stronger than merely adding a third reader.
3. **Contemporary model dependence.** A capable additional non-quantized or hosted reader under the same frozen input design would address the possibility that the findings are tied to local small-model format or arithmetic limitations. This should be an explicit extension with a new freeze, not retroactively merged into the original primary study.
4. **Permutation stability.** Multiple independently seeded permutations on a prespecified subset would quantify variability of the within-user intervention. The current pooled user bootstrap is appropriate for the declared fixed-system sample contrast, but does not estimate individual-user permutation uncertainty.
5. **Mechanistic extraction explanation.** A prespecified retention audit or matched-length representation control could establish whether missing rating associations, unsupported inferences, or representation format drives the extraction cost. The existing pipeline effect is valid without this, but mechanism is presently unresolved.

Not all five are required for every venue. For a credible main-track significance upgrade, prioritize a genuine language-rich extraction replication plus at least one writer or model extension. There is no assurance that these would produce favorable results or acceptance.

## Sources checked

- [PerRecBench: Can Large Language Models Understand Preferences in Personalized Recommendation?](https://arxiv.org/abs/2501.13391). Established critique of rating bias and item-quality confounds; 19-model evaluation.
- [Language-Based User Profiles for Recommendation](https://arxiv.org/abs/2402.15623). Established encoder/decoder profile framework and profile versus raw-history comparisons.
- [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413). Native system is motivated and evaluated on conversational memory, unlike the structured metadata task here.

## Recommendation to the author

Deliver a polished, accurate paper and a correctly formatted anonymous version. Do not advertise that automated reviewers certify ICML readiness. The strongest honest current positioning is a reproducible diagnostic empirical study with a clear narrow finding and careful negative results. Any larger main-track claim should be earned by new evidence, rather than by removing the limitations that currently make the manuscript trustworthy.
