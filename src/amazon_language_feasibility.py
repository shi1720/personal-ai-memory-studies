"""Label-blind support screen for a new language-rich memory experiment.

This is not the protocol for an inference experiment. Eligibility uses identity,
timestamps, distinct items, nonempty history text and catalog coverage. Rating
values and target review content are never used to choose users or report scores.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'data/amazon-language-extension'
HISTORY, TARGETS = 12, 3
EARLIEST_MS = int(datetime(1995, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
LATEST_MS = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def records(path):
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            yield json.loads(line)


def validate_sources(sources, category, root=ROOT):
    base = 'https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/'
    expected = {
        f'data/amazon-language-extension/{category}.jsonl.gz':
            base + f'review_categories/{category}.jsonl.gz',
        f'data/amazon-language-extension/meta_{category}.jsonl.gz':
            base + f'meta_categories/meta_{category}.jsonl.gz',
    }
    if len(sources) != 2 or {s['file'] for s in sources} != set(expected):
        raise ValueError('Acquisition record must identify exactly the two opened category archives')
    for source in sources:
        path = root / source['file']
        if (source['source'] != expected[source['file']]
                or path.stat().st_size != source['bytes']
                or digest(path) != source['sha256']):
            raise ValueError('Archive URL, size or content differs from acquisition record')


def event_projection(record, row):
    user, item, timestamp = record['user_id'], record['parent_asin'], record['timestamp']
    if not isinstance(user, str) or not user or not isinstance(item, str) or not item:
        raise ValueError('Missing identity')
    if (isinstance(timestamp, bool) or not isinstance(timestamp, int)
            or not EARLIEST_MS <= timestamp < LATEST_MS):
        raise ValueError('Timestamp outside the source corpus era in milliseconds')
    if not isinstance(record['text'], str):
        raise ValueError('Review text must be a string')
    # Excludes rating, review title, helpfulness, images and every raw text value.
    return {'user': user, 'item': item, 'timestamp': timestamp,
            'text_characters': len(record['text'].strip()), 'row': row}


def choose_window(events, titled_items, cutoff=None):
    ordered = sorted(events, key=lambda x: (x['timestamp'], x['row']))
    first = {}
    for event in ordered:
        first.setdefault(event['item'], event)
    if len(first) < HISTORY + TARGETS:
        return None, 'fewer_than_15_distinct_items'
    unique = list(first.values())
    if cutoff is None:
        # Initial size screen, not the fixed-date extension design.
        selected = unique[-(HISTORY + TARGETS):]
        history, targets = selected[:HISTORY], selected[HISTORY:]
    else:
        history = [x for x in unique if x['timestamp'] < cutoff][-HISTORY:]
        targets = [x for x in unique if x['timestamp'] > cutoff][:TARGETS]
        if len(history) < HISTORY or len(targets) < TARGETS:
            return None, 'fewer_than_12_prior_and_3_later_items'
        selected = history + targets
    if history[-1]['timestamp'] >= targets[0]['timestamp']:
        return None, 'history_target_boundary_tie'
    if not all(event['item'] in titled_items for event in selected):
        return None, 'missing_catalog_title'
    if not all(event['text_characters'] > 0 for event in history):
        return None, 'empty_history_review'
    return (history, targets), 'eligible'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', choices=['Digital_Music', 'Musical_Instruments'], required=True)
    args = parser.parse_args()
    cutoff = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    source_record = DIRECTORY / ('source-record.json' if args.category == 'Digital_Music'
                                  else 'source-record-Musical_Instruments.json')
    sources = json.loads(source_record.read_text())
    validate_sources(sources, args.category)
    review_path = DIRECTORY / (args.category + '.jsonl.gz')
    meta_path = DIRECTORY / ('meta_' + args.category + '.jsonl.gz')
    memorycd = ROOT / 'data/memorycd/14b934ce3f76f96b6c3c2efa173525f0da62952e/users/cross_domain_users_sampled.jsonl.gz'
    if digest(memorycd) != '8edebfecbd7e05e6461c6dfd86296419eca7e1119c1b534985097b7d0bad390a':
        raise ValueError('Audited-user exclusion source changed')
    excluded = {r['user_id'] for r in records(memorycd)}
    if len(excluded) != 323:
        raise ValueError('Unexpected audited-user cohort')
    counts = Counter()
    for index, record in enumerate(records(review_path)):
        event = event_projection(record, index)
        counts[event['user']] += 1
    enough = {user for user, count in counts.items() if count >= HISTORY + TARGETS}
    candidates = enough - excluded
    events = defaultdict(list)
    for index, record in enumerate(records(review_path)):
        if record['user_id'] in candidates:
            event = event_projection(record, index)
            events[event['user']].append(event)
    titled, seen_meta = set(), set()
    metadata_rows, duplicate_metadata = 0, 0
    for record in records(meta_path):
        metadata_rows += 1
        item = record['parent_asin']
        if item in seen_meta:
            duplicate_metadata += 1
        seen_meta.add(item)
        if isinstance(record['title'], str) and record['title'].strip():
            titled.add(item)
    reasons = Counter()
    private_windows, characters = {}, []
    for user, history in events.items():
        selected, reason = choose_window(history, titled, cutoff=cutoff)
        reasons[reason] += 1
        if selected:
            past, future = selected
            private_windows[user] = {'history_rows': [x['row'] for x in past],
                                     'target_rows': [x['row'] for x in future]}
            characters.append(sum(x['text_characters'] for x in past))
    if duplicate_metadata:
        raise ValueError('Duplicate metadata item keys require explicit resolution before selecting a cohort')
    local = DIRECTORY / (args.category + '-candidate-windows.json')
    local.write_text(json.dumps(private_windows, sort_keys=True, indent=2) + '\n')
    report = {
        'scope': 'Label-blind cohort feasibility; no predictions, tuning or target scoring',
        'category': args.category,
        'source_files': sources,
        'review_rows': sum(counts.values()), 'users': len(counts),
        'users_at_least_15_review_rows': len(enough),
        'previously_audited_users_excluded_from_candidates': len(enough & excluded),
        'metadata_rows': metadata_rows, 'titled_catalog_items': len(titled),
        'eligibility_counts_after_known_user_exclusion': dict(sorted(reasons.items())),
        'eligible_users': len(private_windows),
        'enough_for_60_development_and_200_confirmation_before_context_filter': len(private_windows) >= 260,
        'history_characters_min': min(characters, default=None),
        'history_characters_max': max(characters, default=None),
        'candidate_windows_sha256': digest(local),
        'candidate_windows_redistributed': False,
        'rating_values_used_for_selection': False,
        'prediction_inputs_constructed': False,
        'model_inference_calls': 0,
        'cutoff_utc': '2022-01-01T00:00:00Z',
        'selection': 'Last 12 first-time parent-item events strictly before fixed cutoff and first 3 strictly after; all 15 titled; nonempty earlier review texts',
        'limitations': ['Observed reviews, not randomized exposure or latent preference labels',
            'Catalog is a retrospective snapshot, not point-in-time certified',
            'No context-length or model-format feasibility established yet',
            'Exact parent item IDs deduplicated, not every product alias',
            'Exact review-text duplication is not yet checked by this support screen',
            'Known audited user IDs excluded; identity across unknown source aliases is not established'],
        'code_sha256': digest(Path(__file__)),
    }
    result = ROOT / 'results' / ('amazon-language-feasibility-' + args.category + '.json')
    result.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
