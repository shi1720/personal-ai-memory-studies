# Completed crossed-writer resource check

20 September 2026. Engineering evidence only. No target ratings were opened or
scored, and no reserved confirmation inputs were used.

The frozen three-case experiment completed all 54 planned generation requests:
21 earlier Qwen requests were reused unchanged, and 33 new requests were made.
The new requests comprise six Phi writes, 21 Phi reads and six Qwen reads of
Phi-written evidence. Both server stages exited their runners normally. The
owned Phi server was stopped before the Qwen server was started.

All six writer configurations (three cases by two writers) produced complete,
nonempty native exports and valid task summaries. All 42 reader outputs passed
the frozen three-rating contract. Every generation finished with `stop`.
Independent tokenization agreed exactly with server-reported prompt counts.
There were no failed transports, pretransport rejections, hidden retries or
diagnostic fallback-evidence reads. The 54 saved generation responses match the
54 audited transport responses one to one, including IDs, content hashes and
model identity.

The selected cases remain in their original shortest/median/longest Qwen
full-history-reader order. Their writer outputs are retained unchanged:

| Case position | Qwen native entries | Phi native entries | Qwen summary words | Phi summary words |
| --- | ---: | ---: | ---: | ---: |
| Shortest | 12 | 1 | 244 | 204 |
| Median | 1 | 11 | 197 | 180 |
| Longest | 12 | 12 | 212 | 213 |

These counts describe exported records, not correctness, information fidelity
or superior memory quality. A single aggregate entry is not equivalent in
content or length to a single item-specific entry. The experiment does not
manually standardize this behavior.

The largest new prompt-plus-output allowance was 14,830 tokens; the previously
retained Qwen requests reached 15,321. Both fit the frozen 16,384-token cap.
Summed new request times were 887.17 seconds for the 27 Phi requests and 19.23
seconds for the six Qwen cross reads. These include tokenizer prechecks and
represent different workloads, so they are not a comparative model-speed
benchmark. The slowest new request took 173.28 seconds, within the frozen
360-second timeout. Native whole-write times additionally include embeddings
and store setup.

## Provenance and limits

Implementation and protocol were published before inference at public commit
`cee9b6a` on `research/language-rich-extension`. The final report is
`results/language-cross-preflight.json`, SHA-256
`689e9dc10d83480019ab153e732869e9899c1502aee2d35b3006df3fdc7c23c2`.
The unchanged original Qwen report SHA-256 remains
`bf80f62a77f907bb5da782c1378c024f5c0d14a727dae9fb55fc66b5b6f134d6`.
Raw requests, responses, stores, stage handoffs and execution logs remain in the
private local research record. No hosted API or user-supplied API credential was
used.

A passed three-case screen establishes that this configuration operated on
these cases. It does not estimate a population failure rate or show an accuracy
benefit. The next step is the fixed 60-user development experiment and its
prospective precision gate. Confirmation remains locked until development
integrity and precision have been reviewed. These engineering results are not
added to the completed paper as predictive evidence.
