-- The four buckets must add up to the row count on each side. Returns rows on failure.
with expected as (
    select (select count(*) from {{ ref('rz_ledger_by_payment') }})     as ledger_payments,
           (select count(*) from {{ ref('rz_settlement_by_payment') }}) as settlement_payments
), actual as (
    select
        count(*) filter (where category in ('matched', 'differing', 'ledger_only'))     as ledger_payments,
        count(*) filter (where category in ('matched', 'differing', 'settlement_only')) as settlement_payments,
        count(*) filter (where category not in ('matched','differing','ledger_only','settlement_only')) as unbucketed
    from {{ ref('rz_matched') }}
)
select * from expected, actual
where expected.ledger_payments <> actual.ledger_payments
   or expected.settlement_payments <> actual.settlement_payments
   or actual.unbucketed <> 0
