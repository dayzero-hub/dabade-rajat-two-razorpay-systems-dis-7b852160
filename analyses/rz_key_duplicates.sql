-- What the repeats look like on each side.
select 'ledger' as side, entry_count as rows_per_payment, count(*) as payments
from rz_ledger_by_payment group by 1, 2
union all
select 'settlement', utr_count, count(*)
from rz_settlement_by_payment group by 1, 2
order by 1, 2
