-- One row per payment_id. A payment can have a capture entry and a refund entry in the ledger;
-- the number finance compares is captures minus refunds, so that is what we roll up to.
select
    payment_id,
    min(merchant_id)                                                    as merchant_id,
    count(*)                                                            as entry_count,
    sum(case when entry_type = 'capture' then amount_paise else 0 end)  as captured_paise,
    sum(case when entry_type = 'refund'  then amount_paise else 0 end)  as refunded_paise,
    sum(case when entry_type = 'capture' then amount_paise else -amount_paise end) as net_paise,
    min(case when entry_type = 'capture' then entry_ts end)             as captured_ts,
    min(case when entry_type = 'refund'  then entry_ts end)             as refunded_ts
from {{ ref('stg_rz_ledger') }}
group by payment_id
