# Language-rich personal memory: prospective confirmation protocol draft

Prepared 20 September 2026 during development inference, without reading development outcomes, reserved inputs, or reserved outcomes.

**Status: draft, not frozen, not a preregistration, and not authorization to open reserved inputs or run confirmation.** This is a proposed complete operational specification for implementation and review. No confirmation runner, label gate, scoring integration, or resource adapter is certified by this document. The existing Coat/MovieLens paper and all frozen development dependencies remain unchanged.

## 1. Question and estimand

Evaluate whether the specified native memory construction pipelines preserve useful information for predicting three later observed product ratings from twelve earlier substantive reviews. Compare native memory against its complete source history and against a task-matched summary written by the same model. Cross two fixed writers with two fixed readers. This is a confirmation of specified pipeline contrasts, not a new memory algorithm or a causal study of human preferences.

The unit is the user. For writer `w`, reader `r`, and user `u`, compute the native pipeline's mean absolute error across that user's three targets minus the comparator pipeline's error across the same three targets. The comparator is either full history read by `r` or the summary written by `w` and read by `r`. Positive differences mean greater native-pipeline error. There are exactly eight primary contrasts, and every contrast includes all 200 reserved users under the failure policy below.

The population is the already selected Musical Instruments reviewers, subject to the fixed language, chronology and context screens. It is not all purchasers, all personal assistants, or unobserved preferences. Selectively written reviews, retrospective catalog metadata, shared products, possible reviewer dependence, and unknown model pretraining overlap limit interpretation. No claim of point-in-time deployment accuracy is supported.

## 2. Mandatory gates before reserved access

All of the following must be documented before the confirmation input loader is enabled:

1. Every development stage is complete under its frozen attempt policy, with hashes, full cell coverage, stage handoffs, actual request attribution, model identities and token contracts verified. Ordinary accounted output failures do not by themselves constitute integrity failures.
2. Development target labels are materialized only under the existing completed-development gate. The primary development analysis and the separate computational verifier agree on inputs, validity, operational predictions, metrics, all eight contrasts and the precision decision.
3. The original precision rule returns GO for all eight contrasts: the fixed empirical upper dispersion calculation projects adjusted half-width at most 0.10 MAE at 200 users. Do not relax the target, change the family, enlarge the sample, drop a contrast, or select a favorable writer because of development effects. This is a precision-planning condition, not guaranteed coverage or a favorable-accuracy condition.
4. Publish the complete development results, failure counts, integrity review and precision decision with their hashes. Preserve unfavorable, inconclusive and failed findings. No post hoc minimum success rate is invented from observed development validity; feasibility and integrity must be assessed transparently under the unchanged configuration.
5. Implement and independently review the confirmation runner, reserved-input gate, delayed label materialization, primary scorer, separate numerical verifier and resource adapter. Tests must use invented inputs or the already permitted development records, never reserved cases as new preflights.
6. Freeze and publish the final protocol and implementation before the first reserved prediction. The final manifest must link the passing development decision and exact input, source, model, environment, prompt, parser, inference, analysis and uncertainty hashes. The present draft is not that freeze.

A development NO_GO leaves the reserved cohort unused for this protocol. A changed scientific aim requires a separately identified prospective amendment; it cannot silently turn a failed gate into confirmation. Nothing in this draft guarantees eventual execution or acceptance by a venue.

## 3. Fixed cohort and information boundary

Use exactly the 200 users already assigned to reserved confirmation by the frozen preparation, in its recorded SHA-256 order. Do not replace difficult, invalid, unusually long, or inconvenient users. The 60 development users and history-only donors are excluded. No preflight or development output is reused as a confirmation observation.

Retain the existing input preparation unchanged: deduplicate parent products by first event; select the latest twelve first-time product events strictly before 1 January 2022 UTC and the first three strictly after; require the existing catalog, historical language and token screens. Do not backfill a different history or target window. Keep complete earlier review text, rating, historical date, and selected product metadata exactly as serialized by the frozen builder.

