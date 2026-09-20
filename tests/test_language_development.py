"""Synthetic-only inference persistence tests; no real inputs or model calls."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import run_language_development as dev
from language_cross_runtime import Runtime
from language_model_pins import model_path


class LanguageDevelopmentChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "data/language-development-v1"
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in {"ROOT": self.root, "RUN": self.run,
                            "OUT": self.root / "results/language-development.json",
                            "CROSS_REPORT": self.root / "results/language-cross-preflight.json",
                            "OLD": self.root / "old", "CROSS": self.root / "cross"}.items():
            self.stack.enter_context(patch.object(dev, name, value))
        self.case = "a" * 64
        self.manifest = {"cases": [self.case], "reused_cases": [], "reused_records": {},
                         "reused_raw_hashes": {}, "dependencies": {}}
        dev.save(self.run / "manifest.json", self.manifest)
        self.calls = []

    def cell(self, name="full_history", stage="qwen_base", model="qwen"):
        return dict(case_id=self.case, model=model, name=name,
                    kind="native" if name == "native-writer" else "summary" if name == "summary-writer" else "reader",
                    stage=stage)

    def runtime_client(self, cell, failure=False, content="[3,3,3]", token_count=10):
        runtime = Runtime(cell["model"], self.run / "stages" / cell["stage"], 399,
                          counter=lambda model, messages: {"model": model, "prompt_tokens": token_count})
        def call(**params):
            self.calls.append(params)
            if failure:
                raise TimeoutError("synthetic timeout")
            raw = {"id": f"synthetic-{len(self.calls)}", "model": str(model_path(cell["model"])),
                   "usage": {"prompt_tokens": token_count, "completion_tokens": 8, "total_tokens": token_count + 8},
                   "choices": [{"finish_reason": "stop", "message": {"content": content}}]}
            return SimpleNamespace(model_dump=lambda **kwargs: raw)
        client = runtime.instrument(SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=call))))
        return runtime, client

    def execute_reader(self, cell=None, **kwargs):
        cell = cell or self.cell()
        runtime, client = self.runtime_client(cell, **kwargs)
        messages = [{"role": "user", "content": "synthetic earlier evidence"}]
        return dev.execute_cell(cell, self.manifest, runtime,
                                lambda: runtime.request(client, dev.record_path(cell), messages, 256))

    def test_exact_new_plan_and_reuse_exclusion(self):
        cases = [f"{i:064x}" for i in range(60)]
        manifest = {"cases": cases, "reused_cases": [cases[0], cases[30], cases[-1]]}
        cells = [c for stage in dev.STAGES for c in dev.stage_cells(manifest, stage)]
        self.assertEqual(len(cells), 1026)
        self.assertEqual(len({dev.key_for(c["case_id"], c["model"], c["name"]) for c in cells}), 1026)
        self.assertEqual({s: len(dev.stage_cells(manifest, s)) for s in dev.STAGES},
                         {"qwen_base": 399, "phi": 513, "qwen_cross": 114})
        self.assertFalse(any(c["case_id"] in manifest["reused_cases"] for c in cells))

    def test_failed_transport_is_terminal_and_never_repeated(self):
        cell = self.cell()
        raw = self.execute_reader(cell, failure=True)
        self.assertEqual(raw["status"], "error")
        self.assertEqual(len(self.calls), 1)
        runtime, _ = self.runtime_client(cell)
        again = dev.execute_cell(cell, self.manifest, runtime, lambda: self.fail("must not regenerate"))
        self.assertEqual(raw, again)
        integrity = dev.stage_integrity(self.manifest, "qwen_base")
        self.assertEqual(integrity["recorded_cells"], 1)
        self.assertFalse(integrity["complete"])

    def test_invalid_reader_remains_a_recorded_cell(self):
        raw = self.execute_reader(content="not JSON")
        self.assertFalse(dev.reader_valid(raw))
        self.assertEqual(dev.stage_integrity(self.manifest, "qwen_base")["recorded_cells"], 1)

    def test_interrupt_after_runtime_response_blocks_instead_of_replaying(self):
        cell = self.cell()
        runtime, client = self.runtime_client(cell)
        def interrupted():
            runtime.request(client, dev.record_path(cell), [], 256)
            raise KeyboardInterrupt("synthetic boundary interruption")
        with self.assertRaises(KeyboardInterrupt):
            dev.execute_cell(cell, self.manifest, runtime, interrupted)
        with self.assertRaisesRegex(RuntimeError, "Interrupted or ambiguous"):
            dev.execute_cell(cell, self.manifest, runtime, lambda: self.fail("must not replay"))
        self.assertEqual(len(self.calls), 1)

    def test_unledgered_raw_started_marker_and_orphan_audit_are_blocked(self):
        cell = self.cell()
        path = dev.record_path(cell)
        dev.save(path, {"status": "completed"})
        with self.assertRaisesRegex(RuntimeError, "Unledgered"):
            dev.validate_cell_ledger(cell, self.manifest)
        path.unlink()
        path.with_suffix(".started").write_text("reserved")
        with self.assertRaisesRegex(RuntimeError, "Unledgered"):
            dev.validate_cell_ledger(cell, self.manifest)
        path.with_suffix(".started").unlink()
        audit = self.run / "stages/qwen_base/request-audit/qwen/attempt-001.json"
        dev.save(audit, {"status": "started"})
        with self.assertRaisesRegex(RuntimeError, "Unassigned"):
            dev.stage_integrity(self.manifest, "qwen_base")

    def test_changed_raw_and_audit_records_are_rejected(self):
        cell = self.cell()
        self.execute_reader(cell)
        original = dev.record_path(cell).read_bytes()
        raw = dev.read_json(dev.record_path(cell))
        raw["response"]["choices"][0]["message"]["content"] = "[1,1,1]"
        dev.save(dev.record_path(cell), raw)
        with self.assertRaisesRegex(ValueError, "Recorded file changed"):
            dev.validate_cell_ledger(cell, self.manifest)
        dev.record_path(cell).write_bytes(original)
        ledger = dev.read_json(dev.ledger_path(cell))
        audit_path = dev.checked_path(next(iter(ledger["audit_files"])))
        audit_path.write_text("{}")
        with self.assertRaisesRegex(ValueError, "Recorded file changed"):
            dev.validate_cell_ledger(cell, self.manifest)

    def test_native_failure_before_transport_is_preserved_without_fake_audit(self):
        cell = self.cell("native-writer")
        runtime, _ = self.runtime_client(cell)
        def failure():
            dev.save(dev.record_path(cell), {"model": "qwen", "status": "error", "case_id": self.case,
                     "input": "fixture", "error": "synthetic setup failure", "seconds": 0.0, "traces": []})
        raw = dev.execute_cell(cell, self.manifest, runtime, failure)
        self.assertEqual(raw["status"], "error")
        self.assertEqual(dev.read_json(dev.ledger_path(cell))["audit_files"], {})
        self.assertEqual(self.calls, [])
        self.assertEqual(dev.native_text(raw), "No stored memories are available.")

    def test_token_overflow_is_recorded_without_transport(self):
        cell = self.cell()
        raw = self.execute_reader(cell, token_count=16384)
        self.assertEqual(raw["status"], "error")
        self.assertEqual(self.calls, [])
        self.assertIsNotNone(dev.validate_cell_ledger(cell, self.manifest))

    def test_handoff_requires_completion_and_detects_later_change(self):
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            dev.handoff(self.manifest, "qwen_base", create=True)
        cell = self.cell()
        self.execute_reader(cell)
        with patch.object(dev, "stage_cells", return_value=[cell]):
            dev.handoff(self.manifest, "qwen_base", create=True)
            dev.handoff(self.manifest, "qwen_base")
            path = self.run / "qwen_base-handoff.json"
            value = dev.read_json(path)
            value["manifest_sha256"] = "changed"
            dev.save(path, value)
            with self.assertRaisesRegex(ValueError, "handoff"):
                dev.handoff(self.manifest, "qwen_base")

    def test_phi_cannot_start_without_qwen_handoff(self):
        with self.assertRaises(RuntimeError):
            dev.ensure_prior_handoffs(self.manifest, "phi")

    def test_reuse_inventory_maps_all_54_without_reserializing(self):
        cases = [f"{i:064x}" for i in range(3)]
        preflight = {"cases": cases, "writers": [], "readers": [], "reused_raw_hashes": {}, "new_request_audit": []}
        originals = {}
        for case in cases:
            for model in ("qwen", "phi"):
                directory = dev.OLD / case if model == "qwen" else dev.CROSS / case / model
                writer = {"case_id": case, "writer": model}
                for name, field in (("native-writer", "native_sha256"), ("summary-writer", "summary_sha256")):
                    path = directory / (name + ".json")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b'{ "fixture": true }\n')
                    originals[path] = path.read_bytes()
                    writer[field] = dev.digest(path)
                preflight["writers"].append(writer)
                for arm in dev.ARMS:
                    old = next((k for k, v in dev.OLD_ARM.items() if v == arm), None)
                    path = dev.OLD / case / (old + ".json") if model == "qwen" and old else dev.CROSS / case / model / (arm + ".json")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b'{ "reader": true }\n')
                    originals[path] = path.read_bytes()
                    preflight["readers"].append({"case_id": case, "reader": model, "arm": arm, "raw_sha256": dev.digest(path)})
        records, hashes = dev.build_reuse_inventory(preflight)
        self.assertEqual(len(records), 54)
        self.assertEqual(len(hashes), 54)
        self.assertTrue(all(path.read_bytes() == value for path, value in originals.items()))
        next(iter(originals)).write_text('{"modified":true}')
        with self.assertRaisesRegex(ValueError, "Recorded file changed"):
            dev.build_reuse_inventory(preflight)

    def test_path_traversal_is_rejected(self):
        for name in ("../outside.json", "/tmp/absolute.json"):
            with self.assertRaisesRegex(ValueError, "outside"):
                dev.checked_path(name)

    def test_preflight_gate_rejects_incomplete_without_opening_input_file(self):
        dev.save(self.root / "results/language-extension-input-preparation.json", {})
        dev.save(dev.CROSS_REPORT, {"complete": False, "prototype_pass": False})
        with self.assertRaisesRegex(ValueError, "Completed passed crossed preflight"):
            dev.inputs_and_manifest()
        self.assertFalse((self.run / "manifest.json").read_text().find("expected_combined_cells") >= 0)

    def test_report_does_not_mistake_valid_sentinel_read_for_valid_pipeline(self):
        native = {"status": "error", "seconds": 0.0, "traces": [], "error": "synthetic writer failure"}
        summary = {"status": "completed", "seconds": 0.0, "response": {
            "choices": [{"finish_reason": "stop", "message": {"content": '{"profile":"synthetic earlier profile"}'}}]}}
        reader = {"status": "completed", "seconds": 0.0, "response": {
            "choices": [{"finish_reason": "stop", "message": {"content": "[3,3,3]"}}]}}
        records, hashes = {}, {}
        for name, raw in (("native-writer", native), ("summary-writer", summary), ("native_qwen", reader)):
            path = self.root / "reused" / (name + ".json")
            dev.save(path, raw)
            records[dev.key_for(self.case, "qwen", name)] = {"file": dev.relative(path), "sha256": dev.digest(path)}
            hashes[dev.relative(path)] = dev.digest(path)
        manifest = {**self.manifest, "reused_cases": [self.case], "reused_records": records, "reused_raw_hashes": hashes}
        dev.save(self.run / "manifest.json", manifest)
        report = dev.refresh_report(manifest)
        self.assertFalse(report["complete"])
        self.assertEqual(report["invalid_native_writers"], 1)
        self.assertEqual(report["invalid_readers"], 0)
        self.assertEqual(report["invalid_pipelines"], 1)
        row = report["readers"][0]
        self.assertTrue(row["reader_valid"])
        self.assertFalse(row["required_writer_valid"])
        self.assertFalse(row["pipeline_valid"])
        self.assertTrue(row["diagnostic_fallback_evidence"])
        self.assertTrue(row["operational_constant3_required"])
        self.assertEqual(row["file"], row["raw_path"])

    def test_duplicate_response_id_is_not_two_auditable_generations(self):
        first, second = self.cell("full_history"), self.cell("no_history")
        self.execute_reader(first)
        self.execute_reader(second)
        raw = dev.read_json(dev.record_path(second))
        raw["response"]["id"] = "synthetic-1"
        dev.save(dev.record_path(second), raw)
        ledger = dev.read_json(dev.ledger_path(second))
        audit_path = dev.checked_path(next(iter(ledger["audit_files"])))
        audit = dev.read_json(audit_path)
        audit["response"]["id"] = "synthetic-1"
        dev.save(audit_path, audit)
        ledger["raw_sha256"] = dev.digest(dev.record_path(second))
        ledger["audit_files"][dev.relative(audit_path)] = dev.digest(audit_path)
        dev.save(dev.ledger_path(second), ledger)
        with self.assertRaisesRegex(ValueError, "Duplicate response identity"):
            dev.stage_integrity(self.manifest, "qwen_base")

    def test_completed_audit_rejects_invalid_completion_usage(self):
        cell = self.cell()
        self.execute_reader(cell)
        ledger = dev.read_json(dev.ledger_path(cell))
        original = dev.read_json(dev.checked_path(next(iter(ledger["audit_files"]))))
        for value in (257, -1, True, False, 8.0, "8", None):
            altered = json.loads(json.dumps(original))
            altered["response"]["usage"]["completion_tokens"] = value
            with self.subTest(completion_tokens=value):
                with self.assertRaisesRegex(ValueError, "completion usage"):
                    dev.check_audit(altered, "qwen", 256)
        altered = json.loads(json.dumps(original))
        del altered["response"]["usage"]["completion_tokens"]
        with self.assertRaisesRegex(ValueError, "completion usage"):
            dev.check_audit(altered, "qwen", 256)

    def test_completed_audit_requires_exact_integer_total_tokens(self):
        cell = self.cell()
        self.execute_reader(cell)
        ledger = dev.read_json(dev.ledger_path(cell))
        original = dev.read_json(dev.checked_path(next(iter(ledger["audit_files"]))))
        for value in (17, 19, -1, True, False, 18.0, "18", None):
            altered = json.loads(json.dumps(original))
            altered["response"]["usage"]["total_tokens"] = value
            with self.subTest(total_tokens=value):
                with self.assertRaisesRegex(ValueError, "token total"):
                    dev.check_audit(altered, "qwen", 256)
        altered = json.loads(json.dumps(original))
        del altered["response"]["usage"]["total_tokens"]
        with self.assertRaisesRegex(ValueError, "token total"):
            dev.check_audit(altered, "qwen", 256)

    def test_completed_audit_accepts_zero_and_full_completion_budget(self):
        cell = self.cell()
        self.execute_reader(cell)
        ledger = dev.read_json(dev.ledger_path(cell))
        original = dev.read_json(dev.checked_path(next(iter(ledger["audit_files"]))))
        for value in (0, 256):
            altered = json.loads(json.dumps(original))
            altered["response"]["usage"].update(completion_tokens=value, total_tokens=10 + value)
            dev.check_audit(altered, "qwen", 256)


if __name__ == "__main__":
    unittest.main()
