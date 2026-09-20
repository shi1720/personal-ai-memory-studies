"""Score completed development inference only, with independently checked validity."""
import hashlib
import json
from pathlib import Path

from coat_memory_reader import parse_predictions
from language_development_labels import (
    canonical_bytes, checked_path, verify_hashes, verify_inference_gate, write_once,
)
from language_development_metrics import ARMS, READERS, score_development
from run_language_cross_preflight import native_valid
from run_language_resource_preflight import reader_valid, response_content, summary_text

ROOT = Path(__file__).resolve().parents[1]


def checked_cells(report, load):
    """Reparse saved outputs; report booleans alone never determine scoring."""
    cases = report['cases']
    writers = {}
    for row in report['writers']:
        key = (row['case_id'], row['writer'])
        if key in writers:
            raise ValueError('Duplicate writer cell')
        native = load(row['native_path'])
        summary = load(row['summary_path'])
        writers[key] = {'native': native_valid(native),
                        'summary': summary.get('status') == 'completed' and summary_text(summary) is not None}
    if set(writers) != {(c, m) for c in cases for m in READERS}:
        raise ValueError('Incomplete writer grid')
    cells = {(reader, arm): {} for reader in READERS for arm in ARMS}
    for row in report['readers']:
        case, reader, arm = row['case_id'], row['reader'], row['arm']
        if case not in cases or (reader, arm) not in cells or case in cells[(reader, arm)]:
            raise ValueError('Unknown or duplicate reader cell')
        raw = load(row['raw_path'])
        valid_reader = raw.get('status') == 'completed' and reader_valid(raw)
        valid_writer = True
        if arm.startswith(('native_', 'summary_')):
            kind, writer = arm.split('_', 1)
            valid_writer = writers[(case, writer)][kind]
        valid_pipeline = valid_reader and valid_writer
        expected = {'reader_valid': valid_reader, 'required_writer_valid': valid_writer,
                    'diagnostic_fallback_evidence': not valid_writer, 'pipeline_valid': valid_pipeline,
                    'operational_constant3_required': not valid_pipeline}
        if any(type(row.get(k)) is not bool or row[k] != v for k, v in expected.items()):
            raise ValueError('Report validity differs from reparsed writer/reader evidence')
        cells[(reader, arm)][case] = {
            'valid': valid_pipeline,
            'predictions': parse_predictions(response_content(raw), 3) if valid_reader else None,
        }
    if any(set(values) != set(cases) for values in cells.values()):
        raise ValueError('Incomplete reader grid')
    return cells


def main():
    report_path = ROOT / 'results/language-development.json'
    labels_path = ROOT / 'data/language-development-v1/development-labels.json'
    preparation_path = ROOT / 'results/language-extension-input-preparation.json'
    report = json.loads(report_path.read_text())
    labels = json.loads(labels_path.read_text())
    preparation = json.loads(preparation_path.read_text())
    manifest_path = checked_path(ROOT, report['manifest_path'])
    manifest = json.loads(manifest_path.read_text())
    verify_hashes(ROOT, {report['manifest_path']: report['manifest_sha256']})
    required = {'src/analyze_language_development.py', 'src/language_development_metrics.py',
                'src/language_development_labels.py', 'src/language_precision_planning.py',
                'docs/language-development-protocol.md'}
    if not required.issubset(manifest['dependencies']):
        raise ValueError('Inference manifest must freeze scoring and precision definitions')
    verify_hashes(ROOT, manifest['dependencies'])
    verify_hashes(ROOT, report['raw_file_hashes'])
    cases = preparation['groups']['development']
    verify_inference_gate(report, manifest, cases, report['raw_file_hashes'])
    if (labels.get('phase') != 'development' or labels.get('complete') is not True or
            labels.get('case_order') != cases or set(labels.get('cases', {})) != set(cases)):
        raise ValueError('Label artifact is not the complete fixed development split')
    if hashlib.sha256(canonical_bytes(labels['cases'])).hexdigest() != labels['label_payload_sha256']:
        raise ValueError('Label payload hash mismatch')
    verify_hashes(ROOT, labels['dependencies'])
    report_relative = str(report_path.relative_to(ROOT))
    if labels['dependencies'].get(report_relative) != hashlib.sha256(report_path.read_bytes()).hexdigest():
        raise ValueError('Labels were not gated on this exact completed inference report')
    inputs_path = 'data/language-extension-v1/development-inputs.json'
    verify_hashes(ROOT, {inputs_path: preparation['input_file_hashes'][inputs_path]})
    inputs = json.loads((ROOT / inputs_path).read_text())

    def load(relative):
        path = checked_path(ROOT, relative)
        if relative not in report['raw_file_hashes']:
            raise ValueError('Unverified raw file requested')
        return json.loads(path.read_text())

    cells = checked_cells(report, load)
    targets = {case: labels['cases'][case]['target_ratings'] for case in cases}
    histories = {case: [row['rating'] for row in inputs[case]['history']] for case in cases}
    result = score_development(cases, targets, histories, cells)
    result.update(phase='development', complete=True, target_ratings=180,
                  label_artifact_sha256=hashlib.sha256(labels_path.read_bytes()).hexdigest(),
                  inference_report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
                  manifest_sha256=report['manifest_sha256'],
                  confidence_intervals='None: this is development estimation and precision planning only.',
                  dependencies={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                for name in sorted(required)})
    out = ROOT / 'results/language-development-analysis.json'
    sha = write_once(out, result)
    print(json.dumps({'file': str(out.relative_to(ROOT)), 'sha256': sha,
                      'precision_decision': result['precision_planning']['decision']}, indent=2))


if __name__ == '__main__':
    main()
