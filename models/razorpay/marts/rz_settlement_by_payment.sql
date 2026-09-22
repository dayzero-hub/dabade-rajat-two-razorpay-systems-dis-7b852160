-- One row per payment_id. The bank occasionally settles the same payment under two UTRs
-- (remarks = RESUBMIT); we sum the gross across UTRs so the double settlement shows up as an
-- amount difference against the ledger instead of being silently dropped.
select
    payment_id,
    min(merchant_id)                     as merchant_id,
    count(*)                             as utr_count,
    string_agg(utr, ',' order by utr)    as utrs,
    sum(gross_paise)                     as gross_paise,
    sum(net_paise)                       as net_paise,
    min(captured_on)                     as captured_on,
    min(settled_on)                      as settled_on,
    string_agg(remarks, ',' order by utr) as remarks
from {{ ref('stg_rz_settlement') }}
group by payment_id
