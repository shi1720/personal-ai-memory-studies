# Development runner and protocol review

Reviewed 20 September 2026. This is a bounded internal code and protocol review of the development inference runner. It is not an external review or validation of experimental outcomes. The label/materialization and scoring modules were reviewed separately. No actual inference, manifest creation, target-label access, or reserved-input access occurred in this review.

**Verdict: no remaining runner blocker identified for freezing and executing the specified development evaluation.**

## Checked design and integrity

- The plan uses exactly the 60 prepared development cases, preserves the existing three engineering cases, and excludes them from new generation. Its 1,026 new cells have unique identities and divide into 399 Qwen-base, 513 Phi, and 114 Qwen-cross cells. The 54 original generation records are mapped and reused without reserialization or regeneration. Combined totals are 240 writer generations and 840 reader generations.
- The runner opens the prepared development inputs and pinned engineering artifacts. It does not open the raw source archive, source mapping, target-label files, donor histories, or reserved confirmation input file. Existing serializers preserve the history-only writer boundary.
- The manifest freezes preparation, reused hashes, original prerequisites, model/environment references, new runner and analysis definitions, precision rule, and protocol. Current frozen dependencies are verified before continuation. All analysis modules identified in the separate review are included in the dependency set.
- Sequential stage handoffs verify completed cell ledgers, raw records, and assigned transport audits. The report verifies existing handoffs and rejects later-stage records without prior completed handoffs. A process-wide lock prevents concurrent development runners from mixing stage audits.
- A durable cell reservation precedes execution. Completed errors are retained. Cached records must match their ledger hashes and contracts; ambiguous interrupted cells, unledgered outputs, orphan audits, and changed records block continuation rather than regenerate an answer.
- Per-cell audit membership permits at most one generation for a planned cell, accounts for native failures before transport, and rejects an audit assigned to multiple cells. Response identities and hashes must match retained outputs. Duplicate response IDs are rejected within and across stages and reused records.
- The unchanged runtime enforces model identity, decoding settings, actual tokenizer counts, output allowance and stage caps. Native export validity uses nonempty, complete ID-and-text matching and normal termination. Summary and reader parsing remain frozen.
- Reader validity and required-writer validity are separate. A syntactically valid diagnostic sentinel read does not become a valid memory pipeline. The report correctly flags constant-three predictions whenever either required component is invalid. Completion means all planned cells are accounted for, not that all predictions succeeded.

## Correction and tests

Review identified one missing budget-integrity check: completed server responses could report malformed or excessive completion usage without rejection. This is corrected. Prompt, completion, and total counts must be true integers; completion must lie between zero and the output allowance, and total must equal prompt plus completion. Boolean, negative, fractional, missing, and inconsistent usage is rejected.

Independently ran all 18 focused synthetic runner tests after the correction; all passed. They cover the exact stage plan, reuse immutability, terminal transport failures, invalid outputs, interruption handling, orphan audits, changed files, native setup failures, token overflow, handoffs, pipeline-failure flags, duplicate identities, and completion-usage validation. These tests use temporary synthetic records and do not call a model.

## Scope of the eventual decision

The prospective precision rule measures resolution of paired operational errors, not memory quality. Many constant-three fallbacks can make contrasts precise without demonstrating useful prediction. Preserve and report failures, pipeline validity, and paired valid-only sensitivity when interpreting a future GO. The current protocol appropriately does not make accuracy or usefulness claims from engineering completion alone. Results and persisted-output integrity still require checking after execution, before any confirmation decision.

## Reviewed hashes

- `src/run_language_development.py`: `2315580486a1ecc6e0e23b08f30df45e24ad0b66b1efae82b2a31559993650be`
- `tests/test_language_development.py`: `800f6b2b958be0a7c7b5013655e526d580c012f5c579b977e8c10b064e761504`
- `docs/language-development-protocol.md`: `595a5c1de0eac88bf988096d2da853817f8c4d4736021c31f132752f3048f604`
