# Resume bullets — downside-risk paper

**Project line (pick one):**
- Semiparametric VaR/ES with a Real-Time Misspecification Score — sole-author manuscript, submitted to the *Journal of Financial Econometrics* (advised by Prof. Wenxin Jiang, Northwestern Statistics)
- Tail-Risk Forecasting Research — sole author; JFEC submission

**Full version (3–4 bullets):**

- Built a bank-grade tail-risk engine (GARCH volatility × one pooled gradient-boosted quantile model across hundreds of stocks, extreme-value tail, conformal calibration) that beats the models banks actually run — filtered historical simulation, GARCH-t, RiskMetrics — on 140 CRSP names with date-clustered Diebold–Mariano statistics of 4.4–8.3, and passes both FRTB regulatory exception tests through the 2008 crisis.

- Discovered a real-time "misspecification score" from GARCH residuals that predicts *when* machine learning beats parametric risk models: its top decile carries a +2.7% forecast-accuracy edge (DM 6.5, ~7× the calm-market edge), a pattern that replicates across US equities, FX, 26 country indices, and 43 cross-asset instruments.

- Stress-tested every headline claim like a hostile referee: frozen-specification 2000–2013 holdout with predictions written down in advance, Romano–Wolf familywise error control, point-in-time universe including delisted stocks, strict pre-2008 calendar splits, annual walk-forward refits, and leakage/calibration audits — all conclusions survived.

- Because one pooled fit replaces per-asset estimation, the model prices day-one IPOs and new listings from characteristics alone — risk numbers no per-asset model can produce — with 6–10% accuracy gains on young listings.

**Compact version (2 bullets):**

- Sole-authored a JFEC submission: a semiparametric VaR/Expected Shortfall engine that beats bank-standard models (DM 4.4–8.3, 140 US stocks) and passes FRTB exception tests through the 2008 crisis, plus a real-time score identifying when the machine-learning edge is large (+2.7% top decile, DM 6.5, replicated out-of-era 2000–2013).

- Hardened all results through adversarial-review cycles: frozen-spec holdout with pre-committed predictions, Romano–Wolf multiplicity control, point-in-time universe with delistings, calendar-split and walk-forward leakage audits.

**One-liner (for space-starved resumes):**

- Sole-author JFEC submission: semiparametric VaR/ES engine beating bank-standard models (DM 4.4–8.3) with a real-time score that predicts when the edge is large (+2.7% top decile, replicated on a frozen 2000–2013 holdout).
