-- Count and value of each bucket. The difference column sums to the setup-ticket gap.
select
    category,
    count(*)                    as payments,
    sum(ledger_paise)           as ledger_paise,
    sum(settlement_paise)       as settlement_paise,
    sum(difference_paise)       as difference_paise
from {{ ref('rz_matched') }}
group by category
order by category
