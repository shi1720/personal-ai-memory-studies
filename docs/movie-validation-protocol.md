# Independent second-domain validation

Fixed before downloading and scoring MovieLens 100K. This supplements the Coat
protocol with an independent rating-association and numerical-reader check.
It does not replicate native Mem0 extraction in the movie domain.

Use the official GroupLens ml-100k.zip release. Verify its publisher MD5 and
record SHA-256. Do not load demographic fields. Require users with at least
40 distinct rated items. Order eligible users by SHA-256 of
`movie-memory-validation-v1:user:{id}`. The first 60 are fitting users, the next
30 development users, and the next 200 evaluation users. Other users are unused.

For each selected user, order their rated items by SHA-256 of
`movie-memory-validation-v1:pair:{user}:{item}`. The first 24 form the history
and the next 16 the targets. This is a random observed-rating split, not a
chronological prediction task or randomized exposure. Keep that distinction
explicit relative to Coat. No unseen user-item rating is treated as negative.

Both readers and statistical methods receive only 19 genre indicators and an
anonymous item identifier. Titles, demographic data, reviews and timestamps are
not inputs. The linear predictor adds an intercept for 20 total coordinates.
This controlled metadata setting cannot establish production movie-recommender
quality or optimal use of textual descriptions. Public benchmark contamination
remains possible even when titles are omitted.

Use the same Qwen and Phi reader configurations as Coat. Change only the domain
noun in the reader prompt and label the records as structured movie ratings.
Use no history, full history and within-user permuted-rating history. Preserve
the same shuffle function, output contract, 256-token limit, one worker,
rotating condition order and constant-3 invalid-output fallback. Each model
must first return at least eight valid arrays out of nine fitting-user calls.
This preflight checks output shape only and does not score predictive accuracy.

Select history-only ridge penalty from {0.1,1,10,100} using the 30 MovieLens
development users, with larger penalty breaking ties. Include history mean
and median, fixed constant 3, and shuffled-history ridge as controls. No
evaluation labels train or select any predictor, prompt or penalty.

Four predeclared primary contrasts: permuted minus full-history user-macro MAE
and full-history minus history-only ridge MAE, for each of the two readers.
Together with Coat's six contrasts, these form a family of ten. Report ordinary
95% and ten-comparison-adjusted bootstrap intervals, with alpha 0.05/10,
10,000 user resamples, seed 20260920. Secondary metrics and complete-case
sensitivity follow the Coat protocol. Do not score either independent study
until all planned calls on both datasets are complete.

Planned second-domain calls: 1,200 evaluation reader calls, plus 18 fitting-user
preflight calls. The dataset and generated raw prompts remain local. Credit
GroupLens and Harper and Konstan (2015), and follow its noncommercial research
and no-redistribution terms. This does not imply GroupLens endorsement.

A secondary squared-error diagnostic splits each user's MSE into squared mean
prediction error and centered residual MSE. This is an exact descriptive
identity, not a new theorem or a calibration method. Target means are used
only for retrospective evaluation, never to construct predictions.
