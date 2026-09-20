"""Independent saved-result calculation check for completed development only.

Imports no primary scorer, parser, writer-validity checker, label gate, or
precision planner. No model endpoint or source-label reconstruction is used.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist, stdev

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
READERS = ("qwen", "phi")
ARMS = ("no_history", "full_history", "native_qwen", "summary_qwen",
        "native_phi", "summary_phi", "bm25_history")
CONTRAST_KEYS = tuple(sorted(f"{comparison}__writer_{writer}__reader_{reader}"
                            for comparison in ("native_minus_full", "native_minus_matched_summary")
                            for writer in READERS for reader in READERS))
STAGE_SIZES = {"qwen_base": 399, "phi": 513, "qwen_cross": 114}
REPORT = "results/language-development.json"
LABELS = "data/language-development-v1/development-labels.json"
ANALYSIS = "results/language-development-analysis.json"
PREPARATION = "results/language-extension-input-preparation.json"
INPUTS = "data/language-extension-v1/development-inputs.json"
OUTPUT = "results/language-development-independent-check.json"
REQUIRED = {
    "docs/language-development-protocol.md", "src/language_precision_planning.py",
    "src/language_development_labels.py", "src/language_development_metrics.py",
    "src/analyze_language_development.py", PREPARATION,
}


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def safe_path(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("Expected a nonempty relative artifact path")
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Artifact path escapes root")
    return path


def load_json(root, name):
    return json.loads(safe_path(root, name).read_text())


def verify_hashes(root, hashes):
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("Missing dependency hashes")
    for name, expected in hashes.items():
        if (not isinstance(expected, str) or len(expected) != 64
                or any(c not in "0123456789abcdef" for c in expected)):
            raise ValueError("Malformed SHA-256 digest")
        if file_hash(safe_path(root, name)) != expected:
            raise ValueError("Hash mismatch: " + name)


def require_coverage(dependencies, required):
    if any(dependencies.get(name) != value for name, value in required.items()):
        raise ValueError("Dependency coverage differs from the verified artifacts")


def verify_inference_before_labels(root):
    """Check the complete grid and provenance before opening the label artifact."""
    report = load_json(root, REPORT)
    if report.get("phase") != "development" or report.get("complete") is not True:
        raise ValueError("Completed development inference is required before labels")
    if report.get("stage_status") != {key: "completed" for key in STAGE_SIZES}:
        raise ValueError("All three inference stages must be complete")
    cases = report.get("cases")
    if (not isinstance(cases, list) or len(cases) != 60
            or any(not isinstance(x, str) or not x for x in cases) or len(set(cases)) != 60):
        raise ValueError("Exactly 60 distinct ordered development cases are required")
    verify_hashes(root, {report["manifest_path"]: report["manifest_sha256"]})
    manifest = load_json(root, report["manifest_path"])
    if manifest.get("phase") != "development" or manifest.get("cases") != cases:
        raise ValueError("Manifest phase or development order differs")
    if not REQUIRED.issubset(manifest.get("dependencies", {})):
        raise ValueError("Required method definitions were not frozen")
    verify_hashes(root, manifest["dependencies"])
    if report.get("dependencies") != manifest["dependencies"]:
        raise ValueError("Report and manifest dependency sets differ")
    preparation = load_json(root, PREPARATION)
    if (preparation.get("status") != "prepared" or preparation.get("target_labels_materialized") is not False
            or preparation.get("groups", {}).get("development") != cases):
        raise ValueError("Prepared development cohort differs")
    verify_hashes(root, {INPUTS: preparation["input_file_hashes"][INPUTS]})
    if (manifest.get("prepared_development_path") != INPUTS
            or manifest.get("prepared_development_sha256") != preparation["input_file_hashes"][INPUTS]):
        raise ValueError("Manifest does not identify the prepared development input")
    raw_hashes = report.get("raw_file_hashes")
    verify_hashes(root, raw_hashes)
    reader_rows, writer_rows = report.get("readers", []), report.get("writers", [])
    expected_readers = {(case, reader, arm) for case in cases for reader in READERS for arm in ARMS}
    actual_readers = [(r["case_id"], r["reader"], r["arm"]) for r in reader_rows]
    if len(actual_readers) != 840 or set(actual_readers) != expected_readers:
        raise ValueError("Reader grid must contain every one of 60 x 14 cells exactly once")
    expected_writers = {(case, writer) for case in cases for writer in READERS}
    actual_writers = [(r["case_id"], r["writer"]) for r in writer_rows]
    if len(actual_writers) != 120 or set(actual_writers) != expected_writers:
        raise ValueError("Writer grid is incomplete or duplicated")
    output_paths = []
    for row in reader_rows:
        if row.get("file") != row.get("raw_path") or raw_hashes.get(row["raw_path"]) != row["raw_sha256"]:
            raise ValueError("Reader file aliases or verified hashes disagree")
        output_paths.append(row["raw_path"])
    for row in writer_rows:
        if row.get("model") != row["writer"]:
            raise ValueError("Writer identity aliases disagree")
        for kind in ("native", "summary"):
            name = row[kind + "_path"]
            if row.get(kind + "_file") != name or raw_hashes.get(name) != row[kind + "_sha256"]:
                raise ValueError("Writer file aliases or verified hashes disagree")
            output_paths.append(name)
    if len(set(output_paths)) != 1080:
        raise ValueError("Distinct generation cells must have distinct saved output files")
    for stage, count in STAGE_SIZES.items():
        name = f"data/language-development-v1/{stage}-handoff.json"
        if name not in raw_hashes:
            raise ValueError("Stage handoff is not covered by raw-file hashes")
        handoff = load_json(root, name)
        if (handoff.get("stage") != stage or handoff.get("status") != "completed"
                or handoff.get("manifest_sha256") != report["manifest_sha256"]
                or handoff.get("recorded_cells") != count):
            raise ValueError("Stage handoff disagrees with the complete planned stage")
        if not isinstance(handoff.get("files"), dict) or not handoff["files"]:
            raise ValueError("Stage handoff lacks its file provenance")
        require_coverage(raw_hashes, handoff["files"])
    return report, manifest, preparation


def first_choice(raw):
    response = raw.get("response")
    if not isinstance(response, dict):
        return {}
    choices = response.get("choices")
    return choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}


def stopped_content(raw):
    selected = first_choice(raw)
    message = selected.get("message")
    if selected.get("finish_reason") != "stop" or not isinstance(message, dict):
        return None
    text = message.get("content")
    return text if isinstance(text, str) else None


def decode_reader(raw):
    """Independent implementation of the frozen exact three-number contract."""
    if raw.get("status") != "completed":
        return None
    content = stopped_content(raw)
    if content is None:
        return None
    text = content.strip()
    for prefix in ("```json\n", "```\n"):
        if text.startswith(prefix) and text.endswith("\n```"):
            text = text[len(prefix):-4].strip()
            break
    try:
        values = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(values, list) or len(values) != 3:
        return None
    if any(type(v) not in (int, float) or v < 1 or v > 5 or not math.isfinite(v) for v in values):
        return None
    return [float(v) for v in values]


def valid_summary(raw):
    if raw.get("status") != "completed":
        return False
    content = stopped_content(raw)
    if content is None:
        return False
    text = content.strip()
    if text.startswith("```json\n") and text.endswith("\n```"):
        text = text[8:-4].strip()
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return False
    if not isinstance(value, dict) or set(value) != {"profile"}:
        return False
    profile = value["profile"]
    return isinstance(profile, str) and bool(profile.strip()) and len(profile.split()) <= 400


def valid_native(raw):
    if raw.get("status") != "completed" or raw.get("cleanup_error"):
        return False
    if not isinstance(raw.get("add"), dict) or not isinstance(raw.get("stored"), dict):
        return False
    inserted = raw["add"].get("results")
    exported = raw["stored"].get("results")
    if not isinstance(inserted, list) or not isinstance(exported, list) or not exported:
        return False
    groups = []
    for rows in (inserted, exported):
        mapped = {}
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in mapped:
                return False
            text = row.get("memory")
            if not isinstance(text, str) or not text.strip():
                return False
            mapped[row["id"]] = text
        groups.append(mapped)
    traces = raw.get("traces")
    return (groups[0] == groups[1] and isinstance(traces, list) and bool(traces)
            and all(isinstance(t, dict) and first_choice(t).get("finish_reason") == "stop" for t in traces))


def read_pipelines(report, load):
    """Reparse writer and reader validity instead of trusting report flags."""
    writers = {}
    for row in report["writers"]:
        native = valid_native(load(row["native_path"]))
        summary = valid_summary(load(row["summary_path"]))
        if (type(row.get("native_valid")) is not bool or row["native_valid"] != native
                or type(row.get("summary_valid")) is not bool or row["summary_valid"] != summary):
            raise ValueError("Writer validity flags differ from independently parsed exports")
        writers[(row["case_id"], row["writer"])] = {"native": native, "summary": summary}
    pipelines = {}
    for row in report["readers"]:
        predictions = decode_reader(load(row["raw_path"]))
        arm = row["arm"]
        needed = True
        if arm.startswith("native_") or arm.startswith("summary_"):
            kind, writer = arm.split("_", 1)
            needed = writers[(row["case_id"], writer)][kind]
        reader_ok = predictions is not None
        pipeline_ok = reader_ok and needed
        flags = {"reader_valid": reader_ok, "required_writer_valid": needed,
                 "diagnostic_fallback_evidence": not needed, "pipeline_valid": pipeline_ok,
                 "operational_constant3_required": not pipeline_ok}
        if any(type(row.get(k)) is not bool or row[k] != expected for k, expected in flags.items()):
            raise ValueError("Reader/pipeline validity flags disagree with saved output")
        key = (row["case_id"], row["reader"], arm)
        if key in pipelines:
            raise ValueError("Duplicate pipeline")
        pipelines[key] = (predictions if pipeline_ok else [3.0, 3.0, 3.0], pipeline_ok)
    return pipelines


def metrics(predictions, targets):
    deviations = [predictions[k] - targets[k] for k in range(3)]
    matches = []
    for left in range(3):
        for right in range(left):
            if targets[left] == targets[right]:
                continue
            if predictions[left] == predictions[right]:
                matches.append(0.5)
            else:
                matches.append(float((predictions[left] > predictions[right]) == (targets[left] > targets[right])))
    return {"mae": math.fsum(map(abs, deviations)) / 3.0,
            "mse": math.fsum(x * x for x in deviations) / 3.0,
            "signed_error": math.fsum(deviations) / 3.0,
            "pairwise_concordance": math.fsum(matches) / len(matches) if matches else None,
            "unequal_target_pairs": len(matches)}


def aggregate(rows):
    ranks = [row["pairwise_concordance"] for row in rows if row["pairwise_concordance"] is not None]
    n = len(rows)
    return {"users": n, "mae": math.fsum(row["mae"] for row in rows) / n,
            "rmse": math.sqrt(math.fsum(row["mse"] for row in rows) / n),
            "signed_error": math.fsum(row["signed_error"] for row in rows) / n,
            "pairwise_concordance": math.fsum(ranks) / len(ranks) if ranks else None,
            "ordering_eligible_users": len(ranks), "valid_users": sum(row["valid"] for row in rows)}


def calculate(cases, targets, histories, pipelines):
    systems = {}
    for reader in READERS:
        for arm in ARMS:
            rows = []
            for case in cases:
                predictions, valid = pipelines[(case, reader, arm)]
                rows.append({"case_id": case, "valid": valid, **metrics(predictions, targets[case])})
            systems[reader + "/" + arm] = {"users": rows, "summary": aggregate(rows)}
    for method in ("history_mean", "history_median", "constant_3"):
        rows = []
        for case in cases:
            history = histories[case]
            ordered = sorted(history)
            estimate = (math.fsum(history) / 12.0 if method == "history_mean" else
                        (ordered[5] + ordered[6]) / 2.0 if method == "history_median" else 3.0)
            rows.append({"case_id": case, "valid": True, **metrics([estimate] * 3, targets[case])})
        systems[method] = {"users": rows, "summary": aggregate(rows)}
    contrasts = {}
    for reader in READERS:
        for writer in READERS:
            native = systems[reader + "/native_" + writer]["users"]
            for comparison, other_name in (("native_minus_full", "full_history"),
                                            ("native_minus_matched_summary", "summary_" + writer)):
                other = systems[reader + "/" + other_name]["users"]
                differences, common = [], []
                for nrow, orow in zip(native, other):
                    difference = nrow["mae"] - orow["mae"]
                    differences.append(difference)
                    if nrow["valid"] and orow["valid"]:
                        common.append(difference)
                name = comparison + "__writer_" + writer + "__reader_" + reader
                contrasts[name] = {"users": len(cases), "mean_difference": math.fsum(differences) / len(cases),
                                   "common_valid_users": len(common),
                                   "common_valid_mean_difference": math.fsum(common) / len(common) if common else None,
                                   "paired_user_differences": differences}
    return systems, contrasts


def independent_precision(contrasts):
    """Separate centered-variance and explicit order-statistic implementation."""
    if not isinstance(contrasts, dict) or set(contrasts) != set(CONTRAST_KEYS):
        raise ValueError("Precision requires the complete fixed eight-contrast family")
    rng = np.random.Generator(np.random.PCG64(20260923))
    critical = NormalDist().inv_cdf(1 - 0.05 / 16)
    results = {}
    for name in sorted(contrasts):
        values = np.asarray(contrasts[name]["paired_user_differences"], dtype=np.float64)
        if values.shape != (60,) or not np.all(np.isfinite(values)) or np.any(np.abs(values) > 4):
            raise ValueError("Precision requires exactly 60 bounded paired differences")
        draws = values[rng.integers(0, 60, size=(20000, 60))]
        shifted = draws - draws[:, :1]
        centers = np.sum(shifted, axis=1) / 60.0
        residuals = shifted - centers[:, None]
        deviations = np.sort(np.sqrt(np.sum(residuals * residuals, axis=1) / 59.0))
        position = 0.95 * 19999
        index = int(position)
        upper = float(deviations[index] + (position - index) * (deviations[index + 1] - deviations[index]))
        half_width = critical * upper / math.sqrt(200)
        results[name] = {"development_users": 60, "sample_sd": stdev(values.tolist()),
                         "bootstrap_sd_upper_95_quantile": upper,
                         "projected_adjusted_half_width": half_width, "meets_target": bool(half_width <= 0.10)}
    passes = all(row["meets_target"] for row in results.values())
    return {"complete": True, "contrasts": results, "joint_go": passes, "decision": "GO" if passes else "NO_GO"}


def compare(actual, expected, path="result", tolerance=1e-12):
    """Structural equality and finite numeric closeness, rejecting bool-as-number."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError("Object keys differ at " + path)
        return max([0.0] + [compare(actual[k], v, path + "." + k, tolerance) for k, v in expected.items()])
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError("Array length differs at " + path)
        return max([0.0] + [compare(a, e, path + f"[{i}]", tolerance) for i, (a, e) in enumerate(zip(actual, expected))])
    if type(expected) is bool or expected is None or isinstance(expected, str):
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("Discrete value differs at " + path)
        return 0.0
    if type(expected) is int:
        if type(actual) is not int or actual != expected:
            raise ValueError("Integer differs at " + path)
        return 0.0
    if type(actual) not in (int, float) or not math.isfinite(actual):
        raise ValueError("Invalid numeric value at " + path)
    difference = abs(actual - expected)
    if difference > tolerance:
        raise ValueError("Numeric mismatch at " + path)
    return difference


