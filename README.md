# Personal AI memory studies

Research owner and intended paper author: Shivam Gupta.

**Research in progress.** The two-domain held-out validation is running on 200
users per domain with two readers. Its protocols and primary analysis were
published before reserved-user inference at commit
[2f0d896](https://github.com/shi1720/personal-ai-memory-studies/commit/2f0d896).
The complete manuscript is being prepared from the finished measurements.
No completed paper, external peer review or validated new algorithm is claimed.

Read the [Coat protocol](docs/confirmation-protocol.md),
[MovieLens protocol](docs/movie-validation-protocol.md),
[reproduction guide](docs/confirmation-reproduction.md), and
[execution record](docs/confirmation-execution-record.md).

Start with the [native memory study](docs/coat-memory-development-results.md),
its [results figure](results/figures/coat-memory-development.png), and the
[released-cohort audit](docs/memorycd-baseline-audit-results.md).

## Reproduce the latest figure from released measurements

```sh
python3 -m venv .venv-analysis
.venv-analysis/bin/python -m pip install -r requirements-analysis.txt
.venv-analysis/bin/python src/plot_coat_memory_development.py
.venv-analysis/bin/python -m unittest discover -s tests
```

This renders saved measurements; it does not rerun model inference. The plot
checks the analysis source and result-trace hashes. Full observed-data analyses
also require the original datasets and locally generated raw traces, which are
not redistributed. Experiment protocols, exact model revisions and environment
records are included. The original runtime was Apple Silicon with MLX.
Recorded environment paths describe that runtime and are not a portable
one-command installation. Recreate preflights with local paths in a separate
working copy before attempting fresh inference. Preserve published results.

The earlier exploratory studies used local Git freezes, not public
preregistration. The later two-domain validation has a separate public
pre-inference freeze at commit 2f0d896. Do not retroactively apply that freeze
to the exploratory studies.

## Study status

Status: the retrieval audit, partial-recalibration pilot and three-model
retention audit are complete. The partial-recalibration candidate was rejected
as the main contribution. Pilot 004 completed both models, source audits,
reader-budget checks and answer-format sensitivity. Its current hypothesis
is not being promoted to the main paper contribution.
Source-path inspection subsequently showed that the tested exported prompt is
not on Mem0's active extraction path at the pinned revision. See
`docs/pilot-004-source-correction.md`; this is not a native-pipeline study.
No completed paper or demonstrated new method is claimed. See
`docs/pilot-002-results.md`, `docs/pilot-003-results.md` and
`docs/pilot-004-results.md` for the findings and limitations.
The subsequent memory-confidence screen is complete in
`docs/memory-probe-results.md`: 69 additional generations, no eligible primary
comparison under its output budget, and no prefix-selection gain over the fixed
baseline. Its analytic controls and per-case records are retained without a
novelty claim.
`docs/gated-memory-estimand.md` adds an exact gate-weighting check and a pinned
audit of the author-released Coat ratings. It separates a change of statistical
target from an estimator improvement, and known-item recall from unseen-item
prediction. No new model or causal empirical result is claimed.
`docs/coat-development-results.md` reports the frozen observed-rating screen:
30 development users, 438 new-item targets, useful personalization signal from
established regression baselines. The 200 reserved users remain unscored.
Native Mem0 implementation preflight traces are separate from predictive results.
The completed native-memory prediction study is in
`docs/coat-memory-development-results.md`: 120 calls, 438 scheduled targets,
and a paired MAE difference of +0.0949 with an exploratory interval crossing
zero. It does not establish average extraction-related degradation.
`docs/memorycd-baseline-audit-results.md` records the separate released-data
baseline and timestamp audit, without a benchmark-reproduction claim.
Target standard: ICML, ICLR, NeurIPS or a comparable venue. Venue fit will follow
the contribution and evidence. No acceptance probability is asserted.

## Research question

What prevents a personal assistant from using a changing user history reliably,
and which failure can be addressed by a technically substantive contribution?

The broad idea of a temporal personal knowledge graph is already well explored.
The current phase screens narrower hypotheses, audits datasets, and builds a
reproducible evaluation foundation. Changing the topic is explicitly permitted.

## Contents

- `docs/research-contract.md`: scope, evidence requirements and stopping rules.
- `docs/novelty-screen.md`: candidate decisions, closest work and unresolved gaps.
- `references/screening.json`: bibliographic leads with evidence levels.
- `docs/venue.md`: verified venue requirements and dates.
- `src/`: data validation and experimental infrastructure as it is implemented.
- `tests/`: meaningful tests for measurement correctness.
- `results/`: measured outputs with provenance, never illustrative scores.

Raw third-party data and model weights are not redistributed by default.
All public benchmark data must be treated as potentially synthetic; a public
dataset is not automatically a study of real consenting users.

## Integrity

No invented experiments, reviewer endorsements, novelty guarantees or citations.
Exploratory analyses must be labelled exploratory. Confirmatory evaluation will
use a frozen protocol and held-out data. Prior work is distinguished by verified
method details, not by a missing keyword in its abstract.

## Reproduce the first audit and baseline

The data audit, downloader and lexical pilot use Python's standard library.

```sh
python3 src/fetch_longmemeval.py
python3 -m unittest discover -s tests -v
python3 src/data_audit.py data/longmemeval/98d7416c24c778c2fee6e6f3006e7a073259d48f/longmemeval_s_cleaned.json --output results/longmemeval-s-audit.json
python3 src/retrieval_pilot.py data/longmemeval/98d7416c24c778c2fee6e6f3006e7a073259d48f/longmemeval_s_cleaned.json --output results/pilot-001-retrieval.json
python3 src/plot_pilot.py
```

The optional plotting step requires Matplotlib. No model is involved in these
retrieval measurements. See `docs/pilot-001.md` for exact definitions.

## Local model runtime

On compatible Apple Silicon/macOS, use an isolated Python 3.12 environment and
`requirements-macos.lock`. The pinned weights occupy approximately 2.1 GB.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos.lock
.venv/bin/python src/prepare_local_model.py
.venv/bin/python src/smoke_local_model.py
```

This uses a community 4-bit conversion of Qwen3-4B-Instruct-2507, not the original
BF16 checkpoint. The two smoke examples verify execution only. Model artifacts
and the environment remain git-ignored.

## Partial recalibration feasibility study

`docs/pilot-002.md` fixes the inference protocol; `docs/pilot-002-analysis.md`
describes the trace replay. `docs/partial-recalibration-note.md` states the
deterministic bound and its assumptions, including a computation barrier that
may rule out useful savings at strict risk limits. None is a novelty claim.

```sh
.venv/bin/python src/prepare_personamem_pilot.py
.venv/bin/python src/run_personamem_pilot.py
.venv/bin/python src/analyze_personamem_pilot.py
python3 src/plot_personamem_pilot.py
.venv/bin/python src/analyze_grid_resolution.py
```

Inference resumes only when the code, protocol and input manifests match.
Analysis rejects incomplete traces. PersonaMem-v2 is downloaded at a pinned
revision under its dataset card's CC BY 4.0 license. The 128 selected personas
are development data, with separate 64-persona calibration and evaluation
groups. This is not an official leaderboard run. The constrained-choice reader
uses 3,072 total prompt tokens and a community-quantized model.

The exact interval algorithm and oracle certificate-size diagnostic have
exhaustive small-instance checks. The oracle accesses hidden new outputs and is
not an online acquisition strategy. Partial-run savings measured from the full
trace are offline counterfactual accounting, not observed wall-clock speedups.
Invalid low-precision infrastructure outputs are retained in `results/invalid/`
and excluded from analysis.

One precisely defined input-schema repair is recorded in
`docs/pilot-002-amendment.md`. Previously completed prompts were verified unchanged
before resuming. The final reader already includes this repair; a fresh run does
not need the historical migration script.

The completed pilot required 62 of 64 calls at a 5% marginal risk target and
answered only one of 64 evaluation questions, incorrectly. This is a stopping
result, not a successful efficiency claim. Further work must pass a new research
gate rather than dress up the failed pilot as a conference-ready method.

## Retention audit

Pilot 003 uses fictional journals with exact event-level truth and compares
retained-subset frequencies. These are custom memory writers, not reproductions
of production memory systems. Every model run uses frozen prompts and manifests.
`docs/pilot-003.md`, `docs/pilot-003-controls.md` and
`docs/pilot-003-replication.md` distinguish the original pilot, post-result
controls, and additional-model checks. Model checks reuse development journals.

```sh
python3 src/retention_pilot_data.py
.venv/bin/python src/run_retention_pilot.py
python3 src/analyze_retention_pilot.py
.venv/bin/python src/run_retention_controls.py
python3 src/analyze_retention_controls.py
.venv/bin/python src/prepare_mistral_model.py
.venv/bin/python src/run_retention_replication.py --model mistral
python3 src/analyze_retention_replication.py --model mistral
.venv/bin/python src/prepare_phi_model.py
.venv/bin/python src/run_retention_replication.py --model phi
python3 src/analyze_retention_replication.py --model phi
python3 src/retention_format_sensitivity.py
python3 src/plot_retention_pilot.py
python3 src/plot_retention_pilot.py --sensitivity
```

The syntax-only sensitivity analysis was introduced after observing Phi-4's
Markdown fences. It keeps strict results intact and never repairs identifiers
or extracts arrays from prose. Invalid cases and missing activity groups remain
explicit. Different native model templates limit causal comparisons across
model families. None of the retention metrics is downstream answer accuracy.

## Exported extraction-prompt and reader gate

Pilot 004 uses twelve fresh fictional journals and the exact upstream user-fact
extraction prompt at a pinned Mem0 revision. The exported prompt is not the
active pipeline's prompt, as documented in the source correction. This is a component test, excluding
native memory updates and retrieval. The original protocol and subsequent
reader-budget sensitivity are separate immutable run dependencies.

```sh
python3 src/fetch_mem0_prompt.py
python3 src/extraction_pilot_data.py
.venv/bin/python src/run_extraction_pilot.py --model qwen
python3 src/analyze_extraction_pilot.py --model qwen
.venv/bin/python src/run_extraction_budget_sensitivity.py --model qwen
python3 src/analyze_extraction_budget_sensitivity.py --model qwen
python3 src/audit_extraction_claims.py --model qwen
.venv/bin/python src/prepare_phi_model.py
.venv/bin/python src/run_extraction_pilot.py --model phi
python3 src/analyze_extraction_pilot.py --model phi
.venv/bin/python src/run_extraction_budget_sensitivity.py --model phi
python3 src/analyze_extraction_budget_sensitivity.py --model phi
python3 src/audit_extraction_phi.py
python3 src/extraction_answer_sensitivity.py --phase initial
python3 src/extraction_answer_sensitivity.py --phase budget
python3 src/plot_extraction_pilot.py
python3 src/plot_extraction_pilot.py --answer-format-sensitivity
```

The commands run both models and both budgets before the shared format
sensitivity scripts. The Phi-specific audit reads its completed original trace.
Run models sequentially on the local GPU. Analyses reject incomplete traces.
The higher-budget run requires a complete original trace and reuses its exact
prompts. The claim audit has a limited, post hoc grammar; unsupported prose
requires explicit inspection and is never automatically labelled false.

Neither model demonstrates an overall frequency-answer loss from the unmodified
exported prompt in this development set. Source errors and format sensitivities
are nevertheless present. The oracle count ledger answers frequency questions
but lacks evidence for dated questions. See `docs/pilot-004-results.md` for all
scores, source corrections and limits. Upstream prompt attribution and its Apache 2.0
license are in `licenses/`; downloaded upstream files remain Git-ignored.

## Delivery-partition candidate screen

`docs/delivery-partition-screen.md` separates transport delivery from semantic
consolidation and chronology. It records primary-source overlap and inspection
of the active pinned Mem0 write path. A canonical buffer passes an exhaustive
1,024-partition engineering check with a toy writer; this is not a model result
or a novel memory method. The unrestricted transport-invariance candidate is
not promoted to the paper's main contribution. Reproduction commands and the
assumptions limiting the result are in that note.
