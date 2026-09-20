"""Post-review Monte Carlo endpoint stability, using released summaries only.

This exploratory numerical check does not add validation data, change frozen
primary intervals, or increase the scope of the original statistical claims.
"""
import hashlib
import json
from pathlib import Path
import platform

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (20260921, 20260922)
REPLICATES = 200000
BATCH_SIZE = 2000
TAILS = {'interval_95': (0.025, 0.975),
         'family_adjusted_interval': (0.0025, 0.9975)}


def sampled_means(values, seed, replicates, batch_size):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError('Require a nonempty finite vector of paired user differences')
    if replicates <= 0 or batch_size <= 0:
        raise ValueError('Replicates and batch size must be positive')
    generator = np.random.default_rng(seed)
    means = np.empty(replicates, dtype=float)
    for start in range(0, replicates, batch_size):
        stop = min(start + batch_size, replicates)
        indices = generator.integers(0, len(values), size=(stop - start, len(values)))
        means[start:stop] = values[indices].mean(axis=1)
    return means


def paired_values(records, left, right, expected_users):
    lookup = {(row['user_row'], row['system']): row for row in records}
    if len(lookup) != len(records):
        raise ValueError('Duplicate user/system summaries')
    users = [row['user_row'] for row in records if row['system'] == left]
    right_users = {row['user_row'] for row in records if row['system'] == right}
    if len(users) != expected_users or set(users) != right_users:
        raise ValueError('Mismatched paired user populations')
    differences = []
    for user in users:
        a, b = lookup[user, left], lookup[user, right]
        if a['targets'] != b['targets']:
            raise ValueError('Mismatched target counts for a paired user')
        differences.append(float(a['mae']) - float(b['mae']))
    return np.asarray(differences)


def zero_status(interval):
    if interval[0] > 0:
        return 'positive'
    if interval[1] < 0:
        return 'negative'
    return 'includes_zero'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = [('Coat', 'confirmation-analysis.json', 6),
               ('MovieLens', 'movie-validation-analysis.json', 4)]
    comparisons = []
    input_hashes = {}
    for domain, filename, expected_contrasts in sources:
        path = ROOT / 'results' / filename
        input_hashes[str(path.relative_to(ROOT))] = sha256(path)
        report = json.loads(path.read_text())
        if len(report['primary_contrasts']) != expected_contrasts:
            raise ValueError('Unexpected primary comparison family')
        for name, contrast in report['primary_contrasts'].items():
            original = contrast['operational']
            values = paired_values(report['users'], contrast['left'], contrast['right'], 200)
            if original['users'] != 200 or original['seed'] != 20260920 or original['replicates'] != 10000:
                raise ValueError('Unexpected frozen bootstrap settings')
            if abs(float(values.mean()) - original['mean']) > 1e-12:
                raise ValueError('Paired user mean does not match frozen result')
            result = {'domain': domain, 'contrast': name, 'left': contrast['left'],
                      'right': contrast['right'], 'users': len(values),
                      'mean': float(values.mean()),
                      'frozen': {'seed': original['seed'], 'replicates': original['replicates'],
                                 **{key: original[key] for key in TAILS}},
                      'auxiliary_runs': []}
            for seed in SEEDS:
                means = sampled_means(values, seed, REPLICATES, BATCH_SIZE)
                intervals = {key: np.quantile(means, tails).tolist() for key, tails in TAILS.items()}
                result['auxiliary_runs'].append({
                    'seed': seed, 'replicates': REPLICATES,
                    'intervals': intervals,
                    'zero_status': {key: zero_status(ci) for key, ci in intervals.items()},
                    'matches_frozen_zero_status': {
                        key: zero_status(ci) == zero_status(original[key]) for key, ci in intervals.items()},
                    'endpoint_change_from_frozen': {
                        key: (np.array(ci) - original[key]).tolist() for key, ci in intervals.items()},
                })
            result['frozen']['zero_status'] = {key: zero_status(original[key]) for key in TAILS}
            result['maximum_absolute_endpoint_change_between_auxiliary_seeds'] = {
                key: float(np.max(np.abs(np.array(result['auxiliary_runs'][0]['intervals'][key]) -
                                        result['auxiliary_runs'][1]['intervals'][key]))) for key in TAILS}
            comparisons.append(result)
    maximum_change = {key: max(abs(delta) for row in comparisons for run in row['auxiliary_runs']
                               for delta in run['endpoint_change_from_frozen'][key]) for key in TAILS}
    outcome = {
        'scope': 'Post-review exploratory numerical Monte Carlo endpoint-stability audit; '
                 'uses the same released held-out summaries, not fresh validation data. '
                 'Does not replace or modify frozen primary results.',
        'settings': {'seeds': list(SEEDS), 'replicates_per_seed_per_contrast': REPLICATES,
                     'batch_size': BATCH_SIZE, 'sampling_unit': 'paired user difference',
                     'generator': 'NumPy default_rng (PCG64)', 'percentile_method': 'linear',
                     'tail_probabilities': TAILS, 'family_size': 10},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__},
        'input_sha256': input_hashes, 'source_sha256': sha256(Path(__file__)),
        'comparisons': comparisons,
        'summary': {
            'primary_operational_contrasts': len(comparisons),
            'auxiliary_bootstrap_runs': len(comparisons) * len(SEEDS),
            'all_zero_exclusion_statuses_match_frozen': all(
                matched for row in comparisons for run in row['auxiliary_runs']
                for matched in run['matches_frozen_zero_status'].values()),
            'maximum_absolute_endpoint_change_from_frozen': maximum_change,
            'maximum_absolute_endpoint_change_between_auxiliary_seeds': {
                key: max(row['maximum_absolute_endpoint_change_between_auxiliary_seeds'][key]
                         for row in comparisons) for key in TAILS},
        },
    }
    destination = ROOT / 'results/review-bootstrap-stability.json'
    destination.write_text(json.dumps(outcome, indent=2) + '\n')
    print(json.dumps(outcome['summary'], indent=2))


if __name__ == '__main__':
    main()