def verify(root=ROOT):
    root = Path(root)
    report, manifest, preparation = verify_inference_before_labels(root)
    analysis = load_json(root, ANALYSIS)
    if (analysis.get("phase") != "development" or analysis.get("complete") is not True
            or analysis.get("cases") != report["cases"] or analysis.get("target_ratings") != 180):
        raise ValueError("Analysis is not the completed fixed development evaluation")
    report_hash = file_hash(safe_path(root, REPORT))
    if analysis.get("inference_report_sha256") != report_hash or analysis.get("manifest_sha256") != report["manifest_sha256"]:
        raise ValueError("Analysis report or manifest provenance differs")
    verify_hashes(root, analysis["dependencies"])
    expected_scoring = REQUIRED - {PREPARATION}
    if set(analysis["dependencies"]) != expected_scoring:
        raise ValueError("Analysis does not identify every fixed scoring dependency")
    require_coverage(manifest["dependencies"], analysis["dependencies"])
    labels_hash = file_hash(safe_path(root, LABELS))
    if labels_hash != analysis.get("label_artifact_sha256"):
        raise ValueError("Full label artifact hash differs from scored artifact")
    labels = load_json(root, LABELS)
    cases = report["cases"]
    if (labels.get("phase") != "development" or labels.get("complete") is not True
            or labels.get("case_order") != cases or set(labels.get("cases", {})) != set(cases)
            or labels.get("reserved_rating_fields_accessed") is not False):
        raise ValueError("Labels do not identify the exact outcome-gated development cohort")
    payload_hash = hashlib.sha256(canonical(labels["cases"])).hexdigest()
    if payload_hash != labels.get("label_payload_sha256"):
        raise ValueError("Label payload checksum differs")
    verify_hashes(root, labels["dependencies"])
    required_label_hashes = {**manifest["dependencies"], **report["raw_file_hashes"],
                            REPORT: report_hash, report["manifest_path"]: report["manifest_sha256"],
                            INPUTS: preparation["input_file_hashes"][INPUTS]}
    require_coverage(labels["dependencies"], required_label_hashes)
    # No target_ratings value is accessed until all completion and hash gates above.
    inputs = load_json(root, INPUTS)
    if set(inputs) != set(cases):
        raise ValueError("Prepared input case set differs")
    targets, histories, source_rows = {}, {}, set()
    for case in cases:
        label = labels["cases"][case]
        values, rows, identities = label["target_ratings"], label["target_rows"], label["targets"]
        if (not isinstance(values, list) or len(values) != 3 or
                any(type(v) is not int or not 1 <= v <= 5 for v in values)
                or not isinstance(rows, list) or len(rows) != 3
                or not isinstance(identities, list) or len(identities) != 3):
            raise ValueError("Malformed development target vectors")
        products = set()
        for index, (rating, row, identity) in enumerate(zip(values, rows, identities)):
            if type(row) is not int or row < 0 or row in source_rows:
                raise ValueError("Invalid or repeated target source row")
            source_rows.add(row)
            if (identity.get("source_row") != row or type(identity.get("rating")) is not int
                    or identity["rating"] != rating or identity.get("target") != index + 1
                    or not isinstance(identity.get("parent_asin"), str) or not identity["parent_asin"]):
                raise ValueError("Label payload identity/rating projections disagree")
            products.add(identity["parent_asin"])
        if len(products) != 3:
            raise ValueError("Repeated target product within a user")
        history = inputs[case].get("history")
        if not isinstance(history, list) or len(history) != 12:
            raise ValueError("Expected twelve historical ratings")
        historical_ratings = [row["rating"] for row in history]
        if any(type(v) is not int or not 1 <= v <= 5 for v in historical_ratings):
            raise ValueError("Invalid historical rating")
        targets[case], histories[case] = values, historical_ratings

    def load_output(name):
        if name not in report["raw_file_hashes"]:
            raise ValueError("Unverified raw output requested")
        return load_json(root, name)

    pipelines = read_pipelines(report, load_output)
    systems, contrasts = calculate(cases, targets, histories, pipelines)
    discrepancies = [compare(analysis.get("systems"), systems, "systems"),
                     compare(analysis.get("contrasts"), contrasts, "contrasts")]
    precision = independent_precision(contrasts)
    primary_precision = analysis.get("precision_planning")
    if not isinstance(primary_precision, dict):
        raise ValueError("Missing precision calculation")
    discrepancies.append(compare({k: primary_precision.get(k) for k in precision}, precision, "precision"))
    expected_settings = {"development_users": 60, "confirmation_users": 200, "family_size": 8,
                         "alpha": 0.05, "target_half_width": 0.10,
                         "bootstrap_resamples_per_contrast": 20000, "bootstrap_seed": 20260923,
                         "generator": "NumPy PCG64", "bootstrap_sd_quantile": 0.95,
                         "sample_sd_ddof": 1, "quantile_method": "linear",
                         "normal_critical_value": NormalDist().inv_cdf(1 - 0.05 / 16)}
    settings = primary_precision.get("settings", {})
    discrepancies.append(compare({k: settings.get(k) for k in expected_settings}, expected_settings, "precision.settings"))
    if analysis.get("precision_planning_not_run_reason") is not None:
        raise ValueError("Unexpected reason for skipping precision")
    return {
        "status": "passed", "phase": "development", "development_users": 60,
        "reader_cells_checked": 840, "writer_representations_checked": 240,
        "user_system_records_checked": 1020, "primary_contrasts_checked": 8,
        "precision_bootstrap_runs_checked": 8, "maximum_numeric_discrepancy": max(discrepancies),
        "absolute_numeric_tolerance": 1e-12,
        "scope": ["Complete development case and stage gate", "Full hashes and label-payload checksum",
                  "Independent reader parsing and native/summary validity", "Whole-pipeline constant-three fallback",
                  "Per-user errors and user-macro summaries, ordering, baselines", "All eight operational and common-valid contrasts",
                  "Separate 20000-resample SD-quantile precision implementation"],
        "not_verified": ["External source-label correctness or label acquisition", "Independent model inference",
                         "External laboratory replication or external peer review", "Future confirmation precision or power"],
        "input_sha256": {name: file_hash(safe_path(root, name)) for name in
                         (REPORT, ANALYSIS, LABELS, PREPARATION, INPUTS, report["manifest_path"])},
        "verifier_source_sha256": file_hash(Path(__file__)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    result = verify()
    path = safe_path(ROOT, OUTPUT)
    content = canonical(result)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError("Refusing to replace a different independent-check result")
    else:
        with path.open("xb") as stream:
            stream.write(content)
    print(json.dumps({"status": result["status"], "file": OUTPUT,
                      "maximum_numeric_discrepancy": result["maximum_numeric_discrepancy"]}))


if __name__ == "__main__":
    main()
