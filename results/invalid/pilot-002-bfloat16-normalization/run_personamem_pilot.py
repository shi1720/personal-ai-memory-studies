"""Resumable, single-device inference. All cases are exploratory development data."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

import mlx.core as mx
from mlx_lm import load
from mlx_lm.generate import generate_step
from mlx_lm.sample_utils import make_sampler

from personamem_reader import build_input, conversation_blocks

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/personamem-v2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prediction(model, tokenizer, tokens, label_ids):
    mx.random.seed(0)
    start = time.perf_counter()
    steps = generate_step(mx.array(tokens), model, max_tokens=1,
                          sampler=make_sampler(temp=0.0))
    token, logprobs = next(steps)
    selected = logprobs[mx.array(label_ids)]
    probs = mx.softmax(selected).tolist()
    mass = float(mx.sum(mx.exp(selected)).item())
    result = {"option_probabilities": probs, "label_probability_mass": mass,
              "predicted_index": max(range(4), key=lambda i: probs[i]),
              "confidence": max(probs), "unconstrained_token_id": int(token),
              "prompt_tokens": len(tokens), "seconds": time.perf_counter() - start}
    steps.close()
    mx.clear_cache()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=128, help="Prefix for infrastructure checks, never sample selection")
    args = parser.parse_args()
    examples = json.loads((DATA / "pilot-002-examples.json").read_text())
    assert len(examples) == len({x["persona_id"] for x in examples}) == 128
    dataset_manifest = json.loads((ROOT / "references/personamem-pilot-manifest.json").read_text())
    for entry in dataset_manifest["files"]:
        if sha(DATA / entry["name"]) != entry["sha256"]:
            raise ValueError(f"Data checksum mismatch: {entry['name']}")
    model, tokenizer = load(str(ROOT / "models/qwen3-4b-instruct-2507-4bit"),
                            tokenizer_config={"trust_remote_code": False})
    labels = [tokenizer.encode(label, add_special_tokens=False) for label in "ABCD"]
    if any(len(ids) != 1 for ids in labels):
        raise ValueError("Option labels must be single tokens")
    label_ids = [ids[0] for ids in labels]
    files = ["src/run_personamem_pilot.py", "src/personamem_reader.py", "src/retrieval_pilot.py",
             "docs/pilot-002.md", "references/personamem-pilot-manifest.json",
             "references/local-model-manifest.json"]
    manifest = {"status": "exploratory development pilot, not official benchmark results",
                "hashes": {f: sha(ROOT / f) for f in files}, "seed": 0,
                "choice_token_ids": label_ids, "number_of_examples": len(examples),
                "versions": {p: importlib.metadata.version(p) for p in ["mlx", "mlx-lm", "transformers"]}}
    manifest_path = ROOT / "results/pilot-002-run-manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError("Run identity changed. Preserve this run and declare a new one, do not mix outputs")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    output = ROOT / "results/pilot-002-predictions.jsonl"
    completed = {}
    if output.exists():
        for line in output.read_text().splitlines():
            row = json.loads(line)
            if row["id"] in completed:
                raise ValueError("Duplicate completed example")
            completed[row["id"]] = row
    prompts = DATA / "pilot-002-prompts"
    prompts.mkdir(exist_ok=True)
    for number, example in enumerate(examples[:args.limit], 1):
        if example["id"] in completed:
            continue
        history = json.loads((DATA / example["history_file"]).read_text())["chat_history"]
        blocks = conversation_blocks(history)
        inputs = {name: build_input(tokenizer, example["query"], example["options"], blocks,
                                    example["id"], changed=name == "changed")
                  for name in ["original", "changed"]}
        outputs = {}
        for name, value in inputs.items():
            (prompts / f"{example['id']}-{name}.txt").write_text(value["prompt"])
            if name == "changed" and value["tokens"] == inputs["original"]["tokens"]:
                outputs[name] = {**outputs["original"], "reused_original": True, "seconds": 0.0}
            else:
                outputs[name] = {**prediction(model, tokenizer, value["tokens"], label_ids), "reused_original": False}
            outputs[name].update({k: v for k, v in value.items() if k not in {"prompt", "tokens"}})
            outputs[name]["correct"] = outputs[name]["predicted_index"] == example["correct_index"]
        row = {"id": example["id"], "persona_id": example["persona_id"], "split": example["split"],
               "correct_index": example["correct_index"], **outputs}
        with output.open("a") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        print(f"Completed {number}/128 {example['split']} "
              f"old={outputs['original']['correct']} new={outputs['changed']['correct']} "
              f"cache={outputs['changed']['reused_original']}", flush=True)


if __name__ == "__main__":
    main()
