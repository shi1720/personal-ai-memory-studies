# Pilot 004: Phi-4 source inspection

Completed after the original run. This combines a post hoc literal parser with
model-assisted inspection of every remaining clause. It is not independent human
annotation or a general entailment evaluator. The exported prompt is not on the
active Mem0 extraction path; see `pilot-004-source-correction.md`.

## Scope

The separate Phi parser recognizes grouped dates, dated outcomes and several
explicit numerical count formats observed in these outputs. It preserves
repeated claims rather than deduplicating them into apparent correctness. It
does not interpret unknown prose or repair the experimental JSON schema.
Raw facts inside invalid writer responses are inspected, but remain invalid
and never become reader inputs. Extra `activity_summary` fields are reviewed
separately below, not silently folded into the memory.

## All original writer outputs

“Outcome days” counts distinct source days with a matching explicit activity
and enjoyment claim, out of 24. It is a literal-coverage diagnostic, not a proof
of how much information any optimal reader could infer. “Wrong dated claims”
counts assertions, including attendance and outcome claims about the same day;
it is not a count of independent errors or users.

| Journal | Exported prompt: outcome days / wrong dated claims | Count-aware prompt: outcome days / wrong dated claims | Wrong explicit counts in facts |
| :--- | :--- | :--- | :--- |
| 00 | 22 / 3 | 0 / 0 | 2 of 6 |
| 01 | 23 / 0 | 24 / 0, invalid schema | No counts in facts; extra field below |
| 02 | 24 / 0 | 24 / 0, invalid schema | No counts in facts; extra field below |
| 03 | 24 / 0 | 0 / 0 | 4 of 6 |
| 04 | 23 / 2 | 23 / 2 | 4 of 6 |
| 05 | 23 / 1 | 0 / 0 | 4 of 6 |
| 06 | 22 / 0 | 0 / 0 | 2 of 6 |
| 07 | 23 / 0 | 17 / 0 | 2 of 6 |
| 08 | 24 / 1 | 0 / 0 | 5 of 6 |
| 09 | 22 / 0 | 24 / 0 | 5 of 6 |
| 10 | 24 / 0 | 3 / 0 | 2 of 6 |
| 11 | 23 / 13 | 24 / 0, invalid schema | No counts in facts; extra field below |

Across the exported-prompt outputs, the grammar finds 20 false dated claims
among 574 literal claims. Five of twelve summaries contain at least one such
claim. Four explicitly represent all 24 correct source outcomes. An output can
preserve a correct outcome while adding a conflicting assertion elsewhere.

Across the nine valid count-aware outputs, all nine contain incorrect explicit
counts: 30 of 54 numerical assertions disagree with the source. One also has
two incorrect dated assertions. Some count-aware outputs retain dates and
others retain only aggregate claims, so their event capabilities differ.
These descriptive totals are not error-rate estimates for real users.

## Extra fields in the three invalid writers

The exact-key protocol rejects count-aware outputs 01, 02 and 11 because each
adds an `activity_summary` field. Their facts lists contain all 24 correct
source outcomes. Their extra numerical fields are nevertheless inaccurate.
The following tuples are (total, enjoyed, not enjoyed).

| Journal / activity | Extra-field tuple | Source tuple |
| :--- | :--- | :--- |
| 01 / painting | (9, 5, 4) | (12, 6, 6) |
| 01 / pottery | (11, 8, 3) | (12, 9, 3) |
| 02 / pilates | (10, 4, 6) | (12, 6, 6) |
| 02 / yoga | (9, 7, 2) | (12, 9, 3) |
| 11 / painting | (10, 6, 4) | (12, 6, 6) |
| 11 / pottery | (13, 5, 8) | (12, 6, 6) |

Fifteen of these eighteen values are wrong. This inspection neither changes
writer validity nor establishes what a current product parser would do.

## Residual details and interpretation

All remaining non-punctuation clauses describe the blue mural, brass clock or
purple umbrella. Their explicit date associations, including associations
inherited from the enclosing dated fact, match the source. No residual
numerical or comparative-preference claims remain unreviewed in this small set.
Journal 09's exported output repeats day 09 in a negative badminton list; the
literal audit preserves that repetition. Repetition of a true assertion is not
itself scored as a false event, but can complicate subsequent counting.

The model sometimes writes wrong quantitative claims even when the correct
event-level evidence remains elsewhere in the same output. Conversely, a
reader can still select the right higher-rate activity from incorrect counts.
Source fidelity and answer correctness must therefore remain separate metrics.
The one wrong dated-event answer in the unmodified exported-prompt condition
also occurs despite the correct negative event being present: the reader
invented a conflicting positive report for extract-09's day 09. This is not an
observed omission of that queried event.
This is a bounded diagnostic observation, not a new memory algorithm or evidence
about the active Mem0 pipeline.
