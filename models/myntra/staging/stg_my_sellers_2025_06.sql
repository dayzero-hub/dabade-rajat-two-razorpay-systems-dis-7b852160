select
    seller_id,
    seller_name,
    category,
    city,
    state,
    gstin,
    contact_email,
    snapshot_date::date as snapshot_date
from {{ source('raw', 'my_sellers_2025_06') }}
