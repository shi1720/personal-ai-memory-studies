"""Explicit local model identities for the two-family review-history experiment."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = {
    'qwen':('qwen3-4b-instruct-2507-4bit','local-model-manifest.json'),
    'phi':('phi-4-4bit','phi-model-manifest.json'),
}


def model_path(key):
    return ROOT/'models'/SPECS[key][0]


def verify_model(key, tokenizer_only=False):
    manifest = json.loads((ROOT/'references'/SPECS[key][1]).read_text())
    rows = manifest['files']
    if tokenizer_only:
        rows = [r for r in rows if Path(r['name']).suffix in ('.json','.jinja')
                or r['name'] in ('merges.txt','vocab.txt')]
    if not rows:
        raise ValueError('Empty model pin set')
    for row in rows:
        path = model_path(key)/row['name']
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
        if h.hexdigest() != row['sha256']:
            raise ValueError('Model pin mismatch: '+key+'/'+row['name'])
    return manifest['revision']
