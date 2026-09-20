"""Invented raw-artifact adapter tests, with no dataset or inference access."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from summarize_language_development_resources import normalized_records
from language_resource_summary import summarize_resources

ARMS = ("no_history", "full_history", "native_qwen", "summary_qwen",
        "native_phi", "summary_phi", "bm25_history")


def fixture():
    cases = [f"user{i:03}" for i in range(60)]
    manifest = {"reused_cases": cases[:3], "reused_records": {}}
    report = {"phase": "development", "complete": True, "manifest_sha256": "m" * 64,
              "raw_file_hashes": {}, "request_audit": [], "writers": [], "readers": []}
    files = {}

    def save(name, value):
        files[name] = value
        report["raw_file_hashes"][name] = "a" * 64

    for case in cases:
        for model in ("qwen", "phi"):
            paths = {}
            for condition in ("native-writer", "summary-writer") + ARMS:
                path = f"raw/{case}/{model}/{condition}.json"
                paths[condition] = path
                content = '{"facts":["Earlier preference"]}' if condition == "native-writer" else (
                    '{"profile":"Earlier preferences."}' if condition == "summary-writer" else "[1,2,3]")
                response = {"id": f"{case}:{model}:{condition}", "model": model,
                            "choices": [{"finish_reason": "stop", "message": {"content": content}}],
                            "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110}}
                raw = {"status": "completed", "seconds": 3., "response": deepcopy(response)}
                if condition == "native-writer":
                    raw = {"status": "completed", "seconds": 7.,
                           "add": {"results": [{"id": "memory1", "memory": "Earlier preference"}]},
                           "stored": {"results": [{"id": "memory1", "memory": "Earlier preference"}]},
                           "traces": [{"response": deepcopy(response)}]}
                save(path, raw)
                audit = f"audits/{case}/{model}/{condition}.json"
                save(audit, {"status": "completed", "transport_attempted": True,
                             "tokenizer": {"prompt_tokens": 100}, "response": response,
                             "total_token_allowance": 100 + (2048 if condition.endswith("writer") else 256),
                             "seconds": 2.})
                report["request_audit"].append({"file": audit, "sha256": "a" * 64,
                                                "status": "completed", "transport_attempted": True})
                if case in manifest["reused_cases"]:
                    manifest["reused_records"][f"{case}/{model}/{condition}"] = {
                        "file": path, "sha256": "a" * 64}
                else:
                    stage = "phi" if model == "phi" else (
                        "qwen_cross" if condition in ("native_phi", "summary_phi") else "qwen_base")
                    ledger = f"data/language-development-v1/cells/{stage}/{case}/{model}/{condition}.json"
                    save(ledger, {"status": "recorded", "raw_file": path, "raw_sha256": "a" * 64,
                                  "manifest_sha256": "m" * 64, "audit_files": {audit: "a" * 64}})
            report["writers"].append({"case_id": case, "writer": model,
                                      "native_path": paths["native-writer"], "native_valid": True,
                                      "summary_path": paths["summary-writer"], "summary_valid": True})
            for arm in ARMS:
                report["readers"].append({"case_id": case, "reader": model, "arm": arm,
                                         "raw_path": paths[arm], "reader_valid": True,
                                         "required_writer_valid": True, "pipeline_valid": True,
                                         "diagnostic_fallback_evidence": False,
                                         "operational_constant3_required": False})
    return report, manifest, files


class ResourceAdapterTests(unittest.TestCase):
    def test_complete_reused_and_new_attribution(self):
        report, manifest, files = fixture()
        rows = normalized_records(report, manifest, files.__getitem__)
        self.assertEqual(len(rows), 1080)
        self.assertEqual(sum(row["reused"] for row in rows), 54)
        self.assertEqual(sum(len(row["requests"]) for row in rows), 1080)
        self.assertEqual(len({q["audit_id"] for row in rows for q in row["requests"]}), 1080)
        self.assertTrue(all(row["valid"] for row in rows))
        native = [row for row in rows if row["condition"] == "native-writer"]
        self.assertEqual(len(native), 120)
        self.assertTrue(all(row["memory_entries"] == 1 and row["memory_words"] == 2 for row in native))
        # Integration invokes the production aggregator on the entire invented grid.
        json.dumps(summarize_resources(rows), allow_nan=False)

    def test_invalid_writer_keeps_valid_diagnostic_reader_and_resources(self):
        report, manifest, files = fixture()
        case = "user003"
        files[f"raw/{case}/qwen/native-writer.json"]["stored"]["results"] = []
        for row in report["writers"]:
            if row["case_id"] == case and row["writer"] == "qwen":
                row["native_valid"] = False
        for row in report["readers"]:
            if row["case_id"] == case and row["arm"] == "native_qwen":
                row.update(required_writer_valid=False, pipeline_valid=False,
                           diagnostic_fallback_evidence=True, operational_constant3_required=True)
        rows = normalized_records(report, manifest, files.__getitem__)
        affected = [row for row in rows if row["case_id"] == case and row["condition"] == "native_qwen"]
        self.assertEqual(len(affected), 2)
        self.assertTrue(all(row["reader_valid"] and not row["valid"] for row in affected))
        self.assertEqual(sum(len(row["requests"]) for row in rows), 1080)
        json.dumps(summarize_resources(rows), allow_nan=False)

    def test_reject_incomplete_report_before_loading_any_artifact(self):
        with self.assertRaisesRegex(ValueError, "complete development"):
            normalized_records({"phase": "development", "complete": False}, {},
                               lambda _: self.fail("Must reject before reading artifacts"))

    def test_native_setup_failure_has_no_invented_request_or_memory_size(self):
        report, manifest, files = fixture()
        case = "user003"
        path = f"raw/{case}/qwen/native-writer.json"
        files[path] = {"status": "error", "seconds": 1., "traces": [], "stored": None}
        audit = f"audits/{case}/qwen/native-writer.json"
        report["request_audit"] = [row for row in report["request_audit"] if row["file"] != audit]
        ledger = f"data/language-development-v1/cells/qwen_base/{case}/qwen/native-writer.json"
        files[ledger]["audit_files"] = {}
        for row in report["writers"]:
            if row["case_id"] == case and row["writer"] == "qwen":
                row["native_valid"] = False
        for row in report["readers"]:
            if row["case_id"] == case and row["arm"] == "native_qwen":
                row.update(required_writer_valid=False, pipeline_valid=False,
                           diagnostic_fallback_evidence=True, operational_constant3_required=True)
        rows = normalized_records(report, manifest, files.__getitem__)
        failed = next(row for row in rows if row["case_id"] == case and
                      row["model"] == "qwen" and row["condition"] == "native-writer")
        self.assertEqual(failed["requests"], [])
        self.assertIsNone(failed["memory_entries"])
        self.assertIsNone(failed["memory_words"])
        self.assertEqual(sum(len(row["requests"]) for row in rows), 1079)
        json.dumps(summarize_resources(rows), allow_nan=False)

    def test_failed_transport_preserves_unavailable_usage(self):
        report, manifest, files = fixture()
        path = "raw/user003/qwen/full_history.json"
        files[path] = {"status": "error", "seconds": 360.}
        name = "audits/user003/qwen/full_history.json"
        audit = files[name]
        audit["status"] = "error"
        audit.pop("response")
        for row in report["request_audit"]:
            if row["file"] == name:
                row["status"] = "error"
        for row in report["readers"]:
            if row["raw_path"] == path:
                row.update(reader_valid=False, pipeline_valid=False, operational_constant3_required=True)
        rows = normalized_records(report, manifest, files.__getitem__)
        failed = next(row for row in rows if row["case_id"] == "user003" and
                      row["model"] == "qwen" and row["condition"] == "full_history")
        self.assertFalse(failed["valid"])
        self.assertEqual(len(failed["requests"]), 1)
        request = failed["requests"][0]
        self.assertTrue(request["transport_attempted"])
        self.assertFalse(request["response_present"])
        self.assertEqual(request["prompt_tokens"], 100)
        self.assertIsNone(request["completion_tokens"])
        self.assertIsNone(request["total_tokens"])
        self.assertIsNone(request["response_prompt_tokens"])
        json.dumps(summarize_resources(rows), allow_nan=False)

    def test_reject_duplicate_or_unassigned_audit_and_response_mismatch(self):
        for change in ("duplicate", "unassigned", "mismatched_response", "lost_ledger", "wrong_reuse"):
            report, manifest, files = fixture()
            if change == "duplicate":
                report["request_audit"].append(deepcopy(report["request_audit"][0]))
            elif change == "unassigned":
                row = deepcopy(report["request_audit"][0]); row["file"] = "extra.json"
                raw = deepcopy(files[report["request_audit"][0]["file"]]); raw["response"]["id"] = "extra"
                report["request_audit"].append(row); report["raw_file_hashes"]["extra.json"] = "a" * 64
                files["extra.json"] = raw
            elif change == "mismatched_response":
                files["raw/user000/qwen/full_history.json"]["response"]["usage"]["completion_tokens"] = 11
            elif change == "lost_ledger":
                del report["raw_file_hashes"]["data/language-development-v1/cells/qwen_base/user003/qwen/full_history.json"]
            else:
                manifest["reused_records"]["user000/qwen/full_history"]["file"] = "wrong.json"
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalized_records(report, manifest, files.__getitem__)

    def test_reject_forged_writer_or_pipeline_validity(self):
        for table, field in (("writers", "native_valid"), ("readers", "pipeline_valid")):
            report, manifest, files = fixture()
            report[table][0][field] = False
            with self.subTest(table=table), self.assertRaisesRegex(ValueError, "validity"):
                normalized_records(report, manifest, files.__getitem__)


if __name__ == "__main__":
    unittest.main()