Writers receive `writer_history(instance)` only. They must never receive target product identities, target text, outcomes, or label-derived summaries. Readers receive the same three ordered target catalog title/feature records in all conditions. Excluded target fields remain excluded, including target review text/title, rating, price, aggregate rating, rating count, product description and images. Target products are new to the supplied history, not necessarily unseen in the catalog or pretraining.

The prepared history and full-reader screening limits remain 6,144 and 12,288 tokens per pinned tokenizer, respectively. They are eligibility rules already applied, not permission to truncate an actual request. Every actual constructed request must separately pass the execution budget.

The gated input loader must verify the prepared confirmation file hash and exact ordered case set against the frozen preparation. Reading its bytes to verify the hash is permitted only after the gates above; decoding and inspecting it is also reserved access. No label file or target source mapping is opened by inference. Code must not enumerate donor outcomes or dynamically search for substitutes.

## 4. Fixed models, writing and seven reading conditions

Use the same pinned local Qwen3-4B-Instruct-2507 and Phi-4 4-bit conversions, tokenizer/chat-template files, Mem0 implementation, native configuration, embedding components and client/server environments as the accepted development configuration. Exact revisions and all model-file hashes come from the existing model manifests and are copied into the final confirmation dependency record. A newer model or package version is a different experiment.

Each user has four independently constructed representations: Qwen-native, Qwen-summary, Phi-native and Phi-summary. A native store is isolated by user and writer, ingests the complete history once through the same native path, and exports every stored text under the existing ID/text completeness checks. Both readers consume the same saved representation; never regenerate it per reader. The summary uses the unchanged `SUMMARY_SYSTEM`, output schema, nonempty requirement and maximum 400 whitespace-delimited words. Do not repair or truncate outputs.

Each reader has these seven conditions in the canonical order:

1. `no_history`
2. `full_history`
3. `native_qwen`
4. `summary_qwen`
5. `native_phi`
6. `summary_phi`
7. `bm25_history`

Preserve the existing evidence serialization, reader prompt, sentinel strings and parsers. Full history contains all twelve complete earlier reviews. BM25 uses the combined three-target catalog query to select four complete historical records and presents them chronologically, with the frozen scoring and tie rules. This is target-conditioned retrieval, unlike either history-only writer. It is not a task-independent memory baseline. No donor condition, new recommender, prompt revision, hidden context compression or additional numerical model is introduced.

### Native dates

Preserve native date fields exactly as generated by the pinned implementation at execution time, as in development. Do not substitute 2022, force the development date, remove a native date, or edit a saved prompt. Persist complete actual prompts, request start times, server session times, local timezone and UTC execution timestamps. If a run crosses a date boundary, keep those differences and disclose them. Native calendar context and sequential model stages are limitations of this implementation-level comparison, not randomized effects. A date-normalized method would require a separate prospective amendment and development, not an undocumented confirmation patch.

## 5. Inference settings, order and budget

Use temperature 0, top-p 1, maximum 2,048 generated tokens per writer and 256 per reader, timeout 360 seconds, and zero client retries. Count each complete actual chat-template prompt with the corresponding pinned tokenizer before transport. Prompt count plus reserved output allowance must be at most 16,384. On a returned completed response, require exact tokenizer/server prompt-count agreement and integer completion/total counts consistent with the allowance. Wrong model identity, unexpected extra native generation, missing provenance or a breached transported-request budget is an integrity failure.

Run one pinned model server at a time, sequentially, with the same recorded serving/cache configuration. Use loopback transport and the local non-secret placeholder. Hosted API credentials are not part of this experiment. Record hardware, package versions, server settings, sleep inhibition, pauses and local contention. No concurrency or throughput optimization is introduced during confirmation.

| Stage | Per-user work for all 200 users | Planned cells and maximum audited requests |
| --- | --- | ---: |
| `qwen_base` | Qwen native and summary writes; Qwen reads no history, full history, Qwen native, Qwen summary and BM25 | 1,400 |
| `phi` | Phi native and summary writes; all seven Phi reader conditions | 1,800 |
| `qwen_cross` | Qwen reads Phi native and Phi summary | 400 |

The plan contains 800 writer cells and 2,800 reader cells, totaling 3,600 fresh cells. A cell can fail before transport, so planned cells are not evidence that all 3,600 transports occurred. Count every actual audited attempt, including requests failing before native callbacks, and forbid an extra generation within a cell. A native setup failure may have zero audits; every other cell has exactly one audited request or a documented integrity blocker.

