#!/usr/bin/env python3
"""Load the generated CSVs into raw tables in warehouse.duckdb.

    python3 scripts/load.py --brief <brief>            full load: drop and rebuild every raw table
    python3 scripts/load.py --brief swiggy --day D     the daily job: load ONE day's file

Raw tables live in the `raw` schema and are what the dbt sources point at. Staging models read
them; nothing else touches them.
"""
import argparse
import csv
import glob
import os
import sys
import time

import duckdb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "warehouse.duckdb")
DATA = os.path.join(ROOT, "data")

# brief -> {raw table: csv file}. Every file is loaded whole with DuckDB's CSV reader.
TABLES = {
    "bigbasket": {"bb_order_lines": "order_lines.csv"},
    "myntra": {"my_sellers_2025_06": "sellers_2025_06.csv", "my_sellers_2025_09": "sellers_2025_09.csv",
               "my_orders": "orders.csv"},
    "razorpay": {"rz_ledger": "ledger_2025-09-15.csv", "rz_settlement": "settlement_2025-09-15.csv"},
}

SW_COLUMNS = ["order_id", "customer_id", "restaurant_id", "city", "order_ts", "order_date", "status",
              "amount_paise", "delivery_fee_paise"]


def load_whole(con, brief):
    for table, fname in TABLES[brief].items():
        path = os.path.join(DATA, brief, fname)
        if not os.path.exists(path):
            sys.exit(f"missing {os.path.relpath(path)} — run: make data BRIEF={brief}")
        con.execute(f"create or replace table raw.{table} as select * from read_csv('{path}', header=true)")
        n = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        print(f"  raw.{table}: {n:,} rows")


# ── Swiggy: the daily order pipeline ────────────────────────────────────────────────────
# The nightly job reads one day's file and appends it to raw.sw_orders, batch_day recording
# which file each row came from. It streams the file in batches, as the real job does.

def sw_create(con):
    con.execute("""
        create or replace table raw.sw_orders (
            order_id varchar, customer_id varchar, restaurant_id varchar, city varchar,
            order_ts timestamp, order_date date, status varchar,
            amount_paise bigint, delivery_fee_paise bigint, batch_day date)
    """)


def sql_literal(v):
    return "'" + str(v).replace("'", "''") + "'"


def insert_batch(con, batch):
    # One multi-row INSERT per batch. (Bound parameters would be tidier, but DuckDB binds
    # thousands of them slowly; a literal VALUES list is ~70x faster on this shape of load.)
    values = ",".join("(" + ",".join(sql_literal(v) for v in row) + ")" for row in batch)
    con.execute(f"insert into raw.sw_orders values {values}")


def sw_load_day(con, day, batch_pause=0.0):
    path = os.path.join(DATA, "swiggy", f"orders_{day}.csv")
    if not os.path.exists(path):
        sys.exit(f"no file for {day}: {os.path.relpath(path)}")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        batch, total = [], 0
        for row in reader:
            batch.append([row[c] for c in SW_COLUMNS] + [day])
            if len(batch) == 500:
                insert_batch(con, batch)
                total += len(batch)
                batch = []
                if batch_pause:
                    time.sleep(batch_pause)
        if batch:
            insert_batch(con, batch)
            total += len(batch)
    n = con.execute("select count(*) from raw.sw_orders where batch_day = ?", [day]).fetchone()[0]
    print(f"  {day}: loaded {total:,} rows from file; raw.sw_orders now holds {n:,} rows for that batch_day")


def sw_load_all(con):
    files = sorted(glob.glob(os.path.join(DATA, "swiggy", "orders_*.csv")))
    if not files:
        sys.exit("no daily files in data/swiggy — run: make data BRIEF=swiggy")
    sw_create(con)
    for path in files:
        sw_load_day(con, os.path.basename(path)[len("orders_"):-len(".csv")])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True, choices=["bigbasket", "swiggy", "myntra", "razorpay"])
    ap.add_argument("--day", help="swiggy only: load one day (YYYY-MM-DD) through the daily path")
    ap.add_argument("--batch-pause", type=float, default=0.0,
                    help="swiggy only: seconds to sleep between batches, so a load is slow enough to interrupt")
    args = ap.parse_args()
    if args.day and args.brief != "swiggy":
        sys.exit("--day is the Swiggy daily pipeline; the other briefs load whole files")

    con = duckdb.connect(DB)
    con.execute("create schema if not exists raw")
    if args.brief == "swiggy":
        if args.day:
            sw_load_day(con, args.day, args.batch_pause)
        else:
            sw_load_all(con)
    else:
        load_whole(con, args.brief)
    con.close()
