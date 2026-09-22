-- The full report: every difference, with the identifiers to look it up on either side.
select payment_id, merchant_id, cause, needs_human, difference_paise, ledger_paise, settlement_paise,
       captured_ts, refunded_ts, utrs, bank_captured_on, settled_on, remarks
from rz_differences
order by needs_human desc, cause, payment_id
