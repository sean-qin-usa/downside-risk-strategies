# Cross-Asset VRP Monthly Blotter — September 2026

Scheduled-task report, 2026-09-04. Paper record only — **no orders sent**.

## Ticket: live_xasset_2026-09-01 (LIVE, yfinance delayed)

| Leg | Expiry | Strike | Δ | DTE | Limit (mid) | Prem/strike | Weight | Quote vol/OI |
|---|---|---|---|---|---|---|---|---|
| SELL QQQ put | 2026-09-30 | 658 | −0.118 | 29 | 3.21 | 0.49% | 0.1612 | 5 / 112 |
| SELL USO put | 2026-10-09 | 115 | −0.111 | 38 | 0.92 | 0.80% | 0.0655 | 78 / 63 |
| SELL HYG put | 2026-09-25 | 78 | −0.128 | 24 | 0.10 | 0.13% | 0.7733 | 1 / 3 |

**Validation — PASS on all spec gates:**
- Deltas all in [−0.25, −0.04]; DTE all in [20, 40]; limits = quote mid.
- Weights recomputed from inverse RV21 match file to 4dp; sum = 1.0000 = size_mult.
- size_mult 1.0 correct: last settled cycle (July) +0.25% ≥ 0 → no de-risk.
- Avg premium 0.472% (unweighted), consistent with log.

**Caveats:**
1. **Sleeve universe is 8, not the spec'd 7** — UUP added in code (live_signal.py: "FXE has no tradeable delta-band puts; UUP added as the liquid USD/FX sleeve"), present since the Aug meta but **not in TUNING_GRID_PREREG.md**. No effect this month (log: "no tradeable put for UUP"), but it should be added to the prereg file or reverted.
2. HYG carries 77% of risk weight on a strike quoting 1 lot volume / OI 3 — mid-fill assumption is optimistic; the bid-fill column of the forward log is the honest series.
3. USO quote spread 0.45/1.40: bid-fill premium is 0.39% vs 0.80% at mid.

## Settlements since last report

- **July cycle (2026-07-21, 6 legs): fully settled +0.248% mid / +0.189% bid** (unlevered, on cycle notional).
- **Aug cycle (2026-08-03, 3 legs):** UNG 9P expired 2026-08-28 **OTM** (S_T 10.38): leg +1.00% mid / +0.33% bid, `fill_verified=False` (limit 0.09 vs bid 0.03 — thin). TLT 78.5P and HYG 77P expire **today (2026-09-04)**; both entered ~4.5% / 2.9% OTM. Aggregate Aug row fills after today's close; if it settles negative, the October ticket must print size_mult 0.5x.

## Units reminder

Paper record is **unlevered** (1x cash-secured). The backtest headline (SR 2.33, CAGR 25.3%) is the 10%-vol-target levered series (~6–7x notional). Do not mix.
