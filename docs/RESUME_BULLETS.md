# Resume bullets — drop-in for the paper project

Header as you now have it ("Forecasting Value-at-Risk and Expected Shortfall
with a Real-Time Misspecification Score — Working Paper with Prof. Wenxin
Jiang"). After ScholarOne, change "Working Paper" to "Submitted to the
*Journal of Financial Econometrics*."

**Still to do on the doc:** delete the two old bullets above these
("Building a Bayesian/ML framework… cryptocurrency…" and "…GP surrogates…
CRPS…") — they describe an early version that no longer matches the paper the
GitHub link points to.

**Layman-clear version (replace the three highlighted bullets):**

- Built a model forecasting worst-case daily stock losses (Value-at-Risk/Expected Shortfall): GARCH filtering plus one machine-learned tail model shared across stocks; beats the risk models banks use out of sample (**t-stats 4.4–8.3**), passing regulatory backtests through the 2008 crisis.

- Created a real-time warning score that flags when machine learning will beat classical risk models: forecasts improve **+2.7%** (**t = 6.5**) on flagged days, repeated on untouched 2000–2013 data with predictions written down in advance.

- Amortized the estimation: one model trained across all stocks replaces thousands of individually fitted ones, transfers to stocks never seen in training, and prices brand-new IPOs from day one (no per-stock model can), with **6–10%** gains on young listings.

**Two-bullet squeeze:**

- Built a model forecasting worst-case daily stock losses (VaR/Expected Shortfall) that beats the risk models banks actually use (**t-stats 4.4–8.3** out of sample, Diebold–Mariano), stays accurate through the 2008 crisis in regulatory backtests, and prices brand-new IPOs from day one (**6–10%** gains on young listings).

- Created a real-time warning score flagging when machine learning beats classical risk models: **+2.7%** improvement (**t = 6.5**) on flagged days, repeated on untouched 2000–2013 data with predictions written down in advance.
