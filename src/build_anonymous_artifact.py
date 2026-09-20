"""Build and execute the anonymous, data-free arithmetic review supplement.

The original analyses and original verifier are read-only inputs. The packaged
verifier retains the calculation functions verbatim, replacing only repository
provenance checks with manifest checks for the files actually distributed.
"""
import ast
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output/submission/Personal_AI_Memory_Anonymous_Artifact.zip'
REPORTS = {'confirmation-analysis.json': 6, 'movie-validation-analysis.json': 4}

README = """# Anonymous arithmetic reproducibility supplement

This supplement accompanies *A Controlled Audit of Personal AI Memory for
Rating Prediction*. It reproduces the aggregation and uncertainty calculations from the
released per-user error summaries. It contains 5,400 user-system summary rows
across two datasets and checks all ten primary comparisons, both operational
and paired common-valid estimates.

## Run

Use Python 3.9 through 3.12 and NumPy 1.26.4. From this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/verify_published_results.py
.venv/bin/python -m unittest discover -s tests -v
```

On Windows use `.venv\\Scripts\\python` instead. Verification is CPU-only and
requires no source datasets, inference models, network service, or API key.
Installing the declared dependency requires access to a Python package source.
Do not invoke Python with `-O`: the checker deliberately uses assertions and
rejects execution with assertions disabled.

Successful verification prints a JSON report and writes
`verification-result.json`. The verifier checks the archive member hashes,
per-system means, user-macro RMSE, metric identities and ranges, validity counts,
duplicate rows, and all reported paired bootstrap intervals. There are 10,000
paired user resamples with seed 20260920; the interval endpoints are 0.025 and
0.975 for ordinary intervals and 0.0025 and 0.9975 for the adjusted intervals.
User row order is retained exactly because it determines deterministic bootstrap
resampling. The included tests ensure that damaged aggregates, duplicate rows,
corrupted intervals, changed files, and unsafe manifest paths are rejected.

## Contents and limits

The two analysis JSON files are byte-for-byte copies of the original completed
reports, not anonymized numerical reconstructions. They contain per-user error
summaries, aggregate results, contrast estimates, resource summaries, and relative
dependency names and hashes. The anonymous manifest records their original
SHA-256 values. No source ratings, prediction arrays, full prompts, generated
memory texts, model weights, Git history, or author-identifying links are included.

The source dependency entries inside each original report refer to files from
the complete research artifact which are intentionally not distributed here.
This portable verifier checks the two reports and its distributed code against
the anonymous manifest. It does not validate those absent dependencies, original
trace provenance, correctness of predictions against source targets, dataset
acquisition, or model inference. Hashes detect inconsistency within this package;
they are not an independently signed certificate of authenticity. Computational
consistency is not an external laboratory replication or peer review.

The mathematical verification functions and original two regression tests are
copied unchanged from the completed artifact. Packaging and integrity tests are
additional. Original primary analyses, hypotheses, and results are unchanged.
No third-party source code is included; NumPy is an external dependency governed
by its own license. This temporary anonymous distribution is supplied for review
and reproduction of the accompanying reported calculations.

## Optional numerical stability audit

The separate `src/review_bootstrap_stability.py` and its recorded output are
included. After verifying the package, reproduce this additional calculation:

```sh
.venv/bin/python src/review_bootstrap_stability.py
```

This recomputes 200,000 bootstrap samples for each of the ten operational
contrasts under two additional seeds. It uses the same user summaries, not new
data, and leaves the frozen primary reports untouched. It is a post-review
Monte Carlo stability audit, not an enlarged primary analysis. It overwrites
only `results/review-bootstrap-stability.json`, including current environment
metadata; when using a different Python or NumPy version, the file hash can
therefore change even if its numerical findings agree. Run package integrity
verification before this optional regeneration, or use a fresh extraction.
"""

PORTABLE_MAIN = r'''

def verify_package(root):
    """Check only distributed members; absent original dependencies are not checked."""
    root = Path(root)
    manifest = json.loads((root / 'manifest.json').read_text())
    assert manifest['verification_scope'] == 'summary arithmetic only'
    assert set(manifest['original_report_sha256']) == {
        'confirmation-analysis.json', 'movie-validation-analysis.json'}
    for name, expected in manifest['files'].items():
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts, 'unsafe manifest path'
        path = root / relative
        assert path.is_file(), ('missing member', name)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, ('changed member', name)
    for name, expected in manifest['original_report_sha256'].items():
        assert manifest['files']['results/' + name] == expected, 'original report hash mismatch'
    return manifest


def main():
    if not __debug__:
        raise RuntimeError('Run without -O; assertion checks must remain enabled.')
    verify_package(ROOT)
    checked = []
    for filename, contrasts in [('confirmation-analysis.json', 6),
                                ('movie-validation-analysis.json', 4)]:
        path = ROOT / 'results' / filename
        result = verify(json.loads(path.read_text()), contrasts)
        checked.append({'report': filename,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), **result})
    output = {
        'scope': 'Anonymous released-summary arithmetic and bootstrap verification only',
        'excluded_scope': 'Original trace provenance, source targets, absent dependencies, and fresh inference',
        'checks': checked,
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (ROOT / 'verification-result.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
'''

