# Response to internal reviews

20 September 2026. These are simulated AI editorial reviews, not reviews from the named venues or external peer review. Original review records are preserved alongside this response.

| Concern | Completed revision |
|---|---|
| General personal-memory framing overstates the task | Title and abstract now specify rating prediction. Numerical fidelity is separated from conversational utility. |
| Novelty relative to profile-versus-history studies | Related work explicitly recognizes the earlier Zhou et al. comparison and input-length tradeoff. Contribution is a controlled audit, not invention of memory controls. |
| Weak MovieLens associations might be a reader-specific failure | Results include the ridge permutation penalty in both domains, explaining weaker available metadata association signal. |
| Missing simple-baseline context | Main table includes scale-midpoint and permuted-ridge values, identifying auxiliary versus frozen secondary comparisons. |
| Unclear practical benefit | Discussion supplies an audit procedure and explains when a rating-preserving intervention is meaningful. |
| Extreme bootstrap endpoints could be noisy | Separate same-data audit uses 200,000 resamples under each of two seeds; all ten conclusions persist. Original primary intervals remain unchanged. |
| Native extraction prompt unclear | Appendix names the active ADDITIVE_EXTRACTION_PROMPT and its pinned source. |
| Anonymous artifact not self-contained | Executable ZIP checks released summary arithmetic, with explicit limits on missing raw traces and dependency provenance. Fresh extraction passes eight tests. |
| Anonymous ICML format lacked review line numbers | Official ICML review mode now used. Separate official TMLR submission-format copy added. |
| Assistance and independent validation could be misread | Extensive language-model assistance is explicit. Internal reviews, same-data checks, and external peer review are distinguished. |

All four minor items in `revision-check.md` were resolved before the final build: anonymous ZIP title updated; full manifests described as retained in the full record; language-model assistance named; and endpoint deviations expressed as conservative upper bounds. Every page of the resulting three PDFs was visually inspected.

## Remaining scientific scope

No revision can manufacture broader evidence. Native extraction was tested on Coat with one writer; the two readers are quantized local models; MovieLens uses structured metadata rather than rich conversational history. The results do not identify uniquely personal taste or rank memory systems generally. Raw predictions are not redistributed, so the anonymous supplement supports arithmetic verification, not independent model-output replication. These limitations remain explicit.

The internal ICML and NeurIPS/ICLR perspectives found no fatal calculation error but judged significance and breadth insufficient for a confident main-track recommendation. TMLR is a more plausible submission target for the scoped empirical contribution. No acceptance probability or external approval is claimed.
