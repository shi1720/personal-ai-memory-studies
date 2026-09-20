# Independent internal review of the language resource preflight

Reviewed 20 September 2026. This is an internal computational check of persisted development-run records, not external validation, peer review, or a predictive-accuracy experiment. No inference was rerun and no target ratings were opened.

**Verdict: the recorded three-case Qwen resource preflight passes its declared engineering gates.** No discrepancy was found between the aggregate report and the persisted request, response, export, and token-count records.

Report reviewed: `results/language-extension-resource-preflight.json`  
SHA-256: `bf80f62a77f907bb5da782c1378c024f5c0d14a727dae9fb55fc66b5b6f134d6`

## Checks performed

An independently written checker used standard-library parsing and the pinned local tokenizer without importing the runner's measurement or validation helpers. It checked the prepared development inputs, preparation metadata, local request audit, native exports, reader outputs, and server log. It did not read the raw source archive, source-row mapping, confirmation inputs, or target-label files.

- All recorded source dependency hashes and 21 raw-call file hashes match. The development input hash and relevant tokenizer/configuration hashes match their pinned manifests.
- The selected cases exactly implement the declared shortest, median at index 30, and longest Qwen full-history reader selection among 60 development cases, with the declared deterministic tie break. None is assigned to reserved confirmation.
- There are exactly 21 consecutively numbered completed transport attempts, 21 unique response identifiers, and 21 server completion POSTs. The three native generations, three summary generations, and 15 reader calls match the audit one to one. There are no unexplained extra attempts in the retained records.
- All actual prompt lengths were recomputed with the pinned tokenizer and chat template. They match both the pre-request count and server usage for every call. The largest prompt is 13,273 tokens; the largest prompt plus allowed generation is 15,321 tokens, below the 16,384 engineering cap. Output allowances and usage arithmetic also agree.
- All responses terminate with `stop`. Each native write records exactly one generation. Native exported IDs are unique and match the inserted IDs, and exported memory text matches inserted text by ID. The three exports contain 12, 1, and 12 nonempty memories.
- Native and summary writer inputs match the prepared earlier-history serialization. The summary outputs parse as single-field profile objects and contain 244, 197, and 212 whitespace-delimited words, each within the 400-word limit.
- An independent BM25 implementation reproduces the four selected historical records and their chronological presentation. All five reader evidence conditions match their actual persisted inputs. Target inputs contain only the permitted target index and catalog title/features structure, with no target outcome fields.
- All 15 reader outputs independently parse as exactly three finite, nonboolean numeric ratings in the inclusive range 1 to 5. The report's validity, completeness, and prototype-pass flags agree with these checks.

Aggregate check output is retained locally in `data/language-extension-resource-v1/internal-review-check.json`. Private review text and participant identifiers are intentionally omitted here.

## Interpretation and remaining limits

The run establishes that this exact configuration can complete the selected input-size cases without the observed truncation, parsing, export, or accounting failures. It does not establish accuracy, population reliability, second-family reader compatibility, or confirmation readiness. The selected three cases are a resource stress screen rather than a representative sample.

The single-memory export is not an export-completeness error: it matches what the native extractor inserted. It does illustrate that syntactically valid native extraction can retain substantially different amounts of information. Subsequent evaluation must preserve this variation rather than repair individual outputs after seeing outcomes.

The native and task-summary pipelines have different output-size constraints, so these records do not support an equal-memory-budget claim. Token and elapsed-time accounting are engineering measurements, not a controlled inference-speed benchmark. The prior catalog-snapshot limitation remains unchanged. Larger development validation, the planned independent reader family, and a frozen analysis and decision protocol must precede any held-out confirmation inference.
