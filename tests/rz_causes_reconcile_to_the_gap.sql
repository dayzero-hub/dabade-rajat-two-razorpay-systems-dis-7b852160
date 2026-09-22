-- Every unmatched payment has a cause other than 'unexplained', and the causes sum to the gap.
-- (If a remainder ever appears, this test is what says so — by failing, not by rounding it away.)
select *
from (
    select
        (select count(*) from {{ ref('rz_differences') }} where cause = 'unexplained') as unexplained_rows,
        (select sum(difference_paise) from {{ ref('rz_differences') }})                as explained_paise,
        (select sum(net_paise) from {{ ref('rz_ledger_by_payment') }})
      - (select sum(gross_paise) from {{ ref('rz_settlement_by_payment') }})           as gap_paise
)
where unexplained_rows <> 0 or explained_paise <> gap_paise
