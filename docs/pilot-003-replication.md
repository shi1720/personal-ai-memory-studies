# Pilot 003: additional model checks

Recorded before either additional model generates journal selections. This is
an exploratory replication on the same twelve development journals, not an
independent confirmatory dataset. The two model families are Mistral 7B Instruct
v0.3 and Microsoft Phi-4, using pinned community MLX four-bit conversions.
Model file identities are recorded separately. No remote Python is executed.

Run nine unique conditions for each journal, 108 calls per model: important
plain, important detailed, representative plain, representative detailed,
important antonym, archive negation, archive antonym, proportional negation,
and proportional antonym. Prompts and measurements come unchanged from the
previous pilot and diagnostic controls. Do not duplicate the overlapping
important plain / important negation condition. Temperature zero, seed zero,
maximum 160 output tokens and 4,096 input tokens remain fixed. Save malformed
outputs as failures without repair or retry. Report every planned condition.

Mistral's native default template does not support a system message. Join the
system instruction and journal with two newlines in a single user message.
Phi uses the original system and user roles if supported by its native template.
Record the adapter and full rendered prompt. A model comparison therefore
also changes native templates and, for Mistral, role placement. It is not an
isolated causal estimate of model size or family. No cross-family robustness
claim is justified unless the actual results support it.

Positive fraction, missing activities, journal-average available-activity MAE,
signed bias, ordering and detailed-event recall retain their earlier definitions.
Always report format failures and missing activities alongside conditional
metrics. Do not pool model outputs or random-sampling seeds as independent users.
These models remain local quantized instruction models, not frontier systems.
