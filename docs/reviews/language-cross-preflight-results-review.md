# Cross-preflight persisted-results review

Reviewed 20 September 2026 after both stage records reached completed status. This is an independent internal computational check of saved records, not external validation, an accuracy experiment, or a confirmation result. No inference was performed, no target labels or reserved inputs were opened, and no server was restarted.

**Verdict: the completed run passes the declared engineering gates.** An independently written checker found no discrepancy between the aggregate report and the persisted requests, responses, evidence, native exports, handoff, or token counts.

Report: `results/language-cross-preflight.json`  
SHA-256: `689e9dc10d83480019ab153e732869e9899c1502aee2d35b3006df3fdc7c23c2`

## Verified integrity and input boundary

All recorded dependency hashes and all 42 reused original-Qwen file hashes match, covering its 21 raw call records and 21 request-audit records. The original report hash, input hash, and original source dependencies match the cross-run manifest. The original run was reused without regeneration.

The selected cases are exactly the original shortest, median, and longest Qwen-input development cases, in the same order. Their membership remains disjoint from the reserved group. The Phi handoff matches the cross-run manifest and all six new Phi writer files.

Every writer input matches the serialization of the prepared earlier history only. The actual native system and user messages are identical across the two writer families for each case, and the summary system instruction is identical across all six summary writes. No target catalog block or target-outcome field was introduced into writing.

An independent BM25 calculation reproduces the retrieved four historical records and their chronological presentation. All 42 reader messages match their expected evidence condition and the prepared target catalog. The reader system instruction is identical across model families and conditions. Target inputs have only the allowed target index and title/features structure. No diagnostic fallback was used.

## Verified generation and resource records

- Six writer-pair cells contain 12 writer calls. The 42 reader cells cover all seven evidence conditions under both readers for all three cases.
- All 54 response IDs are unique. Complete response objects, actual request messages, and output allowances match audit records one to one. The 33 new calls consist of 27 Phi and six Qwen calls.
- The server logs contain exactly 21 original Qwen, 27 Phi, and six new Qwen completion POSTs. Consecutive attempt files contain no gaps or unexplained extra attempts. Every attempt completed; there are no recorded transport failures, pretransport rejections, or invalid writer/reader cells.
- All generations terminate with `stop`. Every native write has exactly one generation. Every native export is nonempty, with unique IDs and exact inserted/exported ID and memory-text agreement. In case order, Qwen exports contain 12, 1, and 12 memories; Phi exports contain 1, 11, and 12.
- Every summary parses as the expected single-field profile object. Qwen word counts are 244, 197, and 212; Phi counts are 204, 180, and 213. All satisfy the 400-word limit.
- All 42 reader outputs independently parse as exactly three finite, nonboolean numbers in the inclusive range 1 to 5.
- All actual prompt counts were recomputed with the respective pinned tokenizer and chat template, without importing the runner's measurement helpers. They exactly match pre-request records and server usage. The maximum prompt counts are 13,273 for Qwen and 12,782 for Phi. Maximum prompt plus output allowances are 15,321 and 14,830, respectively, below the 16,384 cap. Completion limits and usage arithmetic also agree.

The checker used standard-library parsing, an independent BM25 calculation, and pinned local tokenizers. Aggregate check results are retained in `data/language-cross-preflight-v1/internal-review-check.json`. Private review text and participant identifiers are omitted from this review.

## Interpretation

The run establishes operability for these three selected development cases under the frozen two-writer, two-reader configuration. It does not establish accuracy, comparative predictive value, or population reliability. In particular, the one-memory native exports are faithful recorded outcomes, not missing export pages; syntactic validity does not establish retained information quality.

The engineering pass does not authorize a scientific claim of equal memory size, a controlled speed comparison, or confirmation readiness. Native and summary constraints differ, the models ran sequentially, and no target outcomes were scored. Broader development checks, precision planning, and the separate confirmation freeze remain necessary.
