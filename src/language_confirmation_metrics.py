"""Pure scoring for the prospective fixed 200-user confirmation design.

No files, models, network, label discovery or execution authorization. Shared
metric definitions match development; uncertainty is the separately specified
joint user bootstrap. A caller must verify provenance and pipeline validity.
"""
from collections.abc import Mapping
from math import isclose

from language_development_metrics import ARMS, READERS, score_development
from language_confirmation_uncertainty import (
    CONFIRMATION_USERS, CONTRAST_KEYS, bootstrap_confirmation,
)


def score_confirmation(cases, targets, histories, cells):
    """Calculate all fixed systems and contrasts without changing the inputs.

    `cases` fixes the common user order. Each of fourteen (reader, arm) entries
    maps every case to a boolean `valid` for the *entire* writer-reader pipeline
    and three numeric `predictions` when valid. Valid diagnostic reader output
    after a failed writer must enter with valid=False and will be replaced by
    constant three. This function cannot infer writer validity from predictions.

    Exactly three targets and twelve historical ratings are required per user.
    Full provenance, split membership, label gating and completeness of actual
    inference must be established separately, before calling this function.
    """
    if (not isinstance(cases, (list, tuple)) or len(cases) != CONFIRMATION_USERS
            or any(not isinstance(case, str) or not case for case in cases)
            or len(set(cases)) != CONFIRMATION_USERS):
        raise ValueError("Exactly 200 distinct nonempty string case IDs are required")
    case_set = set(cases)
    for name, values in (("targets", targets), ("histories", histories)):
        if not isinstance(values, Mapping) or set(values) != case_set:
            raise ValueError(name + " must cover precisely the fixed case order")
    expected = {(reader, arm) for reader in READERS for arm in ARMS}
    if not isinstance(cells, Mapping) or set(cells) != expected:
        raise ValueError("Exactly fourteen reader-condition mappings are required")
    for values in cells.values():
        if not isinstance(values, Mapping) or set(values) != case_set:
            raise ValueError("Every reader-condition must cover all 200 users")
        if any(not isinstance(cell, Mapping) for cell in values.values()):
            raise ValueError("Every supplied pipeline cell must be a mapping")

    # This shared routine never plans development precision for 200 users. It
    # applies the unchanged full-pipeline fallback before constructing errors.
    point = score_development(cases, targets, histories, cells)
    if point["precision_planning"] is not None:
        raise ValueError("Development precision planning cannot run in confirmation")
    if set(point["contrasts"]) != set(CONTRAST_KEYS):
        raise ValueError("The fixed eight-contrast family changed")
    differences = {key: point["contrasts"][key]["paired_user_differences"]
                   for key in CONTRAST_KEYS}
    uncertainty = bootstrap_confirmation(differences)
    contrasts = {}
    for key in CONTRAST_KEYS:
        values = point["contrasts"][key]
        interval = uncertainty["contrasts"][key]
        if not isclose(values["mean_difference"], interval["mean_difference"],
                       rel_tol=0., abs_tol=1e-12):
            raise ValueError("Point estimate disagrees with paired bootstrap input")
        contrasts[key] = {
            **values, **interval,
            "common_valid_interpretation": (
                "Descriptive paired mean on pipelines valid in both conditions; "
                "no interval or significance decision. Selection may change the "
                "population. This sensitivity never replaces the all-user result."
            ),
        }
    return {
        "scope": (
            "Pure calculation for supplied fixed confirmation inputs. This output "
            "does not establish observed-data provenance, independent replication, "
            "completion of inference, or permission to access reserved data."
        ),
        "calculation_complete": True,
        "cases": list(cases),
        "users": CONFIRMATION_USERS,
        "target_ratings": CONFIRMATION_USERS * 3,
        "systems": point["systems"],
        "contrasts": contrasts,
        "uncertainty_settings": uncertainty["settings"],
        "uncertainty_interpretation": uncertainty["scope"],
        "primary_failure_rule": (
            "Use constant [3, 3, 3] for the entire user-condition if its required "
            "writer or reader is invalid; retain every user in every primary contrast."
        ),
        "baseline_interpretation": (
            "History mean, history median and constant three are descriptive "
            "numerical references, outside the eight primary comparisons."
        ),
    }
