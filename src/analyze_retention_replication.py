"""Validate and summarize every planned additional-model case."""
import argparse
import hashlib
import json
from pathlib import Path
from analyze_retention_pilot import measure, summarize
from retention_pilot_data import parse_selection
ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ['important_plain', 'important_detailed', 'representative_plain',
              'representative_detailed', 'important_antonym', 'archive_negation',
              'archive_antonym', 'proportional_negation', 'proportional_antonym']

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True, choices=['mistral', 'phi'])
    args = p.parse_args()
    prefix = ROOT / 'results' / ('pilot-003-' + args.model)
    trace_path = Path(str(prefix) + '-predictions.jsonl')
    trace = [json.loads(line) for line in trace_path.read_text().splitlines()]
    manifest = json.loads(Path(str(prefix) + '-manifest.json').read_text())
    for path, digest in manifest['hashes'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Changed dependency: ' + path)
    journals = {j['id']: j for j in json.loads((ROOT / 'results/pilot-003-journals.json').read_text())}
    expected = {(j, c) for j in journals for c in CONDITIONS}
    keys = [(r['journal'], r['condition']) for r in trace]
    if len(keys) != 108 or set(keys) != expected:
        raise ValueError('Complete unique trace required')
    measured = []
    for row in trace:
        journal = journals[row['journal']]
        parsed = parse_selection(row['text'], {e['id'] for e in journal['events']})
        if parsed != row['selection'] or row['valid'] != (parsed is not None):
            raise ValueError('Parsing inconsistency')
        if hashlib.sha256(row['prompt'].encode()).hexdigest() != row['prompt_sha256']:
            raise ValueError('Prompt mismatch')
        if row['prompt_tokens'] > 4096 or row['generation_tokens'] > 160:
            raise ValueError('Budget violation')
        positive = sum(e['positive'] for e in journal['events'] if parsed is not None and e['id'] in parsed)
        measured.append({'journal': row['journal'], 'condition': row['condition'],
                         'selected_positive': positive if parsed is not None else None,
                         'metrics': measure(journal, parsed) if parsed is not None else None})
    summaries = {}
    for condition in CONDITIONS:
        rows = [r for r in measured if r['condition'] == condition]
        s = summarize(rows)
        s['selected_positive'] = sum(r['selected_positive'] for r in rows if r['metrics'] is not None)
        s['selected_total_valid'] = 6 * s['valid_cases']
        summaries[condition] = s
    result = {'status': 'same-journal exploratory model check, not independent confirmation',
              'model': args.model, 'adapter': manifest['adapter'], 'actual_calls': len(trace),
              'trace_sha256': hashlib.sha256(trace_path.read_bytes()).hexdigest(),
              'analysis_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'reader_seconds': sum(r['reader_seconds'] for r in trace),
              'total_prompt_tokens': sum(r['prompt_tokens'] for r in trace),
              'total_generation_tokens': sum(r['generation_tokens'] for r in trace),
              'summaries': summaries, 'measurements': measured,
              'invalid_outputs': [{k: r[k] for k in ['journal', 'condition', 'text', 'finish_reason', 'generation_tokens']} for r in trace if not r['valid']]}
    Path(str(prefix) + '-analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(summaries, indent=2))
if __name__ == '__main__':
    main()
