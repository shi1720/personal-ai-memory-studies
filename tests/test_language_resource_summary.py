"""Synthetic-only accounting and malformed-record checks."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from language_resource_summary import summarize_resources


ARMS = ("no_history", "full_history", "native_qwen", "summary_qwen",
        "native_phi", "summary_phi", "bm25_history")


def invented_grid():
    rows = []
    for user in range(60):
        for model in ("qwen", "phi"):
            for condition in ("native-writer", "summary-writer", *ARMS):
                writer = condition.endswith("-writer")
                native = condition == "native-writer"
                rows.append({
                    "case_id": f"invented-{user:02}", "model": model,
                    "condition": condition, "reused": user < 3,
                    "status": "completed", "valid": True,
                    "reader_valid": None if writer else True,
                    "required_writer_valid": None if writer else True,
                    "seconds": 2., "memory_entries": 2 if native else None,
                    "memory_words": 10 if native else 8 if writer else None,
                    "requests": [{"audit_id": f"audit-{user}-{model}-{condition}",
                                  "status": "completed", "transport_attempted": True,
                                  "response_present": True, "prompt_tokens": 100,
                                  "response_prompt_tokens": 100, "completion_tokens": 20,
                                  "total_tokens": 120, "total_token_allowance": 100 + (2048 if writer else 256),
                                  "seconds": 1.}],
                })
    return rows


def group(report, condition="native-writer", model="qwen", provenance="combined"):
    return next(row for row in report["groups"] if
                (row["condition"], row["model"], row["provenance"]) == (condition, model, provenance))


def fail_writer(rows, index=0):
    row = rows[index]
    row["valid"] = False
    method = row["condition"].split("-")[0]
    for reader in rows:
        if reader["case_id"] == row["case_id"] and reader["condition"] == method + "_" + row["model"]:
            reader["required_writer_valid"] = False
            reader["valid"] = False


class ResourceSummaryChecks(unittest.TestCase):
    def test_exact_totals_statistics_and_provenance(self):
        result = summarize_resources(invented_grid())
        self.assertTrue(result["complete"])
        self.assertEqual(len(result["groups"]), 54)
        totals = result["totals"]
        self.assertEqual(totals["recorded_cells"], 1080)
        self.assertEqual(totals["unique_audited_requests"], 1080)
        self.assertEqual(totals["attempted_transports"], 1080)
        self.assertEqual(totals["completed_model_responses"], 1080)
        self.assertEqual(totals["reader_cells"], 840)
        self.assertEqual(totals["valid_readers"], 840)
        self.assertEqual((totals["reused_cells"], totals["new_cells"]), (54, 1026))
        for provenance, n in (("reused", 3), ("new", 57), ("combined", 60)):
            g = group(result, provenance=provenance)
            self.assertEqual(g["counts"]["recorded_cells"], n)
            self.assertEqual(g["measurements"]["prompt_tokens"], {
                "n_available": n, "n_missing": 0, "sum": 100 * n, "mean": 100.,
                "median": 100., "max": 100, "complete_sum": True})
            self.assertEqual(g["measurements"]["instrumented_cell_seconds"]["sum"], 2 * n)
            self.assertEqual(g["measurements"]["audit_seconds"]["sum"], n)
            self.assertEqual(g["memory"]["all_writer_cells"]["memory_entries"]["sum"], 2 * n)
        self.assertEqual(group(result, "summary-writer")["memory"]["all_writer_cells"]["memory_words"]["sum"], 480)
        self.assertIsNone(group(result, "full_history")["memory"])
        self.assertNotIn("prompt_tokens", totals)

    def test_failed_empty_writer_diagnostic_readers_do_not_count_as_valid_pipeline(self):
        rows = invented_grid()
        fail_writer(rows)
        rows[0].update(memory_entries=0, memory_words=0)
        report = summarize_resources(rows)
        native = group(report)
        self.assertEqual(native["counts"]["valid_cells"], 59)
        self.assertEqual(native["memory"]["valid_writer_denominator"], 59)
        self.assertEqual(native["memory"]["all_writer_cells"]["memory_words"]["n_available"], 60)
        self.assertEqual(native["memory"]["valid_writer_subset"]["memory_words"]["n_available"], 59)
        self.assertEqual(native["memory"]["valid_writer_subset"]["memory_words"]["mean"], 10)
        for model in ("qwen", "phi"):
            reader_group = group(report, "native_qwen", model)
            counts = reader_group["counts"]
            self.assertEqual(counts["valid_readers"], 60)
            self.assertEqual(counts["valid_cells"], 59)
            self.assertEqual(counts["invalid_required_writers"], 1)
            self.assertEqual(reader_group["valid_required_writer_requests"]["request_count"], 59)
            self.assertEqual(reader_group["valid_required_writer_requests"]["prompt_tokens"]["sum"], 5900)
        self.assertEqual(report["totals"]["unique_audited_requests"], 1080)

    def test_native_setup_without_audit_preserves_denominator(self):
        rows = invented_grid()
        fail_writer(rows)
        rows[0].update(status="error", requests=[], memory_entries=None, memory_words=None)
        report = summarize_resources(rows)
        self.assertEqual(report["totals"]["recorded_cells"], 1080)
        self.assertEqual(report["totals"]["unique_audited_requests"], 1079)
        self.assertEqual(report["totals"]["native_setup_failures_without_audit"], 1)
        self.assertEqual(group(report)["measurements"]["prompt_tokens"]["n_available"], 59)

    def test_missing_usage_and_times_are_not_zero(self):
        rows = invented_grid()
        fail_writer(rows)
        rows[0]["status"] = "error"
        rows[0]["seconds"] = None
        rows[0]["requests"][0].update(status="error", response_present=False)
        for key in ("prompt_tokens", "response_prompt_tokens", "completion_tokens",
                    "total_tokens", "total_token_allowance", "seconds"):
            rows[0]["requests"][0][key] = None
        report = summarize_resources(rows)
        stats = group(report)["measurements"]["completion_tokens"]
        self.assertEqual((stats["n_available"], stats["n_missing"], stats["sum"]), (59, 1, 1180))
        self.assertFalse(stats["complete_sum"])
        self.assertFalse(group(report)["measurements"]["instrumented_cell_seconds"]["complete_sum"])
        self.assertNotIn("memory_entries", group(report, "summary-writer")["memory"]["all_writer_cells"])
        rows = invented_grid()
        for row in rows:
            if row["condition"] == "native-writer":
                row["memory_entries"] = None
        empty = group(summarize_resources(rows))["memory"]["all_writer_cells"]["memory_entries"]
        self.assertIsNone(empty["sum"])
        self.assertFalse(empty["complete_sum"])
        self.assertEqual(empty["n_missing"], 60)

    def test_completed_requests_require_every_count_and_allowance(self):
        for field in ("prompt_tokens", "response_prompt_tokens", "completion_tokens",
                      "total_tokens", "total_token_allowance"):
            rows = invented_grid()
            rows[0]["requests"][0][field] = None
            with self.subTest(field=field), self.assertRaises(ValueError):
                summarize_resources(rows)

    def test_valid_writer_subset_retains_invalid_reader_requests(self):
        rows = invented_grid()
        reader = next(row for row in rows if row["condition"] == "native_qwen")
        reader.update(valid=False, reader_valid=False)
        report = summarize_resources(rows)
        reader_group = group(report, "native_qwen")
        self.assertEqual(reader_group["counts"]["valid_readers"], 59)
        self.assertEqual(reader_group["valid_required_writer_requests"]["request_count"], 60)
        self.assertEqual(reader_group["valid_required_writer_requests"]["prompt_tokens"]["sum"], 6000)
        self.assertIsNone(group(report)["valid_required_writer_requests"])

    def test_failed_transport_and_pretransport_rejection_are_distinct(self):
        for transported in (False, True):
            rows = invented_grid()
            fail_writer(rows)
            rows[0]["status"] = "error"
            rows[0]["requests"][0].update(status="error", transport_attempted=transported,
                response_present=False, response_prompt_tokens=None, completion_tokens=None, total_tokens=None)
            totals = summarize_resources(rows)["totals"]
            self.assertEqual(totals["pretransport_rejections"], int(not transported))
            self.assertEqual(totals["transport_errors"], int(transported))
            self.assertEqual(totals["responses_present"], 1079)

    def test_no_input_mutation_and_record_order_invariance(self):
        rows = invented_grid()
        original = deepcopy(rows)
        report = summarize_resources(rows)
        self.assertEqual(rows, original)
        self.assertEqual(report, summarize_resources(list(reversed(rows))))
        self.assertNotIn("invented-", str(report))
        self.assertNotIn("audit-0", str(report))

    def test_duplicate_audit_duplicate_or_incomplete_grid(self):
        for mutation in (lambda r: r.pop(), lambda r: r.__setitem__(1, deepcopy(r[0])),
                         lambda r: r[1]["requests"][0].update(audit_id=r[0]["requests"][0]["audit_id"])):
            rows = invented_grid()
            mutation(rows)
            with self.assertRaises(ValueError):
                summarize_resources(rows)

    def test_reuse_must_be_exactly_three_whole_cases(self):
        rows = invented_grid()
        rows[0]["reused"] = False
        with self.assertRaises(ValueError):
            summarize_resources(rows)
        rows = invented_grid()
        for row in rows:
            if row["case_id"] == "invented-03":
                row["reused"] = True
        with self.assertRaises(ValueError):
            summarize_resources(rows)

    def test_bad_numbers_and_request_accounting(self):
        malformed = [("seconds", True), ("seconds", -1), ("seconds", float("nan")),
                     ("seconds", float("inf")), ("prompt_tokens", True),
                     ("prompt_tokens", 0), ("completion_tokens", -1),
                     ("completion_tokens", 1.5), ("completion_tokens", 2049),
                     ("response_prompt_tokens", 99), ("total_tokens", 121),
                     ("total_token_allowance", 2149), ("transport_attempted", 1),
                     ("response_present", False), ("audit_id", " ")]
        for field, value in malformed:
            rows = invented_grid()
            rows[0]["requests"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                summarize_resources(rows)

    def test_invalid_cell_shapes_and_linked_validity(self):
        for field, value in (("memory_entries", True), ("memory_words", -1),
                             ("seconds", -1), ("valid", 1), ("model", "unknown"),
                             ("condition", "unknown"), ("status", "pending"),
                             ("reader_valid", True), ("requests", [])):
            rows = invented_grid()
            rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                summarize_resources(rows)
        rows = invented_grid()
        rows[0]["valid"] = False
        with self.assertRaises(ValueError):
            summarize_resources(rows)
        rows = invented_grid()
        rows[2]["reader_valid"] = False
        with self.assertRaises(ValueError):
            summarize_resources(rows)
        rows = invented_grid()
        rows[2]["requests"] = []
        rows[2].update(status="error", valid=False, reader_valid=False)
        with self.assertRaises(ValueError):
            summarize_resources(rows)


if __name__ == "__main__":
    unittest.main()
