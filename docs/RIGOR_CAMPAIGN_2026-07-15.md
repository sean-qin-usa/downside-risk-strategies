# GBC Project — Rigor & Robustness Campaign
**Date:** 2026-07-15  ·  **Scope:** forecasting-model rigor (IQN vs parametric) + trading-strategy robustness

---

## Executive summary

This campaign closed the two outstanding rigor gaps in the forecasting work and stress-tested the four load-bearing trading results. The headline is a **corrected, honest model comparison**: on identical, unit-matched rows, a parametric leverage-GARCH (GJR-GARCH-t) *beats* the neural implicit quantile network (IQN) on single-name equity forward-return quantiles by ~4.5–6.2% — retiring a prior spurious "IQN −38%" figure that had compared mismatched universes. This is consistent with, and strengthens, the project's central thesis: **GARCH owns single-name daily equity; the IQN's edge lives in hourly-crypto, cross-sectional transfer, and amortization**, not in beating GARCH on ordinary equity.

On the trading side, the two robust wins are **weekly (vs monthly) put-writing survives realistic execution cost decisively**, and **cross-asset ETF diversification is stable across in- and out-of-sample**.

---

## PART A — Forecasting rigor (the research portion)

### A1. Same-rows IQN vs GJR-GARCH-t — the −38% fix
**Problem.** An earlier comparison reported the IQN beating a t-GARCH benchmark by ~38%, but the two models were scored on *different* data (IQN on 113 names from 2016; the parametric on 543 names from 2005) and possibly different target scalings. That number was flagged invalid and never to be quoted.

**Method.** We scored both models on **identical (ticker, date, horizon) rows** — 102,391 rows, 111 names, horizons h = 5/10/21/42/63 trading days. The IQN is the production walk-forward network (raw9 features). The parametric benchmark is a clean, unit-matched **GJR-GARCH-t**: zero-mean, Student-t innovations, annual walk-forward refits, h-day quantiles by Monte-Carlo path simulation. Both produce quantiles of the *same* h-day forward return, so **pinball (quantile) loss is directly comparable**.

**Result.**

| Horizon (days) | IQN avg-pinball | GARCH avg-pinball | ratio (IQN/GARCH) | Diebold–Mariano t |
|---|---|---|---|---|
| 5 | 0.01302 | 0.01245 | 1.046 | +12.3 |
| 10 | 0.01871 | 0.01769 | 1.058 | +17.2 |
| 21 | 0.02762 | 0.02602 | 1.062 | +18.1 |
| 42 | 0.03895 | 0.03710 | 1.050 | +14.0 |
| 63 | 0.04757 | 0.04552 | 1.045 | +12.3 |

**GJR-GARCH-t beats the IQN by ~4.5–6.2% at every horizon, all statistically significant (DM t ≈ +12 to +18).** The invalid −38% is retired. Per-quantile diagnosis: the gap is **concentrated in the tails** (downside τ=.05 ≈ 7% worse at all horizons; upside τ=.95 worsening with horizon, 1.03 → 1.18 by h=63), while the **body (τ=.50) is nearly tied** (1.02–1.05, shrinking with horizon). This is exactly the un-spliced-tail deficiency documented earlier.

*Files: `samerows_iqn_garch.json`, `samerows_merged.csv`.*

### A2. Tail-recalibration decomposition — how much of the gap is fixable?
**Question.** The gap is tail-concentrated, and we already have a validated EVT/ACI tail-splice that calibrates coverage exactly. Does splicing close the gap?

