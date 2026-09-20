# Review-history resource preflight results

This is a completed development-only engineering check, not an accuracy experiment or confirmation result. No target ratings were loaded by the runner. The protocol and code were published in commit `95efe92` before inference. All locked dependencies still match.

## Outcome

All 21 attempted model requests completed. All 15 reader outputs satisfy the three-number contract. All three native stores export unique, nonempty memory entries with exact insertion/export ID agreement. Every native generation stops normally; all three task summaries satisfy the JSON and 400-word limits. Every independently counted prompt matches server-reported token usage. The largest prompt-plus-output allowance is 15,321 of the 16,384-token engineering cap.

| Development case selected by input length | Native entries | Native prompt tokens | Native output tokens | Summary words | Valid readers |
| --- | ---: | ---: | ---: | ---: | ---: |
| Shortest | 12 | 10586 | 933 | 244 | 5/5 |
| Median | 1 | 11776 | 113 | 197 | 5/5 |
| Longest | 12 | 13273 | 1042 | 212 | 5/5 |

The native writer produced one aggregate memory for the median case and twelve entries for each other case. These different granularities are retained as pipeline behavior; no memory was rewritten to resemble another case. Nonempty storage and valid JSON do not establish factual completeness or useful prediction.

Total audited request time is 372.7 seconds. This includes local token counting; native wall time additionally includes initialization and embedding/storage. It is not an isolated server-latency benchmark. No commercial API was used.

The model-listing endpoint initially failed because its default Hugging Face cache directory was absent. The owned server was launched with an explicit verified local model path and its health endpoint passed. This discovery-only issue did not cause a model retry, restart, failed completion or protocol amendment. Local Qdrant emitted an expected warning that payload indexes have no effect in local mode.

## Remaining work

The three cases were selected to cover input length, not sampled to estimate reliability. They remain part of the fixed development group. This gate does not demonstrate population validity, predictive advantage, adequate precision or a new memory algorithm.

A prospective two-writer design is described in `docs/reviews/language-extension-confirmation-design.md`. Its Phi writer, matching task summary and cross-reader operation need their own preflight. The full 60-user development run and a declared precision gate must precede reserved inference. No reserved user predictions or outcomes have been accessed in this run. The released paper remains unchanged.
