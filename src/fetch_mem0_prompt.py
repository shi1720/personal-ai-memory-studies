"""Fetch the two pinned upstream files as data; never import upstream code."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'references/mem0-prompt-screen.json').read_text())
    for record in manifest['files']:
        target = ROOT / record['local_path']
        if target.exists():
            content = target.read_bytes()
        else:
            request = urllib.request.Request(record['url'], headers={'User-Agent': 'personal-ai-research-reproduction'})
            with urllib.request.urlopen(request, timeout=60) as response:
                content = response.read()
        if hashlib.sha256(content).hexdigest() != record['sha256']:
            raise ValueError(f"Hash mismatch: {record['local_path']}")
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + '.partial')
            temporary.write_bytes(content)
            temporary.replace(target)
        print(f"Verified {record['local_path']}")


if __name__ == '__main__':
    main()
