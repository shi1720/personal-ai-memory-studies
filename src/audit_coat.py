"""Pin and audit the public Coat research archive without redistributing data."""
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.cs.cornell.edu/~schnabts/mnar/coat.zip'
DIGEST = '6073d0b515ed1f6e830e4fead66dc76ad7991a7553eaa58e228b234a9d19daed'


def main():
    path = ROOT / 'data/coat/coat.zip'
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(URL, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != DIGEST:
            raise ValueError('Upstream archive changed')
        path.write_bytes(data)
    if hashlib.sha256(path.read_bytes()).hexdigest() != DIGEST:
        raise ValueError('Archive hash mismatch')
    with zipfile.ZipFile(path) as archive:
        files = {i.filename: {'bytes': i.file_size, 'sha256': hashlib.sha256(archive.read(i)).hexdigest()}
                 for i in archive.infolist() if not i.is_dir()}
        matrices = {name: np.loadtxt(io.BytesIO(archive.read('coat/'+name+'.ascii')))
                    for name in ['train', 'test', 'propensities']}
    for name, values in matrices.items():
        if values.shape != (290, 300) or not np.isfinite(values).all():
            raise ValueError('Unexpected matrix: ' + name)
        if name == 'propensities':
            if not ((values > 0) & (values <= 1)).all():
                raise ValueError('Unsupported propensities')
        elif not ((values == np.floor(values)) & (values >= 0) & (values <= 5)).all():
            raise ValueError('Invalid rating or missingness sentinel')
    train, test, propensity = [matrices[k] for k in ['train', 'test', 'propensities']]
    masks = {k: matrices[k] > 0 for k in ['train', 'test']}
    summaries = {}
    for name in masks:
        values, mask = matrices[name], masks[name]
        counts, frequencies = np.unique(mask.sum(axis=1), return_counts=True)
        summaries[name] = {
            'observed_ratings': int(mask.sum()),
            'ratings_per_user': {str(int(n)): int(f) for n, f in zip(counts, frequencies)},
            'observed_rating_counts': {str(i): int((values == i).sum()) for i in range(1, 6)},
            'observed_mean': float(values[mask].mean()),
            'items_with_no_observation': int((mask.sum(axis=0) == 0).sum()),
        }
    overlap = masks['train'] & masks['test']
    report = {
        'status': 'exploratory dataset integrity audit; no fitted model or causal result',
        'source': URL, 'archive_sha256': DIGEST,
        'license': 'CC BY-NC 4.0, as linked by the author dataset page; research use only here',
        'license_url': 'https://creativecommons.org/licenses/by-nc/4.0/',
        'source_page': 'https://www.cs.cornell.edu/~schnabts/mnar/',
        'paper': 'https://proceedings.mlr.press/v48/schnabel16.html',
        'files': files, 'shape': [290, 300], 'summaries': summaries,
        'overlapping_user_item_cells': int(overlap.sum()),
        'overlap_disagreeing_ratings': int((train[overlap] != test[overlap]).sum()),
        'propensities': {'kind': 'released learned estimates, not known randomized logging probabilities',
                         'minimum': float(propensity.min()), 'maximum': float(propensity.max()),
                         'mean': float(propensity.mean())},
        'limitations': [
            'This is a small elicited shopping-rating dataset, not longitudinal assistant conversations.',
            'No timestamps are present in the released rating matrices.',
            'Random-item ratings are sparse observations, not exact per-user ground-truth preferences.',
            'Released user features include sensitive attributes; this audit does not use them.',
            'No confirmatory split or predictive evaluation has been conducted.',
        ],
        'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (ROOT / 'results/coat-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['summaries', 'overlapping_user_item_cells', 'overlap_disagreeing_ratings', 'propensities']}, indent=2))


if __name__ == '__main__':
    main()
