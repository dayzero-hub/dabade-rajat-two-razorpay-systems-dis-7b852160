-- Every payment on either side, in exactly one of four buckets. The bucket comes from the join
-- itself (which side is null, do the paise agree), never from a list of known payment ids.
select
    coalesce(l.payment_id, s.payment_id)  as payment_id,
    coalesce(l.merchant_id, s.merchant_id) as merchant_id,
    case
        when s.payment_id is null            then 'ledger_only'
        when l.payment_id is null            then 'settlement_only'
        when l.net_paise = s.gross_paise     then 'matched'
        else                                      'differing'
    end                                   as category,
    l.captured_paise,
    l.refunded_paise,
    l.net_paise                            as ledger_paise,
    s.gross_paise                          as settlement_paise,
    coalesce(l.net_paise, 0) - coalesce(s.gross_paise, 0) as difference_paise,
    l.captured_ts,
    l.refunded_ts,
    s.utr_count,
    s.utrs,
    s.captured_on                          as bank_captured_on,
    s.settled_on,
    s.remarks
from {{ ref('rz_ledger_by_payment') }} l
full outer join {{ ref('rz_settlement_by_payment') }} s using (payment_id)
