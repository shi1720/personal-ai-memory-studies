"""Exploratory lexical baseline; see docs/pilot-001.md."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import time

from data_audit import model_history


def tokenize(text):
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def bm25(query, documents, k1=1.5, b=0.75):
    if not documents:
        return []
    counts = [Counter(tokenize(doc)) for doc in documents]
    lengths = [sum(doc.values()) for doc in counts]
    average = sum(lengths) / len(lengths)
    if not average:
        return [0.0] * len(documents)
    frequency = Counter(term for doc in counts for term in doc)
    terms = set(tokenize(query))
    scores = []
    for doc, length in zip(counts, lengths):
        score = 0.0
        for term in terms:
            tf = doc[term]
            if not tf:
                continue
            df = frequency[term]
            idf = math.log1p((len(documents) - df + 0.5) / (df + 0.5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * length / average))
        scores.append(score)
    return scores


def rank_visible(query, history, method):
    if method == "bm25":
        texts = ["\n".join(turn["content"] for turn in s["messages"]) for s in history]
        scores = bm25(query, texts)
        return sorted(range(len(history)), key=lambda i: (-scores[i], i))
    if method == "recency":
        dates = [datetime.strptime(s["date"], "%Y/%m/%d (%a) %H:%M") for s in history]
        return sorted(range(len(history)), key=lambda i: dates[i], reverse=True)
    raise ValueError(method)


def score_retrieval(selected, gold):
    gold = set(gold)
    if not gold:
        raise ValueError("Cannot score recall without gold evidence")
    hits = len(set(selected) & gold)
    return {"recall": hits / len(gold), "any_hit": int(hits > 0), "all_hit": int(hits == len(gold))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    start = time.perf_counter()
    payload = args.input.read_bytes()
    records = json.loads(payload)
    rows, aggregations = [], defaultdict(list)
    for record in records:
        if record["question_id"].endswith("_abs"):
            continue
        visible = model_history(record)
        row = {"question_id": record["question_id"], "question_type": record["question_type"], "methods": {}}
        for method in ["bm25", "recency"]:
            # The ranker receives no ground truth or original corpus IDs.
            ranked_positions = rank_visible(record["question"], visible, method)
            ranked_ids = [record["haystack_session_ids"][i] for i in ranked_positions]
            scores = {str(k): score_retrieval(ranked_ids[:k], record["answer_session_ids"])
                      for k in [1, 3, 5, 10]}
            row["methods"][method] = {"ranked_positions": ranked_positions, "scores": scores}
            for k, values in scores.items():
                for metric, value in values.items():
                    aggregations[(method, k, metric)].append(value)
        rows.append(row)
        if len(rows) % 100 == 0:
            print(f"Scored {len(rows)} cases", flush=True)
    summary = {}
    for (method, k, metric), values in sorted(aggregations.items()):
        summary.setdefault(method, {}).setdefault(k, {})[metric] = sum(values) / len(values)
    result = {"status": "exploratory retrieval baseline, not answer accuracy or a new method",
              "protocol": "docs/pilot-001.md", "input_sha256": hashlib.sha256(payload).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "loader_sha256": hashlib.sha256(Path(__file__).with_name("data_audit.py").read_bytes()).hexdigest(),
              "python": platform.python_version(), "seconds": time.perf_counter() - start,
              "evaluated_questions": len(rows), "summary": summary, "rows": rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"evaluated_questions": len(rows), "summary": summary, "seconds": result["seconds"]}, indent=2))


if __name__ == "__main__":
    main()
