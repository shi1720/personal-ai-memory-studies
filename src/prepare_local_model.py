"""Fetch pinned quantized weights without running repository Python code."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
MODEL = "mlx-community/Qwen3-4B-Instruct-2507-4bit"
REVISION = "50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b"


def main():
    target = ROOT / "models" / "qwen3-4b-instruct-2507-4bit"
    path = Path(snapshot_download(MODEL, revision=REVISION, local_dir=str(target),
                                 allow_patterns=["*.json", "*.safetensors", "*.txt", "*.jinja", "README.md"]))
    files = []
    for file in sorted(path.iterdir()):
        if not file.is_file():
            continue
        h = hashlib.sha256()
        with file.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        files.append({"name": file.name, "bytes": file.stat().st_size, "sha256": h.hexdigest()})
    manifest = {"model": MODEL, "revision": REVISION, "license": "Apache-2.0",
                "base_model": "Qwen/Qwen3-4B-Instruct-2507",
                "conversion_source": "MLX community conversion, not the original BF16 release",
                "purpose": "local feasibility pilots; no frontier-model generalization",
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "files": files}
    dest = ROOT / "references/local-model-manifest.json"
    if dest.exists():
        old = json.loads(dest.read_text())
        if old["files"] != files or old["revision"] != REVISION:
            raise ValueError("Model differs from recorded manifest")
    else:
        dest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Verified {len(files)} model files at {path}")


if __name__ == "__main__":
    main()
