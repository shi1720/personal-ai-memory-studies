"""Established numerical baselines for a user-disjoint development screen."""
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_HASH = '6073d0b515ed1f6e830e4fead66dc76ad7991a7553eaa58e228b234a9d19daed'
PENALTIES = [.1, 1., 10., 100.]
WEIGHTINGS = ['uniform', 'exposure', 'positive', 'exposure_positive']


def user_split(count=290, fitting=60, development=30):
    if fitting < 1 or development < 1 or fitting+development >= count:
        raise ValueError('Invalid split sizes')
    ordered = sorted(range(count), key=lambda i: hashlib.sha256(f'coat-memory-development-v1:user:{i}'.encode()).hexdigest())
    return {'fitting': ordered[:fitting], 'development': ordered[fitting:fitting+development],
            'reserved_evaluation': ordered[fitting+development:]}


def load_archive():
    path = ROOT / 'data/coat/coat.zip'
    if hashlib.sha256(path.read_bytes()).hexdigest() != ARCHIVE_HASH:
        raise ValueError('Archive changed')
    with zipfile.ZipFile(path) as archive:
        train = np.loadtxt(io.BytesIO(archive.read('coat/train.ascii')))
        test = np.loadtxt(io.BytesIO(archive.read('coat/test.ascii')))
        item = np.loadtxt(io.BytesIO(archive.read('coat/user_item_features/item_features.ascii')))
        names = archive.read('coat/user_item_features/item_features_map.txt').decode().splitlines()
    keep = [i for i, n in enumerate(names) if not n.startswith('onfrontpage:')]
    features = np.column_stack([np.ones(len(item)), item[:, keep]])
    if train.shape != (290, 300) or test.shape != train.shape or features.shape != (300, 32):
        raise ValueError('Unexpected data shape')
    return train, test, features, ['intercept']+[names[i] for i in keep]


def ridge(x, y, weights, penalty, intercept_penalized=True):
    if penalty <= 0 or x.shape[0] != len(y) or len(y) != len(weights) or not len(y):
        raise ValueError('Invalid fit')
    if not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ValueError('Invalid weights')
    regularizer = np.eye(x.shape[1])*penalty
    if not intercept_penalized:
        regularizer[0, 0] = 0
    return np.linalg.solve(x.T @ (weights[:, None]*x)+regularizer, x.T @ (weights*y))


def population_fit(train, test, features, fitting):
    selected = test[fitting]
    u, items = np.nonzero(selected)
    y = selected[u, items]
    beta = ridge(features[items], y, np.ones(len(y)), 10., intercept_penalized=False)
    propensities = ((train[fitting] > 0).sum(axis=0)+1)/(len(fitting)+2)
    return {'beta': beta, 'mean': float(y.mean()), 'propensities': propensities}


def history_weights(ratings, propensities, weighting):
    if weighting not in WEIGHTINGS:
        raise ValueError('Unknown weighting')
    weights = np.ones(len(ratings))
    if weighting in ['exposure', 'exposure_positive']:
        if np.any(propensities <= 0) or np.any(propensities > 1):
            raise ValueError('Invalid propensity')
        weights *= np.minimum(20., 1/propensities)
    if weighting in ['positive', 'exposure_positive']:
        weights *= np.where(ratings >= 4, .9, .1)
    return weights/weights.mean()


def predictions(history, features, population, variant, penalty=None):
    base = features @ population['beta']
    items = np.flatnonzero(history)
    if variant == 'population_mean':
        return np.full(len(history), population['mean'])
    if variant == 'population_features':
        return np.clip(base, 1, 5)
    if variant == 'exact_cache':
        return np.where(history > 0, history, np.clip(base, 1, 5))
    if not len(items) or penalty is None or penalty <= 0:
        raise ValueError('Personalized baseline needs history and penalty')
    residual = history[items]-base[items]
    if variant == 'user_mean':
        delta = residual.sum()/(len(items)+penalty)
        return np.clip(base+delta, 1, 5)
    weights = history_weights(history[items], population['propensities'][items], variant)
    beta = ridge(features[items], residual, weights, penalty)
    return np.clip(base+features @ beta, 1, 5)


def score_users(train, test, features, population, users, variant, penalty=None):
    records = []
    for user in users:
        predicted = predictions(train[user], features, population, variant, penalty)
        record = {'user_row': int(user)}
        for group, mask in [('new', (test[user] > 0) & (train[user] == 0)),
                            ('known', (test[user] > 0) & (train[user] > 0))]:
            errors = predicted[mask]-test[user, mask]
            record[group] = {'targets': int(mask.sum()),
                             'mae': float(np.abs(errors).mean()) if len(errors) else None,
                             'mse': float((errors**2).mean()) if len(errors) else None}
        records.append(record)
    summaries = {}
    for group in ['new', 'known']:
        included = [r[group] for r in records if r[group]['targets']]
        summaries[group] = {'users': len(included), 'targets': sum(r['targets'] for r in included),
                            'excluded_user_rows': [r['user_row'] for r in records if not r[group]['targets']],
                            'macro_mae': float(np.mean([r['mae'] for r in included])) if included else None,
                            'macro_rmse': float(np.sqrt(np.mean([r['mse'] for r in included]))) if included else None}
    return {'variant': variant, 'penalty': penalty, 'summaries': summaries, 'users': records}


def main():
    split_path = ROOT / 'results/coat-user-split.json'
    split = json.loads(split_path.read_text())
    if split['users'] != user_split() or split['archive_sha256'] != ARCHIVE_HASH:
        raise ValueError('Split changed')
    protocol = ROOT / 'docs/coat-development-protocol.md'
    if hashlib.sha256(protocol.read_bytes()).hexdigest() != split['protocol_sha256']:
        raise ValueError('Protocol changed')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != split['baseline_code_sha256']:
        raise ValueError('Baseline code changed since split freeze')
    train, test, features, names = load_archive()
    population = population_fit(train, test, features, split['users']['fitting'])
    results = []
    for variant in ['population_mean', 'population_features', 'exact_cache', 'user_mean']+WEIGHTINGS:
        for penalty in ([None] if variant.startswith('population') or variant == 'exact_cache' else PENALTIES):
            results.append(score_users(train, test, features, population, split['users']['development'], variant, penalty))
    best = {}
    for variant in ['user_mean']+WEIGHTINGS:
        candidates = [r for r in results if r['variant'] == variant]
        chosen = min(candidates, key=lambda r: (r['summaries']['new']['macro_mae'], -r['penalty']))
        best[variant] = {'penalty': chosen['penalty'], 'new_macro_mae': chosen['summaries']['new']['macro_mae']}
    report = {
        'status': 'development-only established baselines; reserved evaluation unscored',
        'features': names, 'fitting_users': len(split['users']['fitting']),
        'development_users': len(split['users']['development']), 'reserved_users': len(split['users']['reserved_evaluation']),
        'population_model': {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in population.items()},
        'selected_penalties': best, 'results': results,
        'versions': {'numpy': np.__version__},
        'hashes': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
                   ['src/coat_baselines.py', 'results/coat-user-split.json', 'docs/coat-development-protocol.md']},
    }
    (ROOT / 'results/coat-development-baselines.json').write_text(json.dumps(report, indent=2)+'\n')
    for r in results:
        print(r['variant'], r['penalty'], r['summaries']['new'])
    print('Selected penalties:', best)


if __name__ == '__main__':
    main()
