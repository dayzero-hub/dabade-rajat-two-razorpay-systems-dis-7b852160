-- The one number the board has to account for: ledger net minus settlement gross, in paise.
select
    (select sum(net_paise)   from rz_ledger_by_payment)     as ledger_net_paise,
    (select sum(gross_paise) from rz_settlement_by_payment) as settlement_gross_paise,
    (select sum(net_paise)   from rz_ledger_by_payment)
  - (select sum(gross_paise) from rz_settlement_by_payment) as difference_paise
