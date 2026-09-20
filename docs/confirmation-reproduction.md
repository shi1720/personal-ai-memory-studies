# Reproducing the independent validation

This study has three reproducibility levels. They have different resource and data requirements.

## 1. Inspect released results and rebuild figures

The public artifact contains per-user error summaries, run metadata, source/model hashes, and code. It excludes original rating archives, model weights, full rating prompts, generated memory text, and local databases.

Install `requirements-analysis.txt` in a fresh environment. Run the unit tests with `python -m unittest discover -s tests`. `python src/verify_published_results.py` independently recomputes the aggregate summaries and all ten paired bootstrap comparisons from the released per-user error records. It needs no source data, model weights or private responses. This checks arithmetic, not the original model predictions against targets. `python src/build_confirmation_figures.py` and `python src/build_confirmation_tables.py` rebuild the figures and LaTeX table inputs. Both verify recorded analysis hashes and the independent-calculation report before using the measurements. This is regeneration from released measurements, not new model inference.

The shared manuscript builds a named ICML 2026 preprint, an anonymous ICML 2026 review copy, and an anonymous TMLR submission copy. Install `requirements-paper.txt` for the Python PDF checker and install the Tectonic and Poppler binaries separately. Run `python src/build_research_paper.py`. Tectonic 0.17.0 builds `paper/main.tex`, `paper/anonymous.tex`, and `paper/tmlr-submission.tex`. Official TMLR style files are pinned to revision `7bf90efe3a0debbba703c05c43f3ff7e4d4a2992`; licenses and sources are recorded in `paper/THIRD-PARTY.md`. Styling does not indicate an ICML submission or acceptance. A future submission must use that venue cycle's actual style and policies.

## 2. Recompute from original raw responses

Obtain the licensed archives using `python src/fetch_confirmation_data.py`. This verifies publisher-source SHA-256 values without modifying released split files or lock files. Read the dataset terms before use. Do not run the development-selection script over the published metadata merely to fetch data.

The original scoring runtime is recorded in `references/confirmation-analysis-environment.json`: Python 3.9.6, NumPy 1.26.4 and Matplotlib 3.9.4. This differs from the separately recorded Python 3.12 inference environment. The frozen scoring commands are:

```sh
python src/analyze_confirmation.py
python src/analyze_movie_validation.py
python src/independent_result_check.py
python src/confirmation_auxiliary_report.py
python src/verify_published_results.py
```

They require the original locally retained raw responses and writer traces under `data/confirmation-v1/evaluation` and `data/movie-validation-v1/evaluation`. Those traces contain source rating records or their derivatives and are not redistributed in this repository. The source archives alone are therefore insufficient to reproduce exact recorded model outputs. Every raw trace is hashed in the released run metadata.

The separate calculation script imports no project metric, parser, or data-loading helpers. It reconstructs the evaluation directly from the archives, recalculates losses with explicit arithmetic, and fits ridge through augmented least squares rather than the main normal-equation solver. It also checks the ten primary effect estimates and their intervals. This is a second implementation on the same data, not an external peer review or independently collected sample.

## 3. Run a fresh model replication

Use a separate checkout so that published records and locks remain intact. The recorded local runtime uses Apple Silicon and MLX; this is not a portable CUDA inference package. The model manifests specify exact community conversion revisions and individual file hashes. Recreate the server environment from `references/confirmation-server-environment.txt` and the native pipeline from `references/mem0-native-complete-environment.txt`. Obtain the pinned Mem0 source revision, model files, BGE embeddings, and spaCy components. Upstream model and data licenses apply separately.

The native preflight configuration records absolute paths from the original runtime. In a replication checkout, regenerate it with local paths and verify the active native implementation and source hashes. Preserve the original records separately. Fit-user preflights and output-contract gates must pass before evaluation. Create new replication lock files for the local path-specific configuration; do not describe a new lock as the historical public registration. The history-only penalties are already selected and must not be retuned on evaluation labels.

Serve Qwen on loopback port 8317 with temperature zero, maximum 2,048 output tokens, one prompt slot, one decode slot, and a one-entry prompt cache. Reader requests independently cap output at 256. Use a single client worker. Run:

```sh
.venv-mem0/bin/python src/run_confirmation.py --model qwen --preflight
.venv-mem0/bin/python src/run_movie_validation.py --model qwen --preflight
.venv-mem0/bin/python src/run_confirmation.py --model qwen
.venv-mem0/bin/python src/run_movie_validation.py --model qwen
```

The Coat reader-only preflight records for both models are also required by the runner. They were generated with `src/confirmation_preflight.py` using fitting-user resource-preflight stores, before the native sequential preflight. A fresh checkout must reproduce those fitting-user stores rather than claim that the released format outcomes validate a different local runtime.

After Qwen is fully complete, stop its server and serve the pinned Phi model with the same server settings. Then run the MovieLens Phi preflight, the Coat Phi evaluation, and the MovieLens Phi evaluation. Phi reads the already-created Qwen memory stores. No accuracy analysis is performed until both datasets and models have finished. The complete-run guards enforce this ordering. Then run the scoring, auxiliary-report, and checking commands above and regenerate the paper figures and tables.

The continuation script in `src/continue_confirmation.py` is a local orchestration aid that waits for explicitly supplied owned process IDs, switches models, and executes those steps. It does not recover arbitrary failed jobs, silently retry generations, or manage cloud resources.

## Interpretation and archival boundaries

Commit `2f0d896` in the public repository is the pre-inference protocol/code publication. Earlier exploratory studies were not publicly preregistered before their data collection. The analysis family, constant-3 invalid-output fallback, two model conversions, user partitions, and primary contrasts were fixed before reserved-user inference. An auxiliary input-integrity audit and a second calculation implementation were added while accuracy remained uninspected; neither changed the frozen primary analysis.

The initial MovieLens split manifest hashes the protocol before its secondary MSE diagnostic paragraph was added. `docs/movie-validation-split-protocol.md` reconstructs that exact earlier text, verified against the recorded hash. The final lock hashes the full protocol used for evaluation. User/item splits and primary comparisons did not change.

Expected limitations include quantized local models, two historical metadata domains, one native writer, no query-time retrieval comparison, and no new longitudinal human study. A successful computational reproduction establishes consistency with this experiment, not universal validity of a personal AI architecture.

## Anonymous review supplement and post-review audit

`output/submission/Personal_AI_Memory_Anonymous_Artifact.zip` is the deliberately limited anonymous supplement. Extract it into a fresh directory and follow its README with Python 3.9 through 3.12 and NumPy 1.26.4. Its verifier recomputes all 5,400 summary rows and all ten operational and common-valid primary comparisons; eight package tests pass. It requires no models, raw ratings, API credentials, or inference. It checks summary arithmetic, not original predictions against targets. Do not substitute the full named public repository for this supplement in anonymous review.

`python src/build_anonymous_artifact.py` regenerates the ZIP and executes it in a fresh extraction. The builder checks identifying text, hashes, tests, assertion-disabled rejection, and numerical stability reproduction. It leaves original analysis reports untouched.

`python src/review_bootstrap_stability.py` reruns each of ten operational contrasts with 200,000 resamples under two additional seeds. Its separate report records post-review Monte Carlo endpoint stability on the same released users. All ordinary and adjusted zero-exclusion conclusions are unchanged. The original 10,000-resample primary results are not replaced.
