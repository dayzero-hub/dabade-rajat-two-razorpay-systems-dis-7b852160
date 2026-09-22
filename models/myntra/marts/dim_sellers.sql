-- The seller dimension as it is today: overwritten every night with whatever the newest
-- export says. One row per seller, no history. This is the model the brief is about.
select
    seller_id,
    seller_name,
    category,
    city,
    state,
    gstin,
    contact_email
from {{ ref('stg_my_sellers_2025_09') }}
