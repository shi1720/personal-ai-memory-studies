"""Complete-trace replay of the declared development pilot, including negatives."""
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

from certificate_cost import oracle_certificate_cost
from partial_calibration import crc_policy, PartialCalibration, shipped_loss_row

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = [0.0] + [round(0.25 + 0.05 * i, 2) for i in range(16)] + [1.01]
ALPHAS = [0.05, 0.10, 0.20, 0.30]


def metrics(rows, threshold, version="changed"):
    values = [row[version] for row in rows]
    accepted = [r for r in values if r["confidence"] >= threshold]
    errors = sum(not r["correct"] for r in accepted)
    return {"n": len(values), "accepted": len(accepted), "shipped_errors": errors,
            "coverage": len(accepted) / len(values), "shipped_error_rate": errors / len(values),
            "conditional_error": errors / len(accepted) if accepted else None,
            "always_answer_accuracy": sum(r["correct"] for r in values) / len(values)}


def summarize(values):
    return {"mean": statistics.mean(values), "min": min(values), "max": max(values),
            "sd_across_orders": statistics.pstdev(values)}


def main():
    path = ROOT / "results/pilot-002-predictions.jsonl"
    trace = [json.loads(line) for line in path.read_text().splitlines()]
    if len(trace) != 128 or len({r["id"] for r in trace}) != 128 or len({r["persona_id"] for r in trace}) != 128:
        raise ValueError("Complete unique-persona trace required; never analyze a convenient prefix")
    run_manifest = json.loads((ROOT / "results/pilot-002-run-manifest.json").read_text())
    for name, expected in run_manifest["hashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Changed run dependency: {name}")
    examples = json.loads((ROOT / "data/personamem-v2/pilot-002-examples.json").read_text())
    identities = {r["id"]: (r["persona_id"], r["split"], r["correct_index"]) for r in examples}
    if {r["id"]: (r["persona_id"], r["split"], r["correct_index"]) for r in trace} != identities:
        raise ValueError("Trace does not match the prepared examples and scoring labels")
    model_manifest = json.loads((ROOT / "references/local-model-manifest.json").read_text())
    for record in model_manifest["files"]:
        file = ROOT / "models/qwen3-4b-instruct-2507-4bit" / record["name"]
        digest = hashlib.sha256()
        with file.open("rb") as handle:
            for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != record["sha256"]:
            raise ValueError(f"Model checksum mismatch: {record['name']}")
    calibration = [r for r in trace if r["split"] == "calibration"]
    evaluation = [r for r in trace if r["split"] == "evaluation"]
    if len(calibration) != 64 or len(evaluation) != 64:
        raise ValueError("Unexpected group split")
    for row in trace:
        for version in ["original", "changed"]:
            r = row[version]
            if r["correct"] != (r["predicted_index"] == row["correct_index"]):
                raise ValueError("Scoring mismatch")
            if abs(sum(r["option_probabilities"]) - 1) > 1e-5 or not 0 <= r["confidence"] <= 1:
                raise ValueError("Invalid probabilities")
            if r["confidence"] != max(r["option_probabilities"]) or r["predicted_index"] != max(range(4), key=lambda i: r["option_probabilities"][i]):
                raise ValueError("Prediction/confidence mismatch")
            if r["prompt_tokens"] > 3072:
                raise ValueError("Budget violation")
        same = row["original"]["prompt_sha256"] == row["changed"]["prompt_sha256"]
        if same != row["changed"]["reused_original"]:
            raise ValueError("Exact cache mismatch")
    old = [shipped_loss_row(r["original"]["correct"], r["original"]["confidence"], THRESHOLDS) for r in calibration]
    new = [shipped_loss_row(r["changed"]["correct"], r["changed"]["confidence"], THRESHOLDS) for r in calibration]
    cached = {i: old[i] for i, r in enumerate(calibration) if r["changed"]["reused_original"]}
    changed = len(calibration) - len(cached)
    policies = []
    for alpha in ALPHAS:
        full = crc_policy(new, alpha)
        stale = crc_policy(old, alpha)
        entry = {"alpha": alpha, "full_policy": full, "full_threshold": THRESHOLDS[full],
                 "full_evaluation": metrics(evaluation, THRESHOLDS[full]),
                 "full_calibration": metrics(calibration, THRESHOLDS[full]),
                 "stale_policy": stale, "stale_threshold": THRESHOLDS[stale],
                 "stale_evaluation": metrics(evaluation, THRESHOLDS[stale]),
                 "oracle_certificate_diagnostic": oracle_certificate_cost(new, alpha, cached),
                 "schedules": []}
        for seed in [None] + list(range(100)):
            priority = None
            if seed is not None:
                order = list(range(len(calibration)))
                random.Random(seed).shuffle(order)
                priority = {i: len(order)-rank for rank, i in enumerate(order)}
            for fraction in [0, 0.25, 0.5, 0.75, 1.0]:
                budget = math.floor(fraction * changed)
                state = PartialCalibration(len(calibration), len(THRESHOLDS), alpha, cached)
                result = state.run(lambda i: new[i], budget=budget, priority=priority)
                if result["policy"] < full or (result["exact"] and result["policy"] != full):
                    raise AssertionError("Certificate dominance/recovery failure")
                called = result["recomputed_indices"]
                result.update({"seed": seed, "budget_fraction": fraction, "budget_calls": budget,
                               "threshold": THRESHOLDS[result["policy"]],
                               "evaluation": metrics(evaluation, THRESHOLDS[result["policy"]]),
                               "replayed_reader_seconds": sum(calibration[i]["changed"]["seconds"] for i in called),
                               "replayed_prompt_tokens": sum(calibration[i]["changed"]["prompt_tokens"] for i in called),
                               "calls_avoided_vs_exact_cache": changed - result["reader_calls"]})
                entry["schedules"].append(result)
        fixed = next(s for s in entry["schedules"] if s["seed"] is None and s["budget_fraction"] == 1)
        random_full = [s for s in entry["schedules"] if s["seed"] is not None and s["budget_fraction"] == 1]
        entry["fixed_exact_calls"] = fixed["reader_calls"]
        entry["random_exact_calls"] = summarize([s["reader_calls"] for s in random_full])
        if not all(s["exact"] for s in [fixed] + random_full):
            raise AssertionError("Full budget did not recover reference")
        policies.append(entry)
    changes = {split: {"n": len(rows),
                       "changed_prompts": sum(not r["changed"]["reused_original"] for r in rows),
                       "changed_predictions": sum(r["original"]["predicted_index"] != r["changed"]["predicted_index"] for r in rows),
                       "correct_to_wrong": sum(r["original"]["correct"] and not r["changed"]["correct"] for r in rows),
                       "wrong_to_correct": sum(not r["original"]["correct"] and r["changed"]["correct"] for r in rows),
                       "original": metrics(rows, 0, "original"), "changed": metrics(rows, 0)}
               for split, rows in [("calibration", calibration), ("evaluation", evaluation)]}
    result = {"status": "exploratory offline replay; no measured partial-run speedup or novel-method claim",
              "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "analysis_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "analysis_dependency_hashes": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                  for name in ["src/partial_calibration.py", "src/certificate_cost.py", "docs/pilot-002-analysis.md"]},
              "thresholds": THRESHOLDS, "changes": changes,
              "calibration_rows": len(calibration), "cached_calibration_rows": len(cached),
              "exact_cache_baseline_new_calls": changed,
              "actual_inference_calls": 128 + sum(not r["changed"]["reused_original"] for r in trace),
              "measured_total_reader_seconds": sum(r[v]["seconds"] for r in trace for v in ["original", "changed"]),
              "policies": policies}
    (ROOT / "results/pilot-002-analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"changes": changes, "cached_calibration_rows": len(cached),
                      "policies": [{k: p[k] for k in ["alpha", "full_threshold", "full_evaluation", "fixed_exact_calls", "random_exact_calls", "oracle_certificate_diagnostic"]} for p in policies]}, indent=2))


if __name__ == "__main__":
    main()
