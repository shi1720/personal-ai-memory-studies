# Closest work for the retention audit

This is a non-exhaustive comparison. It records what was inspected, not a claim
that every related paper has been read or reproduced.

| Work | Existing contribution relevant here | Consequence for this project |
| :--- | :--- | :--- |
| Acerbi and Stubbersfield, PNAS 2023 | Content-dependent survival through repeated LLM summaries, including valence effects | Selective retention and sentiment bias are already known. Changing the application label to personal memory is insufficient novelty. |
| Fisher, Neville and Park, RUMS 2026 | Query-conditioned selection of user attributes using a response-distribution objective | General utility-aware memory selection is already covered. Our current writer acts before future queries and handles repeated events, but that distinction alone is not a contribution. |
| Lu and Li, DAM-LLM 2025 | Affective confidence profiles, weighted evidence updates and entropy-based compression | Storing distributions rather than isolated facts is already covered. Their confidence target differs from our empirical event frequency. |
| Koshorek et al., S-RAG 2025 | Structured ingestion and formal-query execution for aggregative questions | Aggregate completeness and replacing free-text counting with structured queries are already studied. A personal-memory application alone does not establish novelty. |
| Bertsch et al., Oolong 2025 | Aggregate questions over classified texts and conversational histories, including user and date groupings | Counting and distribution benchmarks, iterative labeling plus aggregation, and output-budget limitations are established. |
| Wang et al., FinPerMA 2026 | Event-grounded preference trajectories and separate recall, preference and adaptation tasks | Factual retention versus personalization quality is already distinguished in a larger benchmark. Their targets differ from empirical visit rates. |
| TANGLE 2026 | Irreducible personal-memory conflicts with oracle and native-pipeline tracks | Evidence loss versus reader behavior and conflict-aware clarification are established evaluation concerns. |
| Mem0, pinned source | An exported user-fact prompt covers likes and dislikes; the active inferred-add path uses a different additive prompt | Our six-ID prompt and Pilot 004 do not reproduce the active product. See `pilot-004-source-correction.md`. |
| Zhu et al., AgingBench 2026 | Longitudinal memory evaluation with write, retrieval and utilization interventions | Broad component attribution is already studied. Its authors frame the outputs as repair diagnostics rather than unique causal decompositions. |
| Guan et al., CICL 2026 | Decision-sensitive context utility and typed memory cards | A generic claim of selecting memories for their effect on decisions is insufficient. |

Primary sources:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC10622889/
- https://arxiv.org/html/2604.14473v1
- https://arxiv.org/html/2510.27418v1
- https://arxiv.org/html/2511.08505v1
- https://arxiv.org/html/2511.02817v1
- https://arxiv.org/html/2608.04095v1
- https://arxiv.org/html/2608.13921v1
- https://arxiv.org/html/2605.26302v1
- https://arxiv.org/html/2606.08151v1
- https://github.com/mem0ai/mem0/blob/a39a802bbc93e85b820078cd3c4dbaf53af25dbe/mem0/configs/prompts.py

Evidence levels and source hashes are in `references/screening.json` and
`references/mem0-prompt-screen.json`. No results from these systems were
reproduced in Pilot 003. Classical representative sampling and sufficient
statistics remain mandatory baselines, not proposed inventions.

The surviving question is whether practical memory construction loses aggregate
information that downstream personalized decisions require, under conditions
where a full-history reader succeeds. A publishable result needs realistic
interfaces, workload and budget controls, and a sharper technical contribution
or sufficiently strong new empirical finding. Current toy data do not meet that
standard.
