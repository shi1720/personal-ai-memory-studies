# Pilot 004: reader output-budget sensitivity

Recorded after inspecting early Qwen outputs, before this follow-up is run.
The initial full-history rate answers for extract-00, extract-01 and extract-02
hit the 256-token ceiling while enumerating visits. At least one native-memory
rate answer also truncates. This can confound comparison of memory conditions.
The original protocol, outputs and analysis remain primary and unchanged.

After each original model run completes, rerun ALL 48 rate-question cases for
that model (12 journals x four evidence contexts) with identical rendered
prompts, but a 768-output-token ceiling. Do not select only errors or truncated
cases. Reuse the existing writer outputs without changing or regenerating them.
Repeat a blocked-writer marker if necessary. Both Qwen and Phi receive this
same follow-up. Save full new outputs and reference the original prompt hash.
Assert exact prompt equality before generation. Temperature and seed remain
zero. This is up to 96 additional reader generations, not new journals.

Score these results separately using the original source truth and abstention
labels. Report failures, truncation, paired gains/losses and cases whose answers
change despite an originally completed response. Do not silently replace the
initial results or claim this post hoc choice was preregistered. The event
question results retain their original budget and remain separate. The higher
budget does not cure arithmetic errors or prove memory validity.
