# The misspecification frontier — one axis explains everywhere the nonparametric model wins

Synthesis of every study to date (CRSP US equities, FX, 26 countries, 43 cross-asset instruments, all on real data). The central finding of the project, stated as one relationship.

## The claim
Whether a distribution-free conditional-quantile model (GBM / IQN, the GBC family) beats the industry-standard GARCH-t is governed by a single measurable quantity: **the post-GARCH standardized-residual kurtosis** — how badly GARCH-t's fixed-shape Student-t assumption is *locally* violated. Low kurtosis → GARCH is well-specified and wins. High kurtosis → the nonparametric model wins, and the edge grows with the kurtosis.

## The evidence, placed on the axis (edge = nonparam − GARCH pinball %)
Where GARCH-t wins or ties (residual kurtosis ~4-10):
- Developed equity indices (kurt 4.7, 0/8 significant), emerging indices (5.3, 0/10), FX majors (~5, pooled DM −13.7), FX EM (8, pooled DM −9.5), rates (4.7), metals (5.6), crypto daily (9.7). All GARCH's, most significantly.

Where the nonparametric model significantly wins (residual kurtosis ~10-2000):
- CRSP US equities, top decile of recent residual kurtosis: +2.71%, DM 6.54, p about 0.
- Frontier equity indices (kurt 10): +0.7% mean, 4/8 significant (Sri Lanka DM 3.5, Kenya 3.5, Pakistan 2.4, Nigeria 2.1).
- Credit spreads IG (kurt 14): −4% (ratio 0.96), DM 2.27.
- Volatility indices VIX/VVIX/V2X (kurt 33): 3/3 significant, DM 4.7-5.7.
- Hyperinflation FX ARS/EGP (kurt ~2000): 12-14%, crisis tier pooled DM 4.12, p about 0.

The correlation of edge with log residual-kurtosis is 0.53 across countries and 0.43 across asset classes — positive and consistent. Residual kurtosis is necessary but not sufficient (a few high-kurtosis series with other dynamics, e.g. carbon, still favor GARCH; Baltic Dry freight wins big at low measured kurtosis because its non-GARCH-ness lives in limit-moves/autocorrelation, not kurtosis) — but the axis organizes the whole cross-section.

## Why this matters for the paper
1. It replaces a weak, contestable claim ("nonparametric wins in crises") with a strong, falsifiable one ("nonparametric wins in proportion to local residual misspecification, which we measure"). A dramatic price crash (Korea 2026) with mild residual kurtosis (~5) does NOT favor the nonparametric model — GARCH wins there, significantly — whereas hyperinflation FX and volatility indices do.
2. It yields a deployable rule: run GARCH-t by default; switch to (or blend toward) the nonparametric residual-hybrid when the live residual-kurtosis score is high. Or use the residual-hybrid always, since it provably never underperforms GARCH and captures the high-kurtosis wins automatically.
3. It unifies the forecasting flagship (residual-hybrid + EVT, co-best with CAViaR, calibrated at 99%/97.5%) with the capability flagship (Heston likelihood-free posterior) under one story about where and why distribution-free methods pay off in finance.

## Status of the evidence base (all on real/simulated data, with significance)
- Significance (Diebold-Mariano and/or Model Confidence Set) established on: the FRTB battery, the misspecification frontier, crisis FX, the country gradient, and the cross-asset table.
- Calibration (Kupiec + Christoffersen at 99% and 97.5%) established for the residual-hybrid with EVT tail + conformal recalibration.
- Data-blocked remainder: intraday/high-frequency (Bloomberg bdib stores only ~1 day of bars for the composite crypto tickers) — needs an exchange/tick-data source.
