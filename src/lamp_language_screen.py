"""Development-only LaMP-3 input audit, without targets or model inference.

Only a bounded prefix of the official training questions is acquired. The prefix
is not a random sample, a user split, or a complete-source checksum. Raw text
stays under ignored data/. No development/test questions or gold files are read.
"""
import argparse
from collections import defaultdict
import codecs
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://ciir.cs.umass.edu/downloads/LaMP/LaMP_3/train/train_questions.json'
DIRECTORY = ROOT / 'data/lamp-language-screen'
MARKER = 'review: '


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_prefix(stream, count=64, limit=50 * 1024 * 1024, chunk_size=65536):
    """Read complete JSON array objects; never consume the full 3GB by default."""
    if count <= 0 or limit <= 0 or chunk_size <= 0:
        raise ValueError('Positive limits required')
    decoder = json.JSONDecoder()
    utf = codecs.getincrementaldecoder('utf-8')()
    buffer, opened, separator = '', False, False
    rows, size, digest = [], 0, hashlib.sha256()
    while len(rows) < count:
        chunk = stream.read(min(chunk_size, limit - size + 1))
        if not chunk:
            raise ValueError('Incomplete prefix: EOF before requested complete records')
        size += len(chunk)
        if size > limit:
            raise ValueError('Download exceeds bounded screen limit')
        digest.update(chunk)
        buffer += utf.decode(chunk)
        if not opened:
            buffer = buffer.lstrip()
            if not buffer:
                continue
            if not buffer.startswith('['):
                raise ValueError('Expected a JSON array')
            buffer, opened = buffer[1:], True
        while len(rows) < count:
            buffer = buffer.lstrip()
            if not buffer:
                break
            if separator:
                if buffer[0] != ',':
                    raise ValueError('Expected comma between records')
                buffer, separator = buffer[1:].lstrip(), False
            try:
                row, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                break
            if not isinstance(row, dict):
                raise ValueError('Each record must be an object')
            rows.append(row)
            buffer, separator = buffer[end:], True
    return rows, size, digest.hexdigest()


def normalized(text):
    return ' '.join(text.split()).casefold()


def text_hash(text):
    return sha(normalized(text).encode())


def target_text(row):
    if MARKER not in row['input']:
        raise ValueError('Unrecognized question format')
    return row['input'].split(MARKER, 1)[1]


def summarize(values):
    import numpy as np
    return dict(zip(['min', 'median', 'p90', 'max'],
                    map(float, np.quantile(values, [0, .5, .9, 1]))))


