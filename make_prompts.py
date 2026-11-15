"""Write one model prompt per question variant, ready for any LLM.

Usage:
    python make_prompts.py > prompts.jsonl

Each line: {"id": ..., "variant": ..., "prompt": ...}
Send each prompt to your model, put the returned SQL in
{"id", "variant", "sql"} lines, and score them with evaluate.py.
"""
import json
import sqlite3
import sys
from pathlib import Path

from evaluate import HERE, VARIANTS, load_questions

INSTRUCTIONS = (
    "You are given a SQLite database schema and a question. "
    "Write one SQLite query that answers the question. "
    "If the question is in Arabic, return Arabic names where the schema has them. "
    "Return only the SQL, with no explanation."
)


def schema_text(db):
    con = sqlite3.connect(db)
    rows = con.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    return "\n\n".join(r[0] for r in rows)


def main():
    db = HERE / "gulf_gov.db"
    if not db.exists():
        sys.exit("Database not found. Run: python build_db.py")
    schema = schema_text(db)
    for qid, q in load_questions().items():
        for v in VARIANTS:
            prompt = f"{INSTRUCTIONS}\n\n### Schema\n{schema}\n\n### Question\n{q['question'][v]}\n\n### SQL\n"
            print(json.dumps({"id": qid, "variant": v, "prompt": prompt}, ensure_ascii=False))


if __name__ == "__main__":
    main()
