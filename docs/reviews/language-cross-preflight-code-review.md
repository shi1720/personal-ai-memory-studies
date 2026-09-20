# Cross-preflight code review

Reviewed 20 September 2026 against `docs/language-cross-preflight-protocol.md`.

**Verdict: no remaining blocker identified for freezing and executing the specified engineering preflight.** This is a bounded internal code review, not external validation or a predictive-result review. No new inference, target-label access, or reserved-input access occurred during this review.

The four new modules preserve the frozen three-case selection, history serializer, summary prompt, BM25 retrieval, and original Qwen records. The intended allocation is 27 new Phi calls followed by six new Qwen calls, with 54 combined responses. Model and tokenizer manifests, actual pre-request token counts, output allowances, and stage call caps are enforced. Native insertion/export records correctly use `id` and `memory`; ID and text matching is appropriate for the actual persisted format.

The following issues identified during review are now corrected:

- The transport wrapper checks the returned model identity, preserves a mismatched response in the audit, and records it as failure.
- The combined pass gate requires a unique, exact response bijection using response ID, response-content hash, and model identity. It also requires exactly one generation per native write.
- Stage exceptions and interruptions receive terminal records, with a guarded report refresh that does not mask the original exception. Cached failed or interrupted requests cannot silently regenerate.
- Phi writer hashes are frozen in the handoff. The Qwen stage verifies them before use, and every report refresh validates any existing handoff. A handoff is mandatory once a new Qwen audit attempt or cross-reader output exists, closing the report-only bypass identified during review.
- Invalid evidence receives an explicit diagnostic-fallback flag and cannot satisfy the engineering pass gate. Attempted, completed, rejected, and failed transport counts are distinguished.

The report-only state inspected before inference correctly had zero new transport attempts, 21 reused attempts, three existing writer-pair records, 15 existing reader records, and false completeness and prototype-pass flags. It did not claim that the cross-preflight had succeeded.

Independently ran the ten focused mocked tests in `tests/test_language_cross_preflight.py`; all passed. These cover wrong model and tokenizer rejection, token and call budgets, failed-call caching, interruption reservations, native export/termination failures, response identity and bijection, and handoff integrity. No live model calls are made by these tests.

A successful future run will establish only operability on the frozen development cases. Subsequent persisted-output verification remains necessary. It does not establish accuracy, population reliability, an equal-memory-size comparison, or readiness to score the held-out confirmation set.

## Reviewed source hashes

- `src/language_model_pins.py`: `da54e2ffb5b34c7d15d93bf6281ddcd943faf8c2c3bca538d58481c031ccc5b7`
- `src/count_cross_request_tokens.py`: `a14850abd481c6c900be1f018577caa0d18208266c4d12dc64e79a3458caa92e`
- `src/language_cross_runtime.py`: `a5502a04065c724e6479def7b60b6be1076d00cf309283ec01a575dc25b18b78`
- `src/run_language_cross_preflight.py`: `a9a07c6d75624659242570bbf55d938fb325b3e2c8c78112fde8cfdf924b06ea`
- `tests/test_language_cross_preflight.py`: `199b55e690a83994d1abf5bc838718bba85aaed551b383fbc224804dbc01f400`
