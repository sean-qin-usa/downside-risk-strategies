# P-vs-Q Volatility as a Trading Strategy — First Backtest

*Sean Qin · GBC Downside-Risk Project · 2026-07-04*
*Implements APPLICATIONS.md §1.1 (P-vs-Q premia). Per §4, this document is a trading study and lives under trading evidentiary standards, separate from the paper's forecasting claims.*

## 1. Question and design

The Q-measure (options market) quotes a variance forecast; our P-measure models produce another. Is the wedge tradeable — and does *timing* on the wedge beat simply harvesting the unconditional variance risk premium (VRP)?

Two instruments, one signal family. At each position date the signal is `lr = ln(K_Q / F_P)`: log of implied-variance strike over the P-model's forecast of annualized realized variance for the next 21 trading days. Positive = implied rich → short vol.

**Leg A — synthetic 1M variance swap (1995–2026, monthly non-overlapping, 377 trades).** Strike K = (VIX/100)² at month-start t; settles on annualized realized variance of t+1…t+21 (Carr–Wu). Short-var excess return = (K−RV)/K. Cost: 0.25 vol-pt half-spread on the strike at entry. Returns: FF daily market (1990–2026-05) spliced with Bloomberg SPY total return (corr 0.995 on overlap); VIX from a CBOE mirror cross-checked against the Bloomberg pull (corr 0.999997).

**Leg B — front VIX future (2010–2026, daily, 4,148 days).** Short UX1, roll-adjusted with a reconstructed expiry calendar, positions formed at close t−1 earn day-t returns, 1.5 ticks per unit turnover.

**Leg C — robustness.** Same as A but strike from SPY 30d ATM implied vol (2012+, Bloomberg surface pull).

**Strategies per P-model:** s0 always-short-1 (the null: harvest VRP); s1 = sign(lr); s2 = clip(lr / trailing-36m σ(lr), ±2); s3 = ±1 in top/bottom trailing quintile only. All signal transforms use lagged windows only — no lookahead; the daily leg had a same-bar leakage bug during development that was caught and fixed (it showed up as SR ≈ −1.8, a useful canary).

## 2. P-model tournament (21-day-ahead variance, QLIKE, 377 non-overlapping months)

| model | QLIKE ↓ | RMSE(log var) | DM vs EGARCH-t (p) |
|---|---|---|---|
| GARCH-t | **−2.6227** | 0.724 | 0.19 |
| GJR-t | −2.6216 | **0.694** | 0.08 |
| Gibbs ensemble | −2.6190 | — | 0.18 |
| RM2006 | −2.6016 | 0.704 | 0.72 |
| HAR (direct, log) | −2.5807 | 0.738 | 0.78 |
| EGARCH-t | −2.5874 | — | ref |
| EWMA-94 | −2.5527 | 0.727 | 0.21 |
| RW-21d | −2.4771 | 0.779 | 0.003 |

At the monthly horizon the plain/GJR GARCH-t recursions edge out EGARCH-t (contrast with the daily 1-step tournament, where EGARCH-t won) — multi-step EGARCH forecasts are simulation-based and noisier. One degenerate EGARCH fit (1995-05) required a documented GJR fallback; simulated paths are winsorized at 20× median (EGARCH-t path explosion is a known pathology).

## 3. Results — Leg A (the clean, long-history test)

Unconditional VRP is enormous and the market pays it reliably: mean (K−RV)/K = **+25.2% per month**, positive in 82.5% of months (VIX mean 19.8 vs realized 16.2). Everything below is net of costs; returns are per unit of variance notional × strike.

| strategy (best model) | Sharpe | NW-t | skew | hit | 08-09 SR | 2020 SR |
|---|---|---|---|---|---|---|
| s0 always short | 1.07 | 5.18 | −4.15 | 81% | −0.04 | −0.63 |
| s1 sign, GJR-t | 1.04 | 5.14 | −1.14 | 72% | +0.27 | +2.25 |
| **s2 sized, GJR-t** | **1.35** | **6.14** | −1.51 | 71% | **+1.60** | **+3.17** |
| s2 sized, Gibbs | 1.11 | 5.21 | — | — | — | — |
| s3 quintile-only | ≈0.1 | ns | — | — | — | — |

