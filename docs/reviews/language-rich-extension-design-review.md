# Design review: a language-rich extension with real observed preferences

Date: 20 September 2026. This is a design recommendation, not a registered protocol or a completed experiment. No model inference was run, no confirmation labels were inspected, and no manuscript or frozen analysis was changed for this review.

## Decision

**Conditional GO for a bounded, chronological, fresh-user Amazon review-history audit. NO-GO for treating LaMP-3 as a direct replacement for the current future-preference task.**

The proposed extension asks whether a native memory writer preserves the predictive value of a person's earlier written product experiences when predicting their subsequently observed ratings. The query supplies product catalog information, never the target person's review. This addresses the current paper's strongest scope gap: extraction from natural language rather than conversion of a small categorical rating table.

It is an extension of an empirical audit, not a new memory algorithm or benchmark concept. Success means an informative, reproducible result regardless of which representation wins. A positive or negative extraction effect must not be a condition for publication.

## What is available and what it can support

The pinned local native writer is usable: `src/run_coat_memory_development.py` creates a new Mem0 store per user, invokes its actual extraction path, retains the request/response trace, exports all stored text with a completeness check, and feeds fixed evidence to readers. A new wrapper and configuration should live in separate extension files. Do not repurpose the frozen Coat filenames or overwrite original traces. Preserve no-retry behavior, token/finish-reason recording, sequential local inference, and stage-specific failure accounting. Increasing the writing allowance, changing a wrapper, or using an additional provider must be decided in development and frozen for the new experiment.

The locally available MemoryCD file has 323 users and historical review text, ratings, product IDs, and timestamps. Its entire cohort has already undergone a published target-distribution and baseline audit. It is appropriate for engineering development, not a fresh confirmation cohort. Its four categories are Beauty and Personal Care, Books, Electronics, and Home and Kitchen. Exclude these 323 user IDs from a new Amazon-derived cohort wherever the identifiers can be matched. Do not present a new split of these already audited users as untouched validation.

PersonaMem-v2 contains constructed personas and synthetic conversations, so it does not meet the requested focus on actual observed preferences. It remains useful for a separate controlled synthetic study, not this extension.

LaMP-3's target input includes the target review itself. This is a legitimate personalized text-to-score task, but its information boundary differs fundamentally from forecasting preference for an item from past experience. Target sentiment can explain the score without extracting a stable preference. The parent task's train-only 64-record screen also found own-history target-text duplicates and oversized histories. These findings are development diagnostics, not an accusation about the official benchmark. Label-only permutation would additionally contradict the sentiment in intact history reviews. For the proposed scientific question, masking just the explicit star expression cannot remove the rest of that target-sentiment evidence.

## One feasible experiment

Use the official Amazon Reviews 2023 **Musical Instruments** category. Its published size is approximately three million reviews, substantially smaller than Books or Electronics. It provides actual ratings and timestamped written experiences, with separate product metadata. This recommendation is based on acquisition scale and language-rich product use, not measured model performance. The category has not been downloaded or screened by this reviewer. If it fails the gates below, report the failure rather than searching categories until the desired effect appears.

The task is retrospective prediction of later **observed ratings**, not purchase propensity, unbiased utility, or the preference for unobserved products. Sampling exposure and reviewer selection remain limitations. Public reviews may occur in model pretraining.

### Inputs and chronological boundary

1. Pin archive URLs, revisions where available, download hashes, schema, and a single date boundary before reading outcomes. A feasible initial boundary is 1 January 2022 UTC. Report it as an analyst-chosen cutoff, not the original dataset's official task.
2. Build histories only from reviews strictly before the boundary. Select the most recent 12 distinct parent products with valid text and metadata using a deterministic timestamp/product-ID rule. Deduplicate parent products and exact text before selecting records. Do not inspect ratings to select an informative-looking history.
3. Select the first three distinct new parent products reviewed strictly after the boundary. Exclude products previously reviewed by the same user. Equal timestamp boundary cases must follow a fixed rule, without reading the score. Keep the actual later numeric ratings in a separate labels-only file that prediction and writer processes never load.
4. Each history record contains bounded verbatim review text, its original numeric rating, and product title/features. Apply one deterministic per-record limit, such as the first 256 model tokens of the review and first 80 tokens of catalog description, identically before every arm. Do not call this the user's full lifetime history. The full-history arm means the entire declared 12-record evidence panel.
5. Target records contain only catalog product title/features and anonymous local IDs. Exclude target review text, target review title, images posted by the reviewer, rating counts, average ratings, helpful votes, and other users' review snippets. Also exclude these aggregate fields from history item metadata. Whitelist permitted fields instead of dropping known forbidden fields from a large serialized object.
6. The catalog was collected after some interaction dates and is not a historical snapshot. Restrict to relatively stable product descriptions and state this limitation. Without archived metadata, describe the experiment as a chronological review split with snapshot catalog information, not a fully prospective deployment simulation.

