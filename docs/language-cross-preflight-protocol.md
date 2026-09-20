# Cross-writer and cross-reader resource preflight

## Scope and frozen cases

This is a second-writer and cross-reader engineering gate on three existing development cases. It is not an accuracy experiment, a confirmation run, or evidence of population reliability. No target ratings, reserved confirmation inputs, raw review archive, or source-row mapping may be opened. The run consumes only prepared development inputs and previously persisted development outputs.

Use exactly the three cases already selected by the passed Qwen resource preflight, in its recorded order. That selection was shortest, median at index 30, and longest by Qwen full-history reader token length among 60 development cases, with case-hash tie breaking. Do not select new cases by Phi lengths or substitute cases after failures. These cases remain development data permanently.

The original three Qwen native writes, three Qwen summary writes, and 15 Qwen reader calls are reused from their persisted records. They must not be regenerated. Verify their raw-file hashes, request audit, input dependency hashes, and original passed engineering gates before reuse. Preserve the original report and raw files byte for byte. A broken provenance link blocks the new run rather than triggering regeneration.

## Evidence conditions and call allocation

Each reader receives the same three target catalog descriptions and one of seven evidence conditions:

| Condition | Earlier evidence |
| --- | --- |
| No history | The original fixed no-history string |
| Full history | All 12 prepared historical reviews with their earlier ratings and catalog fields |
| Qwen native | The complete, nonempty native export from the original Qwen write |
| Qwen summary | The original valid task-matched Qwen profile |
| Phi native | The complete, nonempty native export from the new Phi write |
| Phi summary | The new valid task-matched Phi profile |
| BM25 history | The same four raw historical records selected by the frozen joint-query BM25 rule |

The writer family is an experimental condition recorded in the audit. Do not add writer-identity instructions to the reader prompt. Native exports use the same complete-memory serialization as the original preflight; retain all exported memories rather than imposing a new length or relevance filter.

Two sequential local server stages are planned:

1. **Phi stage: 27 new calls.** For each of the same three cases, run one pinned native Phi extraction and one Phi task-matched summary, then have Phi read all seven conditions. This is six writer calls and 21 reader calls. Use the pinned Phi conversion and tokenizer manifest. Isolate each native store by writer and case.
2. **Qwen stage: six new calls.** Stop the Phi server, start the original pinned Qwen conversion, and have Qwen read the Phi-native and Phi-summary evidence for each case. Reuse the existing Qwen reader records for the other five conditions.

There are **33 new planned calls** and **54 combined calls**, comprising 12 writers and 42 readers across both writer and reader families. The original 21 calls contribute six writers and 15 readers. The new run contributes six writers and 27 readers. These numbers count actual generation requests; local embeddings, tokenization, and store operations are not generation calls.

Only one model server runs at a time. Bind it to loopback and preserve the original single prompt slot, single decode slot, and one-entry prompt-cache resource configuration. No hosted provider or paid API is used. The Phi stage has a hard maximum of 27 attempts and the new Qwen stage a hard maximum of six attempts. An unexpected native generation is recorded and counts toward the relevant cap. It must not silently increase the budget or be hidden within a write. Such a deviation fails the planned engineering gate even if later outputs look valid.

## Frozen processing and generation

Reuse the original historical-input serializer, reader prompt, task-summary instruction, output parsers, and BM25 implementation without rewriting them for Phi. The native extraction uses the same pinned upstream Mem0 revision, native prompt, and non-LLM configuration; only the pinned writer model and corresponding tokenizer change. Record any execution-time date fields inserted by the native pipeline. Do not retrofit new native outputs into the original run.

BM25 remains the existing deterministic four-record retrieval against the combined three-target catalog query, with k1=1.5, b=0.75, positive Robertson-style IDF, lowercase alphanumeric tokenization, and deterministic ties. It scores historical review and catalog text, not historical rating values, and presents the selected records chronologically. It is not a per-target retrieval experiment. Verify that retrieval and serialized raw-history evidence are identical for both readers.

Every generation uses temperature zero and top-p one. Writer allowance is 2,048 tokens and reader allowance is 256 tokens. Each complete actual chat prompt plus allowed generation must fit within the common **16,384-token engineering cap**. The timeout is 360 seconds per transport request, and client automatic retries are disabled with `max_retries=0`.

