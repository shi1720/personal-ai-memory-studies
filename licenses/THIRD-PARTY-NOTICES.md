# Third-party notices

`results/pilot-004-extraction-prompt.txt` is derived from
`mem0/configs/prompts.py` in Mem0 (mem0ai/mem0), commit
`a39a802bbc93e85b820078cd3c4dbaf53af25dbe`. It contains the
USER_MEMORY_EXTRACTION_PROMPT with the runtime date fixed to 2026-09-19.
The upstream source is licensed under Apache License 2.0, reproduced in
`mem0-Apache-2.0.txt`. Source and license hashes are recorded in
`references/mem0-prompt-screen.json`.

The rendered prompt retains upstream whitespace, including trailing spaces on
its first two lines, to preserve the exact hashed experimental input.

The count-preservation addendum and evaluation code are separate modifications
in this research project. This isolated prompt test does not imply endorsement
by, or an end-to-end reproduction of, Mem0.

Other Mem0 prompt excerpts embedded in experimental traces retain the same
upstream Apache 2.0 license. The original software license does not supersede
that license or imply authorship of upstream prompt text.

## Dataset attribution and scope

- Coat: Tobias Schnabel and collaborators, Recommendations as Treatments:
  Debiasing Learning and Evaluation, ICML 2016. Author release at
  https://www.cs.cornell.edu/~schnabts/mnar/. Source data are CC BY-NC 4.0.
- MemoryCD: https://arxiv.org/abs/2603.25973 and
  https://huggingface.co/datasets/WZDavid/MemoryCD. The paper's data-use
  statement limits use to noncommercial academic research. The upstream
  repository's code license does not override data terms.
- LongMemEval: https://arxiv.org/abs/2410.10813 and
  https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned.
  The pinned dataset manifest records its upstream MIT declaration.
- PersonaMem-v2: https://arxiv.org/abs/2512.06688 and
  https://huggingface.co/datasets/bowen-upenn/PersonaMem-v2.
  The pinned dataset manifest records CC BY 4.0.

Downloaded source datasets are excluded from this repository. Numerical
measurements, row identifiers and derived evaluation outputs do not relicense
the underlying sources. Acquire datasets from their original providers and
follow their terms. Native observed-user text traces and stores remain excluded.
Model weights are also excluded; pinned model manifests identify upstream
revisions and licenses. No employer, library maintainer or dataset author is
claimed as a sponsor, coauthor or endorser.