def audit(rows, tokenizer):
    # IDs are opaque task identifiers, not assumed independent user IDs.
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate task IDs')
    owners, profile_signatures, profiles = defaultdict(set), [], []
    scored_texts = defaultdict(set)
    for index, row in enumerate(rows):
        profile = row['profile']
        if not profile:
            raise ValueError('Empty history')
        pairs = []
        for item in profile:
            score = int(item['score'])
            if str(score) != str(item['score']) or score not in range(1, 6):
                raise ValueError('Invalid history rating')
            key = text_hash(item['text'])
            owners[key].add(index)
            scored_texts[key].add(score)
            pairs.append((key, score))
        profiles.append(pairs)
        profile_signatures.append(sha(json.dumps(sorted(pairs)).encode()))
    overlaps = defaultdict(int)
    for indices in owners.values():
        ordered = sorted(indices)
        for pos, left in enumerate(ordered):
            for right in ordered[pos + 1:]:
                overlaps[(left, right)] += 1
    output = []
    # A lexical flag is not verified label leakage or a semantic rating parser.
    explicit = re.compile(r'\b(?:[1-5](?:\.0)?|one|two|three|four|five)\s+'
                          r'(?:stars?\b|out of (?:five|5)\b)', re.I)
    for index, row in enumerate(rows):
        profile = row['profile']
        target = target_text(row)
        key = text_hash(target)
        serialized = json.dumps([{'review': p['text'], 'rating': p['score']}
                                 for p in profile], ensure_ascii=False)
        tokens = len(tokenizer.encode(serialized, add_special_tokens=False))
        output.append({
            'prefix_index': index,
            'task_id_sha256': sha(row['id'].encode()),
            'history_records': len(profile),
            'history_characters': sum(len(p['text']) for p in profile),
            'history_payload_tokens': tokens,
            'target_review_tokens': len(tokenizer.encode(target, add_special_tokens=False)),
            'duplicate_history_texts': len(profile) - len(set(k for k, _ in profiles[index])),
            'target_exactly_in_own_history': index in owners.get(key, set()),
            'target_exactly_in_other_histories': len(owners.get(key, set()) - {index}),
            'target_has_star_expression': bool(explicit.search(target)),
        })
    return {
        'scope': 'Input feasibility audit of first 64 training records; not a performance experiment',
        'records': len(rows),
        'no_gold_files_read': True,
        'no_dev_or_test_files_read': True,
        'no_model_inference': True,
        'independent_user_identity_established': False,
        'payload_token_note': 'Qwen tokenizer on JSON review/rating list; excludes chat and writer instructions',
        'history_records': summarize([x['history_records'] for x in output]),
        'history_payload_tokens': summarize([x['history_payload_tokens'] for x in output]),
        'target_review_tokens': summarize([x['target_review_tokens'] for x in output]),
        'histories_over_32768_payload_tokens': sum(x['history_payload_tokens'] > 32768 for x in output),
        'histories_over_131072_payload_tokens': sum(x['history_payload_tokens'] > 131072 for x in output),
        'duplicate_profile_signatures': len(rows) - len(set(profile_signatures)),
        'pairs_sharing_normalized_history_text': len(overlaps),
        'maximum_shared_history_texts_between_pair': max(overlaps.values(), default=0),
        'history_texts_with_conflicting_ratings_across_sample': sum(len(x) > 1 for x in scored_texts.values()),
        'targets_exactly_in_own_history': sum(x['target_exactly_in_own_history'] for x in output),
        'targets_exactly_in_other_histories': sum(x['target_exactly_in_other_histories'] > 0 for x in output),
        'targets_with_star_expression': sum(x['target_has_star_expression'] for x in output),
        'star_expression_note': 'Lexical flag only, not validated target-label disclosure',
        'rows': output,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    sample = DIRECTORY / 'train-prefix-64.json'
    record = DIRECTORY / 'download-record.json'
    if args.fetch and not sample.exists():
        DIRECTORY.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(SOURCE, timeout=60) as response:
            rows, size, digest = read_prefix(response)
        sample.write_text(json.dumps(rows, ensure_ascii=False) + '\n')
        record.write_text(json.dumps({'source': SOURCE,
            'selection': 'first 64 complete array elements; development-only convenience screen',
            'bytes_read': size, 'downloaded_prefix_sha256': digest,
            'complete_source_file_hashed': False, 'records': 64,
            'sample_sha256': sha(sample.read_bytes())}, indent=2) + '\n')
    provenance = json.loads(record.read_text())
    if provenance['source'] != SOURCE or provenance['sample_sha256'] != sha(sample.read_bytes()):
        raise ValueError('Source record or stored sample changed')
    rows = json.loads(sample.read_text())
    if len(rows) != 64:
        raise ValueError('Expected exactly 64 development records')
    from transformers import AutoTokenizer
    tokenizer_dir = ROOT / 'models/qwen3-4b-instruct-2507-4bit'
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir, local_files_only=True,
                                             trust_remote_code=False)
    result = audit(rows, tokenizer)
    result['provenance'] = provenance
    result['tokenizer_files'] = {p.name: sha(p.read_bytes()) for p in tokenizer_dir.glob('*token*json')}
    result['code_sha256'] = sha(Path(__file__).read_bytes())
    path = ROOT / 'results/lamp-language-input-screen.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2))


if __name__ == '__main__':
    main()
