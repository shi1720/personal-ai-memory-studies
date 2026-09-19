# MemoryCD observed-history baseline and timestamp audit

The fixed audit completed on all 323 released cross-domain users and 314,116
interactions. Every domain supplies 969 final-three targets. Rating and timestamp
schema checks passed; no missing user, duplicate user, invalid rating or unknown
domain was silently excluded. Protocol b5a8d2c and implementation cd5265d precede
computation. Four targeted boundary/metric tests pass.

## Established controls

| Domain | Always 5 MAE | History mean MAE | History median MAE | Targets with item already in history |
| --- | ---: | ---: | ---: | ---: |
| Beauty and Personal Care | 0.7709 | 0.7530 | 0.6847 | 20 |
| Books | 0.6914 | 0.7385 | 0.6533 | 7 |
| Electronics | 0.6563 | 0.7206 | 0.6099 | 10 |
| Home and Kitchen | 0.6151 | 0.6811 | 0.5562 | 16 |

All five fixed constant predictors are in the machine-readable results; this
summary shows the high-rating control alongside history statistics. Nothing was
fit to target labels. History mean has lower RMSE than history median in all
four domains, whereas median has lower MAE. Choice of metric changes the
comparison. These established statistics are controls, not a proposed method.

The target distributions favor ratings four and five, but the control errors
are not near zero. The audit does not demonstrate that personalization is
unnecessary. Detailed memory claims should show value beyond these baselines,
as well as strong product-aware recommenders and appropriately matched readers.

## Timestamp support

For the release's Home and Kitchen cross-domain task, 664 of 969 targets have
at least one source event with a later timestamp, across 257 of 323 users.
Later events average only 0.8477% of source history per target. There are no
equal-time source/target pairs and no targets lacking strictly earlier source
history. The unrestricted source mean has MAE 0.73009 versus 0.73054 with a
strict cutoff; the median changes from 0.60320 to 0.60165. The directions differ
and changes are small. This does not establish a material benefit from later
information or explain published model performance.

The release's loader permits retrospective cross-domain transfer. A prospective
prediction study needs a separately stated availability cutoff. Timestamps alone
do not prove when a deployed assistant could access an event, and this audit
makes no causal or misconduct claim. Within-domain train/test boundary ties
occur for 5-7 users per domain; stable order is preserved as in the harness.

## Scope and next decision

The released cross-domain cohort is not the same as the paper's domain-specific
cohorts. Direct comparison of these values with its paper tables would be
invalid. No published model score was reproduced, no LLM inference was used and
no model-selection decisions were based on these targets. Any future use must
label this cohort as already inspected development/audit data, not fresh
confirmation. Raw histories and identifiers remain ignored locally.

This supplies useful controls and an explicit temporal interpretation. It does
not, by itself, establish a new contribution. Combined with MemoryCD and MAP's
prior task definitions, it rules out presenting a new rating-memory wrapper as
an original benchmark. The ongoing independent Coat experiment keeps its
original protocol and untouched reserved users.

Data: https://huggingface.co/datasets/WZDavid/MemoryCD
Code: https://github.com/AgentMemoryWorld/MemoryCD
Paper: https://arxiv.org/html/2603.25973v1
Exact data and harness revisions are in references/memorycd-data-manifest.json.
