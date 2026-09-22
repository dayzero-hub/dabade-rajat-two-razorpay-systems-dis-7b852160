-- Ten rows from each unmatched bucket, to read by hand before inventing causes.
select * from (
    select *, row_number() over (partition by category order by payment_id) as rn
    from rz_matched where category <> 'matched'
) where rn <= 10 order by category, rn
