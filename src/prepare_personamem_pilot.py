"""Prepare a grouped, pinned development pilot. Never uses the benchmark split."""
import ast
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import random

from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/personamem-v2"
REPO = "bowen-upenn/PersonaMem-v2"
REVISION = "ed956dea41521fc4499acbc63f966e0fd3c053ba"
SALT = "partial-recalibration-pilot-002"


def stable_hash(text):
    return hashlib.sha256((SALT + ":" + text).encode()).hexdigest()


def download(name):
    return Path(hf_hub_download(REPO, name, repo_type="dataset", revision=REVISION, local_dir=DATA))


def main():
    base = ["README.md", "column_descriptions.md", "benchmark/text/val.csv"]
    for name in base:
        download(name)
    with (DATA / base[-1]).open() as f:
        rows = list(csv.DictReader(f))
    groups = {}
    for row in rows:
        groups.setdefault(row["persona_id"], []).append(row)
    people = sorted(groups, key=stable_hash)[:128]
    selected = [min(groups[p], key=lambda r: stable_hash(r["user_query"])) for p in people]
    names = sorted({r["chat_history_32k_link"] for r in selected})
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(download, names))
    examples = []
    for i, row in enumerate(selected):
        query = ast.literal_eval(row["user_query"])
        wrong = json.loads(row["incorrect_answers"])
        if len(wrong) != 3 or query["role"] != "user":
            raise ValueError("Unexpected question format")
        options = [row["correct_answer"]] + wrong
        if len(set(options)) != 4:
            raise ValueError("Duplicate answer options")
        permutation = list(range(4))
        random.Random(int(stable_hash(row["persona_id"] + row["user_query"]), 16)).shuffle(permutation)
        examples.append({"id": stable_hash(row["persona_id"] + row["user_query"])[:16],
                         "persona_id": row["persona_id"], "split": "calibration" if i < 64 else "evaluation",
                         "query": query["content"], "options": [options[j] for j in permutation],
                         "correct_index": permutation.index(0),
                         "history_file": row["chat_history_32k_link"]})
    assert len({r["persona_id"] for r in examples}) == 128
    (DATA / "pilot-002-examples.json").write_text(json.dumps(examples, indent=2) + "\n")
    files = []
    for name in base + names + ["pilot-002-examples.json"]:
        data = (DATA / name).read_bytes()
        files.append({"name": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    manifest = {"dataset": REPO, "revision": REVISION, "license": "CC-BY-4.0",
                "source": "https://huggingface.co/datasets/bowen-upenn/PersonaMem-v2",
                "citation": "https://arxiv.org/abs/2512.06688", "protocol": "docs/pilot-002.md",
                "personas": people, "calibration_personas": people[:64], "evaluation_personas": people[64:],
                "files": files}
    (ROOT / "references/personamem-pilot-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared {len(examples)} examples across distinct personas", flush=True)


if __name__ == "__main__":
    main()
