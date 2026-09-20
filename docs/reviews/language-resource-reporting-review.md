# Development resource reporting: bounded review

20 September 2026. Internal independent AI review of new descriptive reporting code and invented-artifact tests only. No real development records, target labels, reserved inputs, model calls, or frozen analysis files were accessed or modified. The resource-report CLI was not run.

## Verdict

No remaining substantive accounting or gating defect found in the reviewed adapter and pure aggregator after the corrections below. This review verifies implementation on synthetic cases, not actual experiment completion, actual resource measurements, or deployment performance.

Reviewed the new adapter, pure aggregator, reporting specification, and their tests. Read the existing completion verifier, stage-handoff checks, and runtime timing boundaries as source context only.

## Accounting and integrity

The CLI verifies complete development inference and stage handoffs before adapting saved artifacts. The adapter separately rejects an incomplete report before its first artifact-loader call. The pure aggregator requires the entire 1,080-cell grid, including exactly three reused users, 54 reused cells, and 1,026 new cells. These are cells, not assumed transport counts.

Audits are uniquely assigned to cells. Reused records are checked against the frozen inventory; new records require covered cell ledgers. Retained model responses are compared in full against their audit responses. Duplicate identities, duplicate assignment, missing ledgers, mismatched responses, and unassigned audits are rejected. Writer operations are counted once per representation, independent of their consumption by two readers.

Native and summary validity are reparsed. Reader validity and whole-pipeline validity remain distinct, preserving the resources used by diagnostic readers after failed writers while excluding those pipelines from valid counts. Invalid or empty native stores are not included in valid-writer size statistics. Failed native setup can correctly produce a recorded cell with zero audited requests; a failed transport with no response retains its known prompt count and unavailable server usage.

The initial pure aggregator accepted completed requests with missing token/usage fields. This conflicted with the specified completed-response integrity contract. The author corrected it: completed requests now require all prescribed counts and allowance, with prompt agreement, budget bounds, and total-token consistency checked. Missing usage remains available as a representation of failed requests. Synthetic tests cover both cases.

## Interpretation

Outer operation durations and nested audit durations are reported separately. The implementation does not add them together. Reused, new, and combined views are identified as overlapping. Token statistics remain separated by model tokenizer, and unavailable observations carry denominators and incomplete-sum flags rather than invented zero consumption.

The specification accurately limits native timings to their recorded boundary before final cleanup and limits reader timings to instrumented requests, excluding prior retrieval and prompt construction. It does not infer cloud prices, concurrency, end-to-end throughput, or repeated-use savings.

Reader groups now also expose descriptive prompt statistics restricted to valid required writers, retaining invalid reader responses within that subset. This prevents diagnostic evidence from being silently treated as successful compression. One interpretation boundary remains: the full-history group's own valid-writer subset contains all users because it requires no writer. Comparing that aggregate directly with a memory arm's smaller subset is not a paired same-user compression estimate. A future paired savings table must apply the memory writer's validity mask to both arms. No such savings claim or paired table is produced here, so this is not a present execution blocker.

## Synthetic verification

Independently ran all 28 resource-related synthetic tests in 0.985 seconds: seven adapter tests, twelve pure-aggregator tests, and nine existing resource-preflight tests. All passed. The invented full-grid fixture checks reuse attribution and exact unique-request counts. Added cases verify native setup failure without an audit, failed transport without usage, invalid-writer diagnostic readers, missing fields, and complete-before-load rejection. No real measurement is implied by these results.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -m unittest discover -s tests -p '*resource*.py' -v
```

Reviewed SHA256 values:

```text
aa1565ee79bf27e327adc6e8375a9b15566013d903584f7ed3225183ab9cdda9  src/summarize_language_development_resources.py
dd128bad38b5e493e29f660fbe244c1b98846799e763f65108b124dae248c9fe  src/language_resource_summary.py
60e12b50b6ca544d7b96784527aec5a3385261e2dab790215fc4fc4e7e8878e2  tests/test_summarize_language_development_resources.py
b7fb576f0863d4f6d533020f75c3cd0e66292eda4694614e32985b25b0dee637  tests/test_language_resource_summary.py
8fb9ba4634c9cb135af1184ee51397ad3f11673926d4b77cf340c9bb8ead4a25  docs/language-resource-reporting.md
```
