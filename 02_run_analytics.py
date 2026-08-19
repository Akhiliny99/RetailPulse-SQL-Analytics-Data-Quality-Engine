"""
RetailPulse — Query Runner
Executes all analytics + data quality queries and prints readable results.
Also exports results to CSV in ../output/ for use in Excel.

Run: python3 02_run_analytics.py
"""

import sqlite3
import csv
import os
import re

BASE = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, "..", "data", "retailpulse.db")
OUTPUT_DIR = os.path.join(BASE, "..", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


def split_statements(sql_text):
    """Split a .sql file into individual statements, keeping named comments as titles."""
    # Split on semicolons that end a statement (naive but fine for this file set)
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    return statements


def get_query_title(stmt):
    lines = stmt.strip().splitlines()
    for line in lines:
        if line.strip().startswith("--") and ("Q" in line or "DQ" in line) and "." in line:
            return line.strip("- ").strip()
    return "Query"


def run_sql_file(path, export_prefix):
    with open(path) as f:
        sql_text = f.read()
    statements = split_statements(sql_text)

    idx = 0
    for stmt in statements:
        # skip pure comment blocks with no actual SQL
        code_only = re.sub(r"--.*", "", stmt).strip()
        if not code_only:
            continue
        idx += 1
        title = get_query_title(stmt)
        print("\n" + "=" * 80)
        print(title)
        print("=" * 80)
        try:
            cur = conn.execute(stmt)
            rows = cur.fetchall()
            if not rows:
                print("(no rows returned)")
                continue
            cols = rows[0].keys()
            print(" | ".join(cols))
            print("-" * 80)
            for r in rows[:15]:
                print(" | ".join(str(r[c]) for c in cols))
            if len(rows) > 15:
                print(f"... ({len(rows) - 15} more rows)")

            # export to csv
            out_path = os.path.join(OUTPUT_DIR, f"{export_prefix}_{idx:02d}.csv")
            with open(out_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(cols)
                for r in rows:
                    writer.writerow([r[c] for c in cols])
        except Exception as e:
            print(f"ERROR running query: {e}")


print("\n" + "#" * 80)
print("# RETAILPULSE — ADVANCED ANALYTICS RESULTS")
print("#" * 80)
run_sql_file(os.path.join(BASE, "..", "sql", "02_advanced_analytics.sql"), "analytics")

print("\n\n" + "#" * 80)
print("# RETAILPULSE — DATA QUALITY CHECK RESULTS")
print("#" * 80)
run_sql_file(os.path.join(BASE, "..", "sql", "03_data_quality_checks.sql"), "dq")

conn.close()
print(f"\n\nAll results exported to: {OUTPUT_DIR}")
