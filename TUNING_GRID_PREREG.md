# Pre-Registered Tuning Grid — VRP Books
*Sean Qin · 2026-07-21 · Written BEFORE any runs (APPLICATIONS.md §4 discipline). Grid and evaluation rules below are fixed; anything outside them is exploratory and must be labeled as such.*

## Why pre-register
~50 model×strategy×leg combos were already evaluated once (PQ_TRADE_BACKTEST.md §5); the SR-1.35 headline is a family max. Every new sweep inflates the max further unless rules are fixed ex-ante. This doc is the commitment device.

## Fixed evaluation rules (all runs)
1. Data: OptionMetrics 2016–25 top-100-liquid panel (single-name); ETF sleeve panel (xasset). No new data pulls mid-grid.
2. Primary metric: **in-sample-era (2016–20) Sharpe at BID execution** — the harshest column. Full-period and mid figures reported but never used for selection.
3. Secondary (tie-break only): worst-month, max DD, at bid.
4. All signals trailing/lagged (RV = trailing 21d unless the RV axis is being tested; one-day lag on everything).
5. Report the FULL grid, not the winner. Winner claims require: (a) beats current spec by >0.15 SR at bid IS, (b) monotone or interpretable across the axis (no isolated spikes), (c) survives the paper-trade forward window before promotion to the production spec.
6. Multiple-testing note: 6 axes × ~4 values ≈ 24 cells per book. Bonferroni-ish haircut: treat p<0.002 as the bar for "significant improvement."

## The grid (per axis; current production value in **bold**)
| Axis | Values | Applies to |
|---|---|---|
| Delta target | −0.05 / **−0.12** / −0.20 | all books |
| Selection cutoff | top 5% / **10%** / 15% / 25% | single-name |
| De-risk multiplier | 0.3× / **0.5×** / 0.7× / 1.0×(off) | all books |
| De-risk trigger | **sign of last period** / magnitude-tiered | all books |
| RV window | 10d / **21d** / 63d | all books (also closes the pending RV-robustness re-run) |
| Tenor mix (weekly:monthly) | 100:0 / 70:30 / 50:50 / **0:100 & 100:0 separate** | single-name |
| Sleeve weighting | **inverse-vol** / equal / risk-parity (trailing corr) | xasset |

## Explicitly OUT of scope (already falsified — do not re-run)
Vol-target sizing of short-vol books (pro-cyclical, DD −38%); VIX gating (look-ahead artifact); stops; delta-hedging; protective puts; magnitude-based de-risk (tested, worse).

## Execution plan
One script per book sweeping the axes independently (no full cross-product; 2-way interactions only for delta×cutoff). Results JSON + a single table per book appended to this doc. Runs happen in the sandbox against existing parquets; nothing touches the live paper pipeline.

## Status
- [ ] Grid runs not yet started (this doc must be committed first)
- [ ] Results section (to be appended below, full grid, no cherry-picking)
