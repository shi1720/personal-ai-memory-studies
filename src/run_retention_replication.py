"""Frozen additional-model checks on the existing development journals."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time
import mlx.core as mx
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler
from retention_pilot_data import messages, parse_selection
from run_retention_controls import make_messages
from run_retention_pilot import sha
ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    'mistral': ('mistral-7b-instruct-v0.3-4bit', 'mistral-model-manifest.json', 'single_user'),
    'phi': ('phi-4-4bit', 'phi-model-manifest.json', 'native_roles'),
}
CONDITIONS = ['important_plain', 'important_detailed', 'representative_plain',
              'representative_detailed', 'important_antonym', 'archive_negation',
              'archive_antonym', 'proportional_negation', 'proportional_antonym']

def case_messages(journal, condition, adapter):
    writer, variant = condition.split('_')
    if variant in ('plain', 'detailed'):
        ms = messages(journal, writer, variant == 'detailed')
    else:
        ms = make_messages(journal, writer, variant)
    if adapter == 'single_user':
        ms = [{'role': 'user', 'content': '\n\n'.join(m['content'] for m in ms)}]
    return ms

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, choices=MODELS)
    args = parser.parse_args()
    folder, manifest_name, adapter = MODELS[args.model]
    directory = ROOT / 'models' / folder
    model_manifest_path = ROOT / 'references' / manifest_name
    for record in json.loads(model_manifest_path.read_text())['files']:
        if sha(directory / record['name']) != record['sha256']:
            raise ValueError('Changed model file')
    journals = json.loads((ROOT / 'results/pilot-003-journals.json').read_text())
    deps = ['src/run_retention_replication.py', 'src/retention_pilot_data.py',
            'src/run_retention_controls.py', 'src/run_retention_pilot.py',
            'docs/pilot-003-replication.md', 'results/pilot-003-journals.json',
            'references/' + manifest_name]
    manifest = {'status': 'development replication, not independent confirmation',
                'model': args.model, 'adapter': adapter, 'expected_calls': 108,
                'conditions': CONDITIONS, 'temperature': 0, 'seed': 0,
                'max_output_tokens': 160, 'max_prompt_tokens': 4096,
                'hashes': {p: sha(ROOT / p) for p in deps},
                'versions': {p: importlib.metadata.version(p) for p in ['mlx', 'mlx-lm', 'transformers']}}
    prefix = ROOT / 'results' / ('pilot-003-' + args.model)
    mp = Path(str(prefix) + '-manifest.json')
    if mp.exists() and json.loads(mp.read_text()) != manifest:
        raise ValueError('Changed run identity')
    mp.write_text(json.dumps(manifest, indent=2) + '\n')
    output = Path(str(prefix) + '-predictions.jsonl')
    completed = set()
    if output.exists():
        for line in output.read_text().splitlines():
            row = json.loads(line)
            key = (row['journal'], row['condition'])
            if key in completed:
                raise ValueError('Duplicate case')
            completed.add(key)
    expected = {(j['id'], c) for j in journals for c in CONDITIONS}
    if len(journals) != 12 or not completed <= expected:
        raise ValueError('Unexpected population or completed case')
    model, tok = load(str(directory), tokenizer_config={'trust_remote_code': False})
    for j in journals:
        for condition in CONDITIONS:
            key = (j['id'], condition)
            if key in completed:
                continue
            prompt = tok.apply_chat_template(case_messages(j, condition, adapter), tokenize=False, add_generation_prompt=True)
            tokens = tok.encode(prompt, add_special_tokens=False)
            if len(tokens) > 4096:
                raise ValueError('Input budget exceeded')
            mx.random.seed(0)
            start = time.perf_counter()
            parts, last = [], None
            for response in stream_generate(model, tok, tokens, max_tokens=160, sampler=make_sampler(temp=0.0)):
                parts.append(response.text)
                last = response
            if last is None:
                raise RuntimeError('No generation response')
            text = ''.join(parts)
            selection = parse_selection(text, {e['id'] for e in j['events']})
            row = {'journal': j['id'], 'condition': condition, 'model': args.model,
                   'adapter': adapter, 'prompt': prompt,
                   'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                   'text': text, 'selection': selection, 'valid': selection is not None,
                   'prompt_tokens': last.prompt_tokens, 'generation_tokens': last.generation_tokens,
                   'finish_reason': last.finish_reason, 'reader_seconds': time.perf_counter() - start}
            with output.open('a') as f:
                f.write(json.dumps(row) + '\n')
                f.flush()
                os.fsync(f.fileno())
            completed.add(key)
            mx.clear_cache()
            print(f'Completed {len(completed)}/108 {key} valid={selection is not None}', flush=True)
if __name__ == '__main__':
    main()
