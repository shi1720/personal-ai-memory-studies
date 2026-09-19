# Preference-reader feasibility preflight

Before a 30-user development comparison, test output completion on the first
three fitting users, whose native memories were already generated. These users
are excluded from development and reserved evaluation. No prompt tuning follows
inspection of accuracy in this preflight. The preflight reports only parsing,
completion and resources; it does not compute predictive error.

One generation predicts all new-item targets for a user, in ascending item order.
The reader receives target attributes and IDs without target ratings. This is
batch prediction of observed ratings, not a conversational benchmark. Contexts
are no personal history, the complete 24-record history, and all native stored
memories. The same target order and reader instruction apply to all contexts.
No retrieved subset is used: this isolates extraction and representation, not
retrieval quality. Native retrieval accuracy is not evaluated by this comparison.

Use the pinned local Qwen3-4B Instruct 2507 4-bit model, greedy generation with
maximum 256 output tokens. Require a JSON array containing one number in [1,5]
per target, in supplied order. Strip surrounding whitespace and one complete
JSON code fence if present. Reject all other extra prose, wrong-length arrays,
booleans, nonnumeric or nonfinite values and out-of-range ratings. No clipping,
imputation, substring recovery or hidden retry. Retain failures.

There are nine scheduled generations, one per user/context. All targets and
input/output traces stay in ignored data/. Report token counts, finish reasons,
parser validity and hashes publicly. Do not inspect score differences to choose
a prompt. Proceed only if every planned response completes and validates; if
not, document the technical failure before revising a separate protocol.
