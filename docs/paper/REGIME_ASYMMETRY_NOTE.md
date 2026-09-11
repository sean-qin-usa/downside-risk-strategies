# Training-Distribution Asymmetry in Volatility Forecasting

*Sean Qin · GBC Downside-Risk Project · 2026-07-04*
*Standalone note; grew out of the P-vs-Q trading study (PQ_TRADE_BACKTEST.md). Candidate section for the paper or a short companion piece.*

## Claim

Volatility-model risk is asymmetric in the *training distribution*, not just the test distribution: observations from stress regimes are irreplaceable, while observations from calm regimes are nearly redundant. A forecaster trained without stress data does not merely degrade in a crisis — it fails in the specific direction that destroys short-volatility positions, understating realized variance by roughly 60%.

## Evidence

Direct-projection HAR forecasting 21-day-ahead market variance, 1990–2026 (377 non-overlapping months). Each month is assigned a point-in-time regime: the expanding-window tercile of the VIX (calm / mid / stress; no look-ahead). Four training sets per forecast date, all restricted to past data: all history, or only past observations from one regime. QLIKE by train × test cell (lower = better):

| train \ test | calm | mid | stress |
|---|---|---|---|
| all history | −3.294 | −2.766 | −1.853 |
| calm only | −3.344 | −2.546 | **−0.650** |
| mid only | −3.350 | −2.752 | −1.629 |
| stress only | −3.190 | −2.725 | −1.841 |

Three observations. First, in calm markets everything works: the spread across training sets is ~0.15 QLIKE, and even the stress-only model is fine (its error is *conservative*: mean log-bias +0.57, i.e. it over-forecasts variance). Second, in stress months the training sets separate violently: stress-trained (−1.841) and all-history (−1.853) are indistinguishable, but the calm-trained model collapses to −0.650 — a gap eight times larger than the reverse direction — with mean log-bias −0.92: it forecasts about 40% of the variance that then realizes. Third, matched-regime training beats all-history only marginally (paired t ≈ −1.6 in calm and stress); all-history is a strong baseline precisely because it contains the crises.

A companion result from the same study: for regression-type forecasters, *which* regimes the training sample covers matters more than its size or recency — a regime-matched noncontinuous sample beat a contiguous 10-year window as a trading signal (Sharpe 0.97 vs 0.74), while randomly discarding 50–75% of training observations changed almost nothing.

## Why it matters

1. **For risk practice.** The models most likely to recommend selling volatility (or holding thin capital) are exactly those estimated on benign samples — the failure is self-selecting. Minimum requirement for any production vol model: the training window must contain at least one stress regime, and backtests should report the calm-trained/stress-tested cell explicitly as a worst-case diagnostic.
2. **For the amortization/transfer agenda.** This is the within-asset, across-time mirror of the paper's cross-asset transfer result: breadth of the training distribution beats quantity and recency. It predicts that the amortized panel IQN's advantage should be largest for assets whose own histories lack crises — testable on the 26-name panel.
3. **For the Gibbs-posterior direction.** Regime-dependence of forecaster skill is the empirical premise behind state-dependent η: if model ranking flips across regimes (as the matrix shows it does for training sets), then online weights should chase performance at regime-dependent speed. The matrix supplies the "regimes exist and matter" preamble with a clean effect size.
4. **For the P-vs-Q trading study.** The unconditional VRP harvest is short a crash; its P-side signal is trustworthy only if the P-model has seen crashes. The matrix quantifies what "has seen" is worth: ~1.2 QLIKE in the state where the position is at maximum risk.

## Caveats and next steps

Single asset (US market factor), single forecaster family (HAR; GARCH cannot be fit on noncontinuous samples, so the regime rows use a regression model), regimes defined by VIX terciles. Next: repeat on the 26-name panel (does the asymmetry shrink for high-beta names whose calm regimes are less calm?); repeat with the IQN (does conditioning on VIX-level features substitute for stress training data? — the transfer question in miniature); connect to the conformal wrapper (does adaptive conformal repair a calm-trained model's stress coverage fast enough to matter?).

*Reproduce: `GBC_data/code/pq_trade/pq_12_regime_matrix.py` → `results/pq_trade/regime_matrix.json`; splits companion `pq_11_splits.py` → `splits_study.json`.*