Within each stage, traverse the full reserved case order. For each user, perform native then summary writing before that stage's reads. Rotate the stage's reader-arm list by `position % len(stage_arms)`, where position is the zero-based index in the complete 200-user reserved list. The lists are the five Qwen-base arms above, all seven canonical arms for Phi, and `(native_phi, summary_phi)` for Qwen-cross. This extends the development ordering rule without selecting order from outcomes. No later stage begins without the prior stage's verified handoff.

## 6. Persistence, failures and complete-pipeline fallback

Freeze one confirmation manifest and acquire an exclusive execution lock. Reserve each cell durably before its operation. Keep raw requests/responses, IDs, response hashes, actual model identity, request audits, exact counts, termination, export records, durations and cell ledgers. Stage handoffs cover every cell and audit hash; final completion must establish an exact planned-cell inventory and one-to-one attribution of every actual transport. Results and errors are immutable.

Resume may skip only a verified terminal cell. It must not regenerate an ambiguous interrupted request, retry a recorded error, increase a timeout, add a reader repair, or change a parser. If a crash leaves unresolved attempt provenance, stop and report an incomplete experiment. Do not invent a fallback prediction for a cell whose attempt status is unknown. Recovery solely from an already persisted auditable response requires a prospectively reviewed, deterministic reconstruction path; absent that implementation, it remains blocked.

The validity rules are unchanged. A reader must terminate normally and yield exactly three finite nonboolean numbers in [1, 5] under the frozen narrow code-fence tolerance. Native memory must be nonempty, normally terminated, free of cleanup error, and fully matched between insertion and export by ID and text. A summary must pass the frozen JSON profile, termination, nonempty and word-count rules. A terminal transport error or invalid completed output remains recorded.

After an invalid writer, execute the same fixed sentinel-evidence reader calls as development, provided their request contracts remain valid. These are diagnostic reads whose resource use is counted. For operational scoring, a required invalid writer makes the entire pipeline invalid even when its reader returns a valid array. Substitute exactly `[3, 3, 3]` whenever a required writer or reader is invalid. No-history, full-history and BM25 require only valid readers. Never drop an invalid user or substitute the diagnostic array for the fixed fallback.

Report writer setup, transport, abnormal termination, format, empty/export and cleanup failures separately where the audit supports that distinction. Engineering completion means every planned cell is accounted for, not universal validity. A wrong-model or broken-provenance run cannot be relabeled successful simply because all files exist.

## 7. Delayed outcomes and seventeen-system scoring

Keep confirmation outcomes unopened until all three stages and all 3,600 cells are accounted for with intact provenance. Only then may a dedicated label-materialization command verify the source archive and the exact frozen reserved target-row mappings. Recheck user identity, distinct parent products, chronology, target order and prepared catalog/history correspondence. Access rating fields for the 600 selected target rows only; do not select labels for donors or new users. Disclose that locating rows parses the source archive. Store labels privately with source and mapping hashes.

Evaluate fourteen reader/condition systems plus history mean, history median and constant 3. Numerical references use only the user's twelve historical ratings and require no model calls. They are descriptive references, not new state-of-the-art competitors. No ridge baseline is added to this language extension.

For each system, report all-user macro MAE, square root of the mean user-level MSE, signed error, validity and denominators. Compute within-user pairwise concordance on unequal-rated target pairs using one for correct order, zero for reversal and one half for an exact prediction tie. Average pairs within user, then eligible users. Users with three equal targets lack only this ordering diagnostic and remain in all error metrics. Do not use tolerance-based tie changes or a new rank objective after seeing results.

The pure scorer must require exactly 200 unique cases in frozen order, twelve valid historical ratings and three target ratings per case, and all fourteen pipeline cells. The integration establishes identities, provenance and whole-pipeline validity; numeric arrays alone cannot establish them. A separate verifier must independently reparse saved outputs and reproduce metrics, contrasts and uncertainty before release.

## 8. Primary uncertainty and descriptive sensitivities

