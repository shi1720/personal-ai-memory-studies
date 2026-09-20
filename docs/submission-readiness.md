# Submission package

**A Controlled Audit of Personal AI Memory for Rating Prediction**

Prepared 20 September 2026. The paper has not been submitted, accepted, or externally peer reviewed.

## Files to use

- **TMLR manuscript:** `output/pdf/Personal_AI_Memory_TMLR_Submission.pdf`. Anonymous, official TMLR style, 17 pages including references and appendices. This is the recommended submission-format file.
- **Anonymous supplementary artifact:** `output/submission/Personal_AI_Memory_Anonymous_Artifact.zip`. Summary arithmetic, verifier, eight tests, and numerical stability report. It excludes source ratings and original predictions.
- **Named reading copy:** `output/pdf/Shivam_Gupta_Personal_AI_Memory_Paper.pdf`. Fourteen-page ICML preprint with author and contact details, for public reading. Do not upload it as an anonymous manuscript.
- **ICML-format reference:** `output/pdf/Personal_AI_Memory_Anonymous.pdf`. Fourteen pages, official ICML 2026 review mode with line numbers. Main text and impact statement fit within eight pages. This is not a currently eligible ICML 2026 submission.

The standard anonymous review headers are supplied by the official templates. They do not indicate an actual submission. Do not attach the named repository, this note, or internal reviews as anonymous supplements.

## Completed checks

All 45 PDF pages were visually inspected. The builds check page dimensions, embedded fonts, unresolved citations, overflow, analysis hashes, anonymous text, metadata, and link annotations. All 113 measurement tests pass. A separate raw-response implementation checks 2,800 reader inputs, 4,600 user-system records and ten contrasts. The extracted anonymous supplement independently checks 5,400 summary rows and passes eight tests. These are computational checks, not external replication.

Three internal AI review perspectives challenged significance, methods, reporting, and venue fit. Revisions clarify the rating-prediction scope, prior work, baseline context, practical audit procedure, provenance, and assistance disclosure. A post-review same-data bootstrap audit at 200,000 resamples with two seeds preserves all ten primary conclusions. Frozen inference, primary analyses, and original intervals are unchanged.

## Submission decision and author responsibilities

The manuscript and supplement are technically prepared for a TMLR submission decision. TMLR is a plausible venue for a useful, carefully supported empirical diagnostic study. Acceptance remains uncertain. Internal simulated reviews did not support a claim of strong ICML or NeurIPS main-track competitiveness: one native writer and two short structured domains limit breadth and significance. The manuscript discloses these limitations.

Before uploading, the human author must read and take responsibility for the complete paper and code; confirm authorship and affiliation; and supply truthful account, conflict, funding, ethics and submission-form declarations. Those personal declarations cannot be inferred or invented. The manuscript openly discloses extensive language-model assistance. Do not submit simultaneously to archival venues.

Current official guidance: [TMLR author guide](https://jmlr.org/tmlr/author-guide.html), [acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html), and [editorial policies](https://jmlr.org/tmlr/editorial-policies.html). TMLR requires anonymous style, allows reasonable manuscript length, accepts PDF/ZIP supplements up to 100 MB, and applies its stated submission license. Both files are well below the size limit.

[ICML 2026](https://icml.cc/Conferences/2026/CallForPapers) closed full-paper submissions on 28 January 2026. [ICLR 2027](https://www.iclr.cc/Conferences/2027/CallForPapers) required abstract registration by 18 September 2026; a later full-paper deadline does not establish eligibility without an existing registration. Recheck any future cycle’s template and policies before using the conference-format copy.
