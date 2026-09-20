"""Prospectively fixed uncertainty calculation for the confirmation family.

Pure numerical analysis only: no file access, inference, or imports of the
development analysis. Callers must supply correctly paired users in the same
fixed order for every contrast. This function cannot verify user identities.
"""
from collections.abc import Mapping
from math import fsum, isfinite
from numbers import Real

import numpy as np


CONFIRMATION_USERS = 200
FAMILY_SIZE = 8
ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 200000
BOOTSTRAP_SEED = 20260924
BATCH_SIZE = 1000
DIRECTION_TOLERANCE = 1e-12
ORDINARY_QUANTILES = (0.025, 0.975)
BONFERRONI_QUANTILES = (0.003125, 0.996875)
CONTRAST_KEYS = tuple(sorted(
    f"{comparison}__writer_{writer}__reader_{reader}"
    for comparison in ("native_minus_full", "native_minus_matched_summary")
    for writer in ("qwen", "phi")
    for reader in ("qwen", "phi")
))


def _validated_matrix(differences):
    if not isinstance(differences, Mapping):
        raise ValueError("Expected a mapping containing the complete eight-contrast family")
    if set(differences) != set(CONTRAST_KEYS):
        raise ValueError("Contrast keys must exactly match the eight canonical names")
    matrix = np.empty((CONFIRMATION_USERS, FAMILY_SIZE), dtype=np.float64)
    for column, key in enumerate(CONTRAST_KEYS):
        values = differences[key]
        if not isinstance(values, (list, tuple, np.ndarray)):
            raise ValueError(f"{key}: expected a one-dimensional list, tuple, or array")
        if isinstance(values, np.ndarray) and values.ndim != 1:
            raise ValueError(f"{key}: expected one dimension")
        if len(values) != CONFIRMATION_USERS:
            raise ValueError(f"{key}: requires exactly 200 paired user differences")
        for row, value in enumerate(values):
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
                raise ValueError(f"{key}: expected real numbers, excluding booleans")
            try:
                number = float(value)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"{key}: expected representable finite numbers") from exc
            if not isfinite(number) or not -4.0 <= number <= 4.0:
                raise ValueError(f"{key}: differences must be finite and within [-4, 4]")
            matrix[row, column] = number
    return matrix


def _direction(lower, upper):
    """Strict endpoint rule: numerical zero and inconclusive are not equivalence."""
    direction = "inconclusive"
    if upper < -DIRECTION_TOLERANCE:
        direction = "native_lower_error"
    elif lower > DIRECTION_TOLERANCE:
        direction = "native_higher_error"
    return direction


def bootstrap_confirmation(differences):
    """Return fixed joint paired-user percentile bootstrap intervals.

    Exactly 200,000 draws resample 200 users with replacement. A single draw's
    user indices are shared across all eight contrasts, preserving their joint
    dependence. Mapping insertion order is ignored; user order is preserved.
    All inputs are validated before drawing. No runtime settings are accepted.
    """
    values = _validated_matrix(differences)
    offsets = values[0].copy()
    centered = values - offsets
    means = np.empty((BOOTSTRAP_RESAMPLES, FAMILY_SIZE), dtype=np.float64)
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    for start in range(0, BOOTSTRAP_RESAMPLES, BATCH_SIZE):
        stop = min(start + BATCH_SIZE, BOOTSTRAP_RESAMPLES)
        indices = rng.integers(0, CONFIRMATION_USERS,
                               size=(stop - start, CONFIRMATION_USERS))
        # Reuse this exact index array for every column; never draw per contrast.
        for column in range(FAMILY_SIZE):
            # Centering preserves a constant input exactly, including at the
            # prespecified direction tolerance, without rounding endpoints.
            means[start:stop, column] = (
                centered[:, column][indices].mean(axis=1) + offsets[column]
            )
    quantiles = np.quantile(
        means, (*ORDINARY_QUANTILES, *BONFERRONI_QUANTILES),
        axis=0, method="linear",
    )
    contrasts = {}
    for column, key in enumerate(CONTRAST_KEYS):
        contrasts[key] = {
            "mean_difference": fsum(values[:, column]) / CONFIRMATION_USERS,
            "ordinary_95": {"lower": float(quantiles[0, column]),
                            "upper": float(quantiles[1, column])},
            "bonferroni_99_375": {"lower": float(quantiles[2, column]),
                                  "upper": float(quantiles[3, column])},
            "direction": _direction(quantiles[2, column], quantiles[3, column]),
        }
    return {
        "scope": (
            "Approximate paired-user percentile bootstrap uncertainty for the fixed "
            "eight-contrast confirmation family. Bonferroni-adjusted percentile "
            "intervals do not guarantee finite-sample simultaneous coverage. "
            "Inconclusive does not establish equivalence or absence of an effect. "
            "Population interpretation depends on the sampling protocol; these "
            "intervals do not correct selection bias."
        ),
        "complete": True,
        "users": CONFIRMATION_USERS,
        "settings": {
            "family_size": FAMILY_SIZE,
            "alpha": ALPHA,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "generator": "NumPy PCG64",
            "batch_size": BATCH_SIZE,
            "quantile_method": "linear",
            "ordinary_quantiles": list(ORDINARY_QUANTILES),
            "bonferroni_quantiles": list(BONFERRONI_QUANTILES),
            "direction_tolerance": DIRECTION_TOLERANCE,
            "random_stream": "one joint user-index stream shared across all eight contrasts",
            "contrast_order": list(CONTRAST_KEYS),
            "user_order": "preserved as supplied within each contrast",
        },
        "contrasts": contrasts,
    }
