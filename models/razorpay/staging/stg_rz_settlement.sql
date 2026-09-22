select
    utr,
    payment_id,
    merchant_id,
    gross_amount,
    fee,
    tax,
    net_amount,
    captured_on::date  as captured_on,
    settled_on::date   as settled_on,
    remarks
from {{ source('raw', 'rz_settlement') }}
