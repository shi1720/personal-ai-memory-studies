"""Pure, fixed-family development scoring. No files, models or target discovery."""
from math import isfinite, sqrt
from numbers import Real
from statistics import mean, median

from language_precision_planning import CONTRAST_KEYS, plan_precision

ARMS = ('no_history', 'full_history', 'native_qwen', 'summary_qwen',
        'native_phi', 'summary_phi', 'bm25_history')
READERS = ('qwen', 'phi')


def rating_vector(values, count):
    if not isinstance(values, (list, tuple)) or len(values) != count:
        raise ValueError('Wrong rating vector length or type')
    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError('Ratings must be real nonboolean numbers')
        value = float(value)
        if not isfinite(value) or not 1 <= value <= 5:
            raise ValueError('Ratings must be finite and between one and five')
        result.append(value)
    return result


def user_metrics(predictions, targets):
    predictions = rating_vector(predictions, 3)
    targets = rating_vector(targets, 3)
    errors = [p - y for p, y in zip(predictions, targets)]
    scores = []
    for i in range(3):
        for j in range(i + 1, 3):
            truth = targets[i] - targets[j]
            if truth == 0:
                continue
            predicted = predictions[i] - predictions[j]
            scores.append(0.5 if predicted == 0 else float(predicted * truth > 0))
    return {
        'mae': mean(abs(e) for e in errors),
        'mse': mean(e * e for e in errors),
        'signed_error': mean(errors),
        'pairwise_concordance': mean(scores) if scores else None,
        'unequal_target_pairs': len(scores),
    }


def aggregate(rows):
    if not rows:
        raise ValueError('Cannot aggregate zero users')
    ordering = [r['pairwise_concordance'] for r in rows if r['pairwise_concordance'] is not None]
    return {
        'users': len(rows),
        'mae': mean(r['mae'] for r in rows),
        'rmse': sqrt(mean(r['mse'] for r in rows)),
        'signed_error': mean(r['signed_error'] for r in rows),
        'pairwise_concordance': mean(ordering) if ordering else None,
        'ordering_eligible_users': len(ordering),
        'valid_users': sum(r['valid'] for r in rows),
    }


def score_development(cases, targets, histories, cells):
    """Score all fixed cells; invalid complete pipelines use constant-three.

    `cells` has exactly fourteen (reader, arm) mappings to all supplied cases.
    A cell contains `valid` (a bool) and, when valid, `predictions` (three ratings).
    Callers must independently establish provenance and whole-pipeline validity.
    This pure calculation cannot establish those properties from numeric inputs.
    """
    if not cases or len(set(cases)) != len(cases):
        raise ValueError('Nonempty unique case order required')
    if set(targets) != set(cases) or set(histories) != set(cases):
        raise ValueError('Targets and histories must cover every case exactly')
    expected = {(reader, arm) for reader in READERS for arm in ARMS}
    if set(cells) != expected or any(set(value) != set(cases) for value in cells.values()):
        raise ValueError('Incomplete or additional reader-condition cells')
    targets = {case: rating_vector(targets[case], 3) for case in cases}
    histories = {case: rating_vector(histories[case], 12) for case in cases}
    systems = {}
    for reader in READERS:
        for arm in ARMS:
            name = reader + '/' + arm
            records = []
            for case in cases:
                cell = cells[(reader, arm)][case]
                if type(cell.get('valid')) is not bool:
                    raise ValueError('Whole-pipeline validity must be a bool')
                valid = cell['valid']
                prediction = rating_vector(cell.get('predictions'), 3) if valid else [3., 3., 3.]
                records.append({'case_id': case, 'valid': valid,
                                **user_metrics(prediction, targets[case])})
            systems[name] = {'summary': aggregate(records), 'users': records}
    for name, estimator in (('history_mean', mean), ('history_median', median),
                            ('constant_3', lambda _: 3.)):
        records = [{'case_id': case, 'valid': True,
                    **user_metrics([estimator(histories[case])] * 3, targets[case])}
                   for case in cases]
        systems[name] = {'summary': aggregate(records), 'users': records}
    contrasts, arrays = {}, {}
    for writer in READERS:
        for reader in READERS:
            native = systems[reader + '/native_' + writer]['users']
            for comparison, arm in (('native_minus_full', 'full_history'),
                                    ('native_minus_matched_summary', 'summary_' + writer)):
                other = systems[reader + '/' + arm]['users']
                key = f'{comparison}__writer_{writer}__reader_{reader}'
                differences = [a['mae'] - b['mae'] for a, b in zip(native, other)]
                common = [a['mae'] - b['mae'] for a, b in zip(native, other)
                          if a['valid'] and b['valid']]
                arrays[key] = differences
                contrasts[key] = {
                    'users': len(cases), 'mean_difference': mean(differences),
                    'common_valid_users': len(common),
                    'common_valid_mean_difference': mean(common) if common else None,
                    'paired_user_differences': differences,
                }
    if set(contrasts) != set(CONTRAST_KEYS):
        raise ValueError('Primary family changed')
    return {'scope': 'Development accuracy, not independent confirmation',
            'cases': list(cases), 'systems': systems, 'contrasts': contrasts,
            'precision_planning': plan_precision(arrays) if len(cases) == 60 else None,
            'precision_planning_not_run_reason': None if len(cases) == 60 else 'Requires exactly 60 development users'}
