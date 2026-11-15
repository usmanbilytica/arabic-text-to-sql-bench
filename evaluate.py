"""Score Text-to-SQL predictions by execution accuracy.

Predictions file: JSON Lines, one object per line:
    {"id": "hr-001", "variant": "ar_gulf", "sql": "SELECT ..."}

variant is one of: en, ar_msa, ar_gulf

Usage:
    python evaluate.py predictions.jsonl
    python evaluate.py --gold-check          # sanity check: gold SQL vs itself

A prediction is correct when its result matches the gold result as a
multiset of rows (row order is ignored). Extra columns are allowed: if the
gold query returns k columns, any k of the predicted columns (kept in order)
may match. Numbers are compared after rounding to 2 decimals.
"""
import argparse
import itertools
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
VARIANTS = ("en", "ar_msa", "ar_gulf")


def load_questions(path=HERE / "questions.jsonl"):
    with open(path, encoding="utf-8") as f:
        return {q["id"]: q for q in map(json.loads, f) if q}


def gold_sql(q, variant):
    return q.get("sql_en", q["sql"]) if variant == "en" else q["sql"]


def norm(v):
    if isinstance(v, str):
        s = v.strip()
        try:
            v = float(s)
        except ValueError:
            return s
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return round(float(v), 2)
    return v


def run(con, sql):
    rows = con.execute(sql).fetchall()
    return [tuple(norm(x) for x in r) for r in rows]


def matches(gold_rows, pred_rows):
    if len(gold_rows) != len(pred_rows):
        return False
    if not gold_rows:
        return True
    k, m = len(gold_rows[0]), len(pred_rows[0])
    if m < k:
        return False
    gold = Counter(gold_rows)
    for cols in itertools.combinations(range(m), k):
        if Counter(tuple(r[i] for i in cols) for r in pred_rows) == gold:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("predictions", nargs="?")
    ap.add_argument("--db", default=str(HERE / "gulf_gov.db"))
    ap.add_argument("--gold-check", action="store_true")
    args = ap.parse_args()

    if not Path(args.db).exists():
        sys.exit("Database not found. Run: python build_db.py")
    con = sqlite3.connect(args.db)
    questions = load_questions()

    if args.gold_check:
        preds = [{"id": i, "variant": v, "sql": gold_sql(q, v)}
                 for i, q in questions.items() for v in VARIANTS]
    elif args.predictions:
        with open(args.predictions, encoding="utf-8") as f:
            preds = [json.loads(l) for l in f if l.strip()]
    else:
        ap.error("give a predictions file or --gold-check")

    score = {v: [0, 0] for v in VARIANTS}
    failures = []
    for p in preds:
        q = questions.get(p["id"])
        if q is None or p.get("variant") not in VARIANTS:
            continue
        v = p["variant"]
        score[v][1] += 1
        try:
            ok = matches(run(con, gold_sql(q, v)), run(con, p["sql"]))
        except sqlite3.Error as e:
            ok = False
            failures.append((p["id"], v, f"SQL error: {e}"))
        else:
            if not ok:
                failures.append((p["id"], v, "wrong result"))
        score[v][0] += ok

    print(f"{'variant':<10}{'correct':>9}{'total':>7}{'accuracy':>10}")
    for v in VARIANTS:
        c, t = score[v]
        acc = f"{100 * c / t:.1f}%" if t else "-"
        print(f"{v:<10}{c:>9}{t:>7}{acc:>10}")
    if failures:
        print("\nMisses:")
        for i, v, why in failures:
            print(f"  {i:<8} {v:<8} {why}")


if __name__ == "__main__":
    main()
