"""Auditable development-only inference, reusing all three crossed preflight cases.

No source archive, outcome mapping, target-label file, donor file, or reserved
confirmation input is opened. Interrupted cells require inspection, never replay.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re

from amazon_language_feasibility import digest
from language_model_pins import ROOT, verify_model, model_path
from language_extension_inputs import writer_history, reader_query
from language_cross_runtime import Runtime, MAX_TOTAL_TOKENS, TIMEOUT
from run_language_resource_preflight import (
    save, select_cases, bm25_selection, SUMMARY_SYSTEM, summary_text,
    reader_valid, response_summary,
)
from run_language_cross_preflight import (
    ARMS, OLD_ARM, native_valid, native_text, writer_summary, response_identity,
)

RUN = ROOT / "data/language-development-v1"
OUT = ROOT / "results/language-development.json"
OLD = ROOT / "data/language-extension-resource-v1"
CROSS = ROOT / "data/language-cross-preflight-v1"
CROSS_REPORT = ROOT / "results/language-cross-preflight.json"
STAGES = ("qwen_base", "phi", "qwen_cross")
STAGE_CAPS = {"qwen_base": 399, "phi": 513, "qwen_cross": 114}
BASE_ARMS = ("no_history", "full_history", "native_qwen", "summary_qwen", "bm25_history")
CROSS_ARMS = ("native_phi", "summary_phi")


def read_json(path):
    return json.loads(Path(path).read_text())


def relative(path):
    return str(Path(path).resolve().relative_to(ROOT.resolve()))


def checked_path(name):
    path = (ROOT / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Artifact path is outside the research root")
    return path


def verify_hashes(files):
    for name, expected in files.items():
        if digest(checked_path(name)) != expected:
            raise ValueError("Recorded file changed: " + name)


def key_for(case, model, name):
    return f"{case}/{model}/{name}"


def stage_for(model, name):
    return "phi" if model == "phi" else ("qwen_cross" if name in CROSS_ARMS else "qwen_base")


def stage_cells(manifest, stage):
    """Return the fixed new-cell plan; preflight cells are never rerun."""
    if stage not in STAGES:
        raise ValueError("Unknown stage")
    model = "phi" if stage == "phi" else "qwen"
    cells = []
    for position, case in enumerate(manifest["cases"]):
        if case in manifest["reused_cases"]:
            continue
        if stage != "qwen_cross":
            for name, kind in (("native-writer", "native"), ("summary-writer", "summary")):
                cells.append(dict(case_id=case, model=model, name=name, kind=kind, stage=stage))
        arms = list(ARMS if stage == "phi" else BASE_ARMS if stage == "qwen_base" else CROSS_ARMS)
        offset = position % len(arms)
        for name in arms[offset:] + arms[:offset]:
            cells.append(dict(case_id=case, model=model, name=name, kind="reader", stage=stage))
    return cells


def record_path(cell):
    return RUN / cell["case_id"] / cell["model"] / (cell["name"] + ".json")


def ledger_path(cell):
    return RUN / "cells" / cell["stage"] / cell["case_id"] / cell["model"] / (cell["name"] + ".json")


def _freeze(path, value):
    """Create once; an interrupted or different existing file is never replaced."""
    if path.exists():
        if read_json(path) != value:
            raise ValueError("Frozen record changed: " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def build_reuse_inventory(preflight):
    records = {}
    for row in preflight["writers"]:
        case, model = row["case_id"], row["writer"]
        directory = OLD / case if model == "qwen" else CROSS / case / model
        for name, field in (("native-writer", "native_sha256"), ("summary-writer", "summary_sha256")):
            key = key_for(case, model, name)
            if key in records:
                raise ValueError("Duplicate preflight writer")
            records[key] = {"file": relative(directory / (name + ".json")), "sha256": row[field]}
    for row in preflight["readers"]:
        case, model, arm = row["case_id"], row["reader"], row["arm"]
        old_arm = next((k for k, v in OLD_ARM.items() if v == arm), None)
        path = OLD / case / (old_arm + ".json") if model == "qwen" and old_arm else CROSS / case / model / (arm + ".json")
        key = key_for(case, model, arm)
        if key in records:
            raise ValueError("Duplicate preflight reader")
        records[key] = {"file": relative(path), "sha256": row["raw_sha256"]}
    expected = {key_for(case, model, name) for case in preflight["cases"]
                for model in ("qwen", "phi") for name in ["native-writer", "summary-writer"] + list(ARMS)}
    if set(records) != expected or len(records) != 54:
        raise ValueError("Preflight does not contain all 54 generation cells")
    files = {v["file"]: v["sha256"] for v in records.values()}
    files.update(preflight["reused_raw_hashes"])
    for row in preflight["new_request_audit"]:
        files[row["file"]] = row["sha256"]
    verify_hashes(files)
    return records, files


def inputs_and_manifest():
    """Only the existing development input file is loaded here."""
    preparation_path = ROOT / "results/language-extension-input-preparation.json"
    preparation, preflight = read_json(preparation_path), read_json(CROSS_REPORT)
    if not (preflight.get("complete") is True and preflight.get("prototype_pass") is True
            and preflight.get("response_bijection") is True
            and preflight.get("combined_transport_attempts") == 54):
        raise ValueError("Completed passed crossed preflight is required")
    verify_hashes(preparation["dependencies"])
    verify_hashes(preflight["dependencies"])
    cases = preparation["groups"]["development"]
    if (len(cases) != 60 or len(set(cases)) != 60
            or any(not isinstance(c, str) or not re.fullmatch(r"[0-9a-f]{64}", c) for c in cases)):
        raise ValueError("Expected exactly 60 prepared development case hashes")
    if preflight["cases"] != select_cases(preparation):
        raise ValueError("Preflight selection differs from the prepared development selection")
    path = ROOT / "data/language-extension-v1/development-inputs.json"
    expected = preparation["input_file_hashes"][relative(path)]
    if digest(path) != expected:
        raise ValueError("Prepared development inputs changed")
    inputs = read_json(path)
    if set(inputs) != set(cases):
        raise ValueError("Development input case set differs from preparation")
    reused_records, reused_hashes = build_reuse_inventory(preflight)
    dependencies = dict(preflight["dependencies"])
    for name in (
        "src/run_language_development.py", "src/language_cross_runtime.py",
        "src/run_language_cross_preflight.py", "src/language_model_pins.py",
        "src/count_cross_request_tokens.py", "src/run_language_resource_preflight.py",
        "src/language_extension_inputs.py", "src/coat_memory_reader.py",
        "src/language_precision_planning.py",
        "src/language_development_labels.py", "src/language_development_metrics.py",
        "src/analyze_language_development.py",
        "docs/language-precision-planning.md",
        "docs/language-development-protocol.md", "results/language-cross-preflight.json",
        "results/language-extension-input-preparation.json",
        "data/language-cross-preflight-v1/manifest.json",
        "data/language-cross-preflight-v1/phi-handoff.json",
    ):
        dependencies[name] = digest(ROOT / name)
    manifest = {
        "phase": "development", "scope": "Development inference only; no target outcomes opened",
        "cases": cases, "reused_cases": preflight["cases"],
        "new_cases": [c for c in cases if c not in preflight["cases"]],
        "prepared_development_path": relative(path), "prepared_development_sha256": expected,
        "dependencies": dependencies, "reused_records": reused_records,
        "reused_raw_hashes": reused_hashes, "stage_request_caps": STAGE_CAPS,
        "expected_new_cells": 1026, "expected_reused_cells": 54,
        "expected_combined_cells": 1080, "arms": list(ARMS),
        "temperature": 0, "top_p": 1, "writer_output_tokens": 2048,
        "reader_output_tokens": 256, "max_total_tokens": MAX_TOTAL_TOKENS,
        "timeout_seconds": TIMEOUT, "max_retries": 0,
        "client_versions": {p: version(p) for p in ("mem0ai", "openai", "fastembed", "qdrant-client", "onnxruntime")},
        "primary_pipeline_failure_rule": "constant three if required writer or reader is invalid",
        "new_condition_order": "rotate stage reader arms by index in the full 60-case preparation order",
        "reused_condition_order": "unchanged original preflight order",
    }
    if any(len(stage_cells(manifest, s)) != STAGE_CAPS[s] for s in STAGES):
        raise ValueError("Unexpected stage plan size")
    _freeze(RUN / "manifest.json", manifest)
    return inputs, manifest


def check_audit(raw, model, budget):
    """Accept recorded transport failures, but reject ambiguous or wrong contracts."""
    if raw.get("status") not in ("completed", "error"):
        raise RuntimeError("Unfinished request audit blocks continuation")
    params = raw.get("params", {})
    if (params.get("model") != str(model_path(model)) or params.get("max_tokens") != budget
            or params.get("temperature") != 0 or params.get("top_p") != 1):
        raise ValueError("Audited request contract differs from the frozen cell")
    if type(raw.get("transport_attempted")) is not bool:
        raise ValueError("Missing explicit transport-attempt state")
    if raw["transport_attempted"]:
        count = raw.get("tokenizer", {}).get("prompt_tokens")
        total = raw.get("total_token_allowance")
        if (raw.get("tokenizer", {}).get("model") != model or type(count) is not int
                or count < 1 or total != count + budget or total > MAX_TOTAL_TOKENS):
            raise ValueError("Audited transported request violates tokenizer/budget contract")
    if raw["status"] == "completed":
        response = raw.get("response", {})
        usage = response.get("usage", {})
        if not isinstance(usage, dict):
            raise ValueError("Successful request completion usage must be an object")
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        if (not raw["transport_attempted"] or response.get("model") != str(model_path(model))
                or type(prompt_tokens) is not int or prompt_tokens != raw["tokenizer"]["prompt_tokens"]
                or response_identity(raw) is None):
            raise ValueError("Successful request response identity or token count mismatch")
        if (type(completion_tokens) is not int or not 0 <= completion_tokens <= budget
                or type(total_tokens) is not int or total_tokens != prompt_tokens + completion_tokens):
            raise ValueError("Successful request completion usage violates the output budget or token total")


def validate_cell_ledger(cell, manifest):
    path = ledger_path(cell)
    if not path.exists():
        raw_path = record_path(cell)
        if raw_path.exists() or raw_path.with_suffix(".started").exists():
            raise RuntimeError("Unledgered or interrupted cell blocks continuation")
        return None
    ledger = read_json(path)
    if ledger.get("status") != "recorded":
        raise RuntimeError("Interrupted or ambiguous cell blocks continuation")
    if ledger.get("cell") != cell or ledger.get("manifest_sha256") != digest(RUN / "manifest.json"):
        raise ValueError("Cell identity or manifest changed")
    expected_file = relative(record_path(cell))
    if ledger.get("raw_file") != expected_file:
        raise ValueError("Cell points to an unexpected raw file")
    verify_hashes({expected_file: ledger["raw_sha256"], **ledger["audit_files"]})
    raw = read_json(record_path(cell))
    if raw.get("status") not in ("completed", "error") or raw.get("model") != cell["model"]:
        raise ValueError("Recorded cell is not a terminal result for the planned model")
    budget = 2048 if cell["kind"] in ("native", "summary") else 256
    audits = [read_json(checked_path(n)) for n in ledger["audit_files"]]
    if len(audits) > 1 or (cell["kind"] != "native" and len(audits) != 1):
        raise ValueError("Unexpected requests per planned generation cell")
    if not audits and raw["status"] != "error":
        raise ValueError("Successful native cell has no audited request")
    for audit in audits:
        check_audit(audit, cell["model"], budget)
        if cell["kind"] != "native" and (audit["params"].get("messages") != raw.get("messages")
                or raw.get("max_tokens") != budget):
            raise ValueError("Persisted request prompt differs from transport audit")
    retained = raw.get("traces", []) if cell["kind"] == "native" else ([raw] if "response" in raw else [])
    identities = [response_identity(x) for x in retained]
    audited = [response_identity(x) for x in audits if "response" in x]
    if any(x is None or x not in audited for x in identities) or len(identities) != len({x["id"] for x in identities if x}):
        raise ValueError("Persisted response is not uniquely backed by its audit")
    if raw["status"] == "completed" and identities != audited:
        raise ValueError("Successful cell responses do not match transport records")
    return ledger


def execute_cell(cell, manifest, runtime, operation):
    """A durable cell reservation surrounds the unchanged runtime invocation."""
    existing = validate_cell_ledger(cell, manifest)
    if existing is not None:
        return read_json(record_path(cell))
    path = ledger_path(cell)
    path.parent.mkdir(parents=True, exist_ok=True)
    before = {relative(p): digest(p) for p in runtime.audit.glob("attempt-*.json")}
    reservation = {"cell": cell, "manifest_sha256": digest(RUN / "manifest.json"), "status": "started",
                   "raw_file": relative(record_path(cell)), "started_at": datetime.now(timezone.utc).isoformat(),
                   "audit_before_count": len(before),
                   "audit_before_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()}
    with path.open("x") as stream:
        json.dump(reservation, stream)
    try:
        operation()
        verify_hashes(before)
        after = {relative(p): digest(p) for p in runtime.audit.glob("attempt-*.json")}
        new = {n: h for n, h in after.items() if n not in before}
        result = {**reservation, "status": "recorded", "raw_sha256": digest(record_path(cell)), "audit_files": new,
                  "recorded_at": datetime.now(timezone.utc).isoformat()}
        save(path, result)
        validate_cell_ledger(cell, manifest)
        return read_json(record_path(cell))
    except BaseException as error:
        save(path, {**reservation, "status": "interrupted", "error": f"{type(error).__name__}: {error}"})
        raise


def stage_integrity(manifest, stage):
    known, response_ids, files, count = set(), set(), {}, 0
    for cell in stage_cells(manifest, stage):
        ledger = validate_cell_ledger(cell, manifest)
        if ledger is None:
            continue
        count += 1
        files[relative(ledger_path(cell))] = digest(ledger_path(cell))
        files[ledger["raw_file"]] = ledger["raw_sha256"]
        for name, expected in ledger["audit_files"].items():
            if name in known:
                raise ValueError("One transport attempt is assigned to multiple cells")
            known.add(name)
            files[name] = expected
            identity = response_identity(read_json(checked_path(name)))
            if identity is not None:
                if identity["id"] in response_ids:
                    raise ValueError("Duplicate response identity across stage cells")
                response_ids.add(identity["id"])
    model = "phi" if stage == "phi" else "qwen"
    found = {relative(p) for p in (RUN / "stages" / stage / "request-audit" / model).glob("attempt-*.json")}
    if found != known:
        raise RuntimeError("Unassigned transport audit blocks continuation")
    if len(found) > STAGE_CAPS[stage]:
        raise ValueError("Stage request ceiling exceeded")
    return {"recorded_cells": count, "planned_cells": len(stage_cells(manifest, stage)),
            "complete": count == len(stage_cells(manifest, stage)), "files": files}


def handoff(manifest, stage, create=False):
    integrity = stage_integrity(manifest, stage)
    if not integrity["complete"]:
        raise RuntimeError("Cannot hand off an incomplete stage")
    value = {"stage": stage, "status": "completed", "manifest_sha256": digest(RUN / "manifest.json"),
             "recorded_cells": integrity["recorded_cells"], "files": integrity["files"]}
    path = RUN / (stage + "-handoff.json")
    if create:
        _freeze(path, value)
    elif not path.exists() or read_json(path) != value:
        raise ValueError("Missing or changed stage handoff: " + stage)
    return value


def ensure_prior_handoffs(manifest, stage):
    for prior in STAGES[:STAGES.index(stage)]:
        handoff(manifest, prior)


def load_record(manifest, case, model, name):
    key = key_for(case, model, name)
    if key in manifest["reused_records"]:
        info = manifest["reused_records"][key]
        path = checked_path(info["file"])
        if digest(path) != info["sha256"]:
            raise ValueError("Reused preflight generation changed")
        return read_json(path), path, True
    cell = dict(case_id=case, model=model, name=name,
                kind="native" if name == "native-writer" else "summary" if name == "summary-writer" else "reader",
                stage=stage_for(model, name))
    ledger = validate_cell_ledger(cell, manifest)
    return (read_json(record_path(cell)), record_path(cell), False) if ledger else (None, record_path(cell), False)


def evidence_for(instance, arm, manifest, case):
    if arm == "no_history":
        return "No earlier personal history is available."
    if arm == "full_history":
        return writer_history(instance)
    if arm == "bm25_history":
        indices = bm25_selection(instance)
        return writer_history({"history": [instance["history"][i] for i in indices]})
    kind, model = arm.split("_")
    raw, _, _ = load_record(manifest, case, model, "native-writer" if kind == "native" else "summary-writer")
    if raw is None:
        raise RuntimeError("Required writer has not been recorded")
    return native_text(raw) if kind == "native" else summary_text(raw) or "No usable profile was generated."


def refresh_report(manifest):
    verify_hashes(manifest["reused_raw_hashes"])
    verify_hashes(manifest["dependencies"])
    raw_files = dict(manifest["reused_raw_hashes"])
    stage_status, stage_reports = {}, {}
    previous_complete = True
    for stage in STAGES:
        status = stage_integrity(manifest, stage)
        if status["recorded_cells"] and not previous_complete:
            raise RuntimeError("Later stage exists without previous completed handoff")
        if (RUN / (stage + "-handoff.json")).exists():
            handoff(manifest, stage)
            stage_status[stage] = "completed"
            raw_files[relative(RUN / (stage + "-handoff.json"))] = digest(RUN / (stage + "-handoff.json"))
        else:
            stage_status[stage] = "incomplete"
        previous_complete = previous_complete and stage_status[stage] == "completed"
        raw_files.update(status["files"])
        stage_reports[stage] = {k: v for k, v in status.items() if k != "files"}
    writers, readers = [], []
    for case in manifest["cases"]:
        valid_writers = {}
        for model in ("qwen", "phi"):
            native, native_path, reused = load_record(manifest, case, model, "native-writer")
            summary, summary_path, _ = load_record(manifest, case, model, "summary-writer")
            if native is not None:
                valid_writers["native_" + model] = native_valid(native)
            if summary is not None:
                valid_writers["summary_" + model] = summary_text(summary) is not None and summary.get("status") == "completed"
            if native is None or summary is None:
                continue
            row = writer_summary(case, model, native, summary)
            row.update(model=model, native_valid=valid_writers["native_" + model], summary_valid=valid_writers["summary_" + model],
                       native_file=relative(native_path), summary_file=relative(summary_path),
                       native_path=relative(native_path), summary_path=relative(summary_path),
                       native_sha256=digest(native_path), summary_sha256=digest(summary_path), reused=reused)
            writers.append(row)
        for model in ("qwen", "phi"):
            for arm in ARMS:
                raw, path, reused = load_record(manifest, case, model, arm)
                if raw is None:
                    continue
                needs_writer = arm.startswith("native_") or arm.startswith("summary_")
                if needs_writer and arm not in valid_writers:
                    raise ValueError("Reader is recorded before its writer")
                writer_ok = valid_writers.get(arm, True)
                reader_ok = bool(raw.get("status") == "completed" and reader_valid(raw))
                readers.append({"case_id": case, "reader": model, "arm": arm,
                                **response_summary(raw), "file": relative(path), "raw_path": relative(path), "raw_sha256": digest(path),
                                "reused": reused, "reader_valid": reader_ok,
                                "required_writer_valid": writer_ok,
                                "diagnostic_fallback_evidence": not writer_ok,
                                "pipeline_valid": reader_ok and writer_ok,
                                "operational_constant3_required": not (reader_ok and writer_ok)})
    audit_files = {n: h for n, h in raw_files.items() if "/request-audit/" in n}
    audit_rows = []
    all_response_ids = set()
    for name, expected in sorted(audit_files.items()):
        raw = read_json(checked_path(name))
        identity = response_identity(raw)
        if identity is not None:
            if identity["id"] in all_response_ids:
                raise ValueError("Duplicate response identity across the combined development run")
            all_response_ids.add(identity["id"])
        audit_rows.append({"file": name, "sha256": expected, "status": raw["status"],
                           "transport_attempted": raw["transport_attempted"],
                           "error": raw.get("error"),
                           "reused": name in manifest["reused_raw_hashes"]})
    complete = bool(all(v == "completed" for v in stage_status.values()) and len(writers) == 120 and len(readers) == 840)
    report = {
        "phase": "development", "scope": "Engineering completion only; target outcomes remain unopened",
        "cases": manifest["cases"], "reused_cases": manifest["reused_cases"],
        "manifest_path": relative(RUN / "manifest.json"), "manifest_sha256": digest(RUN / "manifest.json"),
        "dependencies": manifest["dependencies"], "stage_status": stage_status, "stages": stage_reports,
        "raw_file_hashes": raw_files, "writers": writers, "readers": readers, "request_audit": audit_rows,
        "planned_new_cells": 1026, "reused_cells": 54, "planned_combined_cells": 1080,
        "recorded_new_cells": sum(s["recorded_cells"] for s in stage_reports.values()),
        "observed_transport_attempts": sum(a["transport_attempted"] for a in audit_rows),
        "pretransport_rejections": sum(not a["transport_attempted"] for a in audit_rows),
        "failed_transport_requests": sum(a["transport_attempted"] and a["status"] != "completed" for a in audit_rows),
        "invalid_native_writers": sum(not w["native_valid"] for w in writers),
        "invalid_summary_writers": sum(not w["summary_valid"] for w in writers),
        "invalid_readers": sum(not r["reader_valid"] for r in readers),
        "invalid_pipelines": sum(not r["pipeline_valid"] for r in readers),
        "length_limited_readers": sum(r["finish_reason"] == "length" for r in readers),
        "normally_terminated_invalid_readers": sum(r["finish_reason"] == "stop" and not r["reader_valid"] for r in readers),
        "protocol_error_requests": sum(a["status"] == "error" and any(
            text in (a["error"] or "").lower() for text in ("wrong model", "wrong model identity", "resource allowance", "wrong tokenizer"))
            for a in audit_rows),
        "complete": complete,
        "completion_definition": "all planned cells recorded and transport accounted; invalid outputs do not prevent completion",
    }
    save(OUT, report)
    return report


def run_stage(stage, inputs, manifest):
    ensure_prior_handoffs(manifest, stage)
    stage_integrity(manifest, stage)
    if (RUN / (stage + "-handoff.json")).exists():
        handoff(manifest, stage)
        return refresh_report(manifest)
    model = "phi" if stage == "phi" else "qwen"
    runtime = Runtime(model, RUN / "stages" / stage, STAGE_CAPS[stage])
    client = runtime.client()
    try:
        for cell in stage_cells(manifest, stage):
            if validate_cell_ledger(cell, manifest) is not None:
                continue
            instance = inputs[cell["case_id"]]
            path = record_path(cell)
            path.parent.mkdir(parents=True, exist_ok=True)
            if cell["kind"] == "native":
                history = writer_history(instance)
                operation = lambda: runtime.native_write(cell["case_id"], history, path.parent)
            else:
                if cell["kind"] == "summary":
                    messages = [{"role": "system", "content": SUMMARY_SYSTEM},
                                {"role": "user", "content": writer_history(instance)}]
                else:
                    evidence = evidence_for(instance, cell["name"], manifest, cell["case_id"])
                    messages = reader_query(instance, evidence)
                budget = 2048 if cell["kind"] == "summary" else 256
                operation = lambda: runtime.request(client, path, messages, budget)
            execute_cell(cell, manifest, runtime, operation)
            # Progress is engineering metadata only, never predictions or outcomes.
            print(f"{stage}: recorded {cell['case_id'][:8]}/{cell['name']}", flush=True)
        handoff(manifest, stage, create=True)
        return refresh_report(manifest)
    finally:
        client.close()


@contextmanager
def exclusive_run():
    RUN.mkdir(parents=True, exist_ok=True)
    with (RUN / "execution.lock").open("a+") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another development process holds the execution lock") from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=list(STAGES) + ["report"], required=True)
    args = parser.parse_args()
    for key in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "OPENAI_BASE_URL"):
        os.environ.pop(key, None)
    os.environ.update(MEM0_TELEMETRY="false", HF_HUB_OFFLINE="1", MEM0_DIR=str(RUN / "runtime"),
                      FASTEMBED_CACHE_PATH=str(ROOT / "models/fastembed-cache"))
    with exclusive_run():
        inputs, manifest = inputs_and_manifest()
        if args.stage == "report":
            report = refresh_report(manifest)
        else:
            from mem0_native_preflight import verify_files
            verify_files()
            verify_model("phi" if args.stage == "phi" else "qwen")
            report = run_stage(args.stage, inputs, manifest)
        print(json.dumps({k: report[k] for k in ("phase", "complete", "stage_status", "recorded_new_cells", "invalid_pipelines")}))


if __name__ == "__main__":
    main()