The predictive regression confirms the wedge carries information: standardized ln(K/F_P) predicts the next short-var return with NW-t = **2.60** for GJR-t (corr 0.15); every model gives a positive coefficient. GJR-t — the leverage-aware recursion, consistent with the whole Stage-2 arc — is the most informative P-side.

**The honest headline: the timing edge is real but modest in mean terms.** Paired test of s2-minus-s0: +1.08/yr, NW-t = 1.79 (risk-matched: +0.85/yr, t = 1.46) — not significant at 5% in 31 years of monthly data. What timing demonstrably buys is *tail shape*, not mean: skew improves from −4.15 to −1.51, and s2/GJR is positive in **all six subperiods including both crisis windows**, where always-short loses (crash table: entering 2020-03-05 the signal was net LONG variance, w = −0.62, profiting from COVID; 2008-08-28 exposure cut to w = +0.41 vs the null's 1.0). The seller's blow-up risk is what the P−Q signal removes.

**Leg C kills a naive reading.** Shorting at the SPY *ATM IV* strike since 2012 loses money outright (SR −0.53, t = −1.86): the harvestable premium lives in the VIX-style variance-swap strike — Q-measure *convexity/skew* — not in ATM vol vs P. VRP ≠ "IV is too high"; it is "the variance swap strike is above ATM IV² and both are above P". The P−Q signal turns the ATM version roughly flat (Gibbs s2: SR +0.13) but there is no premium to harvest at the ATM strike.

## 4. Results — Leg B (tradeable-instrument check)

Much weaker, as expected (roll noise, horizon mismatch between spot-VIX-horizon forecasts and futures expiry, daily costs): always-short UX1 SR 0.29 (t = 1.40); best signal RM2006-s2 SR 0.33 (t = 1.62, turnover 84×/yr); GARCH-family signals (stale within month at daily frequency) ≈ 0. Nothing significant. A proper futures test needs daily-refreshed GARCH states and per-contract expiries — noted as follow-up.

## 5. Multiple-testing caveat

~50 model×strategy×leg combinations were evaluated; the headline SR 1.35 is the max of a family whose null (s0) already has SR 1.07. The only claims robust to this: (i) the unconditional VRP itself (t = 5.2, PSR ≈ 1.00, and it is the literature's most replicated fact); (ii) the predictive regression sign (positive for 8/8 models); (iii) the crisis-window sign flip. The +0.28 Sharpe improvement should be treated as suggestive until it survives a pre-registered holdout (e.g. live paper-trading window or the 26-name single-stock panel as cross-validation).

## 6. Where the IQN enters next

This study used variance-level P-forecasts only — exactly what a desk GARCH does. The GBC-native extension is quantile-by-quantile: compare the IQN's P-quantiles against the Q-distribution implied by the IV surface (90/110% moneyness pulls are in hand; 25Δ RR fields came back empty from BBG and need a re-pull if access persists), trade the *skew* wedge (predicted downside asymmetry vs IV skew), and let the confidence signal gate position size. The Leg-C finding sharpens the pitch: since the premium is concentrated in Q-convexity/tails rather than ATM level, a model of the P-*tail* (the IQN's specialty) is aimed at precisely the part of the surface where the premium lives.

## 7. Reproducibility

Code: `GBC_data/code/pq_trade/pq_01_data.py … pq_06_chart.py` (fixed seeds; EGARCH sims seeded per-date). Results JSON: `GBC_data/results/pq_trade/{tourney,bt_monthly,bt_daily,bt_iv,analysis,checks}.json`; series parquets and `pq_trade_cumret.png` alongside. Data: Bloomberg archive `GBC_data/data/raw/` (bbg_impvol, vix_futs_far, etf_totret, iv_SPY) + `ff_factors.csv` + `vix_daily_cboe_mirror.csv` (added; free CBOE mirror, verified vs Bloomberg). Headline numbers independently re-derived from raw inputs by `pq_05_verify.py` (exact match). Known infra quirk: sandbox mount truncates large writes — scripts were executed from /tmp copies.
