# Provisional review of the language-rich confirmation design

Prepared 20 September 2026. This is an internal AI design review, not a locked inference protocol, public preregistration, external peer review, or evidence that an experiment has been run. No target outcomes were accessed for this recommendation. The completed rating-prediction paper and its frozen results remain separate and unchanged.

## Question and fixed population

The prepared cohort contains 60 development users, 200 reserved confirmation users, and 964 disjoint history-only donors. Each evaluated user supplies 12 earlier substantive reviews and three later observed ratings. Histories and target events straddle the fixed 1 January 2022 boundary. The final study should ask how specified memory-construction pipelines preserve useful evidence for predicting these three observed ratings from language-rich histories.

This is not evidence about all purchasers, unreviewed products, general personal understanding, conversational recall, or online deployment. Reviews are selected observations. The verbosity and context-budget screens further select the population. Catalog metadata come from a later snapshot whose availability at the prediction date is not certified. Three target ratings per user limit precision and make within-user ordering a sparse secondary diagnostic.

The fixed sample is 200 confirmation users, not 600 independent observations. Outcomes must not influence inclusion, inference choices, donor assignment, or sample size. Existing confirmation users must not be consumed as additional development cases.

## Minimum one-writer design previously recommended

For each of the two fixed reader families, evaluate no history, all 12 reviews, complete Qwen-written native Mem0 memory, a Qwen-written task-matched history summary, and four full records selected by the specified joint-query BM25 procedure. Include history mean, history median, and constant 3 without model calls.

