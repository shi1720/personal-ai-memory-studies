# Pilot 002 analysis addendum

Recorded while inference is running, before aggregate pilot outcomes are
computed. The original inference protocol and its hash remain unchanged.

Use all four declared alpha values. Replay one fixed index ordering and 100
uniform random permutations of calibration indices, seeds 0 through 99.
Summaries across these orders describe acquisition-order variability on one
fixed calibration table, not independent experimental replicates or population
confidence intervals. Budgets are floor(fraction * changed-calibration-count).

Compare the exact-reference recovery calls to an oracle minimum certificate
size. This diagnostic was derived during the pilot and is post-protocol; it
accesses the full new loss table. It must never be reported as an online method.
See the certificate-complexity calculation in the working technical note.

All computation savings from partial replay are counterfactual counts. Measured
reader-call times can be summed for queried indices, but that sum excludes
prompt preparation, hashing, scheduling and process startup. It is not end-to-end
latency. Preserve every seed, alpha and budget result in the analysis artifact.

Do not stop or change the run based on partial accuracy. A technical failure
must be investigated and documented separately from a model error.
