"""Materialize only development target labels after a complete inference gate.

Importing this module never opens source data. The command is intentionally
separate from inference and requires all three completed development stages.
Raw JSON objects are parsed while streaming, but rating fields are accessed
only for the exact, validated development target rows. Reserved labels are
never selected, projected, or materialized.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from amazon_language_feasibility import digest, records, validate_sources
from language_extension_inputs import catalog_input, valid_rating

ROOT = Path(__file__).resolve().parents[1]
CATEGORY = 'Musical_Instruments'
CUTOFF = int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
LOWER = int(datetime(1995, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
UPPER = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
ARMS = ('no_history', 'full_history', 'native_qwen', 'summary_qwen',
        'native_phi', 'summary_phi', 'bm25_history')
REQUIRED_DEPENDENCIES = ('docs/language-development-protocol.md',
                         'src/language_precision_planning.py',
                         'src/language_development_labels.py',
                         'src/language_development_metrics.py',
                         'results/language-extension-input-preparation.json')
DEVELOPMENT_INPUTS = ('data/language-extension-v1/development-inputs.json',
                      'data/language-extension-v1/source-mapping.json')


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def checked_path(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError('Expected a repository-relative path')
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Dependency path escapes the repository')
    return path


def verify_hashes(root, mapping):
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError('Expected a nonempty dependency hash mapping')
    for name, expected in mapping.items():
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError('Invalid dependency digest')
        if digest(checked_path(root, name)) != expected:
            raise ValueError('Dependency changed: ' + name)


def development_input_hashes(mapping):
    """Select only authorized input files, never open reserved or donor inputs."""
    if not set(DEVELOPMENT_INPUTS).issubset(mapping):
        raise ValueError('Prepared development inputs and source mapping must be hash-pinned')
    return {name: mapping[name] for name in DEVELOPMENT_INPUTS}


def verify_inference_gate(report, manifest, development_cases, raw_hashes):
    """Validate complete logical coverage without reading any target labels."""
    cases = list(development_cases)
    if len(cases) != 60 or len(set(cases)) != 60:
        raise ValueError('Exactly 60 unique development cases are required')
    if report.get('phase') != 'development' or report.get('complete') is not True:
        raise ValueError('Inference must be complete and development-only')
    if report.get('cases') != cases or manifest.get('cases') != cases:
        raise ValueError('Inference case order differs from the prepared development split')
    if report.get('stage_status') != {s: 'completed' for s in ('qwen_base', 'phi', 'qwen_cross')}:
        raise ValueError('All three development stages must be completed')
    if report.get('raw_file_hashes') != raw_hashes or not raw_hashes:
        raise ValueError('Raw inference hashes must be supplied and verified')
    readers = report.get('readers', [])
    cells = [(r['case_id'], r['reader'], r['arm']) for r in readers]
    expected = {(c, m, a) for c in cases for m in ('qwen', 'phi') for a in ARMS}
    if len(cells) != len(expected) or set(cells) != expected:
        raise ValueError('Reader grid is incomplete or duplicated')
    for row in readers:
        if raw_hashes.get(row['file']) != row['raw_sha256']:
            raise ValueError('Reader file is not covered by verified raw hashes')
    writers = report.get('writers', [])
    cells = [(r['case_id'], r['model']) for r in writers]
    expected = {(c, m) for c in cases for m in ('qwen', 'phi')}
    if len(cells) != len(expected) or set(cells) != expected:
        raise ValueError('Writer grid is incomplete or duplicated')
    for row in writers:
        for kind in ('native', 'summary'):
            if raw_hashes.get(row[kind + '_file']) != row[kind + '_sha256']:
                raise ValueError('Writer file is not covered by verified raw hashes')


def project_window_identities(indexed_records, mappings, inputs, cutoff=CUTOFF):
    """First pass over selected windows; no rating field is ever accessed."""
    if set(mappings) != set(inputs) or not mappings:
        raise ValueError('Selected mappings and prepared inputs must match exactly')
    roles = {}
    for case, mapping in mappings.items():
        if mapping.get('group') != 'development':
            raise ValueError('Only development source mappings are allowed')
        if not isinstance(mapping.get('user_id'), str) or not mapping['user_id']:
            raise ValueError('Missing source user identity')
        if len(mapping['history_rows']) != 12 or len(mapping['target_rows']) != 3:
            raise ValueError('Each development case requires 12 history and 3 target rows')
        if len(inputs[case]['history']) != 12 or len(inputs[case]['targets']) != 3:
            raise ValueError('Prepared input shape changed')
        for kind in ('history', 'target'):
            for position, row in enumerate(mapping[kind + '_rows']):
                if type(row) is not int or row < 0 or row in roles:
                    raise ValueError('Invalid or duplicate source row mapping')
                roles[row] = (case, kind, position)
    selected = {}
    for row, record in indexed_records:
        if row not in roles:
            continue
        if row in selected:
            raise ValueError('Source stream repeats a selected row')
        case, kind, position = roles[row]
        user, item, timestamp = (record['user_id'], record['parent_asin'], record['timestamp'])
        if user != mappings[case]['user_id']:
            raise ValueError('Source row belongs to the wrong user')
        if not isinstance(item, str) or not item:
            raise ValueError('Missing product identity')
        if type(timestamp) is not int or not LOWER <= timestamp < UPPER:
            raise ValueError('Invalid source-era timestamp')
        if (kind == 'history' and timestamp >= cutoff) or (kind == 'target' and timestamp <= cutoff):
            raise ValueError('Source row violates chronological cutoff')
        if kind == 'history':
            expected_date = inputs[case]['history'][position]['review_date_utc']
            if datetime.fromtimestamp(timestamp / 1000, timezone.utc).isoformat() != expected_date:
                raise ValueError('Historical source date differs from prepared input')
        selected[row] = {'source_row': row, 'user_id': user,
                         'parent_asin': item, 'timestamp': timestamp}
    if set(selected) != set(roles):
        raise ValueError('Selected source rows are missing')
    output = {}
    for case, mapping in mappings.items():
        history = [selected[row] for row in mapping['history_rows']]
        targets = [selected[row] for row in mapping['target_rows']]
        if len({r['parent_asin'] for r in history + targets}) != 15:
            raise ValueError('Repeated product identity in a selected window')
        for group in (history, targets):
            chronology = [(r['timestamp'], r['source_row']) for r in group]
            if chronology != sorted(chronology):
                raise ValueError('Source mapping is not in chronological row order')
        output[case] = {'history': history, 'targets': targets}
    return output


def verify_catalog(indexed_metadata, windows, inputs):
    """Check selected products against the exact prepared catalog payload."""
    needed = {r['parent_asin'] for w in windows.values() for k in ('history', 'targets') for r in w[k]}
    products = {}
    for record in indexed_metadata:
        item = record['parent_asin']
        if item not in needed:
            continue
        if item in products:
            raise ValueError('Duplicate selected catalog product')
        products[item] = catalog_input(record)
    if set(products) != needed:
        raise ValueError('Selected catalog products are missing')
    for case, window in windows.items():
        for kind in ('history', 'targets'):
            for source, prepared in zip(window[kind], inputs[case][kind]):
                if products[source['parent_asin']] != prepared['product']:
                    raise ValueError('Catalog product differs from prepared input')


def project_development_labels(indexed_records, windows):
    """Second pass: access ratings only after exact selected identity matching."""
    wanted = {}
    for case, window in windows.items():
        if len(window['targets']) != 3:
            raise ValueError('Expected three targets per development case')
        for target in window['targets']:
            row = target['source_row']
            if type(row) is not int or row < 0 or row in wanted:
                raise ValueError('Invalid or duplicate target source row')
            if type(target['timestamp']) is not int or not CUTOFF < target['timestamp'] < UPPER:
                raise ValueError('Invalid target identity timestamp')
            wanted[row] = target
    labels = {}
    for row, record in indexed_records:
        if row not in wanted:
            continue
        if row in labels:
            raise ValueError('Target row is duplicated in source stream')
        expected = wanted[row]
        for key in ('user_id', 'parent_asin', 'timestamp'):
            if record[key] != expected[key]:
                raise ValueError('Target identity changed between source passes')
        # This is the only target-rating access in the entire module.
        labels[row] = valid_rating(record['rating'])
    if set(labels) != set(wanted):
        raise ValueError('Some selected development targets are missing')
    return {case: {'target_rows': [r['source_row'] for r in window['targets']],
                   'target_ratings': [labels[r['source_row']] for r in window['targets']],
                   'targets': [{**r, 'target': i + 1, 'rating': labels[r['source_row']]}
                               for i, r in enumerate(window['targets'])]}
            for case, window in windows.items()}


def write_once(path, value):
    content = canonical_bytes(value)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError('Refusing to replace different development labels')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(content)
    return digest(path)


def materialize(report_path, root=ROOT):
    report_path = Path(report_path)
    report = json.loads(report_path.read_text())
    preparation_path = root / 'results/language-extension-input-preparation.json'
    preparation = json.loads(preparation_path.read_text())
    if preparation['status'] != 'prepared' or preparation['target_labels_materialized'] is not False:
        raise ValueError('Expected outcome-isolated prepared inputs')
    input_hashes = development_input_hashes(preparation['input_file_hashes'])
    if 'results/amazon-language-feasibility-Musical_Instruments.json' not in preparation['dependencies']:
        raise ValueError('Preparation must pin the source-screen report')
    verify_hashes(root, preparation['dependencies'])
    verify_hashes(root, input_hashes)
    cases = preparation['groups']['development']
    manifest_path = checked_path(root, report['manifest_path'])
    if digest(manifest_path) != report['manifest_sha256']:
        raise ValueError('Inference manifest changed')
    manifest = json.loads(manifest_path.read_text())
    if not set(REQUIRED_DEPENDENCIES).issubset(manifest['dependencies']):
        raise ValueError('Inference manifest must pin development protocol and precision planner')
    verify_hashes(root, manifest['dependencies'])
    verify_hashes(root, report['raw_file_hashes'])
    verify_inference_gate(report, manifest, cases, report['raw_file_hashes'])
    inputs = json.loads((root / 'data/language-extension-v1/development-inputs.json').read_text())
    mapping = json.loads((root / 'data/language-extension-v1/source-mapping.json').read_text())
    if set(inputs) != set(cases) or any(c not in mapping for c in cases):
        raise ValueError('Development mappings do not cover the exact prepared case set')
    selected = {case: mapping[case] for case in cases}
    screen_path = root / 'results/amazon-language-feasibility-Musical_Instruments.json'
    screen = json.loads(screen_path.read_text())
    if screen['category'] != CATEGORY or screen['code_sha256'] != digest(root / 'src/amazon_language_feasibility.py'):
        raise ValueError('Source screen provenance changed')
    validate_sources(screen['source_files'], CATEGORY, root=root)
    source_directory = root / 'data/amazon-language-extension'
    candidate_path = source_directory / (CATEGORY + '-candidate-windows.json')
    if digest(candidate_path) != screen['candidate_windows_sha256']:
        raise ValueError('Candidate source mapping changed')
    candidate = json.loads(candidate_path.read_text())
    for case, row in selected.items():
        if hashlib.sha256(('review-history-extension-v1:' + row['user_id']).encode()).hexdigest() != case:
            raise ValueError('Case identifier differs from source user hash')
        source = candidate.get(row['user_id'])
        if source is None or any(source[k] != row[k] for k in ('history_rows', 'target_rows')):
            raise ValueError('Development window differs from frozen candidate mapping')
    archive = source_directory / (CATEGORY + '.jsonl.gz')
    windows = project_window_identities(enumerate(records(archive)), selected, inputs)
    verify_catalog(records(source_directory / ('meta_' + CATEGORY + '.jsonl.gz')), windows, inputs)
    labels = project_development_labels(enumerate(records(archive)), windows)
    archive_hash = next(s['sha256'] for s in screen['source_files']
                        if s['file'] == str(archive.relative_to(root)))
    if digest(archive) != archive_hash:
        raise ValueError('Source archive changed while projecting development labels')
    dependencies = {**preparation['dependencies'], **input_hashes,
                    **manifest['dependencies'], **report['raw_file_hashes']}
    dependencies.update({str(preparation_path.relative_to(root)): digest(preparation_path),
                         str(manifest_path.relative_to(root)): digest(manifest_path),
                         str(report_path.resolve().relative_to(root.resolve())): digest(report_path),
                         'src/language_development_labels.py': digest(root / 'src/language_development_labels.py'),
                         str(candidate_path.relative_to(root)): digest(candidate_path)})
    for source in screen['source_files']:
        dependencies[source['file']] = source['sha256']
    value = {'scope': 'Private development target labels, released only after all development inference; '
                      'reserved-confirmation target rating fields are never accessed.',
             'phase': 'development', 'complete': True, 'case_order': cases, 'cases': labels,
             'source_objects_parsed': True, 'reserved_rating_fields_accessed': False,
             'target_order': 'Frozen source-mapping target_rows, matching prepared target order',
             'dependencies': dependencies,
             'label_payload_sha256': hashlib.sha256(canonical_bytes(labels)).hexdigest()}
    output = root / 'data/language-development-v1/development-labels.json'
    sha = write_once(output, value)
    return {'file': str(output.relative_to(root)), 'sha256': sha,
            'development_cases': len(labels), 'target_labels': sum(len(v['target_ratings']) for v in labels.values())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(materialize(args.report), indent=2))
