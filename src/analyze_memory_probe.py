"""Validate and score the frozen, exploratory memory-probe screen.

Unit of comparison is a journal, not a token or independently sampled person.
Previously completed downstream and limited-grammar source audits are reused.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTEXTS = ['full', 'native', 'count_aware']
SCORES = ['primary_entropy_nats', 'first_32_entropy_nats']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_hashes(hashes):
    for name, digest in hashes.items():
        if sha(ROOT / name) != digest:
            raise ValueError('Dependency changed: ' + name)


def mean(values):
    return sum(values) / len(values) if values else None


def validate_score(row):
    if row['status'] == 'blocked_writer':
        if any(k in row for k in SCORES + ['token_records', 'text']):
            raise ValueError('Blocked row contains a generation')
        return
    if row['prompt_sha256'] != hashlib.sha256(row['prompt'].encode()).hexdigest():
        raise ValueError('Prompt hash mismatch')
    tokens = row['token_records']
    if len(tokens) != row['generation_tokens'] or not tokens:
        raise ValueError('Token accounting mismatch')
    if any(t['eos'] for t in tokens[:-1]):
        raise ValueError('EOS before final token')
    if row['finish_reason'] not in ['stop', 'length']:
        raise ValueError('Unexpected finish reason')
    if tokens[-1]['eos'] != (row['finish_reason'] == 'stop'):
        raise ValueError('Finish reason does not match EOS')
    if row['finish_reason'] == 'length' and len(tokens) != 256:
        raise ValueError('Length limit mismatch')
    for t in tokens:
        if not isinstance(t['id'], int) or not isinstance(t['eos'], bool):
            raise ValueError('Invalid token metadata')
        for k in ['entropy_nats', 'nll_nats']:
            if not math.isfinite(t[k]) or t[k] < -1e-6:
                raise ValueError('Invalid score')
    values = [t['entropy_nats'] for t in tokens if not t['eos']]
    complete = row['finish_reason'] == 'stop' and bool(values)
    if row['status'] != ('complete' if complete else 'unscored'):
        raise ValueError('Score status mismatch')
    expected = [mean(values) if complete else None, mean(values[:32]) if len(values) >= 32 else None]
    for key, value in zip(SCORES, expected):
        if (row[key] is None) != (value is None):
            raise ValueError('Missingness mismatch')
        if value is not None and not math.isclose(row[key], value, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError('Derived entropy mismatch')


def selection_pair(native, alternate, score, outcome):
    """No imputation; ties have exact expected utility under a uniform draw."""
    if native.get(score) is None or alternate.get(score) is None:
        return None
    a, b = native[score], alternate[score]
    selected = ['native'] if a < b else ['count_aware'] if b < a else ['native', 'count_aware']
    correctness = {'native': int(native[outcome] == 'correct'), 'count_aware': int(alternate[outcome] == 'correct')}
    return {
        'journal': native['journal'],
        'native_entropy': a, 'count_aware_entropy': b,
        'native_outcome': native[outcome], 'count_aware_outcome': alternate[outcome],
        'selected': selected,
        'selected_correct': mean([correctness[c] for c in selected]),
        'always_native_correct': correctness['native'],
        'uniform_expected_correct': mean(list(correctness.values())),
        'candidate_correctness_differs': len(set(correctness.values())) > 1,
    }


def main():
    inputs = json.loads((ROOT / 'results/pilot-004-inputs.json').read_text())
    journals = [j['id'] for j in inputs]
    downstream_path = ROOT / 'results/pilot-004-answer-format-budget.json'
    downstream = json.loads(downstream_path.read_text())
    verify_hashes(downstream['hashes'])
    result = {'status': 'post hoc development screen; not a trained-method reproduction',
              'unit': 'one fictional journal; same twelve journals used in both models',
              'models': {}, 'hashes': {}}
    dependencies = ['src/analyze_memory_probe.py', 'results/pilot-004-answer-format-budget.json']
    for model in ['qwen', 'phi']:
        prefix = f'results/memory-probe-{model}'
        manifest = json.loads((ROOT / (prefix + '-manifest.json')).read_text())
        verify_hashes(manifest['hashes'])
        path = ROOT / (prefix + '-predictions.jsonl')
        rows = list(map(json.loads, path.read_text().splitlines()))
        index = {(r['journal'], r['context']): r for r in rows}
        expected = {(j, c) for j in journals for c in CONTEXTS}
        if len(rows) != 36 or len(index) != 36 or set(index) != expected:
            raise ValueError('Incomplete or duplicate probe trace')
        ds = downstream['models'][model]
        if sha(ROOT / f'results/pilot-004-{model}-budget-predictions.jsonl') != ds['trace_sha256']:
            raise ValueError('Downstream trace changed')
        readers = {(r['journal'], r['context']): r for r in ds['measurements'] if r['kind'] == 'rate'}
        writers = {(r['journal'], r['context']): r for r in map(json.loads, (ROOT / f'results/pilot-004-{model}-predictions.jsonl').read_text().splitlines()) if r['stage'] == 'writer'}
        audit_path = ROOT / f'results/pilot-004-{model}-claim-audit.json'
        audit = json.loads(audit_path.read_text())
        if audit['hashes']['trace'] != sha(ROOT / f'results/pilot-004-{model}-predictions.jsonl'):
            raise ValueError('Source audit trace changed')
        audits = {(r['journal'], r['context']): r for r in audit['records']}
        measurements = []
        for key, r in index.items():
            if r['model'] != model:
                raise ValueError('Incorrect model')
            validate_score(r)
            blocked = r['context'] != 'full' and writers[key]['status'] != 'valid'
            if blocked != (r['status'] == 'blocked_writer'):
                raise ValueError('Writer validity mismatch')
            record = {k: r.get(k) for k in ['journal', 'context', 'status', 'finish_reason', 'generation_tokens'] + SCORES}
            record['strict_outcome'] = readers[key]['strict_outcome']
            record['format_outcome'] = readers[key]['outcome']
            if not blocked:
                journal = next(j for j in inputs if j['id'] == r['journal'])
                evidence = journal['journal_text'] if r['context'] == 'full' else json.dumps({'facts': writers[key]['facts']}, ensure_ascii=False)
                if hashlib.sha256(evidence.encode()).hexdigest() != r['evidence_sha256']:
                    raise ValueError('Evidence mismatch')
            if key in audits:
                a = audits[key]
                dated = a['claims'] if model == 'qwen' else a['dated_claims']
                counts = [] if model == 'qwen' else a['count_claims']
                record['audit'] = {
                    'dated_claims': len(dated),
                    'false_dated_claims': sum(not c['matches_source'] for c in dated),
                    'count_claims': len(counts),
                    'false_count_claims': sum(not c['matches_source'] for c in counts),
                    'matching_outcome_days': a['distinct_source_days_with_matching_outcome'] if model == 'qwen' else len(a['matching_outcome_days']),
                    'unparsed_residuals': len(a['unparsed_residuals']),
                }
            measurements.append(record)
        by_key = {(r['journal'], r['context']): r for r in measurements}
        comparisons = {}
        for score in SCORES:
            comparisons[score] = {}
            for outcome in ['strict_outcome', 'format_outcome']:
                pairs = [selection_pair(by_key[(j, 'native')], by_key[(j, 'count_aware')], score, outcome) for j in journals]
                present = [r for r in pairs if r is not None]
                comparisons[score][outcome] = {
                    'eligible_journals': len(present),
                    'excluded_journals': [j for j, p in zip(journals, pairs) if p is None],
                    'selected_counts': dict(Counter('/'.join(r['selected']) for r in present)),
                    **{k: sum(r[k] for r in present) for k in ['selected_correct', 'always_native_correct', 'uniform_expected_correct', 'candidate_correctness_differs']},
                    'pairs': present,
                }
        summaries = {c: {'status_counts': dict(Counter(r['status'] for r in measurements if r['context'] == c)),
                        **{s: {'available': sum(r[s] is not None for r in measurements if r['context'] == c),
                               'mean': mean([r[s] for r in measurements if r['context'] == c and r[s] is not None])} for s in SCORES}}
                     for c in CONTEXTS}
        prompt_groups = {}
        for r in rows:
            if 'prompt_sha256' in r:
                prompt_groups.setdefault(r['prompt_sha256'], []).append(r)
        duplicates = []
        for group in prompt_groups.values():
            if len(group) > 1:
                duplicates.append({'cases': [[r['journal'], r['context']] for r in group],
                                   'identical_text': len({r['text'] for r in group}) == 1,
                                   'identical_token_measurements': all(r['token_records'] == group[0]['token_records'] for r in group[1:])})
        result['models'][model] = {'scheduled_records': len(rows), 'actual_generations': sum('token_records' in r for r in rows),
                                  'unique_prompts': len(prompt_groups), 'duplicate_prompt_checks': duplicates,
                                  'generation_seconds': sum(r.get('generation_seconds', 0) for r in rows),
                                  'summaries': summaries, 'comparisons': comparisons, 'measurements': measurements}
        dependencies.extend([prefix + '-manifest.json', prefix + '-predictions.jsonl', str(audit_path.relative_to(ROOT))])
    result['hashes'] = {p: sha(ROOT / p) for p in dependencies}
    output = ROOT / 'results/memory-probe-analysis.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    for model, r in result['models'].items():
        print(model, 'calls', r['actual_generations'], 'seconds', round(r['generation_seconds'], 1))
        print(json.dumps(r['summaries'], indent=2))
        for score, comparisons in r['comparisons'].items():
            for outcome, value in comparisons.items():
                print(score, outcome, {k: v for k, v in value.items() if k != 'pairs'})


if __name__ == '__main__':
    main()
