"""Descriptive resource accounting after complete development inference.

No labels, source archives, reserved inputs, inference endpoint or model weights
are opened. This is a resource report, not a new accuracy analysis.
"""
import hashlib
import json
from pathlib import Path

import verify_language_development as verification
from language_resource_summary import summarize_resources

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "results/language-development-resources.json"


def response_id(value):
    response = value.get("response")
    identity = response.get("id") if isinstance(response, dict) else None
    if response is not None and (not isinstance(identity, str) or not identity):
        raise ValueError("Recorded model response lacks an identity")
    return identity


def normalized_records(report, manifest, load):
    """Adapt verified raw artifacts without touching target outcomes.

    The caller verifies file hashes and stage handoffs first. This adapter also
    requires one-to-one attribution of every audited request to a planned cell.
    """
    if report.get("complete") is not True or report.get("phase") != "development":
        raise ValueError("Resource accounting requires complete development inference")
    audits, by_response, assigned = {}, {}, set()
    for row in report["request_audit"]:
        name = row["file"]
        if name in audits or report["raw_file_hashes"].get(name) != row["sha256"]:
            raise ValueError("Duplicate or uncovered request audit")
        raw = load(name)
        if (raw.get("status") != row["status"] or
                raw.get("transport_attempted") != row["transport_attempted"]):
            raise ValueError("Audit summary disagrees with saved transport state")
        audits[name] = raw
        rid = response_id(raw)
        if rid is not None:
            if rid in by_response:
                raise ValueError("Duplicate audited model response identity")
            by_response[rid] = name

    writers, records = {}, []

    def requests(case, model, condition, path, raw, reused):
        key = f"{case}/{model}/{condition}"
        retained = raw.get("traces", []) if condition == "native-writer" else (
            [raw] if raw.get("response") is not None else [])
        if reused:
            expected = manifest["reused_records"].get(key)
            if (not expected or expected["file"] != path or
                    expected["sha256"] != report["raw_file_hashes"].get(path)):
                raise ValueError("Reused cell differs from frozen preflight inventory")
            names = []
            for trace in retained:
                rid = response_id(trace)
                if rid not in by_response:
                    raise ValueError("Reused response has no unique transport audit")
                names.append(by_response[rid])
        else:
            stage = "phi" if model == "phi" else (
                "qwen_cross" if condition in ("native_phi", "summary_phi") else "qwen_base")
            ledger_path = f"data/language-development-v1/cells/{stage}/{case}/{model}/{condition}.json"
            if ledger_path not in report["raw_file_hashes"]:
                raise ValueError("New resource cell lacks a verified ledger")
            ledger = load(ledger_path)
            if (ledger.get("status") != "recorded" or ledger.get("raw_file") != path or
                    ledger.get("raw_sha256") != report["raw_file_hashes"].get(path) or
                    ledger.get("manifest_sha256") != report["manifest_sha256"]):
                raise ValueError("New resource cell differs from its recorded ledger")
            names = list(ledger["audit_files"])
            if any(report["raw_file_hashes"].get(n) != h for n, h in ledger["audit_files"].items()):
                raise ValueError("New transport attribution is not hash covered")
        if len(names) > 1 or (not names and not (condition == "native-writer" and raw.get("status") == "error")):
            raise ValueError("Unexpected request count for a resource cell")
        if any(n not in audits or n in assigned for n in names):
            raise ValueError("Request is missing or attributed to multiple cells")
        assigned.update(names)
        # Compare entire retained response objects, not just provider IDs.
        for trace in retained:
            rid = response_id(trace)
            matches = [n for n in names if response_id(audits[n]) == rid]
            if len(matches) != 1 or trace["response"] != audits[matches[0]].get("response"):
                raise ValueError("Raw model response differs from its transport audit")
        if raw.get("status") == "completed" and len(retained) != sum(
                audits[n].get("response") is not None for n in names):
            raise ValueError("Completed resource cell loses an audited response")
        rows = []
        for name in names:
            audit = audits[name]
            response = audit.get("response")
            usage = response.get("usage") if isinstance(response, dict) else None
            usage = usage if isinstance(usage, dict) else {}
            rows.append({
                "audit_id": name, "status": audit["status"],
                "transport_attempted": audit["transport_attempted"],
                "response_present": isinstance(response, dict),
                "prompt_tokens": audit.get("tokenizer", {}).get("prompt_tokens"),
                "response_prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "total_token_allowance": audit.get("total_token_allowance"),
                "seconds": audit.get("seconds"),
            })
        return rows

    def base(case, model, condition, path, raw, valid):
        reused = case in manifest["reused_cases"]
        return {
            "case_id": case, "model": model, "condition": condition,
            "reused": reused, "status": raw["status"], "valid": bool(valid),
            "reader_valid": None, "required_writer_valid": None,
            "seconds": raw.get("seconds"), "memory_entries": None, "memory_words": None,
            "requests": requests(case, model, condition, path, raw, reused),
        }

    for row in report["writers"]:
        case, model = row["case_id"], row["writer"]
        for kind in ("native", "summary"):
            path = row[kind + "_path"]
            raw = load(path)
            valid = verification.valid_native(raw) if kind == "native" else verification.valid_summary(raw)
            if type(row.get(kind + "_valid")) is not bool or row[kind + "_valid"] != valid:
                raise ValueError("Writer validity disagrees with reparsed raw output")
            key = (case, model, kind)
            if key in writers:
                raise ValueError("Duplicate resource writer")
            writers[key] = valid
            record = base(case, model, kind + "-writer", path, raw, valid)
            if kind == "native":
                stored_record = raw.get("stored")
                stored = stored_record.get("results") if isinstance(stored_record, dict) else None
                if isinstance(stored, list):
                    record["memory_entries"] = len(stored)
                    if all(isinstance(r, dict) and isinstance(r.get("memory"), str) for r in stored):
                        record["memory_words"] = sum(len(r["memory"].split()) for r in stored)
            elif valid:
                content = verification.stopped_content(raw).strip()
                if content.startswith("```json\n") and content.endswith("\n```"):
                    content = content[8:-4].strip()
                record["memory_words"] = len(json.loads(content)["profile"].split())
            records.append(record)

    for row in report["readers"]:
        case, model, condition = row["case_id"], row["reader"], row["arm"]
        path = row["raw_path"]
        raw = load(path)
        reader_valid = verification.decode_reader(raw) is not None
        writer_valid = True
        if condition.startswith(("native_", "summary_")):
            kind, writer = condition.split("_", 1)
            writer_valid = writers[(case, writer, kind)]
        pipeline_valid = reader_valid and writer_valid
        flags = {"reader_valid": reader_valid, "required_writer_valid": writer_valid,
                 "pipeline_valid": pipeline_valid, "diagnostic_fallback_evidence": not writer_valid,
                 "operational_constant3_required": not pipeline_valid}
        if any(type(row.get(k)) is not bool or row[k] != value for k, value in flags.items()):
            raise ValueError("Reader resource validity disagrees with complete pipeline")
        record = base(case, model, condition, path, raw, pipeline_valid)
        record.update(reader_valid=reader_valid, required_writer_valid=writer_valid)
        records.append(record)
    if assigned != set(audits):
        raise ValueError("Some audited requests are not attributed to a resource cell")
    return records


def main():
    # This verifies all three completed stages without opening a label artifact.
    report, manifest, _ = verification.verify_inference_before_labels(ROOT)
    import run_language_development as runner
    for stage in runner.STAGES:
        runner.handoff(manifest, stage)

    def load(name):
        if name not in report["raw_file_hashes"]:
            raise ValueError("Resource adapter requested an unverified raw artifact")
        return verification.load_json(ROOT, name)

    result = summarize_resources(normalized_records(report, manifest, load))
    result.update(
        phase="development", accuracy_computed=False,
        inference_report_sha256=verification.file_hash(ROOT / verification.REPORT),
        manifest_sha256=report["manifest_sha256"],
        dependencies={name: verification.file_hash(ROOT / name) for name in (
            "src/summarize_language_development_resources.py", "src/language_resource_summary.py",
            "src/verify_language_development.py", "docs/language-resource-reporting.md")},
    )
    payload = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    path = ROOT / OUTPUT
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("Existing resource summary differs; refusing to overwrite")
    else:
        with path.open("xb") as stream:
            stream.write(payload)
    print(json.dumps({"file": OUTPUT, "sha256": hashlib.sha256(payload).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