INTEGRITY_TESTS = '''"""Package integrity must fail closed on damage or unsafe paths."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from verify_published_results import verify_package


class PackageIntegrityChecks(unittest.TestCase):
    def make_fixture(self, root):
        names = ['confirmation-analysis.json', 'movie-validation-analysis.json']
        (root / 'results').mkdir()
        hashes = {}
        for name in names:
            (root / 'results' / name).write_bytes(b'{}\\n')
            hashes[name] = hashlib.sha256(b'{}\\n').hexdigest()
        manifest = {'verification_scope': 'summary arithmetic only',
                    'original_report_sha256': hashes,
                    'files': {'results/' + k: v for k, v in hashes.items()}}
        (root / 'manifest.json').write_text(json.dumps(manifest))
        return manifest

    def test_changed_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_fixture(root)
            verify_package(root)
            (root / 'results/confirmation-analysis.json').write_bytes(b'{"changed":true}\\n')
            with self.assertRaises(AssertionError):
                verify_package(root)

    def test_unsafe_manifest_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_fixture(root)
            manifest['files']['../outside.json'] = '0' * 64
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(AssertionError):
                verify_package(root)

    def test_original_report_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.make_fixture(root)
            manifest['original_report_sha256']['confirmation-analysis.json'] = '0' * 64
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(AssertionError):
                verify_package(root)


if __name__ == '__main__':
    unittest.main()
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def anonymous_scan(members):
    forbidden = [r'shivam', r'shi1720', r'personal-ai-memory-studies', r'/users/',
                 r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}',
                 r'sk-(?:proj-)?[a-z0-9_-]{16,}', r'github_pat_[a-z0-9_]+',
                 r'gh[pousr]_[a-z0-9]{20,}', r'-----BEGIN .*PRIVATE KEY-----']
    for name, data in members.items():
        text = name + '\n' + data.decode('utf-8')
        for pattern in forbidden:
            if re.search(pattern, text, re.I):
                raise ValueError('Anonymity or secret-pattern check failed in ' + name)


def main():
    source = (ROOT / 'src/verify_published_results.py').read_text()
    tree = ast.parse(source)
    functions = {node.name: ast.get_source_segment(source, node)
                 for node in tree.body if isinstance(node, ast.FunctionDef)}
    header = ('"""Portable verification of anonymous released error summaries. See README.md."""\n'
              'import hashlib\nimport json\nimport math\nfrom pathlib import Path\nimport numpy as np\n\n'
              'ROOT = Path(__file__).resolve().parents[1]\n\n')
    verifier = header + '\n\n'.join(functions[n] for n in ['near', 'interval', 'verify']) + PORTABLE_MAIN
    members = {
        'README.md': README.encode(),
        'requirements.txt': b'numpy==1.26.4\n',
        'src/verify_published_results.py': verifier.encode(),
        'tests/test_published_results.py': (ROOT / 'tests/test_published_results.py').read_bytes(),
        'tests/test_package_integrity.py': INTEGRITY_TESTS.encode(),
    }
    for name in ['src/review_bootstrap_stability.py',
                 'results/review-bootstrap-stability.json',
                 'tests/test_review_bootstrap_stability.py']:
        members[name] = (ROOT / name).read_bytes()
    original = {}
    for name in REPORTS:
        data = (ROOT / 'results' / name).read_bytes()
        members['results/' + name] = data
        original[name] = sha(data)
    manifest = {
        'format_version': 1,
        'verification_scope': 'summary arithmetic only',
        'original_report_sha256': original,
        'original_verifier_sha256': sha(source.encode()),
        'verification_function_sha256': {n: sha(functions[n].encode()) for n in ['near', 'interval', 'verify']},
        'files': {name: sha(data) for name, data in sorted(members.items())},
    }
    members['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    anonymous_scan(members)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 20, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with tempfile.TemporaryDirectory(prefix='anonymous-artifact-check-') as directory:
        root = Path(directory)
        with zipfile.ZipFile(OUTPUT) as archive:
            archive.extractall(root)
        verification = subprocess.run([sys.executable, 'src/verify_published_results.py'],
                                      cwd=root, check=True, capture_output=True, text=True)
        tests = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                               cwd=root, check=True, capture_output=True, text=True)
        optimized = subprocess.run([sys.executable, '-O', 'src/verify_published_results.py'],
                                   cwd=root, capture_output=True, text=True)
        if optimized.returncode == 0 or 'Run without -O' not in optimized.stderr:
            raise RuntimeError('Optimized-mode guard did not reject disabled assertions.')
        original_stability = json.loads((root / 'results/review-bootstrap-stability.json').read_text())
        subprocess.run([sys.executable, 'src/review_bootstrap_stability.py'],
                       cwd=root, check=True, capture_output=True, text=True)
        repeated_stability = json.loads((root / 'results/review-bootstrap-stability.json').read_text())
        for report in [original_stability, repeated_stability]:
            report.pop('environment', None)
        if original_stability != repeated_stability:
            raise RuntimeError('Optional bootstrap stability audit did not reproduce exactly.')
        outcome = json.loads(verification.stdout)
    result = {'artifact': str(OUTPUT.relative_to(ROOT)), 'sha256': sha(OUTPUT.read_bytes()),
              'members': len(members), 'anonymous_text_scan': 'passed',
              'fresh_extraction_verification': outcome['checks'],
              'tests': tests.stderr.strip().splitlines()[-1],
              'test_count': int(re.search(r'Ran (\d+) tests', tests.stderr).group(1)),
              'assertion_disabled_execution': 'rejected',
              'optional_bootstrap_stability_reproduction': 'exact match excluding environment metadata',
              'validation_environment': {'python': sys.version.split()[0], 'numpy': version('numpy')},
              'scope': 'Anonymous summary arithmetic package, not fresh inference'}
    (ROOT / 'results/anonymous-artifact-build-check.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
