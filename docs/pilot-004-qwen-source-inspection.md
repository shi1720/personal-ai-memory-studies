# Pilot 004: exploratory Qwen source inspection

Completed after the original 120-call Qwen run. This is a limited programmatic
claim audit plus model-assisted inspection, not independent human annotation.
No claim about arbitrary natural-language entailment is made.

The tested prompt is an exported definition, not the active Mem0 extraction
path at the pinned revision. `pilot-004-source-correction.md` corrects the earlier
native-interface wording without changing the observations or frozen protocol.

## Method

`audit_extraction_claims.py` recognizes explicit activity/day/outcome clauses
and grouped date lists, then compares those literal claims with the generated
source events. The grammar was developed after looking at the outputs. It
never treats unsupported prose as false or treats an unparsed clause as omitted
information. All residual text is preserved for inspection. Input/output and
parser hashes are saved in `pilot-004-qwen-claim-audit.json`.

Every Qwen summary has a correct activity/day/outcome clause for each of the
24 source visits, either separately or in a grouped list. This is evidence
against selective loss of negative events in this particular native-interface
test. It does not imply every summary is consistent: two summaries add incorrect
claims as well as retaining the correct source evidence.

## Results across all summaries

| Journal | Native extraction | Count-aware extraction |
| :--- | :--- | :--- |
| extract-00 | All 24 core events match; no additional core claim | Same |
| extract-01 | All 24 core events match; three incidental details match their days | Same |
| extract-02 | All 24 core events match; three incidental details match their days | Same |
| extract-03 | All 24 core events match | 42 literal event claims: 24 match, 18 do not |
| extract-04 | All 24 core events match; three incidental details match their days | Same, with paraphrased details |
| extract-05 | All 24 outcomes are represented, but grouped lists add four incorrect core claims | All 24 core events match; details match |
| extract-06 | All 24 core events match | Same |
| extract-07 | All 24 core events match; three detail-only facts match their days | All 24 core events match; details match |
| extract-08 | All 24 core events match; details match | Same |
| extract-09 | All 24 core events match | Same, retaining source-style IDs and dates |
| extract-10 | All 24 core events match; details match | Same, with date-first wording |
| extract-11 | All 24 core events match; details match | Same |

No summary supplies explicit per-activity total/enjoyed/not-enjoyed count triples,
including the count-aware condition. Thus a failure of that control cannot be
interpreted as proof that accurate counts would not help: the model did not
produce the requested representation. The oracle ledger is a separate control.
The date lists do encode counts indirectly, but this requires deduplication and
consistency handling when lists contradict one another.

## Concrete mismatches

In extract-03's count-aware output, the first block assigns pottery visits to
all 24 days, although only twelve are pottery visits. The second block adds
painting claims on six pottery days. There are eighteen incorrect literal
claims, and the true visit claims still appear elsewhere in the same memory.
The parser records every mismatch and the corresponding source event.

In extract-05's native output, a negative chess list incorrectly includes days
02, 21 and 24, which belong to badminton. A negative badminton list includes
day 06, which was enjoyed; the positive list also includes that day. This is
contradictory extracted evidence, not a simple loss of negative memories.
The attendance list additionally omits badminton day 10, but the positive
badminton list retains its correct outcome. We do not count that omission as
a false assertion that no visit occurred.

All residual incidental-detail statements were compared with the source's
three specified detail/day pairs. They preserve the observed pairing. There
are no unreviewed numerical frequency or comparative-preference statements in
these Qwen summaries. Future models may use unsupported syntax and require
separate inspection rather than automatic extrapolation of this audit.

## Interpretation

The first-model component test does not reproduce the earlier forced six-event
selector's omission pattern. It instead retains substantial event detail,
occasionally with added contradictions. The short-budget rate-reader results
are strongly affected by output truncation. The completed post hoc higher-budget
run gives 9/12 correct frequency answers for full, native and count-aware
contexts, with one paired loss and one reverse gain for each extracted context.
See `pilot-004-qwen-results.md` for both budgets. The twelve event
questions are answered correctly with full, native and count-aware evidence;
the count ledger appropriately leads to abstention on all twelve dated events.
These narrow findings do not establish deployed-system performance or novelty.
