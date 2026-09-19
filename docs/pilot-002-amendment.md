# Pilot 002 input-schema amendment

Recorded after a schema failure at example 88, before analysis of the complete
trace. The pinned history has exactly one message with the value
`{"role": "assistant"}`, with no content field. An audit of all 128 histories
found no other non-system message with a missing or non-string content field.

The reader now skips exactly this role-only assistant record. It does not insert
text, change any label, replace an example, alter retrieval, or permit other
malformed schemas. All 128 examples remain in the original order and split.
The change is a narrowly defined input repair, not an outcome-selected exclusion.

The original reader, manifest, and first 87 predictions are preserved in
`results/amendments/pilot-002-empty-assistant/`. The executable migration verifies
that all 127 other histories produce identical conversation blocks, and that all
174 prompts for the 87 completed examples are byte-identical to saved prompts
with identical token counts and matching recorded hashes. Only the reader hash
in the run manifest is updated. The verification report records both hashes.

The original frozen protocol remains unchanged. This amendment is part of the
experimental record and must accompany any reuse of the results. A regression
test verifies the precise skipped schema and rejection of a role-only user.
