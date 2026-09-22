-- Is payment_id unique on each side? Count, do not assume.
select 'ledger' as side, count(*) as rows_, count(distinct payment_id) as distinct_payment_ids,
       count(*) - count(distinct payment_id) as extra_rows
from stg_rz_ledger
union all
select 'settlement', count(*), count(distinct payment_id), count(*) - count(distinct payment_id)
from stg_rz_settlement
union all
select 'ledger_by_payment', count(*), count(distinct payment_id), count(*) - count(distinct payment_id)
from rz_ledger_by_payment
union all
select 'settlement_by_payment', count(*), count(distinct payment_id), count(*) - count(distinct payment_id)
from rz_settlement_by_payment
