"""Download a pinned upstream release and record content hashes.

This script intentionally does not download the 3 GB long-history variant.
Data remains git-ignored. The upstream dataset card declares the MIT license.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

REPO = "xiaowu0162/longmemeval-cleaned"
REVISION = "98d7416c24c778c2fee6e6f3006e7a073259d48f"
FILES = ("README.md", "longmemeval_oracle.json", "longmemeval_s_cleaned.json")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    target = args.root / "data" / "longmemeval" / REVISION
    target.mkdir(parents=True, exist_ok=True)
    records = []
    for name in FILES:
        path = target / name
        url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{name}"
        if not path.exists():
            temporary = path.with_suffix(path.suffix + ".partial")
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as out:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    out.write(block)
            temporary.replace(path)
        if name.endswith(".json"):
            with path.open() as stream:
                payload = json.load(stream)
            if not isinstance(payload, list) or len(payload) != 500:
                raise ValueError(f"Unexpected data shape for {name}")
        records.append({"file": str(path.relative_to(args.root)), "url": url,
                        "bytes": path.stat().st_size, "sha256": digest(path)})
        print(f"Verified {name}: {path.stat().st_size:,} bytes", flush=True)
    manifest = {"dataset": REPO, "revision": REVISION,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "license_declared_by_upstream": "MIT", "files": records}
    out = args.root / "references" / "longmemeval-manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        old = json.loads(out.read_text())
        if old["files"] != records:
            raise ValueError("Pinned local data differs from the existing manifest")
        print("Existing manifest verified; acquisition timestamp preserved")
    else:
        out.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
