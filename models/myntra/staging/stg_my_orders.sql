select
    order_id,
    order_date::date  as order_date,
    seller_id,
    customer_id,
    sku,
    amount_paise::bigint as amount_paise,
    status
from {{ source('raw', 'my_orders') }}
