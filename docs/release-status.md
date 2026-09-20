# Completed paper release

The final study and manuscript are complete. The named and anonymous PDFs, all final evaluation reports, computational checks, source code, and figures are included in the public artifact:
https://github.com/shi1720/personal-ai-memory-studies

The study contains 400 held-out user profiles, 6,160 target ratings, 200 native writes, and 2,800 reader calls. All ten primary comparisons were fixed before evaluation. Public commit `2f0d896` is the final study's pre-inference freeze. The completed research paper is a preprint, not submitted or peer reviewed.

See `docs/confirmation-results.md` for the findings and `docs/confirmation-reproduction.md` for reproduction levels. The final release manifest supersedes the initial exploratory snapshot manifest, which remains in Git history and the release-history directory. No source rating archives, weights, raw rating prompts, generated memory text, or credentials are included.

## Historical initial release record

The following is retained as history, not the current status.

# Public research artifact

Released 19 September 2026:
https://github.com/shi1720/personal-ai-memory-studies

This is an explicitly exploratory research artifact, not a conference paper.
Initial public commit: bbf7c2d. The release snapshot originates from local
development commit e97fc2d. Public history starts after data collection; local
freeze records must not be described as external preregistration.

The release checkout is /Users/shivamgupta/Downloads/personal-ai-memory-studies.
The continuing development checkout is personal-ai-research. The release
manifest records 230 exported files. No raw downloaded datasets, model weights,
private observed-user text traces, or environments were exported.

A fresh Python 3.12 analysis environment passed all 97 tests and regenerated
the latest figure. GitHub Actions was added in commit 54f4c1e to test measurement
logic and figure regeneration on Linux. Hosted CI completed successfully:
https://github.com/shi1720/personal-ai-memory-studies/actions/runs/35461366272

The full research objective remains unfinished: a technically substantive new
contribution, independent evaluation and manuscript are still required.
