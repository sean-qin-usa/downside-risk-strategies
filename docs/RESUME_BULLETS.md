# Resume bullets — drop-in for the paper project

Header stays as on your resume ("Semiparametric Value-at-Risk/Expected
Shortfall with a Real-Time Misspecification Score (GitHub) — Working Paper
with Prof. Wenxin Jiang, Northwestern University"). After ScholarOne, change
"Working Paper" to "Submitted to the Journal of Financial Econometrics."

**Delete the first two current bullets** ("Building a Bayesian/ML framework…
cryptocurrency…" and "Developing a reproducible evaluation pipeline… GP
surrogates… CRPS…") — they describe an early version of the project that no
longer matches the paper, and the GitHub link next to them invites the
cross-check.

**Replace all five with these three:**

- Built a semiparametric VaR/Expected Shortfall engine: GARCH volatility, one shared machine-learned quantile model, extreme-value tail; beats industry-standard risk models out of sample (**DM 4.4–8.3**) and passes regulatory backtests through the 2008 crisis.

- Introduced a real-time misspecification score predicting when ML beats parametric risk models; its top decile carries a **+2.7% accuracy edge (DM 6.5)**, replicated on a frozen 2000–2013 holdout with pre-committed predictions.

- One pooled fit replaces per-asset estimation, prices day-one listings no per-asset model can, and gains **6–10%** on newly listed names.

**Two-bullet version if space is tight:**

- Built a semiparametric VaR/ES engine (GARCH volatility, one shared ML quantile model, EVT tail) that beats industry-standard risk models out of sample (**DM 4.4–8.3**) and passes regulatory backtests through the 2008 crisis; prices day-one listings no per-asset model can (**6–10%** gains on young names).

- Introduced a real-time misspecification score predicting when ML beats parametric models; top decile carries **+2.7% (DM 6.5)**, replicated on a frozen 2000–2013 holdout with pre-committed predictions.
