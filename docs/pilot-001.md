# Pilot 001: measurement and retrieval sanity check

Recorded before running retrieval. This is exploratory infrastructure validation,
not a test of a new method and not a confirmatory paper experiment.

Data: pinned LongMemEval cleaned S revision in the acquisition manifest.
All 500 records are audited. Retrieval is scored on the 470 non-abstention cases,
following the upstream distinction between evidence retrieval and abstention.

Represent each session using only role/content. Use both user and assistant
messages. Do not index question IDs, original session IDs, answers, evidence
labels or the current question itself. Dates remain available to a separate
chronological baseline, but are not included in lexical documents.

Baselines: session BM25 with k1=1.5, b=0.75 and positive Robertson IDF; newest
session first by parsed dates. Regex Unicode word tokenization and lowercasing,
without stopword filtering. Ties retain input position. No hyperparameter tuning.
This custom baseline is not claimed as a reproduction of published BM25 scores.

Report mean fraction of distinct gold sessions found, fraction of questions
with any gold session found, and fraction with all gold sessions found, at
k=1,3,5,10. Original session IDs are used only after ranking to match gold labels.
Repeated candidate IDs remain at distinct positions; scoring counts an ID once.

Questions are not claimed to be independent real users. The audit found exact
evidence overlap between some questions. No confidence intervals or hypothesis
tests are used for this initial deterministic sanity check.

Log input hashes, code hash, Python version, runtime, all rankings and individual
scores. This does not measure answer quality, end-to-end memory, or a trained
model. Later experiments require tokenizer budgets and faithful modern baselines.
