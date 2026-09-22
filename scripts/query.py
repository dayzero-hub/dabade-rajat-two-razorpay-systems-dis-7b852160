#!/usr/bin/env python3
"""Run one query against warehouse.duckdb and print the result as CSV.

    python3 scripts/query.py "select count(*) from raw.sw_orders"
    python3 scripts/query.py analyses/daily_totals.sql > docs/before.csv

The argument is SQL, or the path of a .sql file. Commit the .sql file, not the number.
"""
import csv
import os
import sys

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        sys.exit('usage: python3 scripts/query.py "<sql>" | path/to/file.sql')
    q = sys.argv[1]
    if q.endswith(".sql"):
        with open(q) as f:
            q = f.read()
    con = duckdb.connect(os.path.join(ROOT, "warehouse.duckdb"), read_only=True)
    cur = con.execute(q)
    w = csv.writer(sys.stdout)
    w.writerow([c[0] for c in cur.description])
    w.writerows(cur.fetchall())
