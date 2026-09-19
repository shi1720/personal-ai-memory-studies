# Post hoc syntax-only sensitivity analysis

This amendment is written after inspecting the first four Phi-4 outputs. Each
contained exactly a JSON array inside a Markdown code fence. The original
protocol correctly counts them as format failures, because it required bare
JSON. Those outputs, traces, strict parser and primary analysis remain unchanged.

After completing the planned run, also report a separately labelled sensitivity
analysis that accepts exactly one fenced JSON array with optional `json` tag,
whitespace, and no additional prose. Remove only the enclosing fence, then use
the same six-unique-known-ID validator. Do not extract arrays from prose, quote
bare identifiers, invent missing IDs, remove duplicates, or repair invalid IDs.
Apply the same rule to every model and condition, without regeneration.

This analysis was motivated by observed outputs and is not preregistered. It
separates harmless serialization differences from semantic selection failures.
It cannot overwrite the primary strict-format results. Report strict validity,
fence-only recovery, and remaining invalidity separately. The same missingness
and development-data limitations apply to the recovered selections.
