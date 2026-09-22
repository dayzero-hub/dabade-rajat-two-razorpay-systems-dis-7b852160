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

## Four-way classification (ticket 2)

`rz_matched` full-outer-joins the two per-payment rollups and puts every payment in exactly one
bucket, decided by the join (which side is null; do the paise agree). Two singular tests hold it
together: `tests/rz_categories_cover_both_sides.sql` (the buckets add up to 19,200 ledger payments
and 18,893 settlement payments, and nothing is unbucketed) and `tests/rz_categories_sum_to_the_gap.sql`
(the per-bucket differences sum to the 107,463,730 paise gap).

`make query Q="select * from rz_category_summary"`:

| category | payments | ledger paise | settlement paise | difference (ledger − settlement) |
|---|---|---|---|---|
| matched | 17,934 | 4,958,123,312 | 4,958,123,312 | 0 |
| ledger_only | 1,207 | 341,035,149 | — | +341,035,149 |
| settlement_only | 900 | — | 225,952,484 | −225,952,484 |
| differing | 59 | 13,123,242 | 20,742,177 | −7,618,935 |
| **total** | | | | **+107,463,730** ✓ |

Ledger side: 17,934 + 59 + 1,207 = 19,200 ✓. Settlement side: 17,934 + 59 + 900 = 18,893 ✓.

### Hand reading (`make query Q=analyses/rz_unmatched_sample.sql`)

**ledger_only (10 read):** three of the ten were captured after 18:00 (19:11, 20:02, 21:32) with
no refund — those look like the bank has simply not settled them yet. The other seven (01:07,
03:00, 03:12, 03:50, 11:10, 11:46, 14:25) were captured well before 18:00 and still have no UTR;
nothing about the row explains it. Checking the whole bucket by hour: 1,200 of the 1,207 are
18:00 or later, 7 are earlier.

**settlement_only (10 read):** every one has `captured_on = 2025-09-14` and `settled_on =
2025-09-15`, and the UTRs are consecutive (UTR5017999 onwards). The bank is settling yesterday's
late captures today; our ledger for the 15th naturally has no row for them. All 900 rows in the
bucket have `captured_on = 2025-09-14`.

**differing (10 read):** three shapes —
1. off by exactly 1 paise either way (199939 vs 199940, 99909 vs 99908): the bank rounds
   differently to us somewhere;
2. we refunded in full or in half after 18:00 (`refunded_ts` 18:08, 20:44, 21:25, 22:12) and the
   bank settled the full capture — our net is lower by the refund;
3. two UTRs for one payment, the second marked `RESUBMIT`, bank total exactly 2× ours.

These are the shapes the causes in the next ticket come from. Nothing in the sample fell outside
them, but that is a sample, not the whole bucket — ticket 3 classifies every row and names any
remainder.

## Causes, and reconciling to zero (ticket 3)

`rz_differences` gives every unmatched payment a cause from the row itself — the capture
timestamp against the 18:00 cut-off, the bank's `captured_on` date, the number of UTRs, the
refund timestamp, the size of the gap. There is no list of known payment ids anywhere; a new
day's data gets classified by the same rules, and anything the rules do not cover comes out as
`unexplained`, which `tests/rz_causes_reconcile_to_the_gap.sql` fails on.

`make query Q="select * from rz_reconciliation_report"`:

| cause | needs a human? | payments | difference (paise) |
|---|---|---|---|
| timing_captured_after_cutoff — captured ≥ 18:00 on the 15th, bank will settle on the 16th | no, expected | 1,200 | +340,485,491 |
| timing_prior_day_capture — captured on the 14th after cut-off, bank settled on the 15th | no, expected | 900 | −225,952,484 |
| refund_after_cutoff — we refunded ≥ 18:00, bank had already settled the full capture; nets out next day | no, expected | 27 | −6,294,161 |
| rounding — bank's rupee figure is 1 paise off ours (27 rows, +1/−1, nets to +5) | no, noise | 27 | +5 |
| **settled_twice** — two UTRs for one payment, second marked `RESUBMIT`; bank has paid 2× | **yes** — ask the bank to reverse the duplicate UTRs | 5 | −1,324,779 |
| **missing_never_settled** — captured before the cut-off, no UTR at all | **yes** — escalate; this is the money that may be lost | 7 | +549,658 |
| **total** | | **2,166** | **+107,463,730** |

The total equals the gap measured in the setup ticket, 107,463,730 paise, exactly. **Remainder:
0 paise.** Unexplained rows: 0.

What that means for finance: of the ₹10,74,637.30, ₹10,82,388.51 is timing that reverses itself
tomorrow plus 5 paise of rounding, and the two lines that need a person are ₹13,247.79 the bank
paid twice (5 UTRs to reverse) and ₹5,496.58 across 7 payments that never reached settlement.

The full row-level report — every difference with `payment_id`, `merchant_id`, the UTR(s), and
both timestamps so it can be looked up on either side — is `analyses/rz_report.sql`; a generated
copy for the 15th is `docs/reconciliation_report_2025-09-15.csv` (2,166 rows, humans-first).