The smallest useful primary family in that design has four paired user-MAE contrasts: native minus full history, and native minus task-matched summary, separately for each reader. Other comparisons are descriptive. Both writers receive histories only, never target identities or outcomes. Both readers consume the same stored outputs. The history-only summary is an established profile-generation baseline, not a new method; see [Zhou et al., Language-Based User Profiles for Recommendation](https://arxiv.org/abs/2402.15623).

This design adds a language-rich domain and a task-specific baseline. It does not test writer-model robustness: two readers of Qwen-written stores are still one writer configuration.

## Recommended prospective upgrade: two writers with matched summaries

**Add both Phi-native Mem0 and Phi task-matched summary, retaining their Qwen counterparts.** Adding Phi-native alone provides some writer breadth, but comparing it only with a Qwen task summary changes the writer model and construction procedure simultaneously. A summary from each writer permits meaningful within-writer comparisons and avoids that additional confounding.

Use a two-writer by two-reader crossing. For every user, construct four independent history-only representations:

1. Native Mem0 with the pinned Qwen writer.
2. Task-matched summary with the same pinned Qwen writer.
3. Native Mem0 with the pinned Phi writer.
4. Task-matched summary with the same pinned Phi writer.

Each reader receives seven evidence conditions: no history, full history, the four representations, and BM25-selected history. Generate every representation once and read it with both readers. Reset native stores independently by user and writer. Keep the source batch, active native implementation, summary instruction, decoding policy, and export checks fixed. Use each model's native chat template. Writer prompts must remain target-independent.

The matched summaries control writer identity, but native versus summary is still a comparison of complete specified pipelines. It does not isolate wording, storage, information loss, or compression. Equal generation-token allowances across tokenizers are not equal information budgets, and a 400-word summary cap does not equalize native-memory length.

Engineering preflight must verify both writers and both readers before commitment. The current Qwen-only three-case preflight cannot certify Phi-native operation, Phi summary compliance, cross-reader context limits, or Phi runtime feasibility. If a configuration fails, record the development failure and revise before freezing; do not silently substitute a different writer during confirmation.

## Primary family for the recommended two-writer design

Predeclare eight paired contrasts, indexed by native writer w and reader r:

- Four native-versus-full contrasts: MAE(native_w read by r) minus MAE(full history read by r).
- Four native-versus-matched-summary contrasts: MAE(native_w read by r) minus MAE(summary_w read by r).

Positive values indicate greater error for native memory under that particular writer-reader configuration. Report all eight separately. Do not average across writer-reader cells and then claim robustness: opposite effects can cancel. A statement that an effect holds across both tested writers and readers requires the relevant cell-specific evidence, not a pooled result.

Use ordinary 95% intervals plus Bonferroni-adjusted 99.375% intervals for the family of eight. For percentile bootstrap intervals, the adjusted quantiles are 0.003125 and 0.996875. Dependence between contrasts does not justify treating eight correlated outcomes as extra independent evidence. The procedure is an approximate bootstrap uncertainty analysis, not an exact finite-sample guarantee.

If the intended primary question is only whether native-memory effects replicate across writers, an alternative is the four native-versus-full comparisons alone, with all matched-summary comparisons explicitly secondary. Decide this before scoring development outcomes and retain that decision regardless of effect direction. My preference is the eight-contrast family because both breadth and task alignment motivate the additional representations. Do not introduce new confirmatory writer-interaction claims after observing the results.

## Development and precision decision before reserved inference

After the engineering preflights, freeze a candidate configuration and run all 60 development users across the complete selected design. Materialize only development target ratings for this phase. Inspect all failures rather than restricting analysis to successful cases. Check export completeness, complete native request lengths, output termination, reader validity, summary length compliance, and the resource budget.

Choose the precision target before inspecting development accuracy. A reasonable planning choice is a maximum adjusted-interval half-width of 0.10 MAE at 200 confirmation users, described as an analyst-selected resolution rather than a universal practical-importance threshold. For each of the eight contrasts, estimate dispersion of paired user-level differences on development data. Use a prespecified conservative upper dispersion estimate, such as a fixed-seed upper bootstrap quantile, to project the interval width at n=200 with the eight-test critical value. Record all assumptions and uncertainty. This is a planning gate, not a guarantee of future precision or power.

Compared with four primary tests, eight tests have a larger normal-approximation critical value, approximately 2.73 rather than 2.50. Thus the same 0.10 half-width target requires a dispersion estimate of approximately 0.52 MAE or less at 200 users, before any additional conservative inflation. These approximate figures are planning aids, not measured development results.

If a contrast misses the chosen precision requirement, declare the planning NO-GO before reserved inference. Do not add donor outcomes, extend the fixed sample, relax the target after seeing the direction, or keep only favorable comparisons. A changed aim would need an explicit prospective amendment and an honest distinction from the originally proposed confirmation. Engineering reliability and statistical precision are separate gates.

For the final frozen analysis, use at least 100,000 fixed-seed paired-user bootstrap resamples, fixed ordering and quantile interpolation, and report the complete family. Keep all-user operational results with constant-3 fallback and paired common-valid sensitivity. Do not claim equivalence from an interval containing zero. Report writer and reader failure categories separately. Do not retry, repair, drop, or regenerate failed confirmation responses unless the locked protocol defines a specific transport procedure consistently in advance.

## Call budget

Counts below assume each native write produces exactly one model request, as verified in preflight. A native pipeline can make additional requests, so the eventual protocol must explicitly bound and record actual calls rather than infer them from users.

| Design | Users | Writer calls | Reader calls | Total |
| --- | ---: | ---: | ---: | ---: |
| One writer, development | 60 | 120 | 600 | 720 |
| One writer, confirmation | 200 | 400 | 2,000 | 2,400 |
| Two writers, development | 60 | 240 | 840 | 1,080 |
| Two writers, confirmation | 200 | 800 | 2,800 | 3,600 |

The recommended two-writer development plus confirmation totals 4,680 calls, excluding all engineering preflights, failed development configurations, and any native extra calls. It adds 1,560 calls relative to the one-writer design. Phi writing may be materially slower than Qwen writing on the local hardware; preflight runtime and full-prompt memory requirements must inform the feasibility decision. Do not weaken the scientific design silently to meet an unstated runtime budget.

## Fairness controls and resource interpretation

Keep all 12 full historical reviews intact in the full-history arm. Export every stored native text and verify completeness. BM25 receives target catalog strings and may therefore select target-relevant history; describe it as query-conditioned retrieval, not a target-independent memory. Its selected raw records must also fit without silent truncation.

History mean and median should remain visible even if they outperform all language-model arms. Their success can demonstrate the importance of rating tendencies, but it cannot establish that language evidence is useless in general. Report user-macro MAE, RMSE, limited within-user concordance, validity, prompt/output tokens, and construction/read costs separately. Treat elapsed engineering timings as including their documented overhead rather than isolated model speed.

Freeze source hashes, partitions, prompts, model conversions, actual budgets, condition order, parser, fallback, failures, contrasts, resampling, and scoring guards publicly before the first reserved prediction. Withhold reserved accuracy until every planned configuration is complete. Preserve unfinished or failed runs and their reasons rather than reporting only a successful configuration.

## Donor control recommendation

Do not include donor inference in the minimum confirmation or its primary family. The 964 donors can remain unused. Replacing a user's history changes product support, semantics, rating distributions, and often length; it cannot reproduce the original Coat control's rating-preserving estimand.

If a donor sensitivity is prospectively retained, assign histories deterministically without replacement using no future outcomes, exclude donors who reviewed any recipient target product, and lock all matching and tie rules. Keep each donor's review-rating associations intact. Describe the estimand as own-history versus assigned-donor-history utility, not a pure personalization or preference-understanding effect. Any matching by historical ratings or length controls only those chosen observed properties; it cannot equalize semantic support.

## Contribution boundary

The two-writer design is a substantive expansion of empirical coverage: language-rich chronological histories, a new observational domain, two native writer models, two readers, and matched task summaries. It still studies only three observed future ratings per user in a selected population. It does not create a new memory algorithm, establish generic frontier-model performance, or justify a claim of ICML-level novelty or acceptance. The purpose of confirmation is to learn whether earlier findings persist or fail under this more informative setting, including an inconclusive or opposite result.
