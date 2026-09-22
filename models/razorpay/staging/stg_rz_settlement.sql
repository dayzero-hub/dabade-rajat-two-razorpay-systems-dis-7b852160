-- The bank sends rupees with two decimals; everything downstream compares in integer paise.
-- round() before the cast so 499.99 * 100 = 49998.999... becomes 49999, not 49998.
select
    utr,
    payment_id,
    merchant_id,
    round(gross_amount * 100)::bigint as gross_paise,
    round(fee * 100)::bigint          as fee_paise,
    round(tax * 100)::bigint          as tax_paise,
    round(net_amount * 100)::bigint   as net_paise,
    captured_on::date  as captured_on,
    settled_on::date   as settled_on,
    remarks
from {{ source('raw', 'rz_settlement') }}
