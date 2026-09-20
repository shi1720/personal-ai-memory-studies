"""Pure descriptive resource accounting for a completed development grid.

No file access, outcome scoring, inference, or imports of frozen study code.
Times are instrumented operations, not end-to-end latency. Audit times are
nested and must never be added to their enclosing cell times.
"""
from math import fsum, isfinite
from numbers import Integral, Real
from statistics import median


MODELS = ("phi", "qwen")
WRITERS = ("native-writer", "summary-writer")
ARMS = ("no_history", "full_history", "native_qwen", "summary_qwen",
        "native_phi", "summary_phi", "bm25_history")
CONDITIONS = tuple(sorted(WRITERS + ARMS))
PROVENANCES = ("reused", "new", "combined")
CELL_FIELDS = {"case_id", "model", "condition", "reused", "status", "valid",
               "reader_valid", "required_writer_valid", "seconds",
               "memory_entries", "memory_words", "requests"}
REQUEST_FIELDS = {"audit_id", "status", "transport_attempted", "response_present",
                  "prompt_tokens", "response_prompt_tokens", "completion_tokens",
                  "total_tokens", "total_token_allowance", "seconds"}
TOKEN_FIELDS = ("prompt_tokens", "response_prompt_tokens", "completion_tokens",
                "total_tokens", "total_token_allowance")


def _integer(value, name, minimum=0):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f"{name} must be a nonboolean integer >= {minimum}, or None")
    try:
        finite = isfinite(float(value))
    except (ValueError, OverflowError):
        finite = False
    if not finite:
        raise ValueError(f"{name} must be finite")
    return int(value)


