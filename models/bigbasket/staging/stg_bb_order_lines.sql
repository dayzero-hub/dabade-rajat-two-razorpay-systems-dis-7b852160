-- One row per raw order line. Rename and type only; no business logic in staging.
select
    order_id,
    line_no::integer                              as line_no,
    order_ts::timestamp                           as order_ts,
    order_ts::date                                as order_date,
    nullif(customer_id, '')                       as customer_id,
    customer_name,
    city,
    sku,
    product_name,
    category,
    qty::integer                                  as qty,
    unit_price_paise::bigint                      as unit_price_paise,
    (qty * unit_price_paise)::bigint              as line_total_paise,
    delivery_fee_paise::bigint                    as delivery_fee_paise
from {{ source('raw', 'bb_order_lines') }}
