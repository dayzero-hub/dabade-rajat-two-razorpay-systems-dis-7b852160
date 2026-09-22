-- One row per order, with the seller's CURRENT attributes. Last quarter's orders carry
-- whatever category the seller is in today.
select
    o.order_id,
    o.order_date,
    o.seller_id,
    s.category      as seller_category,
    o.customer_id,
    o.sku,
    o.amount_paise,
    o.status
from {{ ref('stg_my_orders') }} o
left join {{ ref('dim_sellers') }} s on s.seller_id = o.seller_id
