# Language-rich extension: input and literature screen

20 September 2026. This is a separate development record. It changes none of the
released paper's frozen protocols, results, PDFs, or submission supplement.
No new model inference or accuracy comparison has been performed.

## Why an extension is needed

The completed study supports a bounded finding about structured rating prediction.
Its internal reviewers identified limited native-writer and task coverage as a
remaining obstacle to a stronger main-conference claim. A second domain should
test meaningful written experiences, with correct input boundaries, rather than
add another categorical table or a new name for an established memory method.

The [design review](reviews/language-rich-extension-design-review.md) recommends
testing a pinned native extractor against earlier source reviews and a
task-matched summary, with simple and retrieval-based controls. This is an
empirical extension, not an established new algorithm. A new inference protocol
must be frozen before confirmation users are scored.

## Literature boundary

- [MemRerank](https://arxiv.org/html/2603.29247v1), Sections 3–5, already trains
  preference memory for downstream product selection and compares raw context,
  off-the-shelf extractors, and a Mem0 prompt baseline. Query-independent,
  task-aware preference summaries are not a new contribution here. The proposed
  extension instead tests the complete pinned extraction path and later observed
  ratings without the later review in the query. That difference does not by
  itself establish methodological novelty.
- [MAP](https://arxiv.org/html/2505.03824v1), Sections 3–5, already applies
  history retrieval to sequential and cross-domain rating prediction. A rating
  memory wrapper or history retrieval baseline is not a new method.
- [LaMP](https://arxiv.org/html/2304.11406v4), task definitions and Appendix A/F,
  supplies a legitimate personalized review-to-rating task. It gives the target
  review text as input. That is a different information boundary from forecasting
  a later observed rating from earlier experience and catalog information.

These sources were screened beyond their abstracts. Their results have not been
reproduced here, and this bounded screen is not an exhaustive novelty proof.

## LaMP-3 train-prefix screen

The official training questions file is approximately 3.04 GB. Only its first
64 complete JSON records were acquired, requiring 9,699,328 source bytes. This is
a convenience sample, not a random or representative benchmark sample. The
downloaded prefix and saved sample have separate hashes; the complete remote
file was not hashed. Raw text remains under ignored `data/`.

No gold-output, development or test files were acquired. No task identifier is
assumed to be a verified independent user identifier.

| Input observation | Measured value in these 64 records |
|---|---:|
| Historical reviews per record | 99–800; median 149 |
| Qwen-tokenized full-history payload | 4,544–267,259; median 16,358 |
| Payloads above 32,768 tokens | 16 |
| Payloads above 131,072 tokens | 4 |
| Target review text also present in its own history | 5 |
| Target review text present in another sampled history | 0 |
| Target texts containing a star-expression lexical flag | 3 |

Token counts apply to a JSON list of full reviews and ratings and exclude chat
and writer instructions. They are input-size diagnostics, not model throughput
measurements. Normalized duplicate detection folds case and whitespace only.
The five own-history matches also match case-sensitively in this sample. Matching
text does not establish that the product, target rating, or underlying review is
the same. The star-expression flag has not been semantically adjudicated and is
not a verified label-leakage rate. Two historical text keys have conflicting
ratings within the sample. No effect on a published benchmark score is claimed.

**Decision:** do not relabel LaMP-3 as prospective preference prediction. Do not
copy the Coat rating-only permutation into intact natural-language reviews:
changing a rating while preserving its review can create an internally
contradictory record. A coherent donor-record control would estimate a different
quantity and must be described accordingly.

Implementation: `src/lamp_language_screen.py`. Results and exact input hashes:
`results/lamp-language-input-screen.json`. Six tests cover chunked parsing,
UTF-8, malformed input, bounded acquisition, overlap counting and rating/schema
validation. LaMP's authors list its product-rating task under CC BY-NC-SA 4.0;
raw records are not redistributed here.

## Amazon category feasibility

The proposed information boundary uses 12 earlier full reviews with their
ratings to predict three later first-time parent-item ratings. Targets supply
catalog title/features, never target review text, review title, rating, aggregate
product rating, review count, helpfulness or mutable price. Catalog text remains
a retrospective snapshot; its point-in-time availability is not certified.

The input-only feasibility screen uses an analyst-chosen fixed cutoff of
1 January 2022 UTC, following the design review. For each user, it retains the
first event for each parent item, selects the most recent 12 before the cutoff
and first three strictly after it, then requires nonempty prior review text and
catalog titles for all 15 items. Equal-time events at the cutoff are excluded.
Users in the previously audited 323-user MemoryCD cohort are excluded by exact
source ID. This cannot establish identity equivalence across unknown aliases.

The earlier coarse Digital Music size screen considered any latest 15 first-time
item events and found 198 eligible users. The fixed-date screen is stricter and
finds **18**, among 130,434 reviews and 100,952 source users. Neither screen
examined prediction accuracy or used rating values for eligibility. Digital Music
therefore cannot supply the proposed 60 development and 200 confirmation users,
even before a donor pool and context-length filters. It is a data-support
NO-GO, not an unfavorable model result.

Musical Instruments is the next candidate because its official category is
larger and contains written product-use experiences. At this note's creation,
its complete archives are still being acquired. Do not claim it passes the data
gate until `src/amazon_language_feasibility.py --category Musical_Instruments`
has completed on the verified full archives. The same fixed-date screen applies.

The candidate-window mapping stays local and contains source row indexes only.
Public reports expose counts and file hashes, not user IDs or review text.
The screen has eight tests covering field isolation, first-time item handling,
fixed and relative chronology, boundary ties, missing metadata/text and invalid
timestamps and binding source records to the exact archives opened. The
independent code review reproduced the 18-user count, then prompted stricter
source and timestamp validation. Exact review-text deduplication remains an
unresolved data-design choice, and context-length checks remain outstanding.
These counts are preliminary support, not a passed inference gate. Input-support checks do not establish language quality, model
validity, precision or a novel contribution. Those remain explicit next gates.

Source documentation: [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/).
The acquired category files remain governed by their source terms. Research use
does not establish permission to redistribute reviews or use them commercially.

## Prediction-boundary prototype

`src/language_extension_inputs.py` implements a separate, unexecuted input
serializer for the proposed experiment. Its writer receives earlier history
only. The reader receives earlier evidence and whitelisted target catalog
title/features. Target rating, target review text/title, source user identity,
aggregate ratings, counts, price, descriptions and images are excluded. Earlier
review text is retained verbatim, with no silent clipping. Chronology, identity,
rating validity, nonempty catalog titles and duplicate earlier text fail closed.

Five targeted tests insert canary target labels and unapproved fields, alter
future outcomes, and verify identical model-visible inputs. They also check
writer query independence, duplicate text rejection, malformed timestamps,
chronology and long-review preservation. These are source-boundary tests of the
prototype, not evidence that model inference or the complete cohort is valid.
The data-support screen is deliberately looser: duplicate-text and real token
budget checks can still remove preliminary candidates. Freeze all final rules
and disclose the resulting population before confirmation inference.


## Completed input preparation

The Musical Instruments archives are now complete and hash-verified. The fixed-date
screen found 2,091 candidate users among 3,017,439 reviews. Subsequent outcome-isolated
preparation retained 1,224 users: 60 development, 200 reserved confirmation and
964 donors. Rejections were 674 with a review under five words, 54 with fewer
than 240 historical words total, 42 with duplicated normalized history text,
and 97 exceeding the fixed token limits. These are sequential rejection categories.

Historical review text is preserved without truncation. Maximum complete reader
input counts are 7,924 for Qwen and 7,630 for Phi. The separate input-preparation
review verifies identity disjointness, saved hashes, chronological panels and
target field restrictions. Donor inputs contain histories only, although donor
eligibility shares the same future-activity and catalog-availability screen.
No model predictions or target scores were used in these selection decisions.

The next gate is the three-case development resource preflight, documented in
`docs/language-extension-resource-preflight.md`. Prepared inputs alone do not
establish memory quality, output validity, sufficient statistical precision or
new research novelty. The completed paper and original evaluation remain separate.
