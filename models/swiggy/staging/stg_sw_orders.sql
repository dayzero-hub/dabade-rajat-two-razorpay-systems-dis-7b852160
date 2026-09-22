-- One row per loaded order row. Typing only.
select
    order_id,
    customer_id,
    restaurant_id,
    city,
    order_ts,
    order_date,
    status,
    amount_paise,
    delivery_fee_paise,
    batch_day
from {{ source('raw', 'sw_orders') }}
