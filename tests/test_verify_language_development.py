"""Invented data only: independent parser, complete-family and artifact checks."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import verify_language_development as audit


def response(content="[1,3,5]", finish="stop"):
    return {"status": "completed", "response": {"choices": [
        {"finish_reason": finish, "message": {"content": content}}]}}


def native():
    return {"status": "completed", "add": {"results": [{"id": "a", "memory": "Earlier preference"}]},
            "stored": {"results": [{"id": "a", "memory": "Earlier preference"}]},
            "traces": [response("{}")]}


def raw_grid(cases):
    files, writers, readers = {}, [], []
    for case in cases:
        for writer in audit.READERS:
            npath, spath = f"raw/{case}/{writer}/native.json", f"raw/{case}/{writer}/summary.json"
            files[npath] = native()
            files[spath] = response('{"profile":"Earlier preferences."}')
            writers.append({"case_id": case, "writer": writer, "model": writer,
                            "native_path": npath, "native_file": npath, "native_valid": True,
                            "summary_path": spath, "summary_file": spath, "summary_valid": True})
        for reader in audit.READERS:
            for arm in audit.ARMS:
                path = f"raw/{case}/{reader}/{arm}.json"
                files[path] = response()
                readers.append({"case_id": case, "reader": reader, "arm": arm,
                                "file": path, "raw_path": path, "reader_valid": True,
                                "required_writer_valid": True, "diagnostic_fallback_evidence": False,
                                "pipeline_valid": True, "operational_constant3_required": False})
    return {"cases": cases, "writers": writers, "readers": readers}, files


class IndependentCalculationTests(unittest.TestCase):
    def test_reader_contract_rejects_malformed_and_truncated_values(self):
        for text in ("[true,3,5]", "[1,3]", "[1,3,5,4]", "[NaN,3,5]", "[Infinity,3,5]",
                     "[0,3,5]", "[1,3,6]", '["1",3,5]', "explanation [1,3,5]", "null"):
            with self.subTest(text=text):
                self.assertIsNone(audit.decode_reader(response(text)))
        self.assertIsNone(audit.decode_reader(response("[1,3,5]", "length")))
        self.assertEqual(audit.decode_reader(response("```json\n[1,3,5]\n```")), [1., 3., 5.])
        self.assertEqual(audit.decode_reader(response("```\n[1,3,5]\n```")), [1., 3., 5.])
        self.assertIsNone(audit.decode_reader({"status": "error", **{"response": response()["response"]}}))

    def test_summary_and_native_validity_do_not_trust_export_flags(self):
        self.assertTrue(audit.valid_summary(response('{"profile":"Earlier preferences."}')))
        for text in ('{"profile":""}', '{"profile":"p","extra":1}',
                     json.dumps({"profile": "word " * 401}), '```\n{"profile":"p"}\n```'):
            self.assertFalse(audit.valid_summary(response(text)))
        self.assertFalse(audit.valid_summary(response('{"profile":"p"}', "length")))
        self.assertTrue(audit.valid_native(native()))
        for mutation in ("empty", "different_text", "duplicate", "length", "cleanup"):
            raw = native()
            raw["export_complete"] = True
            if mutation == "empty": raw["stored"]["results"] = []
            elif mutation == "different_text": raw["stored"]["results"][0]["memory"] = "Different"
            elif mutation == "duplicate": raw["stored"]["results"].append(raw["stored"]["results"][0])
            elif mutation == "length": raw["traces"][0]["response"]["choices"][0]["finish_reason"] = "length"
            else: raw["cleanup_error"] = "failure"
            with self.subTest(mutation=mutation): self.assertFalse(audit.valid_native(raw))

    def test_invalid_writer_valid_reader_forces_operational_three(self):
        report, files = raw_grid(["case"])
        row = next(w for w in report["writers"] if w["writer"] == "phi")
        files[row["native_path"]]["stored"]["results"] = []
        row["native_valid"] = False
        for reader in report["readers"]:
            if reader["arm"] == "native_phi":
                reader.update(required_writer_valid=False, diagnostic_fallback_evidence=True,
                              pipeline_valid=False, operational_constant3_required=True)
        pipelines = audit.read_pipelines(report, files.__getitem__)
        self.assertEqual(pipelines[("case", "qwen", "native_phi")], ([3., 3., 3.], False))
        self.assertEqual(pipelines[("case", "qwen", "full_history")], ([1., 3., 5.], True))
        report["readers"][0]["pipeline_valid"] = False
        with self.assertRaisesRegex(ValueError, "validity flags"):
            audit.read_pipelines(report, files.__getitem__)

    def test_whole_family_metrics_common_valid_baselines_and_rmse(self):
        cases = [f"c{i}" for i in range(60)]
        targets = {c: [1., 3., 5.] if i % 2 == 0 else [2., 2., 2.] for i, c in enumerate(cases)}
        histories = {c: [1] * 6 + [5] * 6 if i % 2 == 0 else [2] * 12 for i, c in enumerate(cases)}
        cells = {(c, r, a): (targets[c][:], True) for c in cases for r in audit.READERS for a in audit.ARMS}
        for reader in audit.READERS:
            cells[(cases[0], reader, "native_phi")] = ([3., 3., 3.], False)
        systems, contrasts = audit.calculate(cases, targets, histories, cells)
        self.assertEqual(len(systems), 17)
        self.assertEqual(len(contrasts), 8)
        row = systems["qwen/native_phi"]["summary"]
        self.assertAlmostEqual(row["mae"], 1 / 45)
        self.assertAlmostEqual(row["rmse"], math.sqrt(2 / 45))
        self.assertAlmostEqual(row["pairwise_concordance"], 29.5 / 30)
        self.assertEqual(row["valid_users"], 59)
        for reader in audit.READERS:
            for name in ("native_minus_full", "native_minus_matched_summary"):
                contrast = contrasts[f"{name}__writer_phi__reader_{reader}"]
                self.assertAlmostEqual(contrast["mean_difference"], 1 / 45)
                self.assertEqual(contrast["common_valid_users"], 59)
                self.assertEqual(contrast["common_valid_mean_difference"], 0.)
                self.assertEqual(len(contrast["paired_user_differences"]), 60)
        self.assertAlmostEqual(systems["constant_3"]["summary"]["mae"], 7 / 6)
        self.assertAlmostEqual(systems["constant_3"]["summary"]["rmse"], math.sqrt(11 / 6))
        self.assertAlmostEqual(systems["constant_3"]["summary"]["signed_error"], 0.5)
        self.assertAlmostEqual(systems["history_mean"]["summary"]["mae"], 2 / 3)
        self.assertEqual(systems["history_mean"], systems["history_median"])

    def test_ordering_none_ties_and_reversal(self):
        self.assertIsNone(audit.metrics([1, 2, 3], [4, 4, 4])["pairwise_concordance"])
        self.assertEqual(audit.metrics([3, 3, 3], [1, 3, 5])["pairwise_concordance"], .5)
        self.assertEqual(audit.metrics([5, 3, 1], [1, 3, 5])["pairwise_concordance"], 0.)

    def test_precision_uses_exact_fixed_family_and_known_bounded_dispersion(self):
        names = sorted(f"{name}__writer_{w}__reader_{r}" for name in
                       ("native_minus_full", "native_minus_matched_summary") for w in audit.READERS for r in audit.READERS)
        contrasts = {n: {"paired_user_differences": [0.] * 60} for n in names}
        contrasts[names[0]]["paired_user_differences"] = [-4., 4.] * 30
        result = audit.independent_precision(contrasts)
        expected_sd = math.sqrt(16 * 60 / 59)
        self.assertAlmostEqual(result["contrasts"][names[0]]["bootstrap_sd_upper_95_quantile"], expected_sd)
        self.assertFalse(result["joint_go"])
        self.assertAlmostEqual(result["contrasts"][names[0]]["projected_adjusted_half_width"],
                               NormalDist().inv_cdf(1 - .05 / 16) * expected_sd / math.sqrt(200))
        del contrasts[names[0]]
        with self.assertRaisesRegex(ValueError, "complete fixed"):
            audit.independent_precision(contrasts)

    def test_no_common_valid_users_is_none_not_zero(self):
        cases = ["a", "b"]
        targets = {c: [1, 3, 5] for c in cases}
        histories = {c: [3] * 12 for c in cases}
        cells = {(c, r, a): ([3., 3., 3.], False) for c in cases for r in audit.READERS for a in audit.ARMS}
        _, contrasts = audit.calculate(cases, targets, histories, cells)
        for contrast in contrasts.values():
            self.assertEqual(contrast["mean_difference"], 0.)
            self.assertEqual(contrast["common_valid_users"], 0)
            self.assertIsNone(contrast["common_valid_mean_difference"])


class SavedArtifactChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = [f"{i:064x}" for i in range(60)]
        self.report, files = raw_grid(self.cases)
        raw_hashes = {name: self.write(name, value) for name, value in files.items()}
        for row in self.report["readers"]: row["raw_sha256"] = raw_hashes[row["raw_path"]]
        for row in self.report["writers"]:
            row["native_sha256"] = raw_hashes[row["native_path"]]
            row["summary_sha256"] = raw_hashes[row["summary_path"]]
        inputs = {c: {"history": [{"rating": 3} for _ in range(12)]} for c in self.cases}
        inputs_hash = self.write(audit.INPUTS, inputs)
        preparation = {"status": "prepared", "target_labels_materialized": False,
                       "groups": {"development": self.cases}, "input_file_hashes": {audit.INPUTS: inputs_hash}}
        self.write(audit.PREPARATION, preparation)
        deps = {}
        for name in audit.REQUIRED:
            if name != audit.PREPARATION:
                self.write(name, {"synthetic_definition": name})
            deps[name] = audit.file_hash(self.root / name)
        self.manifest_name = "data/language-development-v1/manifest.json"
        manifest = {"phase": "development", "cases": self.cases, "dependencies": deps,
                    "prepared_development_path": audit.INPUTS, "prepared_development_sha256": inputs_hash}
        manifest_hash = self.write(self.manifest_name, manifest)
        for stage, count in audit.STAGE_SIZES.items():
            name = f"data/language-development-v1/{stage}-handoff.json"
            first = next(iter(raw_hashes))
            handoff = {"stage": stage, "status": "completed", "recorded_cells": count,
                       "manifest_sha256": manifest_hash, "files": {first: raw_hashes[first]}}
            raw_hashes[name] = self.write(name, handoff)
        self.report.update(phase="development", complete=True, raw_file_hashes=raw_hashes,
                           stage_status={s: "completed" for s in audit.STAGE_SIZES},
                           dependencies=deps, manifest_path=self.manifest_name, manifest_sha256=manifest_hash)
        report_hash = self.write(audit.REPORT, self.report)
        payload = {}
        for position, case in enumerate(self.cases):
            rows = list(range(3 * position, 3 * position + 3))
            payload[case] = {"target_ratings": [1, 3, 5], "target_rows": rows,
                             "targets": [{"source_row": row, "rating": rating, "target": i + 1,
                                          "parent_asin": f"p{i}"} for i, (row, rating) in enumerate(zip(rows, [1, 3, 5]))]}
        labels = {"phase": "development", "complete": True, "case_order": self.cases, "cases": payload,
                  "reserved_rating_fields_accessed": False,
                  "label_payload_sha256": hashlib.sha256(audit.canonical(payload)).hexdigest(),
                  "dependencies": {**deps, **raw_hashes, self.manifest_name: manifest_hash,
                                   audit.REPORT: report_hash, audit.INPUTS: inputs_hash}}
        label_hash = self.write(audit.LABELS, labels)
        self.analysis = self.analytic_perfect_result()
        self.analysis.update(phase="development", complete=True, target_ratings=180,
                             inference_report_sha256=report_hash, manifest_sha256=manifest_hash,
                             label_artifact_sha256=label_hash,
                             dependencies={n: h for n, h in deps.items() if n != audit.PREPARATION})
        self.write(audit.ANALYSIS, self.analysis)

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audit.canonical(value))
        return audit.file_hash(path)

    def analytic_perfect_result(self):
        # Hand-specified expectations: all readers exactly predict [1,3,5];
        # all three numerical baselines predict constant three.
        perfect = {"mae": 0., "mse": 0., "signed_error": 0., "pairwise_concordance": 1., "unequal_target_pairs": 3}
        baseline = {"mae": 4 / 3, "mse": 8 / 3, "signed_error": 0., "pairwise_concordance": .5, "unequal_target_pairs": 3}
        systems = {}
        for name in [r + "/" + a for r in audit.READERS for a in audit.ARMS] + ["history_mean", "history_median", "constant_3"]:
            values = perfect if "/" in name else baseline
            rows = [{"case_id": c, "valid": True, **values} for c in self.cases]
            systems[name] = {"users": rows, "summary": {"users": 60, "valid_users": 60,
                "ordering_eligible_users": 60, "mae": values["mae"], "rmse": math.sqrt(values["mse"]),
                "signed_error": 0., "pairwise_concordance": values["pairwise_concordance"]}}
        names = sorted(f"{n}__writer_{w}__reader_{r}" for n in ("native_minus_full", "native_minus_matched_summary")
                       for w in audit.READERS for r in audit.READERS)
        contrasts = {n: {"users": 60, "mean_difference": 0., "common_valid_users": 60,
                         "common_valid_mean_difference": 0., "paired_user_differences": [0.] * 60} for n in names}
        precision = {"complete": True, "joint_go": True, "decision": "GO",
                     "contrasts": {n: {"development_users": 60, "sample_sd": 0.,
                         "bootstrap_sd_upper_95_quantile": 0., "projected_adjusted_half_width": 0.,
                         "meets_target": True} for n in names},
                     "settings": {"development_users": 60, "confirmation_users": 200, "family_size": 8,
                         "alpha": .05, "target_half_width": .10, "bootstrap_resamples_per_contrast": 20000,
                         "bootstrap_seed": 20260923, "generator": "NumPy PCG64", "bootstrap_sd_quantile": .95,
                         "sample_sd_ddof": 1, "quantile_method": "linear",
                         "normal_critical_value": NormalDist().inv_cdf(1 - .05 / 16)}}
        return {"cases": self.cases, "systems": systems, "contrasts": contrasts,
                "precision_planning": precision, "precision_planning_not_run_reason": None}

    def test_complete_saved_family_passes_without_writing_output(self):
        result = audit.verify(self.root)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["reader_cells_checked"], 840)
        self.assertEqual(result["user_system_records_checked"], 1020)
        self.assertEqual(result["primary_contrasts_checked"], 8)
        self.assertFalse((self.root / audit.OUTPUT).exists())

    def test_incomplete_stage_rejected_before_label_file_open(self):
        self.report["stage_status"]["qwen_cross"] = "incomplete"
        self.write(audit.REPORT, self.report)
        original = audit.load_json
        opened = []
        def guarded(root, name):
            opened.append(name)
            if name == audit.LABELS: self.fail("Labels opened before inference completion gate")
            return original(root, name)
        with patch.object(audit, "load_json", side_effect=guarded):
            with self.assertRaisesRegex(ValueError, "stages"):
                audit.verify(self.root)
        self.assertNotIn(audit.LABELS, opened)

    def test_duplicate_grid_rejected_before_label_file_open(self):
        self.report["readers"][-1] = deepcopy(self.report["readers"][0])
        self.write(audit.REPORT, self.report)
        with self.assertRaisesRegex(ValueError, "Reader grid"):
            audit.verify(self.root)

    def test_modified_raw_file_is_rejected(self):
        name = self.report["readers"][0]["raw_path"]
        self.write(name, response("[2,3,4]"))
        with self.assertRaisesRegex(ValueError, "Hash mismatch"):
            audit.verify(self.root)

    def test_label_full_hash_and_payload_hash_are_both_checked(self):
        labels = audit.load_json(self.root, audit.LABELS)
        labels["cases"][self.cases[0]]["target_ratings"][0] = 2
        changed_hash = self.write(audit.LABELS, labels)
        with self.assertRaisesRegex(ValueError, "Full label artifact hash"):
            audit.verify(self.root)
        self.analysis["label_artifact_sha256"] = changed_hash
        self.write(audit.ANALYSIS, self.analysis)
        with self.assertRaisesRegex(ValueError, "payload checksum"):
            audit.verify(self.root)

    def test_changed_aggregate_and_common_valid_contrast_rejected(self):
        self.analysis["systems"]["qwen/full_history"]["summary"]["mae"] = .1
        self.write(audit.ANALYSIS, self.analysis)
        with self.assertRaisesRegex(ValueError, "Numeric mismatch"):
            audit.verify(self.root)
        self.analysis["systems"]["qwen/full_history"]["summary"]["mae"] = 0.
        next(iter(self.analysis["contrasts"].values()))["common_valid_users"] = 59
        self.write(audit.ANALYSIS, self.analysis)
        with self.assertRaisesRegex(ValueError, "Integer differs"):
            audit.verify(self.root)

    def test_changed_precision_setting_or_decision_is_rejected(self):
        self.analysis["precision_planning"]["settings"]["confirmation_users"] = 201
        self.write(audit.ANALYSIS, self.analysis)
        with self.assertRaisesRegex(ValueError, "Integer differs"):
            audit.verify(self.root)
        self.analysis["precision_planning"]["settings"]["confirmation_users"] = 200
        self.analysis["precision_planning"]["joint_go"] = False
        self.write(audit.ANALYSIS, self.analysis)
        with self.assertRaisesRegex(ValueError, "Discrete value differs"):
            audit.verify(self.root)

    def test_numeric_booleans_and_escaping_paths_are_rejected(self):
        with self.assertRaises(ValueError): audit.compare(True, 1.0)
        with self.assertRaises(ValueError): audit.safe_path(self.root, "../outside.json")
        with self.assertRaises(ValueError): audit.safe_path(self.root, "/tmp/absolute.json")


if __name__ == "__main__":
    unittest.main()
