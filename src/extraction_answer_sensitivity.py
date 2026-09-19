"""Separately score an exact letter-plus-displayed-option format, post hoc."""
import argparse
import hashlib
import json
from pathlib import Path
from extraction_pilot_data import parse_answer, parse_json_only
from analyze_extraction_pilot import aggregate, classify

ROOT = Path(__file__).resolve().parents[1]
CONTEXTS = ['full', 'native', 'count_aware', 'ledger']


def parse_option_answer(text, options):
    strict = parse_answer(text, set(options))
    if strict is not None:
        return strict
    value = parse_json_only(text)
    if not isinstance(value, dict) or set(value) != {'reason', 'answer'}:
        return None
    if any(not isinstance(v, str) for v in value.values()):
        return None
    for letter, option in options.items():
        if value['answer'] == letter + '. ' + option:
            return {'reason': value['reason'], 'answer': letter}
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--phase', choices=['initial', 'budget'], default='initial')
    args = p.parse_args()
    inputs = {j['id']: j for j in json.loads((ROOT/'results/pilot-004-inputs.json').read_text())}
    gold = {j['id']: {a['kind']: a for a in j['answers']} for j in json.loads((ROOT/'results/pilot-004-gold.json').read_text())}
    models = {}
    for model in ['qwen', 'phi']:
        prefix = f'pilot-004-{model}' + ('-budget' if args.phase == 'budget' else '')
        path = ROOT/'results'/f'{prefix}-predictions.jsonl'
        analysis_path = ROOT/'results'/f'{prefix}-analysis.json'
        if not analysis_path.exists():
            raise ValueError(f'Complete strict analysis required: {analysis_path.name}')
        analysis = json.loads(analysis_path.read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != analysis['hashes']['trace']:
            raise ValueError('Trace differs from completed strict analysis')
        rows = [r for r in map(json.loads, path.read_text().splitlines()) if r['stage'] == 'reader']
        kinds = ['rate', 'event'] if args.phase == 'initial' else ['rate']
        expected = {(j, c, k) for j in inputs for c in CONTEXTS for k in kinds}
        if len(rows) != len(expected) or {(r['journal'], r['context'], r['question_kind']) for r in rows} != expected:
            raise ValueError('Incomplete or duplicate reader cases')
        measured = []
        for row in rows:
            revised = dict(row)
            recovered = False
            if row['status'] != 'blocked_writer':
                query = next(q for q in inputs[row['journal']]['queries'] if q['kind'] == row['question_kind'])
                parsed = parse_option_answer(row['text'], query['options'])
                recovered = row['status'] == 'invalid' and parsed is not None
                revised.update(status='valid' if parsed is not None else 'invalid', parsed_answer=parsed)
                if row['status'] == 'valid' and parsed != row['parsed_answer']:
                    raise ValueError('Changed a strictly valid answer')
            truth = gold[row['journal']][row['question_kind']]
            measured.append({'journal': row['journal'], 'context': row['context'], 'kind': row['question_kind'],
                             'outcome': classify(revised, truth), 'strict_outcome': classify(row, truth), 'recovered': recovered})
        summaries = {c: {k: aggregate([r for r in measured if r['context'] == c and r['kind'] == k]) for k in kinds} for c in CONTEXTS}
        paired = {}
        for c in CONTEXTS[1:]:
            paired[c] = {}
            for kind in kinds:
                pairs = []
                for j in inputs:
                    full = next(r for r in measured if r['journal'] == j and r['context'] == 'full' and r['kind'] == kind)
                    compressed = next(r for r in measured if r['journal'] == j and r['context'] == c and r['kind'] == kind)
                    pairs.append({'journal': j, 'full': full['outcome'], 'compressed': compressed['outcome']})
                paired[c][kind] = {'full_correct': sum(r['full'] == 'correct' for r in pairs),
                    'retained_correct': sum(r['full'] == r['compressed'] == 'correct' for r in pairs),
                    'losses': {o: sum(r['full'] == 'correct' and r['compressed'] == o for r in pairs) for o in ['wrong', 'abstained', 'invalid', 'blocked_writer']},
                    'reverse_gains': sum(r['full'] != 'correct' and r['compressed'] == 'correct' for r in pairs), 'pairs': pairs}
        models[model] = {'recovered': sum(r['recovered'] for r in measured), 'summaries': summaries,
                         'paired': paired, 'measurements': measured, 'trace_sha256': analysis['hashes']['trace']}
    result = {'status': 'post hoc exact-option format sensitivity, not primary analysis', 'phase': args.phase,
              'models': models, 'hashes': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [
                  'src/extraction_answer_sensitivity.py', 'src/extraction_pilot_data.py', 'src/analyze_extraction_pilot.py',
                  'docs/pilot-004-answer-format-sensitivity.md', 'results/pilot-004-inputs.json', 'results/pilot-004-gold.json']}}
    out = ROOT/'results'/f'pilot-004-answer-format-{args.phase}.json'
    out.write_text(json.dumps(result, indent=2)+'\n')
    for model, value in models.items():
        print(model, 'recovered', value['recovered'])
        for c, summary in value['summaries'].items():
            print(c, {k: {o: s[o] for o in ['correct', 'wrong', 'abstained', 'invalid', 'blocked_writer']} for k, s in summary.items()})


if __name__ == '__main__':
    main()
