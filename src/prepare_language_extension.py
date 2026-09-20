"""Prepare outcome-isolated inputs after the separate cohort-support screen.

No model inference, prediction scoring or target-label materialization. Existing
prepared files cannot silently change. Rules are documented before execution in
docs/language-extension-input-protocol.md.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from amazon_language_feasibility import ROOT, DIRECTORY, digest, records, validate_sources
from language_extension_inputs import build_inputs, writer_history, reader_query

CATEGORY = 'Musical_Instruments'
CUTOFF = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
MODELS = {'qwen': 'qwen3-4b-instruct-2507-4bit', 'phi': 'phi-4-4bit'}
MAX_HISTORY_TOKENS = 6144
MAX_READER_TOKENS = 12288


def case_id(user):
    return hashlib.sha256(('review-history-extension-v1:' + user).encode()).hexdigest()


def partition(users):
    users = list(users)
    if len(users) != len(set(users)):
        raise ValueError('User identifiers are not unique')
    if len(users) < 320:
        raise ValueError('Need 60 development, 200 confirmation and at least 60 donor users')
    ordered = sorted(users, key=case_id)
    return {'development': ordered[:60], 'reserved_confirmation': ordered[60:260],
            'donors': ordered[260:]}


def project_record(record, history):
    value = {k: record[k] for k in ('user_id', 'parent_asin', 'timestamp')}
    if history:
        value.update(text=record['text'], rating=record['rating'])
    return value


def language_reason(history):
    counts = [len(r['text'].split()) for r in history]
    if any(n < 5 for n in counts):
        return 'review_under_5_words'
    if sum(counts) < 240:
        return 'history_under_240_words'
    texts = [' '.join(r['text'].split()).casefold() for r in history]
    if len(texts) != len(set(texts)):
        return 'duplicate_history_text'
    return None


def token_counts(instance, tokenizers):
    evidence = writer_history(instance)
    query = reader_query(instance, evidence)
    result = {}
    for name, tokenizer in tokenizers.items():
        ids = tokenizer.apply_chat_template(query, tokenize=True,
                                            add_generation_prompt=True, return_dict=False)
        if not isinstance(ids, list) or any(not isinstance(i, int) for i in ids):
            raise ValueError('Chat tokenizer must return a flat list of token IDs')
        result[name] = {'history_payload':len(tokenizer.encode(evidence, add_special_tokens=False)),
                        'full_history_reader':len(ids)}
    return result


def write_once(path, value):
    content = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError('Refusing to replace different prepared data: ' + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_bytes(content)
        temporary.replace(path)
    return digest(path)


def load_tokenizers():
    from transformers import AutoTokenizer
    tokenizers, hashes = {}, {}
    for name, directory in MODELS.items():
        manifest_name = 'local-model-manifest.json' if name == 'qwen' else 'phi-model-manifest.json'
        manifest = json.loads((ROOT / 'references' / manifest_name).read_text())
        model = ROOT / 'models' / directory
        expected = {row['name']:row['sha256'] for row in manifest['files']}
        files = [p for p in model.iterdir() if p.is_file() and
                 (p.suffix in ('.json', '.jinja') or p.name in ('merges.txt', 'vocab.txt'))]
        for path in files:
            if path.name not in expected or digest(path) != expected[path.name]:
                raise ValueError('Tokenizer/config file differs from pinned model: ' + path.name)
        hashes[name] = {p.name:digest(p) for p in sorted(files)}
        tokenizers[name] = AutoTokenizer.from_pretrained(model, local_files_only=True,
                                                        trust_remote_code=False)
    return tokenizers, hashes


def main():
    report_path = ROOT / 'results/amazon-language-feasibility-Musical_Instruments.json'
    screen = json.loads(report_path.read_text())
    if screen['category'] != CATEGORY or screen['code_sha256'] != digest(ROOT / 'src/amazon_language_feasibility.py'):
        raise ValueError('Support report does not match current source')
    validate_sources(screen['source_files'], CATEGORY)
    path = DIRECTORY / (CATEGORY + '-candidate-windows.json')
    if digest(path) != screen['candidate_windows_sha256']:
        raise ValueError('Candidate window mapping changed')
    windows = json.loads(path.read_text())
    if len(windows) != screen['eligible_users']:
        raise ValueError('Candidate count mismatch')
    row_roles = {}
    for user, window in windows.items():
        for key, role in [('history_rows', True), ('target_rows', False)]:
            for row in window[key]:
                if row in row_roles:
                    raise ValueError('Source row assigned more than once')
                row_roles[row] = (user, role)
    selected = {}
    for row, record in enumerate(records(DIRECTORY / (CATEGORY + '.jsonl.gz'))):
        if row not in row_roles:
            continue
        user, role = row_roles[row]
        if record['user_id'] != user:
            raise ValueError('Row belongs to a different user')
        selected[row] = project_record(record, role)
    if set(selected) != set(row_roles):
        raise ValueError('Some selected rows are absent from the archive')
    needed = {r['parent_asin'] for r in selected.values()}
    metadata = {}
    for record in records(DIRECTORY / ('meta_' + CATEGORY + '.jsonl.gz')):
        if record['parent_asin'] in needed:
            if record['parent_asin'] in metadata:
                raise ValueError('Duplicate metadata key')
            metadata[record['parent_asin']] = {'title':record['title'], 'features':record.get('features', [])}
    tokenizers, tokenizer_hashes = load_tokenizers()
    reasons, eligible, counts = Counter(), {}, {}
    for user, window in windows.items():
        history = [selected[row] for row in window['history_rows']]
        targets = [selected[row] for row in window['target_rows']]
        reason = language_reason(history)
        if reason:
            reasons[reason] += 1
            continue
        instance = build_inputs(history, targets, metadata, CUTOFF)
        sizes = token_counts(instance, tokenizers)
        if any(s['history_payload'] > MAX_HISTORY_TOKENS or
               s['full_history_reader'] > MAX_READER_TOKENS for s in sizes.values()):
            reasons['context_budget'] += 1
            continue
        reasons['eligible'] += 1
        eligible[user], counts[user] = instance, sizes
    result = {
        'scope':'Input-only preparation; no model inference or target scoring',
        'status':'prepared' if len(eligible) >= 320 else 'insufficient_cohort',
        'candidate_users':len(windows), 'eligibility_counts':dict(reasons),
        'target_outcomes_used':False, 'target_labels_materialized':False,
        'source_objects_parsed':True,
        'review_text_truncated':False,
        'tokenizer_hashes':tokenizer_hashes,
        'dependencies':{p:digest(ROOT / p) for p in [
            'docs/language-extension-input-protocol.md', 'src/prepare_language_extension.py',
            'src/language_extension_inputs.py', 'src/amazon_language_feasibility.py',
            'results/amazon-language-feasibility-Musical_Instruments.json']},
        'limits':{'history_payload_tokens':MAX_HISTORY_TOKENS, 'reader_chat_tokens':MAX_READER_TOKENS},
        'writer_full_request_budget_checked':False,
        'inference_protocol_frozen':False,
    }
    if len(eligible) >= 320:
        groups = partition(eligible)
        directory = ROOT / 'data/language-extension-v1'
        files = {}
        for group, users in groups.items():
            if group == 'donors':
                data = {case_id(u):{'history':eligible[u]['history']} for u in users}
            else:
                data = {case_id(u):eligible[u] for u in users}
            path = directory / (group + '-inputs.json')
            files[str(path.relative_to(ROOT))] = write_once(path, data)
        path = directory / 'source-mapping.json'
        files[str(path.relative_to(ROOT))] = write_once(path,
            {case_id(u):{'user_id':u, 'group':g, **windows[u]} for g, us in groups.items() for u in us})
        result['groups'] = {g:[case_id(u) for u in us] for g, us in groups.items()}
        result['input_file_hashes'] = files
        result['token_counts'] = {case_id(u):counts[u] for u in sorted(eligible, key=case_id)}
    output = ROOT / 'results/language-extension-input-preparation.json'
    write_once(output, result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('groups','token_counts','tokenizer_hashes')}, indent=2))


if __name__ == '__main__':
    main()
