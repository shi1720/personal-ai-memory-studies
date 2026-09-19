# Closest-work comparison for recalibration candidate

Working assessment, 2026-09-19. This is a candidate-selection document, not a
claim that the literature search is exhaustive. Exact sources and reading depth
are recorded in `references/screening.json`.

| Work | Established idea | Difference from the pilot | Implication |
| --- | --- | --- | --- |
| Conformal Risk Control, Angelopoulos et al., ICLR 2024 | Expected bounded monotone risk control using a finite-sample correction | Pilot asks how much computation is needed to recover its fixed reference policy after inputs change | The risk guarantee belongs to existing CRC |
| Stochastic Score Classification, Gkenosis et al., ESA 2018 | Costly queries reveal hidden values until a decision is certified | Here a query reveals one monotone loss row, with adjacent threshold witnesses | Generic certificate arguments and adaptive querying are established |
| Active Testing, Kossen et al., ICML 2021 | Adaptive acquisition for finite-pool model evaluation with selection correction | Pilot pays to recompute model predictions, rather than acquire ground-truth labels | Changing the cost source alone is not a contribution |
| Semi-Supervised Risk Control via Prediction-Powered Inference, Einbinder et al. | Proxy losses and verified labels improve risk-control calibration | Old losses could act as a proxy for new losses | A generic control-variate extension is insufficiently distinct |
| Prediction-Powered Active Testing | Proxy-assisted adaptive evaluation and corrected uncertainty | A recalibration application could reuse its statistical machinery | Requires faithful comparison before any efficiency claim |
| BARGAIN | Adaptive accuracy certification for cheap/strong LLM cascades | Different policy target and source of evaluation expense | Finite-sample certification of cheaper LLM pipelines is already explored |
| Prediction-Powered Risk Monitoring, Zhang et al., ICML 2026 per arXiv v2 | Anytime-valid monitoring with synthetic and verified labels | Monitoring a running risk differs from recovering a finite-pool threshold | Broad deployment-monitoring novelty is unavailable |

## Current contribution boundary

Implemented: an elementary interval-revelation procedure, exact certificate-size
diagnostic, exhaustive correctness tests, and a frozen memory-availability pilot.
Derived: a strict-risk computation barrier, a singleton-boundary obstruction, and
monotonicity of oracle certificate cost under nested grid refinement.

These observations are mathematically useful for deciding whether the proposed
engineering optimization can work. Their present form is not sufficient evidence
of a new ICML-level method. The threshold-counting proof is closely related to
standard decision-certificate arguments. A literature search failing to find the
same application name would not establish novelty.

## What would have to change for a full study

1. A meaningful application-specific information source must provide tighter
   valid bounds than unrestricted unknown losses. Exact prompt reuse is already
   the baseline, not such a contribution by itself.
2. If probabilistic or approximate recovery is used, state the new guarantee and
   compare with established active-testing and prediction-powered methods. Do
   not attribute gains from a weaker target to a better exact algorithm.
3. Show practical utility at matched risk and coverage. Cheap certification of
   universal abstention is not evidence of a useful personal assistant.
4. Use stronger readers, multiple model families, repeated memory changes and
   an independent confirmatory sample before generalizing pilot results.

No new candidate is selected merely to rescue this one. The full-trace results
will determine whether to stop this direction or investigate a specific gap.
