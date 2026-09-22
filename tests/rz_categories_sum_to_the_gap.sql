-- The per-category differences must sum to the ledger-minus-settlement gap exactly.
select *
from (
    select (select sum(difference_paise) from {{ ref('rz_category_summary') }}) as by_category,
           (select sum(net_paise) from {{ ref('rz_ledger_by_payment') }})
         - (select sum(gross_paise) from {{ ref('rz_settlement_by_payment') }}) as gap
)
where by_category <> gap