def _seconds(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("Seconds must be a finite nonboolean nonnegative number or None")
    try:
        value = float(value)
    except (ValueError, OverflowError) as error:
        raise ValueError("Seconds must be finite") from error
    if not isfinite(value) or value < 0:
        raise ValueError("Seconds must be finite and nonnegative")
    return value


def _request(value, budget, seen):
    if not isinstance(value, dict) or set(value) != REQUEST_FIELDS:
        raise ValueError("Request must have exactly the prescribed fields")
    row = dict(value)
    audit = row["audit_id"]
    if not isinstance(audit, str) or not audit.strip() or audit in seen:
        raise ValueError("Audit IDs must be unique nonempty strings")
    seen.add(audit)
    if row["status"] not in ("completed", "error"):
        raise ValueError("Request status must be completed or error")
    for field in ("transport_attempted", "response_present"):
        if type(row[field]) is not bool:
            raise ValueError(f"{field} must be boolean")
    if row["response_present"] and not row["transport_attempted"]:
        raise ValueError("A response requires an attempted transport")
    if row["status"] == "completed" and not (row["transport_attempted"] and row["response_present"]):
        raise ValueError("Completed requests require transport and response")
    for field in TOKEN_FIELDS:
        row[field] = _integer(row[field], field, 0 if field == "completion_tokens" else 1)
    row["seconds"] = _seconds(row["seconds"])
    prompt, reported, completion, total, allowance = (row[k] for k in TOKEN_FIELDS)
    if row["status"] == "completed" and any(row[field] is None for field in TOKEN_FIELDS):
        raise ValueError("Completed requests require complete tokenizer counts, server usage, and allowance")
    if not row["response_present"] and any(x is not None for x in (reported, completion, total)):
        raise ValueError("Server usage cannot be present without a response")
    if prompt is not None and reported is not None and prompt != reported:
        raise ValueError("Tokenizer and server prompt counts disagree")
    if completion is not None and completion > budget:
        raise ValueError("Completion count exceeds the fixed output allowance")
    if prompt is not None and allowance is not None and allowance != prompt + budget:
        raise ValueError("Total allowance must equal prompt count plus fixed output allowance")
    if row["transport_attempted"] and allowance is not None and allowance > 16384:
        raise ValueError("Transported request exceeds the fixed context allowance")
    effective_prompt = reported if reported is not None else prompt
    if total is not None and effective_prompt is not None:
        if total < effective_prompt:
            raise ValueError("Total usage cannot be smaller than prompt usage")
        if completion is not None and total != effective_prompt + completion:
            raise ValueError("Total usage disagrees with prompt plus completion")
    if total is not None and completion is not None and total <= completion:
        raise ValueError("Total usage must include positive prompt usage")
    if total is not None and allowance is not None and total > allowance:
        raise ValueError("Total usage exceeds the request allowance")
    return row


def _validate(records):
    if not isinstance(records, list) or len(records) != 1080:
        raise ValueError("Expected the complete list of 1080 development cells")
    cells, audits = {}, set()
    for value in records:
        if not isinstance(value, dict) or set(value) != CELL_FIELDS:
            raise ValueError("Cell must have exactly the prescribed fields")
        row = dict(value)
        case = row["case_id"]
        if not isinstance(case, str) or not case.strip():
            raise ValueError("Case IDs must be nonempty strings")
        if row["model"] not in MODELS or row["condition"] not in CONDITIONS:
            raise ValueError("Unknown model or condition")
        key = (case, row["model"], row["condition"])
        if key in cells:
            raise ValueError("Duplicate case-model-condition cell")
        if row["status"] not in ("completed", "error"):
            raise ValueError("Cell status must be completed or error")
        for field in ("reused", "valid"):
            if type(row[field]) is not bool:
                raise ValueError(f"{field} must be boolean")
        if row["valid"] and row["status"] != "completed":
            raise ValueError("Valid cells must have completed status")
        writer = row["condition"] in WRITERS
        if writer:
            if row["reader_valid"] is not None or row["required_writer_valid"] is not None:
                raise ValueError("Writer cells must not supply reader-validity fields")
        else:
            if type(row["reader_valid"]) is not bool or type(row["required_writer_valid"]) is not bool:
                raise ValueError("Reader validity fields must be boolean")
            if row["reader_valid"] and row["status"] != "completed":
                raise ValueError("Valid readers must have completed status")
            if row["valid"] != (row["reader_valid"] and row["required_writer_valid"]):
                raise ValueError("Whole-pipeline validity must include required writer validity")
            if row["memory_entries"] is not None or row["memory_words"] is not None:
                raise ValueError("Memory sizes belong to writer cells only")
        row["seconds"] = _seconds(row["seconds"])
        for field in ("memory_entries", "memory_words"):
            row[field] = _integer(row[field], field)
        requests = row["requests"]
        if not isinstance(requests, list) or len(requests) > 1:
            raise ValueError("Each cell must have zero or one request")
        if not requests and not (row["condition"] == "native-writer" and row["status"] == "error"):
            raise ValueError("Only a failed native setup may have no request")
        row["requests"] = [_request(r, 2048 if writer else 256, audits) for r in requests]
        if row["status"] == "completed" and row["requests"][0]["status"] != "completed":
            raise ValueError("Completed cells require a completed request")
        cells[key] = row
    cases = {key[0] for key in cells}
    expected = {(case, model, condition) for case in cases for model in MODELS for condition in CONDITIONS}
    if len(cases) != 60 or set(cells) != expected:
        raise ValueError("Expected exactly 60 users with every model and condition")
    reused = set()
    for case in cases:
        flags = {cells[(case, model, condition)]["reused"] for model in MODELS for condition in CONDITIONS}
        if len(flags) != 1:
            raise ValueError("Reuse provenance must be identical across every cell of a user")
        if flags == {True}:
            reused.add(case)
        for model in MODELS:
            for arm in ARMS:
                expected_valid = True
                if arm.startswith(("native_", "summary_")):
                    method, writer_model = arm.split("_")
                    expected_valid = cells[(case, writer_model, method + "-writer")]["valid"]
                if cells[(case, model, arm)]["required_writer_valid"] != expected_valid:
                    raise ValueError("Required writer validity disagrees with its writer cell")
    if len(reused) != 3:
        raise ValueError("Exactly three complete users must be reused and 57 must be new")
    return [cells[key] for key in sorted(cells)]


def _statistics(values):
    available = [value for value in values if value is not None]
    n = len(available)
    # An empty or entirely unavailable subset is not observed zero consumption.
    total = (sum(available) if all(isinstance(v, int) for v in available)
             else fsum(available)) if n else None
    return {
        "n_available": n, "n_missing": len(values) - n,
        "sum": total, "mean": total / n if n else None,
        "median": float(median(available)) if n else None,
        "max": max(available) if n else None,
        "complete_sum": bool(n and n == len(values)),
    }


def _counts(rows):
    requests = [request for row in rows for request in row["requests"]]
    readers = [row for row in rows if row["condition"] in ARMS]
    return {
        "planned_cells": len(rows), "recorded_cells": len(rows),
        "valid_cells": sum(row["valid"] for row in rows),
        "invalid_cells": sum(not row["valid"] for row in rows),
        "completed_cells": sum(row["status"] == "completed" for row in rows),
        "error_cells": sum(row["status"] == "error" for row in rows),
        "reader_cells": len(readers),
        "valid_readers": sum(row["reader_valid"] for row in readers),
        "invalid_readers": sum(not row["reader_valid"] for row in readers),
        "invalid_required_writers": sum(not row["required_writer_valid"] for row in readers),
        "unique_audited_requests": len(requests),
        "attempted_transports": sum(r["transport_attempted"] for r in requests),
        "pretransport_rejections": sum(not r["transport_attempted"] for r in requests),
        "completed_model_responses": sum(r["status"] == "completed" for r in requests),
        "error_requests": sum(r["status"] == "error" for r in requests),
        "responses_present": sum(r["response_present"] for r in requests),
        "transport_errors": sum(r["transport_attempted"] and r["status"] == "error" for r in requests),
        "transports_without_response": sum(r["transport_attempted"] and not r["response_present"] for r in requests),
        "native_setup_failures_without_audit": sum(not row["requests"] for row in rows),
    }


def summarize_resources(records):
    """Validate the complete grid and return aggregate-only descriptive tables.

    Three provenance views overlap. Never sum the reused, new and combined views
    together. Token measurements stay within their model tokenizer. A request
    predicts three targets jointly; writers are counted once per representation.
    """
    rows = _validate(records)
    groups = []
    for model in MODELS:
        for condition in CONDITIONS:
            matched = [row for row in rows if row["model"] == model and row["condition"] == condition]
            for provenance in PROVENANCES:
                selected = [row for row in matched if provenance == "combined" or
                            row["reused"] == (provenance == "reused")]
                requests = [request for row in selected for request in row["requests"]]
                measurements = {field: _statistics([r[field] for r in requests]) for field in TOKEN_FIELDS}
                measurements["instrumented_cell_seconds"] = _statistics([row["seconds"] for row in selected])
                measurements["audit_seconds"] = _statistics([r["seconds"] for r in requests])
                valid_writer_requests = None
                if condition in ARMS:
                    subset = [request for row in selected if row["required_writer_valid"]
                              for request in row["requests"]]
                    valid_writer_requests = {
                        "scope": (
                            "Descriptive prompt statistics for requests whose required writer "
                            "is valid, including invalid reader responses. Conditions without "
                            "a required writer retain every request. Not a compression claim "
                            "or replacement for the all-user accuracy estimand."
                        ),
                        "request_count": len(subset),
                        "prompt_tokens": _statistics([r["prompt_tokens"] for r in subset]),
                        "response_prompt_tokens": _statistics([r["response_prompt_tokens"] for r in subset]),
                    }
                memory = None
                if condition in WRITERS:
                    memory_fields = ("memory_entries", "memory_words") if condition == "native-writer" else ("memory_words",)
                    memory = {
                        "all_writer_cells": {field: _statistics([r[field] for r in selected])
                                             for field in memory_fields},
                        "valid_writer_subset": {field: _statistics([r[field] for r in selected if r["valid"]])
                                                for field in memory_fields},
                        "valid_writer_denominator": sum(row["valid"] for row in selected),
                    }
                groups.append({"model": model, "condition": condition, "provenance": provenance,
                               "counts": _counts(selected), "measurements": measurements, "memory": memory,
                               "valid_required_writer_requests": valid_writer_requests})
    return {
        "complete": True,
        "scope": (
            "Descriptive saved-operation accounting, not outcome scoring, isolated model "
            "latency, deployment throughput, monetary cost, or end-to-end pipeline timing. "
            "Audit times are nested inside cell times. Reused/new/combined views overlap. "
            "Token counts are not pooled across model tokenizers. Empty or failed memory "
            "is not evidence of successful compression. Missing usage is not zero usage."
        ),
        "totals": {**_counts(rows), "users": 60, "reused_users": 3, "new_users": 57,
                   "reused_cells": 54, "new_cells": 1026},
        "groups": groups,
    }