Count each actual request before transport using that server model's pinned tokenizer and chat template, including native system-prompt overhead. Verify the tokenizer/configuration files and record tokenizer library versions. The server-reported prompt count must exactly equal the independently computed count. This cap is an engineering choice, not a claim about either model's maximum supported context.

The summary must parse as the original single-field profile object, contain nonempty text, and contain no more than 400 whitespace-delimited words. Do not truncate or regenerate a long summary. Native exports must contain nonempty memories, unique IDs, and the exact inserted memory IDs and corresponding text. An empty or incomplete export fails. A short but complete export is retained unchanged.

Readers must return exactly three finite, nonboolean numeric ratings in the inclusive range 1 to 5 under the original parser, including its permitted JSON-fence handling. No answer repair, extraction of a convenient subset, coercion of invalid values, or accuracy-dependent choice is allowed.

## Failure records, provenance, and stage handoff

Write an attempt marker before every request and preserve the actual request, response or error, finish reason, elapsed time, token usage, actual prompt count, and model identity. Count transport attempts even if native parsing fails before its callback. Pretransport rejections, timeouts, interruptions, and failed native calls stay in the record. Do not retry, rerun, or overwrite any failed call. A later corrective experiment requires a separately documented protocol and output directory; it cannot replace this run.

The manifest must freeze the protocol, runner modules, relevant source dependencies, both model/tokenizer manifests, input preparation report, prepared development input hash, original Qwen report hash, and reused raw-file hashes before the first new inference. Record client and server environments and stage start/stop information. The combined report must distinguish reused from newly generated records and retain hashes linking every result to its raw record. Do not count a reused record as a new transport attempt.

Before the Qwen stage, verify persisted Phi writer outputs and handoff hashes. Invalid or missing Phi evidence must not be repaired or replaced with fabricated valid memory. If diagnostic reads with a predeclared fallback are retained by the implementation, they must be explicitly marked as diagnostic and cannot satisfy the intended Phi evidence condition. The combined gate fails regardless of whether those diagnostic reads parse. An incomplete run is reported as incomplete, with planned, attempted, completed, blocked, and invalid counts distinguished.

Request wall times include the tokenizer precheck. Native total wall time also includes embeddings and store setup. Preserve request-level time separately from whole-write time, and do not duplicate a whole-write duration across generation calls.

## Engineering decision rule and limits

Mark the combined engineering gate passed only if all expected writer and reader cells are present, every writer is valid, every native export is complete and nonempty, all summaries satisfy the word limit, all 42 reader outputs are valid, all generations finish with `stop`, all token agreements are exact, all request budgets are respected, and all provenance checks pass. The planned 33 new calls must match retained transport records one to one, with no hidden retries, substituted cases, or additional generations. Any failure or missing cell means this engineering gate has not passed.

A pass establishes operability for these frozen development cases under the recorded local configuration. It does not establish predictive performance, superior memory quality, a new algorithm, transfer to unseen users, or a population reliability rate. No target scoring or accuracy comparison belongs in this preflight. Native memories and 400-word summaries have different length constraints, so the comparison does not isolate equal memory size. Sequential model stages also do not constitute a controlled inference-speed benchmark. The existing catalog snapshot limitation remains.

Larger development validation, precision planning, and a separate public analysis freeze remain prerequisites for held-out confirmation. This cross-reader screen does not unlock reserved inputs by itself.

## Frozen reference anchors

The following hashes anchor the original passed records and shared definitions when this protocol was written. The run manifest additionally freezes the new implementation and the exact reused raw records before inference.

| Reference | SHA-256 |
| --- | --- |
| `results/language-extension-resource-preflight.json` | `bf80f62a77f907bb5da782c1378c024f5c0d14a727dae9fb55fc66b5b6f134d6` |
| `src/run_language_resource_preflight.py` | `59014d22a472f637ec3698bbcf4c4b6bb48e46ffd64748e98018bf19a4097ba1` |
| `src/language_extension_inputs.py` | `8d8768f1a6d04e69e911f5f2ea148e944410002955928b090a155378e8a808a8` |
| `src/count_language_request_tokens.py` | `f976371fc12000509c6e674902e50a0b69cd1af49497c4fb9b61ad0d1b92fb9b` |
| `references/local-model-manifest.json` | `539676dc2ffde3643d164f8bf20cfa5e560b0be04b59c6f092aa62987f7207a9` |
| `references/phi-model-manifest.json` | `590c8f5465bd6d0c9216db820a4d4b06aa71b7dfcdea411ef6069e0f2e74d331` |