Use a strict common input budget, for example 8,192 tokens under every tested tokenizer, including instructions and all target records. Decide exact bounds on development only. Never silently truncate the full-history arm at runtime. If the deterministic panel does not fit, exclude before inference using a frozen, label-blind rule and report coverage. The same accepted users and source panel must reach every evidence arm.

### Separation before development

A label-blind manifest-builder may stream user IDs, product IDs, dates, field presence, and duplicate fingerprints to determine eligibility. It must not calculate target rating histograms or model scores on reserved users. Record that this metadata inspection occurred.

Use a salted fixed hash of the original user ID to allocate disjoint users to:

- A fitting/donor pool, sufficiently large for rating-matched donor records and any explicitly population-trained comparator.
- Sixty development users, including format preflights and prompt/budget decisions.
- A reserved confirmation cohort, initially 200 users, with the final size determined before confirmation from a precision calculation using development paired-loss dispersion. Set a prespecified ceiling, such as 400, rather than extending until significant.

Freeze membership before model development and do not reuse development users as confirmations. Users excluded for absent metadata or invalid timestamps cannot be replaced based on their ratings. Exclude known previously audited MemoryCD IDs. Unresolvable overlap with users in older public datasets or pretraining must remain disclosed; a fresh local split is not a guarantee of previously unseen humans.

### Evidence arms

Keep the query, target order, reader model, output contract, and inference settings fixed.

| Arm | Evidence | Question answered |
|---|---|---|
| No history | Target catalog information only | Baseline without personal history |
| Source history | The declared 12 original review/rating records | Value of the supplied source panel |
| Native memory | All text exported from the pinned native Mem0 write | End-to-end native construction and reading effect |
| Task-matched summary | A fixed writer prompt asking for supported preferences and dislikes, under the same declared output ceiling | Whether an extraction loss is specific to generic task-agnostic instructions |
| Rating-matched donor history | Coherent complete review records from fitting users, matched to the recipient's historical score counts | Usefulness of whose experiences are supplied beyond the rating histogram |

The task-matched summary is a standard baseline, not a proposed new method. It should use the same writer model as native extraction so that its first comparison primarily changes the instruction/pipeline, not model strength. Record actual output lengths because equal output ceilings do not imply equal lengths. Store writes occur without the targets, preserving query independence.

Run two fixed readers on all five arms. Reusing Qwen and Phi makes this an interpretable domain extension; adding one stronger hosted reader later would address a different gap and needs its own declared settings and budget. The current design does not require a paid API to be feasible. At 200 confirmation users, two writers and ten reader calls per user imply roughly 2,400 calls, excluding development. Wall-clock time must be estimated from actual development timings rather than promised in advance.

### Why the donor control replaces label-only permutation

A review such as “the keys stick and I returned it” cannot coherently retain its wording while receiving an arbitrarily permuted high rating. Instead, take the entire donor record, including its original text, product metadata, and rating, as a unit. For each recipient history position, sample a fitting-pool record with the same numeric rating and pre-cutoff timestamp; reject the recipient's own products and targets. Use a fixed seed, no outcome-based matching, and no target labels. Preserve the recipient's rating histogram and record count exactly. Match record lengths by prespecified bins where feasible and report remaining length differences rather than claim exact token matching.

This control changes product support, semantic content, and ownership together. It is **not** the Coat assignment-permutation estimand, does not isolate pure individual taste, and need not remove all shared product preferences. It is a coherent negative control for personally assigned experience conditional on rating marginals. Do not call a collection of donor records an observed real person's history. If exact rating matching fails, mark that control unavailable under a predefined coverage rule; never relabel donor reviews.

### Metrics and statistical family

Use user-macro MAE across all three later ratings, with RMSE and equal-user ordering diagnostics secondary. A three-target ranking score will be noisy and undefined for users whose targets tie; report eligible coverage. Bootstrap uncertainty is conditional on the fixed fitting/donor pool; reused donor records do not supply independent validation units. History mean, median, constant midpoint, and no-history model predictions are indispensable. Any text-feature regression comparator uses the fitting pool only and is explicitly distinguished from per-user-only methods.

