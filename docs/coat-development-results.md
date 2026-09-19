# Observed-rating development results

The frozen Coat screen finds useful personalization signal. It does not yet
establish a new memory method or a conference contribution. All model selection
uses 30 development users. The 200 reserved users remain unscored.

The 60 fitting users supply population parameters. Development has 438 new-item
targets across all 30 users and 42 known-item targets across 25 users. The latter
are reported separately because exact history lookup recovers them by construction.

| Established baseline | Selected penalty | New-item macro MAE | New-item macro RMSE |
| --- | ---: | ---: | ---: |
| Population mean | Fixed | 1.0375 | 1.1988 |
| Population item features | Fixed at 10 | 1.0398 | 1.2053 |
| User mean adaptation | 10 | 1.0085 | 1.1641 |
| Uniform attribute adaptation | 1 | 0.8948 | 1.1325 |
| Estimated exposure weighting | 1 | 0.8990 | 1.1339 |
| Positive-outcome weighting | 1 | 1.0082 | 1.2614 |
| Exposure and positive-outcome weighting | 0.1 | 1.0101 | 1.3327 |

Selection minimizes development MAE, not RMSE. For example, uniform adaptation
at penalty 10 has MAE 0.9433 and RMSE 1.0971. The criteria favor different
settings. All settings and per-user errors remain in the results JSON.

Uniform adaptation at penalty 1 improves MAE for 19 users and worsens it for 11
relative to population item features. The aggregate reduction is about 0.145
rating points. This is descriptive development evidence, not a confirmatory
confidence interval. Positive-rating emphasis performs worse in aggregate in
this setting. It is a specified heuristic, not a reproduction or refutation of
a learned gate in CALMRec or another published memory system.

The exact-cache diagnostic has zero known-item error, as intended, and identical
new-item predictions to population item features. Pooling the two target groups
would conflate recall with preference prediction. The population-feature model's
known-item MAE is 0.9492.

## Interpretation and next experiment

Observed histories contain information beyond the population baseline. This is
enough to justify testing an actual memory system. A fair next stage needs the
native extraction, persistence and retrieval implementation, a shared downstream
reader, full-history and retrieval controls, and explicit resource accounting.
These data are item ratings serialized as records, not natural conversations or
longitudinal evidence of changing preferences. No causal preference claim follows.

The current experiment is deliberately not called a new algorithm. It provides
an established baseline that a new memory contribution must justify exceeding
or complementing. The reserved set must remain closed while the method and
comparisons are developed.

## Reproduction and checks

Protocol, split and baseline code were committed at 509b23b before fitting.
Run `python3 src/coat_baselines.py` and `python3 src/plot_coat_development.py`.
The runner verifies protocol, split and code hashes. Five targeted tests check
split disjointness, reserved-user isolation, exclusion of target labels from
personalization, constant-gate invariance and the exact-cache control. The
figure was rendered and visually inspected. See the author-hosted dataset's
CC BY-NC 4.0 terms; raw data are not redistributed here.
