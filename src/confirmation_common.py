"""Shared, target-label-free representations for the independent study."""
import hashlib
import json
from pathlib import Path
import numpy as np
from coat_memory_reader import ROOT, records, targets, messages, parse_predictions
from coat_baselines import ridge

CONDITIONS = ['no_history', 'full_history', 'shuffled_history', 'native_memory']
MODELS = {'qwen': 'qwen3-4b-instruct-2507-4bit', 'phi': 'phi-4-4bit'}


def shuffled_history(history, user):
    """Preserve rated items and the rating multiset; permute their assignment."""
    seed = int.from_bytes(hashlib.sha256(f'coat-association-control-v1:{user}'.encode()).digest()[:8], 'little')
    rng = np.random.default_rng(seed)
    out = history.copy()
    items = np.flatnonzero(history)
    out[items] = rng.permutation(history[items])
    return out


def history_only(history, features, variant, penalty=None):
    """Standard baselines, without labels from other users."""
    items = np.flatnonzero(history)
    if not len(items):
        return np.full(len(history), 3.)
    if variant == 'history_mean':
        return np.full(len(history), np.mean(history[items]))
    if variant == 'history_median':
        return np.full(len(history), np.median(history[items]))
    if variant == 'history_ridge':
        beta = ridge(features[items], history[items] - 3., np.ones(len(items)), penalty)
        return np.clip(3. + features @ beta, 1., 5.)
    raise ValueError(variant)


def evidence_for(user, history, features, names, native_texts):
    from run_coat_memory_development import history_message
    return {
        'no_history': 'No personal history is available.',
        'full_history': history_message(records(history, features, names)),
        'shuffled_history': history_message(records(shuffled_history(history, user), features, names)),
        'native_memory': '\n'.join(sorted(native_texts)) if native_texts else 'No stored personal memories are available.',
    }


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)
