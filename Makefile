.PHONY: data seed build test backfill query clean

# Which brief this repository is working on. `make data BRIEF=<company>` writes it to `.brief`;
# every later target reads it from there, and dbt sees it as DBT_BRIEF (see dbt_project.yml).
BRIEF ?= $(shell cat .brief 2>/dev/null)
export DBT_BRIEF := $(BRIEF)

USAGE := bigbasket, swiggy, myntra or razorpay

# Generate this brief's CSVs into data/<brief>/. Deterministic — the same files every time.
# No account, no download. Run it once; run it again if you want a clean copy of the data.
data:
	@test -n "$(BRIEF)" || { echo "usage: make data BRIEF=<$(USAGE)>"; exit 1; }
	python3 generate_data.py $(BRIEF)
	@echo $(BRIEF) > .brief
	@echo "Selected brief: $(BRIEF) (written to .brief)"

# Load the CSVs in data/<brief>/ into raw tables in warehouse.duckdb. A full, clean load:
# every raw table is dropped and rebuilt from the files.
seed:
	@test -n "$(BRIEF)" || { echo "No brief selected yet. Run: make data BRIEF=<$(USAGE)>"; exit 1; }
	python3 scripts/load.py --brief $(BRIEF)

# The whole project end to end: load the raw tables, then run every model and every test.
build: seed
	dbt build

test:
	dbt test

# Swiggy only: re-run ONE day through the daily load path, exactly as the nightly job does.
# Usage: make backfill DAY=2025-08-14
backfill:
	@test -n "$(DAY)" || { echo "usage: make backfill DAY=YYYY-MM-DD"; exit 1; }
	python3 scripts/load.py --brief $(BRIEF) --day $(DAY)

# Run a query against the warehouse and print CSV. Q is SQL text or a path to a .sql file.
# Usage: make query Q="select count(*) from raw.sw_orders"
#        make query Q=analyses/daily_totals.sql > docs/before.csv
query:
	@python3 scripts/query.py "$(Q)"

clean:
	dbt clean
	rm -f warehouse.duckdb warehouse.duckdb.wal