Primary family: native-minus-source MAE for two readers and task-summary-minus-native MAE for the same readers, four comparisons total. Declare paired user bootstrap settings and multiplicity adjustment before confirmation. Donor-minus-source and source-minus-no-history are prespecified secondary descriptive diagnostics unless included in a larger primary family before freeze. Do not promote whichever secondary comparison succeeds after scoring.

Use a single permissive but exact output format, sufficient development-tested output allowance, and an explicit invalid-output fallback. A midpoint fallback is acceptable for continuity with the current study, but report paired common-valid sensitivity because rating concentration can make it competitive. Extraction errors and empty memories remain in the operational results. Do not interpret writing cost as lifetime cost or saved input tokens as improved utility.

## Explicit go/no-go gates

Before any confirmation inference:

1. **Data GO:** the category supports at least 260 eligible, distinct users outside known prior audit IDs, plus a disjoint donor pool. Product metadata and strictly ordered history/targets are available. All forbidden target fields are structurally absent from prediction inputs. If not, NO-GO for this design as specified.
2. **Language GO:** development records retain substantive original prose after deterministic bounds; report word/token distributions and examples selected without outcome preference. If clipping reduces most inputs to labels or empty titles, this does not repair the language-rich scope gap.
3. **Boundary GO:** duplicate detection, field-whitelist tests, chronology assertions, and target-label isolation tests pass. Artificial canary labels must never reach writer/reader input. A failed boundary test is a stop condition, not a reason to exclude only inconvenient cases after scoring.
4. **Execution GO:** development format validity is at least 95% per arm/reader, all selected inputs fit the declared context, and native exports are complete. Fix development-only wrappers/budgets if necessary, then freeze the final version. Do not make these fixes after inspecting reserved accuracy.
5. **Precision GO:** the prespecified maximum sample supports the declared interval precision using development paired-loss dispersion, or the study is explicitly marked an estimation pilot. Do not claim a tight null or equivalence if it does not.
6. **Interpretation GO:** evaluate all frozen arms and report their outcomes, including an unchanged or reversed extraction effect. There is no gate requiring a statistically significant memory failure, model win, or improvement over history median.

These conditions justify proceeding with an additional empirical experiment. They do not certify ICML acceptance or establish a new method. If data or timing gates fail, preserve this as a documented no-go and keep the existing paper's narrower scope.

## Closest-work overlap and defensible contribution

[Language-Based User Profiles for Recommendation](https://arxiv.org/abs/2402.15623) already compares language profiles with raw rating history. [MAP](https://arxiv.org/abs/2505.03824) already studies memory-assisted personalized recommendation. The extension cannot claim either idea as new.

[MemRerank](https://arxiv.org/html/2603.29247v1) is especially close: it evaluates extracted preference memories and raw context with multiple downstream readers, including a Mem0-style prompt baseline, on Amazon-derived product selection. Its task uses rewritten search queries and sampled alternatives. The proposed extension instead predicts actually observed subsequent ratings without giving the target review to the model, and tests a pinned native implementation with coherent rating-matched negative controls. This is a difference in audit scope and evidence boundary, not proof of broad novelty or a superior benchmark. It does not refute that paper or reproduce its reported comparisons.

[MemoryCD](https://huggingface.co/datasets/WZDavid/MemoryCD) already supplies real review histories for memory evaluation. The published local 323-user audit must be cited as prior inspected data. A new language-rich result is useful as a controlled extension of the current paper, not because “real review memory” is unexplored.

[LaMP](https://arxiv.org/html/2304.11406v3) evaluates personalized language tasks and gives a useful established alternative if the research question changes to review interpretation. It should not be silently relabeled prospective preference prediction.

The [official Amazon Reviews 2023 documentation](https://amazon-reviews-2023.github.io/) distinguishes user review fields from product metadata, including aggregate ratings and mutable prices. That schema motivates the field whitelist and snapshot-metadata limitation above. Data remain governed by their source terms; publish code, hashes, and aggregate error summaries rather than redistributing raw personal review text by default.

## Recommendation

Proceed only with a separately frozen review-history experiment that preserves the correct target-information boundary. Do not spend inference on label-shuffled natural-language reviews or a target-review task presented as unseen-item preference forecasting. A carefully executed native-extraction replication with coherent controls is more informative than another large but ambiguous model comparison.
