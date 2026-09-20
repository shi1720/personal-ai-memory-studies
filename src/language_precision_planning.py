"""Fixed, outcome-direction-independent precision planning for the extension.

This module has no data-loading or inference path. Callers supply the complete
development differences after constructing them under the separate protocol.
The calculation is approximate planning, not a coverage or power guarantee.
"""
from collections.abc import Mapping
from math import isfinite, sqrt
from numbers import Real
from statistics import NormalDist

import numpy as np


DEVELOPMENT_USERS = 60
CONFIRMATION_USERS = 200
FAMILY_SIZE = 8
ALPHA = 0.05
TARGET_HALF_WIDTH = 0.10
BOOTSTRAP_RESAMPLES = 20000
BOOTSTRAP_SEED = 20260923
SD_UPPER_QUANTILE = 0.95
SD_DDOF = 1
QUANTILE_METHOD = "linear"
_BATCH_SIZE = 1000

CONTRAST_KEYS = tuple(sorted(
    f"{comparison}__writer_{writer}__reader_{reader}"
    for comparison in ("native_minus_full", "native_minus_matched_summary")
    for writer in ("qwen", "phi")
    for reader in ("qwen", "phi")
))


def _validated_values(differences):
    """Validate the entire family before consuming any random numbers."""
    if not isinstance(differences, Mapping):
        raise ValueError("Expected a mapping containing all eight canonical contrasts")
    if set(differences) != set(CONTRAST_KEYS):
        raise ValueError("Contrast names must exactly match CONTRAST_KEYS")
    arrays = {}
    for key in CONTRAST_KEYS:
        values = differences[key]
        if not isinstance(values, (list, tuple, np.ndarray)):
            raise ValueError(f"{key}: expected a one-dimensional list, tuple, or array")
        if isinstance(values, np.ndarray) and values.ndim != 1:
            raise ValueError(f"{key}: expected one dimension")
        if len(values) != DEVELOPMENT_USERS:
            raise ValueError(f"{key}: requires exactly 60 paired user differences")
        converted = []
        for value in values:
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
                raise ValueError(f"{key}: values must be real numbers, not booleans")
            try:
                numeric = float(value)
            except (OverflowError, TypeError, ValueError) as exc:
                raise ValueError(f"{key}: values must be representable finite numbers") from exc
            if not isfinite(numeric) or not -4.0 <= numeric <= 4.0:
                raise ValueError(f"{key}: differences must be finite and within [-4, 4]")
            converted.append(numeric)
        arrays[key] = np.asarray(converted, dtype=np.float64)
    return arrays


def plan_precision(differences):
    """Return the fixed eight-contrast planning gate, or reject invalid input.

    Mapping insertion order is ignored. User order within every contrast is
    retained and must be fixed by the caller's development pairing protocol.
    All settings are prescribed here and cannot be passed as overrides.
    """
    arrays = _validated_values(differences)
    critical_value = NormalDist().inv_cdf(1.0 - ALPHA / (2.0 * FAMILY_SIZE))
    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    results = {}
    for key in CONTRAST_KEYS:
        values = arrays[key]
        bootstrap_sds = np.empty(BOOTSTRAP_RESAMPLES, dtype=np.float64)
        for start in range(0, BOOTSTRAP_RESAMPLES, _BATCH_SIZE):
            stop = min(start + _BATCH_SIZE, BOOTSTRAP_RESAMPLES)
            sampled_indices = rng.integers(
                0, DEVELOPMENT_USERS, size=(stop - start, DEVELOPMENT_USERS)
            )
            bootstrap_sds[start:stop] = np.std(
                values[sampled_indices], axis=1, ddof=SD_DDOF
            )
        upper_sd = float(np.quantile(
            bootstrap_sds, SD_UPPER_QUANTILE, method=QUANTILE_METHOD
        ))
        half_width = critical_value * upper_sd / sqrt(CONFIRMATION_USERS)
        results[key] = {
            "development_users": int(values.size),
            "sample_sd": float(np.std(values, ddof=SD_DDOF)),
            "bootstrap_sd_upper_95_quantile": upper_sd,
            "projected_adjusted_half_width": half_width,
            "meets_target": bool(half_width <= TARGET_HALF_WIDTH),
        }
    passes = all(row["meets_target"] for row in results.values())
    return {
        "scope": (
            "Approximate pre-confirmation precision planning on development users; "
            "not a confidence-interval coverage or power guarantee, not new validation, "
            "and not a directional accuracy or scientific-success criterion."
        ),
        "settings": {
            "development_users": DEVELOPMENT_USERS,
            "confirmation_users": CONFIRMATION_USERS,
            "family_size": FAMILY_SIZE,
            "alpha": ALPHA,
            "target_half_width": TARGET_HALF_WIDTH,
            "bootstrap_resamples_per_contrast": BOOTSTRAP_RESAMPLES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "generator": "NumPy PCG64",
            "bootstrap_sd_quantile": SD_UPPER_QUANTILE,
            "sample_sd_ddof": SD_DDOF,
            "quantile_method": QUANTILE_METHOD,
            "normal_critical_value": critical_value,
            "random_stream": "one stream consumed in sorted canonical contrast order",
            "user_order": "preserved as supplied within each contrast",
        },
        "complete": len(results) == FAMILY_SIZE,
        "contrasts": results,
        "joint_go": bool(passes and len(results) == FAMILY_SIZE),
        "decision": "GO" if passes else "NO_GO",
    }
