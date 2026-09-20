# Fixed development precision-planning calculation

Prescribed on 20 September 2026 before development accuracy inspection. This is
a pre-development planning component, not the final inference protocol or a
claim of public registration. It chooses no writer configuration and performs
no inference, data acquisition, label extraction, or file access.

`src/language_precision_planning.py` exposes `plan_precision(differences)`.
Supply all eight arrays using the exported `CONTRAST_KEYS`. Names have the form
`native_minus_full__writer_qwen__reader_phi` or
`native_minus_matched_summary__writer_phi__reader_qwen`, covering both writers
and readers for each comparison. Every array must contain exactly 60 finite
paired user-MAE differences in [-4, 4]. Each difference is the native arm's
user-level MAE minus its stated comparator's MAE on the same user's three
targets. The caller must establish this pairing; numeric arrays alone cannot
prove correct user identity or prevent fabricated inputs.

The function rejects incomplete or unknown contrasts, wrong sample sizes,
booleans, nonnumeric or nonfinite values, out-of-range differences, and arrays
with more than one dimension. It validates the entire family before calculating
anything. Invalid input raises `ValueError`; it never produces a partial GO.
No configurable sample-size, family-size, error-rate, or target override is
exposed. Inputs are not modified.

## Prescribed calculation

For each contrast, draw 20,000 bootstrap samples of 60 paired user differences
with replacement. Compute sample standard deviation with ddof=1 for each
sample. Take the 95th percentile of these deviations using linear quantile
interpolation. Call this empirical upper dispersion estimate `s_upper`.

The projected adjusted half-width is

`NormalDist().inv_cdf(1 - 0.05 / (2 * 8)) * s_upper / sqrt(200)`.

This uses alpha=0.05, family size eight, and the fixed 200-user confirmation
sample. A contrast passes if and only if its projected half-width is at most
0.10 MAE. The joint decision is GO only when all eight complete contrasts pass.
Means, signs, statistical significance, or favorable effect directions are not
conditions of the gate. A large constant adverse effect can pass this precision
screen: that says nothing about whether a method is desirable.

One NumPy PCG64 stream with seed 20260923 is consumed in lexicographically sorted
canonical contrast order. Mapping insertion order has no effect. User order
within each input array is retained, so the caller must freeze that order.
The implementation uses batches of 1,000 resamples without changing the random
draw sequence. The report includes every sample SD, upper bootstrap SD,
projected half-width, individual decision, joint decision, and fixed settings.

## Limits and interpretation

This is approximate planning, not guaranteed confidence coverage or power. The
bootstrap 95th percentile of development SDs is an empirical dispersion guard,
not a proven one-sided 95% confidence bound. Sixty development users can miss
rare events or underestimate confirmation variability. Constant development
differences yield zero estimated width without proving zero population
variance. Development and confirmation may differ, and quantized-model errors
or output-contract failures can increase variability.

The normal-approximation half-width does not guarantee the same width for the
final paired percentile-bootstrap intervals. The fixed 0.10 resolution is an
analyst-selected planning criterion, not a universal threshold for practical
importance. Eight contrasts remain eight even when correlated. Their three
ratings per user are not treated as three independent user observations.

No inference settings, hypothesis family, target width, or sample size should
be changed merely to turn an observed NO_GO into GO. A changed scientific aim
requires a separate prospective decision before reserved inference. Engineering
integrity and execution feasibility require their own checks; passing this
function neither authorizes inference nor certifies the experimental pipeline.

Run the isolated tests with:

`python3 -m unittest discover -s tests -p test_language_precision_planning.py -v`

Tests use invented numeric arrays only. They cover constant and boundary cases,
a separate raw-moment variance and interpolation calculation, direction
invariance, canonical ordering, joint failure, and malformed inputs. No source
dataset, prepared input, development outcome, or confirmation result is read.
