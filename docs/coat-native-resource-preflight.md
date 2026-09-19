# Coat native memory resource preflight

Run only the first three users in the frozen fitting split, in split order.
Read only their 24 observed self-selected ratings and the released item
attributes. Do not load random-item target ratings. Serialize records in item
index order, explicitly stating that the order is not chronological. Exclude
front-page promotion and user demographic attributes. Do not fabricate chat
history: the message says these are structured records from a rating study.

Use the complete native Mem0 configuration validated in the fictional preflight,
with a local Qwen3-4B 4-bit writer, temperature zero, output maximum 2048, native
BGE embedding, local Qdrant, native keyword search and spaCy components. One
add call per user, separate user scopes, all 24 records in a single message.
No custom extraction prompt or memory quota. Keep the native parser and store.

Record completion/length stop reason, prompt/output token counts, extracted and
stored memory counts, wall time, persisted text bytes, and exact trace hashes.
Raw data-derived messages and memories remain under ignored data/, respecting
the existing nonredistribution policy. No correctness score, automatic factual
judge or preference accuracy is part of this preflight. Do not interpret
memory count as recall. A missing record may be abstracted into another memory.
A successful add call need not imply a complete or faithful user model.

If any call truncates or fails, retain it without a hidden retry. This run only
checks resource feasibility and implementation readiness. It cannot establish
superiority, causality, statistical significance or conference readiness.
