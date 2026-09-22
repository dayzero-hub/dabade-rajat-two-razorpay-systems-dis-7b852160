-- The summary finance reads: one line per cause, plus the total, which must equal the gap.
with by_cause as (
    select
        cause,
        bool_or(needs_human)      as needs_human,
        count(*)                  as payments,
        sum(difference_paise)     as difference_paise
    from {{ ref('rz_differences') }}
    group by cause
)
select cause, needs_human, payments, difference_paise from by_cause
union all
select 'TOTAL (should equal the setup-ticket gap)', null, sum(payments), sum(difference_paise) from by_cause
order by needs_human nulls last, difference_paise
