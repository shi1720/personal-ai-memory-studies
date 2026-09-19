"""Local runtime smoke test only. These two synthetic cases are not a benchmark."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import mlx.core as mx
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest_path = ROOT / "references/local-model-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    model, tokenizer = load(str(ROOT / "models/qwen3-4b-instruct-2507-4bit"),
                            tokenizer_config={"trust_remote_code": False})
    cases = [
        {"id": "static", "history": "2025-06-01: I live in Milan.", "expected_city": "Milan"},
        {"id": "updated", "history": "2025-06-01: I live in Milan.\n2025-07-01: I moved to Paris permanently.",
         "expected_city": "Paris"},
    ]
    outputs = []
    for case in cases:
        messages = [{"role": "system", "content": "Answer only from the supplied personal history. Reply with the city name only."},
                    {"role": "user", "content": case["history"] + "\nToday is 2025-07-02. Where do I currently live?"}]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        mx.random.seed(0)
        start = time.perf_counter()
        output = generate(model, tokenizer, prompt=prompt, max_tokens=32,
                          sampler=make_sampler(temp=0.0), verbose=False)
        outputs.append({**case, "messages": messages, "rendered_prompt": prompt,
                        "prompt_tokens": len(tokenizer.encode(prompt)), "output": output,
                        "seconds": time.perf_counter() - start})
        print(case["id"], repr(output), flush=True)
    result = {"status": "runtime smoke test on two synthetic examples, not research evidence",
              "model": manifest["model"], "revision": manifest["revision"],
              "quantization": "4-bit community MLX conversion", "seed": 0, "temperature": 0,
              "max_output_tokens": 32,
              "model_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "versions": {p: importlib.metadata.version(p) for p in ["mlx", "mlx-lm", "transformers"]},
              "outputs": outputs}
    (ROOT / "results/local-runtime-smoke.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
