# Native memory pipeline preflight

This is an implementation preflight, not a performance benchmark. It uses a
small fictional interaction before any Coat user is passed to the system.

Run the unmodified Mem0 OSS package at commit
`a39a802bbc93e85b820078cd3c4dbaf53af25dbe` (package version 2.1.0). Use its
supported OpenAI-compatible LLM provider with a local MLX Qwen3-4B Instruct
2507 4-bit server. The provider name denotes an interface; no remote inference
provider or paid key is used. Generation uses temperature zero and a 2048-token
maximum. MLX does not implement constrained JSON decoding through this field;
record raw responses and finish reasons, and let the native parser handle them.
Use native FastEmbed BGE-small-en-v1.5, pinned cached files, native local Qdrant
and SQLite. Telemetry is disabled. No custom extraction instructions or prompt
replacement. No graph, reranker or platform-only functionality is claimed.

The synthetic input states three likes/dislikes and one numeric rating. Check
that add returns stored memories, that search retrieves user-scoped memories,
and that reopening the on-disk store returns the same memory IDs. Also search
a distinct unused user ID to check isolation. Record the exact input, output,
LLM messages, runtime, configuration, versions and relevant source hashes.
A passing smoke check establishes wiring only, not factual fidelity, preference
accuracy, completeness, fair budget comparison or reproduction of paper results.

The database and model files stay ignored. Preserve the synthetic trace in
results. Use a unique run directory and refuse overwriting an existing run.
No evaluation labels or actual Coat users enter this preflight.
