# Pilot 004 source-path correction

Recorded after Qwen's original and budget-sensitivity runs completed and while
Phi-4's original run was in progress. This corrects the interpretation, not the
frozen experimental inputs, prompts or outputs.

## Verified source distinction

The tested `USER_MEMORY_EXTRACTION_PROMPT` really is exported by
`mem0/configs/prompts.py` at commit
`a39a802bbc93e85b820078cd3c4dbaf53af25dbe`. However, inspecting the executable
`mem0/memory/main.py` at that same commit shows that the ordinary inferred-add
path imports and uses `ADDITIVE_EXTRACTION_PROMPT` with
`generate_additive_extraction_prompt`. It does not import the tested constant.
The sync path constructs this request around lines 939-960; its response parser
reads the `memory` field around lines 978-981. The inspected async path likewise
uses that output field. This is source inspection, not a runtime reproduction.

The earlier inspection of a prompt definition did not verify whether that
definition was on the active execution path. Calling it the current native
extraction interface was therefore too strong. The correct description of
Pilot 004 is **a pinned, upstream-exported prompt component test**.

Primary source:
[Mem0 memory/main.py at the pinned commit](https://github.com/mem0ai/mem0/blob/a39a802bbc93e85b820078cd3c4dbaf53af25dbe/mem0/memory/main.py).
The downloaded source hash is in `references/mem0-parser-screen.json`.

## What remains valid

The recorded requests use the documented exported prompt without changing its
text, apart from the declared fixed date and the separate count-aware condition.
The recorded model outputs, source comparisons, budgets, scores and timings
remain observations of those requests. They are not observations of the active
Mem0 pipeline. The original protocol already excluded end-to-end product claims;
this correction additionally limits the claimed authenticity of the component.

The JSONL `context: native` field is a historical condition identifier meaning
the unmodified exported prompt. It must not be read as a deployed/native-system
label. Frozen manifests retain their original descriptive strings and hashes
for auditability; this correction governs their interpretation.

## Consequences

1. The current experiment does not pass a native-pipeline external-validity gate,
   regardless of the second model's eventual score.
2. Its exact-key facts parser is our protocol choice. A rejected extra field
   is not evidence that Mem0 itself would reject that response.
3. The completed Qwen result still rejects transferring the forced six-event
   omission claim to this unrestricted exported prompt, within this small test.
4. Finish the already specified bounded component test for its diagnostic value,
   but do not scale it as a reproduction or describe it as product performance.
5. Any future current-pipeline study must trace active request construction,
   provider/schema handling, updates, embeddings, retrieval and output handling
   before freezing a protocol. An exported symbol alone is insufficient evidence.

No acceptance, novelty or deployed-system conclusion follows from this audit.
