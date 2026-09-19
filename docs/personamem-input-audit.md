# PersonaMem-v2 input-boundary inspection

Status: static code and data inspection, not a finding about the published
accuracy values or a verified benchmark defect. Source identities are recorded
in `references/personamem-upstream-code.json` and the pilot data manifest.

The downloaded conversation files begin with a system message containing a
structured synthetic persona. Our pilot excludes it deliberately. This keeps
the reader's information boundary to the conversation evidence, as fixed in the
pilot protocol. It is not an exact reproduction of every upstream input path.

At upstream code revision `d29d91d016add354e459dfeb0d24af08bc402e2a`:

- The standard inference loader retains the conversation list, and the evaluator
  appends the current question and a multiple-choice instruction. Its OpenAI
  path passes the message list onward. This code path does not remove the first
  persona system message in the inspected functions.
- The VERL preprocessing loader likewise returns the conversation list and
  includes its messages in the constructed prompt.
- The MemAgent preprocessing path explicitly drops the initial system message
  before memory processing.

These are different information boundaries. They do not prove leakage of the
correct option, and the structured persona is not identical to the current
preference label. A published run may use another revision, preprocessed input,
or provider-specific conversion. Those paths and the release history must be
checked before attributing any effect to reported results.

The standard multiple-choice instruction permits reasoning before a final
letter. Our pilot instead uses one-token constrained choice probabilities. Its
retrieved excerpts also occupy a much smaller context than the full history.
Both differences limit comparisons to reported benchmark accuracy.

The dataset intentionally contains forgetting and sensitive-information cases.
Its correct option can be a generic response when using a personal detail would
violate an earlier instruction. Thus greater specificity is not always correct.
This is part of the benchmark's intended task, not evidence of a bad label.

Before any future benchmark-comparison study, document which profile fields are
available to every arm, preserve the same output protocol and token accounting,
and evaluate profile-only and history-only ablations. No such ablation result
has been measured yet.