**Method.** Applied a past-only, pooled-across-names, monthly-refit conformal/EVT recalibration to the IQN quantiles (standardize z = (y − p50)/(p75 − p25); spliced quantile = p50 + scale·Q_pool(τ) from prior months' pooled residuals) and re-scored on the same rows.

**Result.** Recalibration **fixes coverage** — the 5%-quantile breach falls from 0.071–0.089 to **0.051–0.064** (near the 0.05 target) — but only **partially closes the pinball gap**: ratio 1.045–1.062 → **1.029–1.048** (roughly halved at long horizons, a third at short). **GARCH-t still wins after tail-splicing.** Therefore the deficiency is **not purely a fixable tail-calibration artifact**; a real structural/training-budget residual of ~3–4% remains.

*File: `samerows_iqn_calibrated.json`.*

### A3. Training-budget arm — GPU K=5 retrain (running)
To attribute the residual ~3–4%, a larger-capacity retrain is underway on the GPU box: **K=5 ensemble (vs production K=3), 70 epochs (vs 40)**, same raw9 features and walk-forward design. When it completes, the new quantiles are merged onto the existing same-rows table (the GARCH-t Monte-Carlo columns are already stored, so nothing is recomputed) and re-scored. **Interpretation rule:** if the ratios move toward 1.0, the residual was training budget; if GARCH-t stays ~1–2% ahead, it is structural. *Prior evidence (A2) predicts partial closure with GARCH-t remaining ahead — i.e., mostly structural.*

### A4. Bottom line for the paper
On single-name equity daily/multi-day forecasting, the parametric leverage-GARCH is the honest benchmark to beat and the IQN does **not** beat it (it trails ~5%, tails included). The IQN's demonstrated advantages remain: hourly crypto (statistically decisive), forecasting **unseen** assets from characteristics (transfer, which GARCH structurally cannot do), and the amortized cross-sectional problem. The corrected framing is more defensible than the retired −38%.

---

## PART B — Trading-strategy robustness

### B1. Weekly vs monthly put-writing — net of realistic cost
Built the weekly (5–15 DTE) VRP series (178,787 puts, 542 names, 2016–25) directly comparable to the monthly (20–40 DTE) book. Selection is cross-sectional: each period sell puts only on the top-10% of names by VRP = (implied vol of the δ≈−0.12 put) − (trailing 21-day realized vol).

At **mid** execution, weekly beats monthly at every selection tier (top-10% Sharpe 3.46 vs 2.38) with a far smaller worst month (−1.2% vs −8.4%). The decisive test is **net of the full bid/ask half-spread**:

| top-10% VRP | mid Sharpe | **bid (net) Sharpe** | bid worst month | half-spread eats |
|---|---|---|---|---|
| **Weekly** | 3.46 | **2.08** | −1.4% | 57% of gross |
| **Monthly** | 2.38 | **0.51** | −9.6% | 82% of gross |

At the bid, **monthly collapses (2.38 → 0.51)** while **weekly holds up (3.46 → 2.08)**: the half-spread eats 82% of monthly's fat deep-OTM premium but only 57% of weekly's tighter near-dated premium, and weekly's structural tail truncation (−1.4% vs −9.6% worst month) dominates. **Weekly is the better vehicle net of cost.** (Caveats: "bid" is worst-case full-cross; posting at mid lands between — weekly ~2–3, monthly ~1–2. Liquid names only; illiquid names widen and would degrade weekly more.)

*File: `netcost_weekly_vs_monthly.json`, `weekly_qside_results.json`.*

### B2. Cross-asset ETF diversification — stable in/out of sample
Seven liquid ETF option sleeves (QQQ, TLT, GLD, USO, UNG, FXE, HYG), average pairwise correlation **0.05**:

- Combined risk-weighted Sharpe: **full 2.33, in-sample (2016–20) 2.30, out-of-sample (2021–25) 4.46** — the diversification benefit is **stable across eras** (unlike a VIX-regime gate, which proved to be a look-ahead artifact).
- Per-sleeve Sharpes rotate across eras (QQQ robust; USO/HYG weak-IS → strong-OOS; TLT/UNG weak), which is precisely why the *combination* is what matters.
- 10%-vol-target combined book: **CAGR 25.3%, max drawdown −12.2%.** This is the scalable ($100M–$B) sleeve of the book.

*File: `xasset_oos_results.json`.*

### B3. Earnings-VRP — refined
Earnings names carry richer premium (VRP 0.137 vs 0.078 non-earnings; 186 vs 142 bp per trade) but **do not carry the Sharpe**: earnings-only Sharpe 1.94 ≈ non-earnings 1.99. The non-earnings VRP is strong on its own, so the edge does **not** critically depend on earnings gap risk. Sizing earnings down 0.5× slightly *hurts* (2.38 → 2.24). **Verdict: accept earnings exposure at full weight as priced; no filter needed.**

*File: `earnings_deep_results.json`.*

### B4. Forward paper-trade — harness validated + live signals
The production spec (top-100 liquid → top-10% VRP → post at mid → 0.5× after a down month) was replayed through the live signal harness over 116 months and reproduces the strategy (mid Sharpe 2.22, out-of-sample > in-sample). A sample broker-ready ticket was generated. **The harness never places orders — a human submits.** Two scheduled signal generators now run: **monthly** (1st of month) and **weekly** (Mondays), building parallel out-of-sample paper records to measure real limit-fill quality — the one number no backtest can provide.

*File: `paper_sim_results.json`.*

---

## Reproducibility notes
- All backtests use lagged (prior-period) signals, trailing realized vol, and single-consistent-spot settlement via Black–Scholes delta inversion (split-robust). Same-rows scoring restricts to identical (ticker, date, horizon) tuples with unit-matched targets.
- Result artifacts (JSON) and the merged same-rows table accompany this memo. The full running strategy state is in `strategy_research_state.md` (section 8 = this campaign).
- GPU K=5 retrain is running on the GPU box; completion auto-fetches and re-scores against the stored GARCH-t columns.
