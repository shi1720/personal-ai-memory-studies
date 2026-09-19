# Pilot 004: Phi-4 component results

Original and higher-budget runs are complete. This is a pinned exported
prompt test, not the active Mem0 pipeline. See `pilot-004-source-correction.md`.

## Original execution

All 120 scheduled cases are accounted for: 114 actual generations and six
reader cases blocked by three invalid count-aware writers. No writer or reader
hit its output-token limit. Measured generation time was 1,371.27 seconds,
excluding model loading, verification, preprocessing and analysis.

All twelve unmodified exported-prompt writers pass the facts-only schema.
Nine of twelve count-aware writers pass; the other three add an
`activity_summary` key. This is invalid under our exact-key protocol, not an
observed rejection by the Mem0 product. The raw responses are preserved.
Valid exported-prompt outputs average 6.92 facts and 511.33 UTF-8 bytes. Valid
count-aware outputs average 8.33 facts and 592.89 bytes; these averages exclude
the three invalid writers and are not matched storage budgets.

## Strict results and answer-format sensitivity

Every entry is out of twelve scheduled cases. The count order is correct / wrong
/ abstained / invalid / blocked. Six frequency answers use exactly the displayed
option after the letter, such as `D. swimming`. The original protocol requires
a bare letter and rejects them. A separately declared post hoc sensitivity
accepts only an exact letter-plus-option match, without changing the reason,
JSON schema or any writer validity decision.

| Context | Frequency, strict | Frequency, exact-option sensitivity | Dated event, both parsers |
| :--- | :--- | :--- | :--- |
| Full journal | 8 / 3 / 0 / 1 / 0 | 9 / 3 / 0 / 0 / 0 | 12 / 0 / 0 / 0 / 0 |
| Exported prompt | 9 / 2 / 0 / 1 / 0 | 10 / 2 / 0 / 0 / 0 | 11 / 1 / 0 / 0 / 0 |
| Count-aware prompt | 4 / 3 / 0 / 2 / 3 | 6 / 3 / 0 / 0 / 3 | 3 / 0 / 6 / 0 / 3 |
| Exact count ledger | 10 / 0 / 0 / 2 / 0 | 12 / 0 / 0 / 0 / 0 | 0 / 0 / 12 / 0 / 0 |

With the exact-option parser, the exported-prompt condition retains all nine
frequency answers that full history gets right and gains one additional answer.
It loses one dated-event answer. The count-aware condition loses one correct
frequency answer and blocks two others relative to the nine correct full-history
cases. These small paired observations do not show a general frequency loss
from the unmodified exported prompt.

The exported-prompt condition's one dated-event error occurs in extract-09.
The reader says day 09 had conflicting enjoyment reports, although its supplied
memory lists that day only among not-enjoyed badminton visits. The memory repeats
the negative day number, but the observation does not establish that repetition
caused the reader's mistake. It should not be labelled an omitted-source failure.

## Source fidelity

The source inspection finds incorrect dated assertions in five of twelve
exported-prompt summaries. Every valid count-aware summary contains at least
one incorrect numerical claim. Thirty of their 54 explicit count assertions
disagree with source truth. Some still imply the correct ordering of activities,
so a correct multiple-choice answer does not establish an accurate memory.

The invalid count-aware outputs retain correct dated events in their facts lists
but add inaccurate numerical summaries outside that list. They remain blocked
in all downstream analyses. The literal audit, its residual-clause inspection
and all extra-field comparisons are in `pilot-004-phi-source-inspection.md`.
Inspection is model-assisted and post hoc, not independent human annotation.

## Decision boundary

The completed original run does not support a general claim that this exported
prompt degrades aggregate answers relative to full history. It does reveal
different output representations and source errors from Qwen. These are
exploratory observations on twelve fictional development journals, not evidence
of a new method or of deployment performance.

The completed 768-token sensitivity contains 45 actual reader generations and
three blocked records. All 45 responses match their original normally terminated
outputs exactly. Generation time is 418.09 seconds. Strict and exact-option
scores therefore stay as shown above. A larger reader budget does not repair
the incorrect stored counts in this run. The completed two-model interpretation
is in `pilot-004-results.md`.
