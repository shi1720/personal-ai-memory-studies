# Pilot 004: post hoc exact-option answer sensitivity

Declared after inspecting all original Phi reader outputs. Six invalid readers
ended normally and returned an answer such as `D. swimming`, rather than the
required bare letter. Each suffix exactly matches the displayed answer option.
This is a protocol-format mismatch, not an unreadable response.

Keep strict scores unchanged. Separately accept an answer field only if it is
either the original bare allowed letter or exactly `letter + ". " + option`.
Require the same JSON keys and string types as before. Do not infer a letter
from free prose, change case, correct an option's wording, or repair JSON.
Apply the rule to all planned readers in both models and both output budgets
once each trace and its original analysis are complete. Preserve blocked writer
cases. This does not re-interpret writer schemas or generate new reader calls.

The choice of rule is post hoc. It measures sensitivity to one observed format,
not a new primary metric or independent confirmation. Report source-truth
accuracy separately from evidence faithfulness; parsing a correct option says
nothing about whether the accompanying counts are correct.
