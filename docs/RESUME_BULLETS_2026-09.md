# Resume — research project section (updated 2026-09-04, one-entry form)

## Heading
**Semiparametric Value-at-Risk and Expected Shortfall with a Real-Time Misspecification Score** (GitHub: github.com/sean-qin-usa/downside-risk-paper) — March 2026–Present
*Working paper (sole author), advised by Prof. Wenxin Jiang, Northwestern University*

## Bullets
- Built a semiparametric VaR/ES engine (GARCH scale x cross-sectionally amortized residual-shape model, extreme-value tail, conformal recalibration) that beats historical simulation, RiskMetrics, GARCH-t, GJR-skew-t, and FHS on 140 CRSP names / 155k obs (date-clustered DM 4.4–8.3), removes an 8–11% ES97.5 over-statement (~5–15bp of capital per 100bp of ES-driven charge), and passes Kupiec/Christoffersen exception tests at both regulatory levels — including a 2008-crisis test window where HS and EWMA fail.
- Identified a real-time misspecification score (rolling kurtosis/asymmetry of GARCH-standardized residuals) that predicts when flexible tails beat parametric risk models: +2.7% pinball edge in its top decile (DM 6.5); replicated under a pre-registered, frozen specification on an untouched 2000–2013 CRSP panel of 701k obs (+0.9%, DM 2.2), and validated across US equities, FX (12–14% on hyperinflation currencies), 26 country indices, and 43 cross-asset instruments.
- Showed one model amortized across hundreds of names replaces per-asset estimation, beats own-history benchmarks at every listing age (6–10% for young listings), and prices IPOs day one — the regime where no per-asset model can be estimated; full public replication package (code and derived statistics; licensed data rebuilt from documented queries).
- Companion work with Prof. Jiang on generative Bayesian computation: amortized likelihood-free posteriors validated by simulation-based calibration (rough-volatility Hurst recovery; 90% credible coverage 0.91), and a ~1.6x Bayesian-overconfidence diagnosis on VaR with a GARCH-residual fix restoring honest coverage.

Notes: one entry keeps depth over count (interview-proof); the companion bullet preserves the GBC identity and the Jiang collaboration honestly. Link the paper repo, not the private strategies repo. All numbers trace to results/ JSONs in the repo.
