"""Post hoc fence-only diagnostic; never replaces frozen strict results."""
import hashlib
import json
from pathlib import Path
import re
import statistics
from analyze_retention_pilot import measure, summarize
from retention_pilot_data import parse_selection
ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ['important_plain', 'important_detailed', 'representative_plain',
              'representative_detailed', 'important_antonym', 'archive_negation',
              'archive_antonym', 'proportional_negation', 'proportional_antonym']

def parse_fenced_selection(text, allowed):
    strict = parse_selection(text, allowed)
    if strict is not None:
        return strict, 'strict'
    matched = re.fullmatch(r'\s*```(?:json)?\s*\n([\s\S]*?)\n```\s*', text)
    if matched is None:
        return None, 'invalid'
    parsed = parse_selection(matched.group(1), allowed)
    return (parsed, 'fence_only') if parsed is not None else (None, 'invalid')

def qwen_rows():
    rows = []
    for line in (ROOT / 'results/pilot-003-predictions.jsonl').read_text().splitlines():
        r = json.loads(line)
        r['condition'] = r['writer'] + ('_detailed' if r['detailed'] else '_plain')
        rows.append(r)
    for line in (ROOT / 'results/pilot-003-controls-predictions.jsonl').read_text().splitlines():
        r = json.loads(line)
        if r['writer'] == 'important' and r['wording'] == 'negation':
            continue
        r['condition'] = r['writer'] + '_' + r['wording']
        rows.append(r)
    return rows

def main():
    journals = {j['id']: j for j in json.loads((ROOT / 'results/pilot-003-journals.json').read_text())}
    output = {'status': 'post hoc syntax-only sensitivity; strict results remain primary', 'models': {}}
    traces = {'qwen': qwen_rows()}
    for model in ['mistral', 'phi']:
        path = ROOT / 'results' / f'pilot-003-{model}-predictions.jsonl'
        traces[model] = [json.loads(line) for line in path.read_text().splitlines()]
    expected = {(j, c) for j in journals for c in CONDITIONS}
    for model, rows in traces.items():
        if len(rows) != 108 or {(r['journal'], r['condition']) for r in rows} != expected:
            raise ValueError('Complete unique model traces required')
        measured = []
        for r in rows:
            j = journals[r['journal']]
            selection, status = parse_fenced_selection(r['text'], {e['id'] for e in j['events']})
            measured.append({'journal': j['id'], 'condition': r['condition'], 'parse_status': status,
                             'selection': selection,
                             'metrics': measure(j, selection) if selection is not None else None,
                             'selected_positive': sum(e['positive'] for e in j['events'] if selection is not None and e['id'] in selection)})
        summaries = {}
        for c in CONDITIONS:
            subset = [r for r in measured if r['condition'] == c]
            s = summarize(subset)
            s['parse_counts'] = {k: sum(r['parse_status'] == k for r in subset) for k in ['strict', 'fence_only', 'invalid']}
            s['selected_positive'] = sum(r['selected_positive'] for r in subset)
            s['selected_total_valid'] = 6 * s['valid_cases']
            summaries[c] = s
        pairs = {}
        for writer in ['important', 'representative']:
            effects = []
            for jid in journals:
                by_condition = {r['condition']: r for r in measured if r['journal'] == jid}
                a, b = [by_condition[writer + '_' + variant] for variant in ['plain', 'detailed']]
                if a['metrics'] is None or b['metrics'] is None:
                    continue
                complete = not a['metrics']['missing_activities'] and not b['metrics']['missing_activities']
                effects.append({'journal': jid, 'complete_activity_pair': complete,
                    'detail_recall_delta': b['metrics']['detail_event_recall'] - a['metrics']['detail_event_recall'],
                    'positive_fraction_delta': (b['selected_positive'] - a['selected_positive']) / 6,
                    'mae_delta_available': b['metrics']['mae_available'] - a['metrics']['mae_available']})
            complete_effects = [e for e in effects if e['complete_activity_pair']]
            pairs[writer] = {'valid_pairs': len(effects), 'complete_activity_pairs': len(complete_effects),
                'mean_detail_recall_delta': statistics.mean(e['detail_recall_delta'] for e in effects) if effects else None,
                'mean_positive_fraction_delta': statistics.mean(e['positive_fraction_delta'] for e in effects) if effects else None,
                'mean_mae_delta_complete_activity_pairs': statistics.mean(e['mae_delta_available'] for e in complete_effects) if complete_effects else None,
                'effects': effects}
        output['models'][model] = {'summaries': summaries, 'paired_rendering': pairs, 'measurements': measured}
    files = ['src/retention_format_sensitivity.py', 'src/analyze_retention_pilot.py',
             'docs/pilot-003-format-sensitivity.md', 'results/pilot-003-journals.json',
             'results/pilot-003-predictions.jsonl', 'results/pilot-003-controls-predictions.jsonl',
             'results/pilot-003-mistral-predictions.jsonl', 'results/pilot-003-phi-predictions.jsonl']
    output['input_hashes'] = {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files}
    (ROOT / 'results/pilot-003-format-sensitivity.json').write_text(json.dumps(output, indent=2) + '\n')
    for model, results in output['models'].items():
        print(model)
        for c, s in results['summaries'].items():
            print(c, s['parse_counts'], 'MAE', round(s['mean_journal_mae_available'], 4) if s['valid_cases'] else None,
                  'bias', round(s['mean_journal_signed_bias_available'], 4) if s['valid_cases'] else None)
if __name__ == '__main__':
    main()
