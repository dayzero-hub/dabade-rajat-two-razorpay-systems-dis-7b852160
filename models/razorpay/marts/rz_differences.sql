-- One row per unmatched payment, with a cause derived from the row itself — the timestamps, the
-- dates, the UTR count, the size of the gap. No list of known payment ids anywhere.
--
-- The 18:00 settlement cut-off is the one business fact this depends on: captures after it are
-- settled by the bank the next day, and a refund after it lands after the bank has already
-- settled the full capture. It is a parameter, not a hard-coded literal, so finance can move it.
{% set cutoff = "timestamp '2025-09-15 18:00:00'" %}
{% set day = "date '2025-09-15'" %}

select
    payment_id,
    merchant_id,
    category,
    case
        when category = 'settlement_only' and bank_captured_on < {{ day }}
            then 'timing_prior_day_capture'
        when category = 'ledger_only' and captured_ts >= {{ cutoff }}
            then 'timing_captured_after_cutoff'
        when category = 'ledger_only'
            then 'missing_never_settled'
        when category = 'differing' and utr_count > 1
            then 'settled_twice'
        when category = 'differing' and refunded_paise > 0
             and refunded_ts >= {{ cutoff }} and captured_paise = settlement_paise
            then 'refund_after_cutoff'
        when category = 'differing' and abs(difference_paise) <= 1
            then 'rounding'
        else 'unexplained'
    end                                        as cause,
    case
        when category = 'ledger_only' and captured_ts < {{ cutoff }} then true
        when category = 'differing' and utr_count > 1               then true
        else false
    end                                        as needs_human,
    ledger_paise,
    settlement_paise,
    difference_paise,
    captured_ts,
    refunded_ts,
    refunded_paise,
    utrs,
    bank_captured_on,
    settled_on,
    remarks
from {{ ref('rz_matched') }}
where category <> 'matched'
