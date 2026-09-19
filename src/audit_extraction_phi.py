"""Post hoc literal audit for Phi's observed grouped dates and count formats.

This inspects raw output without changing protocol validity or reader inputs.
Residual prose and extra JSON fields remain explicit for separate inspection.
"""
import hashlib
import json
from pathlib import Path
import re
from audit_extraction_claims import literal_claims
from extraction_pilot_data import parse_json_only

ROOT = Path(__file__).resolve().parents[1]
DATES = r'((?:[Dd]ay\s+)?\d+(?:,\s*(?:[Dd]ay\s+)?\d+)*)'


def grouped_claims(text):
    compact = re.match(r'^Day (\d+): (\w+) session (enjoyed|not enjoyed)(?=$|[,.])', text)
    if compact:
        day, activity, outcome = compact.groups()
        return [{'activity': activity.lower(), 'day': int(day), 'positive': outcome == 'enjoyed'}], text[compact.end():].strip(' .')
    match = re.match(r'^(Attended|Enjoyed|Did not enjoy) (\w+) sessions? on [Dd]ays?:?\s+' + DATES, text)
    if not match:
        return literal_claims(text)
    verb, activity, dates = match.groups()
    outcome = None if verb == 'Attended' else verb == 'Enjoyed'
    claims = [{'activity': activity, 'day': int(day), 'positive': outcome}
              for day in re.findall(r'\d+', dates)]
    residual = text[match.end():]
    while True:
        continuation = re.match(r'^(?: and |; |, and )(did not enjoy|enjoyed)(?: them)? on [Dd]ays?:?\s+' + DATES, residual)
        if continuation is None:
            break
        verb, dates = continuation.groups()
        claims.extend({'activity': activity, 'day': int(day), 'positive': verb == 'enjoyed'}
                      for day in re.findall(r'\d+', dates))
        residual = residual[continuation.end():]
    return claims, residual.strip(' .') if claims else text


def count_claims(text):
    triple = re.fullmatch(r'Total (?:visits to )?(\w+) sessions: (\d+), Enjoyed: (\d+), Did not enjoy: (\d+)\.?', text)
    if triple:
        activity, total, positive, negative = triple.groups()
        return [{'activity': activity, 'quantity': q, 'value': int(v)}
                for q, v in [('total', total), ('positive', positive), ('negative', negative)]], ''
    compact = re.fullmatch(r'Attended (\d+) (\w+) sessions, (\d+) not-enjoyed, (\d+) enjoyed\.?', text)
    if compact:
        total, activity, negative, positive = compact.groups()
        return [{'activity': activity, 'quantity': q, 'value': int(v)}
                for q, v in [('total', total), ('positive', positive), ('negative', negative)]], ''
    compact_positive = re.fullmatch(r'Attended (\d+) (\w+) sessions: (\d+) enjoyed, (\d+) not[- ]enjoyed\.?', text)
    if compact_positive:
        total, activity, positive, negative = compact_positive.groups()
        return [{'activity': activity, 'quantity': q, 'value': int(v)}
                for q, v in [('total', total), ('positive', positive), ('negative', negative)]], ''
    claims = []
    unparsed = []
    patterns = [('total', r'Total (\w+) sessions: (\d+)', False),
                ('positive', r'Enjoyed (\d+) (\w+) sessions', True),
                ('negative', r'Did not enjoy (\d+) (\w+) sessions', True),
                ('positive', r'Enjoyed (\w+) sessions: (\d+)', False),
                ('negative', r'Did not enjoy (\w+) sessions: (\d+)', False)]
    for sentence in text.split('.'):
        sentence = sentence.strip()
        if not sentence:
            continue
        for quantity, pattern, value_first in patterns:
            match = re.fullmatch(pattern, sentence)
            if not match:
                continue
            a, b = match.groups()
            activity, value = (b, a) if value_first else (a, b)
            claims.append({'activity': activity, 'quantity': quantity, 'value': int(value)})
            break
        else:
            unparsed.append(sentence)
    return claims, '. '.join(unparsed) if claims else text


def main():
    path = ROOT / 'results/pilot-004-phi-predictions.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if len(rows) != 120:
        raise ValueError('Complete original trace required')
    gold = {j['id']: j for j in json.loads((ROOT / 'results/pilot-004-gold.json').read_text())}
    records = []
    for row in rows:
        if row['stage'] != 'writer':
            continue
        value = parse_json_only(row['text'])
        facts = value.get('facts') if isinstance(value, dict) else None
        if not isinstance(facts, list) or any(not isinstance(f, str) for f in facts):
            facts = []
        source = {e['day']: e for e in gold[row['journal']]['events']}
        true_counts = {a: {'total': 12, 'positive': n, 'negative': 12-n}
                       for a, n in zip(gold[row['journal']]['activities'], gold[row['journal']]['counts'])}
        dated, counts, unparsed = [], [], []
        for index, fact in enumerate(facts):
            events, residual = grouped_claims(fact)
            quantities, residual = count_claims(residual)
            for claim in events:
                target = source.get(claim['day'])
                match = target is not None and target['activity'] == claim['activity'] and (claim['positive'] is None or target['positive'] == claim['positive'])
                dated.append({'fact_index': index, **claim, 'matches_source': match})
            for claim in quantities:
                truth = true_counts.get(claim['activity'], {}).get(claim['quantity'])
                counts.append({'fact_index': index, **claim, 'source_value': truth, 'matches_source': claim['value'] == truth})
            if residual.strip(' .'):
                unparsed.append({'fact_index': index, 'text': residual})
        records.append({'journal': row['journal'], 'context': row['context'],
                        'protocol_writer_status': row['status'], 'raw_facts_inspected': len(facts),
                        'dated_claims': dated, 'count_claims': counts, 'unparsed_residuals': unparsed,
                        'extra_json_fields_unjudged': {k:v for k,v in value.items() if k != 'facts'} if isinstance(value, dict) else {},
                        'matching_outcome_days': sorted({c['day'] for c in dated if c['positive'] is not None and c['matches_source']})})
    result = {'status': 'post hoc limited grammar plus raw extra fields for inspection; not independent annotation',
              'records': records, 'hashes': {'trace': hashlib.sha256(path.read_bytes()).hexdigest(),
              'gold': hashlib.sha256((ROOT / 'results/pilot-004-gold.json').read_bytes()).hexdigest(),
              'code': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'base_parser': hashlib.sha256((ROOT / 'src/audit_extraction_claims.py').read_bytes()).hexdigest(),
              'json_parser': hashlib.sha256((ROOT / 'src/extraction_pilot_data.py').read_bytes()).hexdigest()}}
    (ROOT / 'results/pilot-004-phi-claim-audit.json').write_text(json.dumps(result, indent=2)+'\n')
    for r in records:
        print(r['journal'], r['context'], r['protocol_writer_status'],
              'dated mismatches', sum(not c['matches_source'] for c in r['dated_claims']),
              'count mismatches', sum(not c['matches_source'] for c in r['count_claims']),
              'matching outcome days', len(r['matching_outcome_days']),
              'unparsed', len(r['unparsed_residuals']), 'extra fields', list(r['extra_json_fields_unjudged']))


if __name__ == '__main__':
    main()
