# Completed paper release

**A Controlled Audit of Personal AI Memory for Rating Prediction**

Shivam Gupta, independent research. September 2026.

This release contains the polished named preprint, anonymous ICML review-format copy, anonymous TMLR submission-format manuscript, executable anonymous supplement, final evaluation reports, frozen protocols, source code, vector figures, and reproducibility checks. The named and ICML copies have 15 pages with main text and impact within eight pages. The TMLR copy has 17 pages. The work has not been submitted or externally peer reviewed. See `docs/submission-readiness.md` for file selection, venue fit, and author responsibilities.

## Evidence

- 400 held-out user profiles across Coat and MovieLens, with 6,160 target ratings.
- 200 native Mem0 writes and 2,800 Qwen/Phi reader calls. All scheduled calls are retained; 150 invalid reader outputs receive the predeclared fallback.
- Ten predeclared paired comparisons, each based on 200 users, with 10,000 bootstrap resamples and family adjustment.
- Separate calculation check of 4,600 user-system records, all 2,800 reader inputs, and every primary contrast. Maximum continuous-metric discrepancy below 2.1e-14.
- Additional verification of all 5,400 released error summaries without source data or models.
- 113 local measurement tests passed. GitHub Actions runs the suite, summary verifier, and figure/table generators in a fresh Linux environment.
- All three final PDFs rendered and visually inspected across all 47 pages; no unresolved references, overfull boxes, clipped tables, or identifying metadata in the anonymous manuscript.

Three internal AI review perspectives informed revisions to scope, prior work, baseline interpretation, practical guidance, and artifact provenance. A new anonymous ZIP passes eight tests and verifies 5,400 summary rows after extraction. A post-review same-data bootstrap audit using 200,000 resamples under each of two seeds preserves all ten primary conclusions. This is numerical stability, not additional independent data. The manuscript is technically prepared in TMLR format; selective conference competitiveness and acceptance are not claimed.

The frozen primary analyses are unchanged. Public commit `2f0d896` preceded reserved-user inference. The final release includes post-freeze computational checks that were developed before accuracy inspection. `docs/confirmation-execution-record.md` documents the boundaries and the final reporting-dependency fix.

## What the findings establish

Native extraction increases Coat prediction error relative to full history for both readers, while still improving on no history. Correct historical assignments help on Coat, but the smaller MovieLens association effects remain inconclusive after family adjustment. History-only ridge has lower error in three of four full-history LLM comparisons. These are measured findings for the tested systems and tasks, not a general ranking of memory libraries or a claim of uniquely personal preference identification.

## Reproduction and provenance

See the README and `docs/confirmation-reproduction.md` for separate instructions for rebuilding published calculations, recomputing original raw-response scores, and running new model inference. Public measurements can be checked without downloading models or source ratings. Exact raw-response recomputation requires locally retained traces, which are not redistributed. Fresh model inference requires the pinned third-party models and licensed archives.

`release-manifest.json` hashes the released files and records the local development source commit. That local commit is source provenance, not public preregistration. The public pre-inference freeze has its own explicit commit above. The manifest excludes itself and `.git`.

The initial exploratory release notes and manifest are preserved under `release-history/initial-exploratory/`. Their recorded hashes describe that earlier snapshot, not the present files. Earlier pilot studies remain historical material and are not pooled with the final evaluation.

## Preserved unfinished extension

The language-rich research branch has been merged into `main` to preserve its
history, protocols, engineering preflights, code, and synthetic tests. The author
stopped the experiment, and its local model files were removed. It has no
completed confirmation results and is not part of the paper's evidence. No
further inference is running or scheduled. Historical prospective protocols
describe proposed work, not authorization to restart it. See
`docs/language-extension-status.md` for this boundary. The merged release
manifest covers these preserved files as well as the completed paper; inclusion
in that manifest does not change their scientific status.

No raw rating archives, model weights, full observed-user prompts, generated memory texts, local databases, API credentials, or local environment directories are included. Existing third-party notices and dataset/model rights remain separate from the repository's code license.