Use exactly the eight canonical contrasts from `docs/language-confirmation-uncertainty.md`. Apply its fixed calculation without runtime overrides: 200,000 paired-user resamples, NumPy PCG64 seed 20260924, batches of 1,000, common resampled user indices across all eight contrasts, lexicographic contrast order, preserved user order, centered resample means and linear quantiles. Report ordinary 95% intervals and the primary Bonferroni-adjusted 99.375% intervals with tails 0.003125 and 0.996875.

Use a descriptive direction label only from adjusted endpoints with the prescribed 1e-12 numerical tolerance. Report all eight effects and unrounded endpoints, including inconclusive or adverse results. No new writer-reader interaction test, pooled effect, favorable-cell subset, secondary significance family or equivalence claim is introduced. The intervals are approximate percentile-bootstrap summaries, not exact simultaneous coverage. The planning GO does not guarantee their realized width.

For each of the eight comparisons, retain **common-valid paired mean difference and user count only**. Common validity requires both complete pipelines to be valid. With zero eligible users, report count zero and mean unavailable; with one, report that single paired difference and count one. Do not compute additional common-valid intervals, p-values or directional significance labels. These selection-sensitive descriptions cannot replace all-user primary estimates or alter the primary family. This resolves the earlier provisional suggestion of common-valid intervals before any reserved results exist.

Do not pool confirmation with development to enlarge the primary sample. Show development separately if scientifically useful and clearly label it. The older Coat/MovieLens results answer different questions and are not additional users in this confirmation.

## 9. Resource reporting and release

Port the reviewed resource-accounting contract to the 3,600-cell confirmation grid without reusing the development-only hard-coded 1,080-cell aggregator as if compatible. All confirmation observations are new; there is no reused-preflight resource stratum. Count each construction once and each unique audit once. Separate actual prompt/completion usage from reserved token allowance. Treat absent failed-request usage as unavailable, with denominators, rather than zero. Completed requests require complete consistent usage.

Separate operation durations from nested audit durations. Native outer time includes its recorded setup, encoding, instrumentation, request, extraction and export boundary before cleanup. Reader and summary timings exclude prior evidence loading, BM25 selection and prompt construction. Server loading, stage pauses and analysis are not included. Do not add nested timings or infer production throughput, billing, energy or lifetime savings.

Keep model tokenizers and operation types separate. Report invalid-writer stores separately from valid memory-size statistics. Preserve diagnostic-reader resource use. Any paired prompt-size comparison with full history must apply the same memory-valid user mask to both arms; do not subtract aggregates from differently composed subsets.

Publish aggregate results, all primary contrasts, reliability/resource summaries, relevant source/input hashes, final protocol, implementation, deviations and independent computational checks. Do not release raw review text, target labels, private source user IDs, complete model traces or credentials. Any anonymous submission artifact must be separately checked for identity leakage and clearly distinguish arithmetic recomputation from reproducing model outputs. Report incomplete or invalid runs honestly rather than issuing an apparently final result table.

## 10. Concrete work still required before freeze

This draft fixes the intended scientific choices but leaves implementation work, not result-dependent discretion:

* Development must actually finish and pass both gates. This draft records no passing decision.
* Implement the gated reserved-input loader, 200-user runner, full attempt/response accounting, handoffs and final integrity verifier with synthetic failure tests. Confirm actual paths and manifest schema in reviewed code; do not assume development-only constants can simply be reused.
* Implement and review the delayed reserved-label extractor and exact correspondence checks. It must be impossible for a report-only or partial-stage command to open the target label artifact.
* Integrate the pure 200-user scorer and fixed uncertainty module with a genuinely separate saved-output calculation check. The common-valid contract is mean plus N only.
* Implement the confirmation resource adapter and clarify any recovery-only mechanism before freezing. Until deterministic recovery is specified and tested, ambiguous interrupted cells block completion and are never regenerated.
* Record the final public freeze commit and every dependency hash only after implementation review and before reserved prediction. Decide operational scheduling and measured resource feasibility from completed development engineering records, without using effect direction to redesign the experiment.

No current question requires inventing favorable outcomes, changing the existing development method, or opening reserved data to finish this document.
