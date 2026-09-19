"""Inspect a LongMemEval release without performing model inference.

Never treat metadata shortcut rates as legitimate retrieval performance.
Shared sessions do not, by themselves, establish shared real-world users.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import statistics


def canonical_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def model_history(record):
    """Allowlist model-visible fields; gold labels and original IDs stay out."""
    errors = validate_record(record)
    if errors:
        raise ValueError(errors)
    return [{"date": date, "messages": [
        {"role": turn["role"], "content": turn["content"]} for turn in session
    ]} for date, session in zip(record["haystack_dates"], record["haystack_sessions"])]


def validate_record(record):
    fields = ("question_id", "question_type", "question", "answer", "question_date",
              "haystack_dates", "haystack_session_ids", "haystack_sessions", "answer_session_ids")
    errors = ["missing field: " + key for key in fields if key not in record]
    if errors:
        return errors
    lengths = [len(record[k]) for k in ("haystack_dates", "haystack_session_ids", "haystack_sessions")]
    if len(set(lengths)) != 1:
        errors.append("parallel session arrays have unequal lengths")
    for session in record["haystack_sessions"]:
        for turn in session:
            if not isinstance(turn.get("content"), str) or not isinstance(turn.get("role"), str):
                errors.append("invalid role/content type")
    return errors


def components(nodes, groups):
    parent = {x: x for x in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for members in groups:
        members = sorted(set(members))
        for member in members[1:]:
            parent[find(member)] = find(members[0])
    buckets = defaultdict(list)
    for node in nodes:
        buckets[find(node)].append(node)
    return sorted((sorted(v) for v in buckets.values()), key=lambda v: (-len(v), v))


def summarize(values):
    return {"min": min(values), "median": statistics.median(values), "max": max(values)}


def audit(records):
    if not records:
        raise ValueError("Empty dataset")
    ids = [r["question_id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Question IDs are not unique")
    defects = {r["question_id"]: validate_record(r) for r in records if validate_record(r)}
    if defects:
        raise ValueError(json.dumps(defects))
    history_groups, evidence_groups = defaultdict(set), defaultdict(set)
    sessions_per_question, words_per_question = [], []
    missing_evidence, chronology_violations, metadata_rows, duplicate_ids = [], [], [], []
    with_turn_gold = 0
    for record in records:
        qid = record["question_id"]
        gold = set(record["answer_session_ids"])
        present = set(record["haystack_session_ids"])
        repeated = [sid for sid, n in Counter(record["haystack_session_ids"]).items() if n > 1]
        if repeated:
            duplicate_ids.append({"question_id": qid, "duplicated_ids": sorted(repeated),
                                  "includes_gold": bool(set(repeated) & gold)})
        missing = gold - present
        if missing:
            missing_evidence.append({"question_id": qid, "missing_ids": sorted(missing),
                                     "abstention": qid.endswith("_abs")})
        times = [datetime.strptime(d, "%Y/%m/%d (%a) %H:%M") for d in record["haystack_dates"]]
        if times != sorted(times):
            chronology_violations.append(qid)
        history = model_history(record)
        sessions_per_question.append(len(history))
        words_per_question.append(sum(len(t["content"].split()) for s in history for t in s["messages"]))
        for sid, session, visible in zip(record["haystack_session_ids"], record["haystack_sessions"], history):
            # Dates excluded: reused content may be timestamped differently.
            h = canonical_hash(visible["messages"])
            history_groups[h].add(qid)
            if sid in gold:
                evidence_groups[h].add(qid)
            if any("has_answer" in turn for turn in session):
                with_turn_gold += 1
        guessed = {sid for sid in present if sid.startswith("answer_")}
        if not qid.endswith("_abs"):
            metadata_rows.append({"question_id": qid, "tp": len(guessed & gold),
                                  "predicted": len(guessed), "gold": len(gold),
                                  "exact_set": guessed == gold})
    tp = sum(x["tp"] for x in metadata_rows)
    predicted = sum(x["predicted"] for x in metadata_rows)
    gold_total = sum(x["gold"] for x in metadata_rows)
    evidence_components = components(ids, evidence_groups.values())
    return {
        "status": "exploratory dataset audit; no LLM or method result",
        "questions": len(records), "question_types": dict(sorted(Counter(r["question_type"] for r in records).items())),
        "abstention_questions": sum(q.endswith("_abs") for q in ids),
        "sessions_per_question": summarize(sessions_per_question),
        "whitespace_words_per_question_not_model_tokens": summarize(words_per_question),
        "unique_session_contents": len(history_groups),
        "session_contents_reused_across_questions": sum(len(v) > 1 for v in history_groups.values()),
        "evidence_contents_reused_across_questions": sum(len(v) > 1 for v in evidence_groups.values()),
        "evidence_overlap_component_sizes": [len(x) for x in evidence_components],
        "evidence_overlap_components": evidence_components,
        "sessions_with_turn_level_gold_fields": with_turn_gold,
        "questions_with_nonchronological_arrays": chronology_violations,
        "missing_evidence_sessions": missing_evidence,
        "questions_with_duplicate_session_ids": duplicate_ids,
        "forbidden_metadata_shortcut": {
            "rule": "select original session IDs starting with answer_",
            "purpose": "detect why original IDs must not be model inputs",
            "evaluated_nonabstention_questions": len(metadata_rows),
            "micro_precision": tp / predicted if predicted else None,
            "micro_recall": tp / gold_total if gold_total else None,
            "exact_gold_set_fraction": sum(x["exact_set"] for x in metadata_rows) / len(metadata_rows) if metadata_rows else None,
            "rows": metadata_rows,
        },
        "interpretation_limits": [
            "Metadata shortcut is deliberately invalid and must never count as model performance.",
            "No claim that the upstream official evaluator exposes these labels to a model.",
            "Shared content does not establish user identity or statistical dependence of outcomes.",
            "Unsorted dates are expected in the oracle file; do not reorder without recording preprocessing.",
            "Word counts are not tokenizer counts.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    result = audit(json.loads(raw))
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("questions", "question_types", "abstention_questions",
          "unique_session_contents", "session_contents_reused_across_questions",
          "evidence_contents_reused_across_questions")}, indent=2))
    print("Metadata shortcut:", {k: v for k, v in result["forbidden_metadata_shortcut"].items() if k != "rows"})


if __name__ == "__main__":
    main()
