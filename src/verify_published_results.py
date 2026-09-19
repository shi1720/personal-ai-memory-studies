"""Verify released user-level summaries without datasets, raw traces or inference.

This checks aggregation and paired bootstrap reporting. It cannot validate the
original predictions against undistributed targets; independent_result_check.py
performs that separate local check. No project measurement helpers are imported.
"""
import hashlib
import json
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def near(actual, expected, label):
    if expected is None:
        assert actual is None, label
    else:
        assert actual is not None and math.isfinite(actual), label
        assert math.isclose(actual, expected, rel_tol=0, abs_tol=1e-10), (label, actual, expected)


def interval(values, recorded):
    assert len(values) == recorded['users'] and recorded['replicates'] == 10000
    assert recorded['seed'] == 20260920
    near(recorded['mean'], math.fsum(values) / len(values), 'paired mean')
    generator = np.random.default_rng(20260920)
    # Reconstruct resamples independently in batches, preserving RNG order.
    sampled = []
    a = np.asarray(values, dtype=float)
    for _ in range(100):
        indices = generator.integers(len(values), size=(100, len(values)))
        sampled.extend(np.sum(a[indices], axis=1) / len(values))
    for key, tails in [('interval_95', [.025, .975]),
                       ('family_adjusted_interval', [.0025, .9975])]:
        for actual, expected in zip(recorded[key], np.quantile(sampled, tails)):
            near(actual, float(expected), key)
    assert recorded['positive_users'] == sum(v > 0 for v in values)
    assert recorded['negative_users'] == sum(v < 0 for v in values)
    assert recorded['zero_users'] == sum(v == 0 for v in values)


def verify(report, expected_contrasts):
    records = report['users']
    lookup = {(r['user_row'], r['system']): r for r in records}
    assert len(lookup) == len(records), 'duplicate user/system'
    systems = set(r['system'] for r in records)
    assert systems == set(report['summaries'])
    for system in systems:
        rows = [r for r in records if r['system'] == system]
        summary = report['summaries'][system]
        assert len(rows) == summary['users'] == 200
        assert sum(r['targets'] for r in rows) == summary['targets']
        valid = [r for r in rows if r['valid']]
        assert len(valid) == summary['valid_users']
        assert sum(r['targets'] for r in valid) == summary['valid_targets']
        for r in rows:
            near(r['mse'], r['level_mse'] + r['centered_mse'], 'MSE identity')
            near(r['level_mse'], r['signed_error'] ** 2, 'mean error square')
            assert 0 <= r['mae'] <= 4 and 0 <= r['mse'] <= 16
            assert r['pairwise_accuracy'] is None or 0 <= r['pairwise_accuracy'] <= 1
        for kind, subset in [('operational', rows), ('valid_only', valid)]:
            result = summary[kind]
            for key in ['mae', 'signed_error', 'level_mse', 'centered_mse']:
                expected = math.fsum(r[key] for r in subset) / len(subset) if subset else None
                near(result[key], expected, system + '/' + kind + '/' + key)
            expected = math.sqrt(math.fsum(r['mse'] for r in subset) / len(subset)) if subset else None
            near(result['rmse'], expected, 'user-macro RMSE')
            pairs = [r['pairwise_accuracy'] for r in subset if r['pairwise_accuracy'] is not None]
            near(result['pairwise_accuracy'], math.fsum(pairs)/len(pairs) if pairs else None, 'pairwise mean')
    assert len(report['primary_contrasts']) == expected_contrasts
    for name, contrast in report['primary_contrasts'].items():
        left, right = contrast['left'], contrast['right']
        # Published row order is the frozen user order, not a sorted reindexing.
        users = [r['user_row'] for r in records if r['system'] == left]
        assert len(users) == 200
        diffs = [lookup[u, left]['mae'] - lookup[u, right]['mae'] for u in users]
        interval(diffs, contrast['operational'])
        common = [u for u in users if lookup[u, left]['valid'] and lookup[u, right]['valid']]
        assert set(contrast['excluded_common_valid']) == set(users) - set(common)
        if common:
            interval([lookup[u, left]['mae'] - lookup[u, right]['mae'] for u in common], contrast['common_valid'])
        else:
            assert contrast['common_valid'] is None
    return {'user_system_rows': len(records), 'systems': len(systems),
            'primary_contrasts': expected_contrasts, 'status': 'passed'}


def main():
    checked = []
    for filename, contrasts in [('confirmation-analysis.json', 6), ('movie-validation-analysis.json', 4)]:
        path = ROOT / 'results' / filename
        report = json.loads(path.read_text())
        result = verify(report, contrasts)
        for source, expected in report['hashes'].items():
            assert hashlib.sha256((ROOT / source).read_bytes()).hexdigest() == expected, source
        checked.append({'report': filename, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **result})
    output = {'scope': 'Released-summary arithmetic and bootstrap verification; not fresh inference or external replication',
              'checks': checked, 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (ROOT / 'results/published-results-verification.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
