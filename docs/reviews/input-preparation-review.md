# Review of language-extension input preparation

Date: 20 September 2026. Reviewed the input protocol, `prepare_language_extension.py`, `language_extension_inputs.py`, twelve associated tests, the completed Musical Instruments feasibility report, and the completed input-preparation manifest. This was a bounded software and information-boundary review. No inference, outcome scoring, manuscript changes, or source/report edits were performed.

## Verdict

**GO for development and final inference-protocol preparation. Not yet a GO for confirmation inference.**

The prepared data can support a genuinely reserved user-level confirmation cohort under the declared information boundary. I found no target-outcome use in the preparation decisions or serialized model inputs. The identity split is deterministic and disjoint. The actual reader-template counts are measured as flat token-ID sequences, so the earlier mapping-length issue has been corrected before the completed preparation.

The pipeline preserves the distinction between a chronological review split and historically certified catalog information. It does not establish random exposure, stable underlying human tastes, English-language quality, or a newly invented preference benchmark.

## Checks completed

All five serialization tests and seven preparation tests pass. All five recorded dependency hashes match the inspected source/protocol files. All four prepared input/mapping file hashes match the manifest.

The preparation report records 2,091 first-stage candidates and the following second-stage disposition:

| Disposition | Users |
|---|---:|
| Eligible | 1,224 |
| Any review shorter than five whitespace-delimited words | 674 |
| Total history shorter than 240 words | 54 |
| Duplicate normalized history text | 42 |
| Context budget exceeded | 97 |

These categories are sequential, mutually exclusive rejection reasons, not independent prevalence estimates. For example, a short duplicate review is counted under the earlier word-count rejection rather than duplicate text.

Independent structural inspection of the prepared files confirmed:

- Exactly 60 development, 200 reserved confirmation, and 964 donor cases.
- All case hashes recompute from the corresponding private source user IDs.
- All group boundaries equal the declared sorted-hash partitions.
- No case belongs to multiple groups, and all 1,224 cases are accounted for.
- Each source panel contains twelve records.
- Each non-donor case contains exactly three target catalog records, with only the `target` and `product` keys; catalog products contain only `title` and `features`.
- Donor outputs contain histories only, with no target catalog records.
- No normalized historical review-text key is shared across development, confirmation, and donor groups in these saved inputs. No complete normalized review/rating multiset profile is shared across groups either. This is an auxiliary input-only exact-match check, not semantic deduplication or proof of distinct real-world human identities.

Observed maximum token counts are:

| Tokenizer | History payload | Full-history reader template |
|---|---:|---:|
| Qwen | 6,138 | 7,924 |
| Phi | 5,978 | 7,630 |

These satisfy the declared 6,144 payload and 12,288 reader-template limits. The native Mem0 instruction and generated memory output have not yet been included in a complete writer request check, as the manifest explicitly states.

## Outcome isolation

`project_record(..., history=False)` accesses only user identity, parent product identity, and timestamp. Its guarded test would fail if target rating, review body, or review title were accessed through that projection. Subsequent input serialization uses only target metadata from the permitted catalog fields. The query-independent writer receives `instance['history']` only.

The source JSON reader necessarily parses raw objects containing target labels before projection. The protocol correctly says those values are not consulted or used, rather than claiming they were never loaded from disk. No target-label output file is produced in this phase. Later development-label materialization must be explicitly restricted to the sixty development cases. A separate confirmation-label loader should not be invoked until the final inference record is complete, except for a separately justified fixed scoring workflow.

History ratings are retained and validated. This is legitimate observed evidence. Input token limits may consequently depend in a tiny way on tokenization of the observed historical numeric values; the protocol's claim is that no **target** outcome affects eligibility, not that historical evidence is absent from preprocessing.

## Chronology and selection integrity

The selected rows inherit the first-stage rule: first event per parent product, then the last twelve such events before 1 January 2022 and first three after it. The source-window hash and source archive verification tie preparation to that rule. `build_inputs` independently checks the panel sizes, one user identity, distinct products, within-panel ordering, strict cutoff separation, and source-era millisecond timestamp bounds.

The historical reviews are copied without truncation. Duplicate review text and word-count filtering occur before partitioning and before scoring. These restrictions intentionally select a more verbose, manageable-context population. They are not evidence that the selected users are representative or that their opinions are more valid. The protocol already says this clearly.

Metadata title and feature strings are whitelisted, while raw numeric aggregates, review fields, descriptions, price, and images are omitted. A field whitelist does not prove that a seller's title or feature prose contains no testimonial or score-like language. The actual claim should remain field-level exclusion, with the retrospective catalog limitation retained. Any additional semantic metadata filtering must be specified before confirmation and applied consistently, not triggered by observed model errors.

## Remaining gates and minor hardening

1. **Complete writer budget remains mandatory.** Count actual Mem0-generated chat requests plus output allowance during a development preflight. History-payload bounds alone do not certify the native extraction request, retrieval behavior, complete memory export, or empty-store handling.
2. **Freeze the actual model call settings.** The current reader-template count is valid for `reader_query` and the pinned tokenizer files. If the inference wrapper adds system text, reasoning controls, target descriptions, response schemas, or chat-template kwargs, recalculate exact request bounds before confirmation. Do not reuse these numbers for a changed prompt.
3. **Record tokenizer library versions.** File hashes bind configuration, but Transformers and tokenizers versions also influence template/API behavior. Add versions to a separate execution manifest before model calls. There is no need to change the already completed immutable preparation artifact solely to add this metadata.
4. **Check completeness of the tokenizer pin set.** The loader verifies each existing relevant config/tokenizer file against the model manifest, but does not explicitly require every expected relevant file to exist. I checked the current model directories and found no missing relevant manifest files. Thus this is defensive hardening, not a current-result defect. A later loader can compare expected and actual relevant file-name sets before proceeding.
5. **Respect the reserved count.** This preparation fixes two hundred confirmation users. The precision calculation must therefore either justify that sample, retain the study as an estimation experiment with its attainable uncertainty, or freeze a separately documented redesign before inference and before using extra users as fitted donors. Do not expand after a significance check. The 964 donors are not an unannounced backup confirmation set.
6. **Distinguish donor input from donor eligibility.** Donor exports contain only prior histories, but donors were selected through the same future-activity and target-metadata/context eligibility screen as other cases. Calling them “history-only donor inputs” is accurate; claiming that future product availability played no part in their eligibility would not be accurate. No future numeric outcome was used.
7. **Retain immutable artifacts.** `write_once` rejects differing outputs and uses an atomic replace for a newly created file. This is appropriate for preserving preparation evidence. Any later change to filtering or cohort construction should receive a new versioned directory/report rather than bypassing the immutability check.

None of these points invalidates the prepared cohort. They define what must be locked or tested next. The code and current report support input-isolated development followed by confirmation; they do not yet support a claim that an extraction experiment has been completed, replicated, or made ICML-ready.
