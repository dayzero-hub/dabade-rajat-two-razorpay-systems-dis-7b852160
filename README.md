# dbt + DuckDB warehouse starter

A small **dbt** project on an embedded **DuckDB** warehouse. There is no database server and no
Docker — the whole warehouse is one `warehouse.duckdb` file that `make build` rebuilds from CSVs.

This one repository serves four briefs. Each has its own raw data, its own staging models and its
own story; you pick yours once with `make data BRIEF=…` and everything else follows from that.

| `BRIEF=` | The story | What is already here |
|---|---|---|
| `bigbasket` | Model grocery baskets — a star schema where the grain is the decision | staging over the raw order lines |
| `swiggy` | Backfill a month of orders without double-counting a day | a daily load, a month of history, `make backfill DAY=` |
| `myntra` | A seller dimension that keeps history when a category changes | staging, an overwrite-style `dim_sellers`, `fct_orders`, two seller snapshots |
| `razorpay` | Two systems disagree about one day — find every paisa | the internal ledger and the bank's settlement file, both in staging |

The data is **generated, not downloaded**. `make data` writes deterministic CSVs shaped for your
brief — no account, no network. Each brief's page names the public Kaggle dataset its story is
modelled on; that link is the real-world set for context, not something you need to fetch.

## 1. Install the tools

You need **Python 3.10+** and **git**. From the repo root:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip3 install dbt-duckdb        # pulls dbt-core and DuckDB with it
dbt debug                      # last line should read: All checks passed!
```

Windows: `.venv\Scripts\activate` instead of `source …`. Run every command below from the repo
root with the venv active.

## 2. Generate your brief's data

```bash
make data BRIEF=bigbasket      # or swiggy, myntra, razorpay
```

This writes the CSVs into `data/<brief>/` (gitignored — never commit them) and records your
choice in `.brief`, which the other targets read. Commit `.brief`.

## 3. Build it

```bash
make build      # load the CSVs into raw tables, then run every model and every test
make test       # the tests only
```

`make build` is green on a fresh clone once the data exists — that is the "it works before I
change anything" check. Before `make data`, it stops and tells you to run it.

## Looking at the warehouse

There is no database client to install. `make query` runs SQL and prints CSV:

```bash
make query Q="select * from stg_bb_order_lines limit 5"
make query Q=analyses/daily_totals.sql > docs/before.csv     # a committed query, a generated file
```

Raw tables live in the `raw` schema (`raw.bb_order_lines`, `raw.sw_orders`, …); dbt models are in
`main`. `dbt build` prints which ones were built.

## Layout

```
dbt_project.yml     project config — which brief's models are enabled, materialisations
profiles.yml        project-local profile pointing dbt at warehouse.duckdb
Makefile            data · seed · build · test · backfill · query · clean
generate_data.py    make data — writes data/<brief>/*.csv
scripts/load.py     make seed — loads data/<brief>/ into raw.* tables (and the Swiggy daily load)
scripts/query.py    make query
data/               generated CSVs (gitignored)
models/<brief>/
  staging/          stg_* — one per raw table, views, typing and renames only
  marts/            dim_* / fct_* — what you build (some briefs start with a model here)
tests/              singular tests you write
analyses/           committed queries (dbt compiles them; make query runs them)
docs/               your write-ups: the grain decision, the reconciliation, the before/after
```

## Per-brief notes

**bigbasket** — one raw file, `order_lines.csv`, one row per line of a basket. Guest checkouts
have no `customer_id`. `delivery_fee_paise` is an order-level amount the export repeats on every
line. Nothing in `marts/` yet: the dimensions and the fact are the project.

**swiggy** — one file per day, `orders_2025-08-01.csv` … `orders_2025-08-31.csv`. The nightly job
(`scripts/load.py --day`) appends one file to `raw.sw_orders`, stamping `batch_day` with the file's
date. `make build` does a clean full load of the month; `make backfill DAY=2025-08-14` runs one
day through the nightly path exactly as production would. `fct_daily_orders` is the number that
goes to finance. `--batch-pause 0.5` slows the daily load down so you can interrupt it.

**myntra** — two exports of the seller master, `sellers_2025_06.csv` and `sellers_2025_09.csv`,
and `orders.csv` from January to September. `dim_sellers` is the overwrite-style dimension the
brief describes; `fct_orders` joins to it on `seller_id`.

**razorpay** — `ledger_2025-09-15.csv` (ours: one row per entry, integer paise) and
`settlement_2025-09-15.csv` (the bank's: one row per UTR, rupees with two decimals). Finance
compares the ledger's captures minus refunds for the day against the settlement file's gross.

## Common problems

- **`No brief selected yet`** — run `make data BRIEF=…` first; it writes `.brief`.
- **`dbt build` says "Nothing to do"** — you ran `dbt` directly without `DBT_BRIEF` set. Go
  through `make`, or `export DBT_BRIEF=$(cat .brief)`.
- **`Could not find profile`** — run from the repo root, where `profiles.yml` lives.
- **`ModuleNotFoundError: duckdb`** — the venv is not active. `source .venv/bin/activate`.
- **A stale warehouse** — `make clean` deletes `warehouse.duckdb`; `make build` recreates it.
