"""Post hoc base-model probe on Pilot 004; not a trained MMPO reproduction."""
import argparse
import hashlib
import importlib.metadata
import inspect
import json
import math
import os
from pathlib import Path
import time

import mlx.core as mx
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    'qwen': ('qwen3-4b-instruct-2507-4bit', 'local-model-manifest.json'),
    'phi': ('phi-4-4bit', 'phi-model-manifest.json'),
}
# 17-word research prompt quoted from MMPO Appendix E.1; see protocol attribution.
ANCHOR = 'Based on current memory, what is our task progress and what information is still needed?'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, choices=MODELS)
    args = parser.parse_args()
    directory, model_manifest = MODELS[args.model]
    model_path = ROOT / 'models' / directory
    for item in json.loads((ROOT / 'references' / model_manifest).read_text())['files']:
        if sha(model_path / item['name']) != item['sha256']:
            raise ValueError('Model hash mismatch')
    dependencies = [
        'docs/memory-probe-information.md', 'src/run_memory_probe_screen.py',
        'results/pilot-004-inputs.json',
        f'results/pilot-004-{args.model}-predictions.jsonl',
        'references/' + model_manifest,
    ]
    manifest = {
        'status': 'post hoc development proxy test; untrained base model',
        'model': args.model, 'temperature': 0, 'seed': 0,
        'max_input_tokens': 4096, 'max_output_tokens': 256,
        'scheduled_records': 36,
        'entropy': 'full-vocabulary natural logs, float32 before logsumexp, exclude EOS',
        'hashes': {p: sha(ROOT / p) for p in dependencies},
        'stream_generate_source_sha256': hashlib.sha256(inspect.getsource(stream_generate).encode()).hexdigest(),
        'versions': {p: importlib.metadata.version(p) for p in ['mlx', 'mlx-lm', 'transformers']},
    }
    prefix = ROOT / 'results' / f'memory-probe-{args.model}'
    manifest_path = Path(str(prefix) + '-manifest.json')
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError('Run identity changed')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    output_path = Path(str(prefix) + '-predictions.jsonl')
    completed = {}
    if output_path.exists():
        for line in output_path.read_text().splitlines():
            row = json.loads(line)
            key = (row['journal'], row['context'])
            if key in completed:
                raise ValueError('Duplicate output')
            completed[key] = row
    inputs = json.loads((ROOT / 'results/pilot-004-inputs.json').read_text())
    writers = {}
    for line in (ROOT / f'results/pilot-004-{args.model}-predictions.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['stage'] == 'writer':
            writers[(row['journal'], row['context'])] = row
    expected = {(j['id'], c) for j in inputs for c in ['full', 'native', 'count_aware']}
    if len(expected) != 36 or not set(completed) <= expected:
        raise ValueError('Unexpected cases')
    model, tokenizer = load(str(model_path), tokenizer_config={'trust_remote_code': False})

    def save(row):
        key = (row['journal'], row['context'])
        if key in completed:
            raise ValueError('Duplicate write')
        row['model'] = args.model
        with output_path.open('a') as handle:
            handle.write(json.dumps(row) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        completed[key] = row
        print(f"{len(completed)}/36 {key} {row['status']}", flush=True)

    for journal in inputs:
        question = next(q['question'] for q in journal['queries'] if q['kind'] == 'rate')
        for context in ['full', 'native', 'count_aware']:
            key = (journal['id'], context)
            if key in completed:
                continue
            row = {'journal': journal['id'], 'context': context}
            if context == 'full':
                evidence = journal['journal_text']
            else:
                writer = writers[key]
                if writer['status'] != 'valid':
                    save(dict(row, status='blocked_writer'))
                    continue
                evidence = json.dumps({'facts': writer['facts']}, ensure_ascii=False)
            messages = [
                {'role': 'system', 'content': 'Assess the task using only the supplied memory. Describe progress and remaining information needs concisely.'},
                {'role': 'user', 'content': f'Task:\n{question}\n\nCurrent memory:\n{evidence}\n\n{ANCHOR}'},
            ]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            tokens = tokenizer.encode(prompt, add_special_tokens=False)
            if len(tokens) > 4096:
                raise ValueError('Prompt exceeds fixed budget')
            mx.random.seed(0)
            start = time.perf_counter()
            pieces, token_records = [], []
            last = None
            for response in stream_generate(
                model, tokenizer, tokens, max_tokens=256, sampler=make_sampler(temp=0.0),
                logits_processors=[lambda ids, logits: logits.astype(mx.float32)],
            ):
                last = response
                pieces.append(response.text)
                logp = response.logprobs.astype(mx.float32)
                p = mx.exp(logp)
                mass = mx.sum(p).item()
                ent = (-mx.sum(mx.where(p > 0, p * logp, 0))).item()
                nll = (-logp[response.token]).item()
                if not math.isfinite(ent) or not math.isfinite(nll) or abs(mass - 1) > 1e-5:
                    raise ValueError('Invalid probability computation')
                token_records.append({'id': response.token, 'entropy_nats': ent, 'nll_nats': nll,
                                      'eos': response.token in tokenizer.eos_token_ids})
            if last is None:
                raise RuntimeError('No generation')
            non_eos = [t['entropy_nats'] for t in token_records if not t['eos']]
            row.update(
                status='complete' if last.finish_reason == 'stop' and non_eos else 'unscored',
                prompt=prompt, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                evidence_sha256=hashlib.sha256(evidence.encode()).hexdigest(),
                text=''.join(pieces), token_records=token_records,
                prompt_tokens=last.prompt_tokens, generation_tokens=last.generation_tokens,
                finish_reason=last.finish_reason, generation_seconds=time.perf_counter() - start,
                primary_entropy_nats=sum(non_eos)/len(non_eos) if last.finish_reason == 'stop' and non_eos else None,
                first_32_entropy_nats=sum(non_eos[:32])/32 if len(non_eos) >= 32 else None,
            )
            save(row)
            mx.clear_cache()


if __name__ == '__main__':
    main()
