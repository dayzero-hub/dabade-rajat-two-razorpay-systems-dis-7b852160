# Reconciliation — 2025-09-15

## The gap (setup ticket)

Ledger captures minus refunds: **5,312,281,703 paise** (19,200 captures = 5,324,897,245; 61 refunds = 12,615,542).
Settlement gross: **5,204,817,973 paise** (18,898 UTRs).
Difference (ledger − settlement): **107,463,730 paise** = ₹10,74,637.30. Everything below has to add up to this.

Queries: `make query Q=analyses/rz_totals.sql`.

## Data

The data is generated, not downloaded: `make data BRIEF=razorpay` writes `data/razorpay/*.csv`.
`data/*` is already in `.gitignore` (only `data/.gitkeep` is tracked); `.brief` is committed.

Amounts: the ledger is already integer paise. The bank's file is rupees with two decimals, so
`stg_rz_settlement` converts every amount with `round(x * 100)::bigint`. Nothing downstream
touches a float.

## Matching key

**`payment_id`** — it is on both files, and it is the only thing that is. `utr` exists only on the
bank side, `entry_id` only on ours.

### Is it unique? (counted, `analyses/rz_key_uniqueness.sql`)

| side | rows | distinct payment_id | repeats |
|---|---|---|---|
| ledger | 19,261 | 19,200 | 61 payments with 2 rows |
| settlement | 18,898 | 18,893 | 5 payments with 2 rows |

So it is **not unique on either side**.

- Ledger: the 61 repeats are all a `capture` row plus a `refund` row for the same payment. No
  payment has two captures or two refunds (`analyses/rz_key_duplicates.sql`).
- Settlement: the 5 repeats are two UTRs for the same payment, same amount, the second marked
  `remarks = RESUBMIT`.

### Rule for the non-unique case (many-to-one)

Roll each side up to **one row per `payment_id`** before matching:

- `rz_ledger_by_payment.net_paise = sum(capture) − sum(refund)` — that is the number finance
  compares, and a refund is part of the same payment, not a separate one.
- `rz_settlement_by_payment.gross_paise = sum(gross_paise)` across the payment's UTRs, with the
  UTRs kept in a `utrs` column. Summing means a double settlement shows up later as an amount
  difference (bank has 2× what we captured) rather than disappearing in a `distinct`.

Both rollups carry a `unique` test on `payment_id`, so if either side ever repeats a key in a way
these rules do not cover, `make build` goes red instead of the join fanning out.

### Coverage

| side | rows | payments the key covers |
|---|---|---|
| ledger | 19,261 | 19,200 (100% of rows — every row has a `payment_id`, `not_null` tested) |
| settlement | 18,898 | 18,893 (100% of rows) |
