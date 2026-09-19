# Research contract

Recorded 2026-09-19 before our first experiment.

## Deliverable

A technically correct paper, actual code, figures generated from recorded runs,
reproducibility instructions, and a GitHub artifact. Shivam Gupta is the intended
author. Prepare a named author version and an anonymized submission version when
a venue is selected. Do not invent coauthors, institutional affiliations or a
human-subjects study.

The preferred domain is personal AI memory, changing context and user modelling.
The topic may change if the closest literature or pilot results invalidate its
promise. Technical depth must come from a defensible contribution, not notation
or unnecessary architectural complexity.

## Selection gates

1. State a precise question and falsifiable claim. Explain the practical cost of
   the failure and the assumptions under which it can happen.
2. Read the closest papers beyond their abstracts. Trace references, subsequent
   work, released code, and older foundations such as belief revision, database
   provenance, information theory and sequential decision-making.
3. Specify exactly what remains unresolved. A new combination or name is not
   sufficient evidence of novelty.
4. Test the failure with controls that can disprove it. Reject a method when an
   inexpensive established baseline explains its gains.
5. Continue to a full study only after a credible signal. Failed pilots remain
   in the research record. They are not silently converted to positive claims.

## Experimental standard

- Separate development and confirmatory datasets before tuning. Hash manifests.
- Compare equivalent token, retrieval, memory and compute budgets. Account for
  preprocessing, retries and hidden calls as well as answer generation.
- Include no-memory, raw-history, sparse and dense retrieval, and the strongest
  applicable published method. Oracle context is a diagnostic, not a deployable
  competitor. A weak prompt is not a faithful reproduction of a baseline.
- Include simple structure-aware baselines when relevant: last-write-wins,
  explicit revision chains, deduplication and provenance propagation.
- Use more than one model family and meaningful capacity variation. Small local
  pilots are feasibility tests, not evidence about frontier systems.
- Evaluate on suitable existing datasets and carefully designed interventions.
  Synthetic interventions need semantic validity checks and must be labelled.
- Report paired effects, uncertainty, individual failures and resource costs.
  Identify the independent sampling unit before bootstrap or significance tests.
  Do not count paraphrases of one user as independent users.
- Record all configurations, prompts, outputs, errors, versions, random seeds and
  dataset/model revisions. No tuning against a test leaderboard.
- Distinguish retrieval correctness, answer correctness, calibration and action
  utility. Explain adjudication and scoring failures.
- Include ablations, sensitivity to assumptions, distribution shifts and limits.

## Commercial relevance

Potential applications include personal assistants, enterprise account memory,
support systems and agents that revise plans after a customer changes a need.
Application claims will depend on measured reliability, cost and deployment
constraints. There is no permission to ingest private customer conversations.

## Current resources

Local ARM64 Mac, 24 GiB RAM, 12 CPUs; approximately 110 GiB disk available at
initial inspection. No provider API key was configured in the current shell.
Use an isolated environment. Do not modify the unrelated AssemblyAI project.

## Publication readiness

Acceptance is not predictable from a topic alone. A paper proceeds only if it
states a meaningful contribution, survives comparison with close prior work,
has reproducible evidence, and follows the target venue's current policies.
Author responsibility and any applicable disclosure requirements remain binding.
