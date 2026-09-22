-- What finance and the restaurant partners are paid against: one row per day.
select
    order_date,
    count(*)                                                   as order_rows,
    count(distinct order_id)                                   as orders,
    sum(case when status = 'delivered' then amount_paise end)  as delivered_revenue_paise
from {{ ref('stg_sw_orders') }}
group by 1
order by 1
