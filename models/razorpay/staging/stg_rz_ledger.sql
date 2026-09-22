select
    entry_id,
    payment_id,
    merchant_id,
    entry_type,
    amount_paise::bigint  as amount_paise,
    currency,
    entry_ts::timestamp   as entry_ts,
    method
from {{ source('raw', 'rz_ledger') }}
