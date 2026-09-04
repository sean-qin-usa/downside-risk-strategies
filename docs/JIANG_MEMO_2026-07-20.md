# Research Progress Memo — Generative Bayesian Computation for Conditional Downside-Risk Forecasting

To: Prof. Wenxin Jiang (Northwestern, Statistics & Data Science)
From: Sean Qin
Date: July 20, 2026 · Reporting period: July 6 – July 20, 2026

Companion materials: full study reports, result JSONs, and reproducible code in the project Drive (FRTB battery, misspecification frontier, uncertainty-coverage arms, Heston/rough-volatility SBC, joint-sampler studies, cross-country studies). A restructured full paper draft (with tables, figures, and reconciled bibliography) accompanies this memo.

## 1. Summary

The two weeks since the last memo converted the project from a collection of studies into a paper with a single organizing principle and five crisp contributions. The organizing principle is a **misspecification frontier**: a live, per-asset, per-day score — the excess kurtosis and asymmetry of recent GARCH-standardized residuals — that predicts, with per-date Diebold–Mariano significance, exactly when distribution-free conditional quantile methods beat the parametric standard. Where the score is in its top decile the nonparametric edge is +2.71% (DM 6.5); over the other ninety percent of days the two tie and GARCH-t is as good or better. The same axis organizes results across four universes.

## 1a. Wins, losses, and direction — at a glance

Every win below carries its magnitude, because the size of the edge is the most important part of the result.

**Wins (magnitude · significance):**

| Result | Magnitude | Significance |
|---|---|---|
| Misspec frontier, top decile (200 CRSP names) | **+2.71%** pinball | DM 6.54, p≈0 |
| Hyperinflation FX (USDARS / USDEGP) | **+12% / +14%** | DM 2.86 / 3.80; tier-pooled DM 4.12 |
| FRTB engine vs GARCH-t / FHS / EWMA / HS | +0.3% / +0.4% / +1.5% / +1.9% | DM 4.4 / 5.7 / 8.3 / 7.3 |
| ES97.5 capital: FHS & GARCH-t over-state, hybrid exact | **8–11% capital over-charge removed** | pred −5.80 vs realized −5.76 |
| Exception tests | only entrant passing at both levels | Kupiec+Christoffersen@99 (EVT tail); Kupiec@97.5 (conformal) |
| 10-day FRTB horizon vs √h-scaling | +0.4% (h=1) → **+1.4% (h=10)**, ~5% at h=20 | holds in 2020/2022 stress |
| Edge concentration by vol regime | **×4** calm→turbulent quintile (gap 0.0059→0.0247) | both nonparam models win every quintile |
| Frontier equity indices (Sri Lanka, Kenya, Pakistan, Nigeria) | up to +3% | 4 significant, DM 2.1–3.5; corr(kurt, edge)=0.53 |
| Vol indices VIX/VVIX/V2X | ~+1.3% | 3/3 significant; VIX passes Christoffersen both levels |
| Amortized transfer vs own-history | **+6–10% young names**, positive at every age (benchmark = own EWMA-t/empirical, not full GARCH — mature-age comparison vs GARCH open) | full-scale 1.32M rows; cold-start: only feasible model |
| Uncertainty bands on (VaR, ES) | coverage 0.89–0.95 vs 0.90 target | block bootstrap + EVT interval, 150 names |
| Rough-vol likelihood-free posterior (GBC proper) | **Hurst H: 42% of prior uncertainty removed** | SBC cov90 = 0.91 (calibrated) |
| Deep 1% co-crash tail (concentrated books) | Gaussian/DCC ~**2× too many breaches**; hybrid on target (0.0085 vs 0.01) | every weighting scheme |

**Losses and ties (reported as such, with magnitudes):** single-name daily equity: GJR-GARCH-t beats the neural IQN by **4.5–6.2%** at every horizon (DM +12 to +18) — the retired "−38%" claim was a mismatched-universe artifact; equity portfolio tails: multivariate GARCH/DCC beats direct nonparametric models three separate ways (weight-input IQN ~2× worse); daily crypto and major/EM FX: GARCH wins (pooled DM −9 to −14); Korea 2026 crisis: GARCH wins all 23 assets (DM −2.5 to −5) — a price crash is not residual misspecification; learned regime gate: **+0.0%** over always-nonparametric; hierarchical own-history blends: hurt 0.3–4.3% at every age; CAViaR: statistical tie with our engine (DM 0.59) — co-best, not uniquely dominant; electricity: earlier "win" was a log-return artifact, GARCH wins on differences.

**Direction:** (i) the paper is now assembled — full draft with tables, figures, author-year format, and reconciled bibliography (finance/econometrics standard; not IEEE); (ii) the thesis-core weighting continues to shift from benchmark-beating toward what only the generative framework can do — calibrated uncertainty and likelihood-free inference; (iii) the remaining items are compute jobs, listed in §9, queued for the GPU box and the Bloomberg host.

## 2. The misspecification frontier (the organizing empirical result)

GARCH-t assumes standardized residuals are i.i.d. Student-t with fixed shape; static fat tails do not hurt it (ν absorbs them). What hurts is the shape being *locally* violated — recent residuals far fatter-tailed or more asymmetric than any fixed t.

On 200 CRSP names (221.6k test rows), bucketing the per-(name, day) pinball edge of the amortized nonparametric model over GARCH-t by deciles of the trailing 63-day residual excess kurtosis: the edge is ~0 (occasionally negative) in deciles 1–8, 0.52% in decile 9, and **2.46% in decile 10**. Per-date Diebold–Mariano confirms this is real: top decile +2.71% with DM 6.54 (p≈0); bottom decile +0.19%, DM 1.41 (p=0.079, not significant — GARCH is fine where well-specified). Residual *asymmetry* drift is an equally strong trigger (top decile +2.37%). The overall average edge is only +0.44% precisely because it is concentrated: this is a top-decile phenomenon, not a linear trend.

The same axis explains the geography of the edge:

- **26 equity country indices** (Bloomberg): developed mean ratio 1.007 (residual kurtosis ~4.7, zero significant nonparametric wins), emerging 1.012 (kurt 5.3, zero), frontier 0.993 (kurt 10.0, four significant wins — Sri Lanka DM 3.20, Kenya 3.52, Pakistan 2.38, Nigeria 2.06). corr(log residual kurtosis, edge) = 0.53.
- **24 FX pairs**: majors and ordinary EM go to GARCH (pooled DM −13.7 and −9.5). The crisis tier is the exception: USDARS 12% better (DM 2.86), USDEGP 14% (DM 3.80), tier-pooled DM 4.12 (p≈0). The smoking gun is residual kurtosis: crisis tier ~1,900 (ARS 3,298) vs majors 39 vs EM 8.
- **43 cross-asset instruments**: 13/43 significant nonparametric wins, concentrated in volatility indices (VIX/VVIX/V2X, 3/3), Baltic freight (−15%, DM 9.4), credit spreads (IG OAS −4%, DM 2.27), rates-vol (MOVE). corr(log kurt, edge) = 0.43.
- **Negative control — Korea 2026**: a dramatic *price* crash is not residual misspecification. GARCH-t significantly beats the nonparametric model on all 23 Korean assets (DM −2.5 to −5.0); Korean residual kurtosis is only 4–13. The frontier is about the residual *shape*, not headline turbulence.

Honest limits: kurtosis is necessary but not sufficient (carbon has kurt 288 and ties; NGN/UAH/TRY have huge kurt and GARCH holds), so the frontier is presented as a strong, monotone regularity with significance in the pooled/top-decile statistics — not a per-asset law.

## 3. An industry-standard-and-above risk engine (the FRTB chapter)

Banks do not run bare GARCH: under FRTB the regulatory objective is ES97.5 and the workhorses are Historical Simulation and GARCH-FHS, backtested by VaR exceptions. The battery is therefore HS, EWMA/RiskMetrics, GARCH-t, GJR-GARCH-skew-t, GARCH-FHS, and (added after an anti-strawman audit) Engle–Manganelli SAV-CAViaR — evaluated on ES97.5, average pinball, Kupiec and Christoffersen at 99% and 97.5%, per-date Diebold–Mariano, and Hansen's Model Confidence Set (140 CRSP names, 155k obs).

The winning object is the **residual-hybrid**: GARCH supplies the conditional scale; a state-conditioned nonparametric model supplies the residual shape; an EVT/GPD tail (τ≤0.025) and a split-conformal per-level recalibration finish the tails. Results:

- Pinball: hybrid 0.3551 — +0.3% over GARCH-t (0.3561, DM 4.38), +0.4% over FHS (0.3565, DM 5.70), +0.6% over GJR-skew-t (DM 5.73), +1.9% over HS (DM 7.34), +1.5% over EWMA (DM 8.33), all p≈0.
- The MCS honesty check: adding CAViaR produces a statistical tie (0.3460 vs 0.3461, DM 0.59; 90% MCS = both). The hybrid is **co-best with CAViaR**, not uniquely dominant — and still significantly beats everything banks actually run.
- ES97.5 calibration is the practical headline: hybrid predicted −5.80 vs realized −5.76 (nearly exact), while FHS (−6.20 vs −5.59) and GARCH-t (−6.17 vs −5.65) **over-state ES by 8–11% — a direct capital over-charge** the hybrid removes.
- Exception tests: the raw hybrid's 99% tail was slightly hot (1.19%); the EVT tail fixes it (1.04%, Kupiec p=0.10, Christoffersen p=0.20 — the only entrant passing both at 99% while topping the accuracy table). The 97.5% level, which *every* raw model failed, is fixed by the conformal layer (Kupiec p=0.24 after recalibration).
- The edge grows at the FRTB 10-day horizon (+0.4% at h=1 → +1.4% at h=10, ~5% at h=20 in the amortized panel) and holds in the 2020/2022 stress window. At 10 days GARCH √h-scaling badly over-states ES (−19.4 predicted vs −15.4 realized) while the directly-learned quantiles are calibrated (−19.05 vs −17.70).

Cross-asset winners audit (with corrections): VIX is a clean calibrated win (+0.9%, DM 1.74, passes Christoffersen at both levels); IG credit (+52% accuracy, DM 30.6) and Baltic freight (+15%, DM 9.4) fail breach-independence — flagged for repair, not claimed; the earlier electricity "win" was a log-return artifact on near-zero/negative prices — refit on differences, GARCH wins ERCOT and PJM, and electricity is removed from the win list.

## 4. Honest uncertainty on the risk number

This chapter's deliverable is calibrated uncertainty bands on (VaR, ES) — which no standard model (GARCH, CAViaR, FHS, or our own hybrid) provides. To keep the framing honest: **the constructions that actually deliver calibration are the block bootstrap on GARCH residuals, adaptive conformal inference, and an EVT tail interval.** The Gibbs posterior enters where it has real results — one measured negative that answers your caution, and one repaired variant — and nowhere else.

**(a) Your caution, confirmed as a number.** On 80 CRSP names (τ=0.05), the naive Gibbs posterior SD of the VaR level is 0.108 while the moving-block-bootstrap sampling SD is 0.179: naive Gibbs on raw returns **understates VaR uncertainty ~1.6×**. The i.i.d.-bootstrap ratio is 1.19, so the 1.19→1.64 gap isolates the serial-dependence contribution — dependence shrinks the effective sample size and the product-form posterior over-concentrates, exactly as you warned.

**(b) The fix is residual space, and bootstrap/conformal do the work.** The identical construction on GARCH-standardized residuals gives ratio 0.79 — overconfidence gone. On residuals, block and i.i.d. bootstraps agree (0.947 vs 0.953 at α=2.5%), the direct diagnostic that dependence has been filtered out. On the coverage side, adaptive conformal inference attains the best and most stable realized VaR coverage under drift (5.03% realized at the 5% level; rolling max-deviation 0.042 vs 0.074 for a fixed empirical window; 200 names).

**(c) Calibrated bands on (VaR, ES), end to end (150 names, target 0.90):** block bootstrap on residuals: VaR ~0.95, 2.5% ES 0.90 exactly; the 99% ES gap (0.86 — too few tail points) is closed by a GPD peaks-over-threshold interval (0.887 at 1%, 0.90 at 2.5%, at the honest price of ~1.6× wider intervals). The Gibbs posterior with naive ω over-covers (0.987–0.993); calibrating ω against the block-bootstrap SD brings it to 0.953–0.967 — a workable variant, but the bootstrap it is calibrated against is doing the statistical work, and the paper says so.

## 5. Likelihood-free calibration of intractable models (the GBC chapter proper)

The capability GARCH/MLE structurally cannot offer: amortized likelihood-free posteriors validated by simulation-based calibration.

- **Heston** (40k simulated paths, 10 path summaries): posteriors calibrated (cov80 0.78–0.80, cov90 0.85–0.90, all five parameters); informative where a single path identifies — vol-of-vol info-gain 36.5%, long-run variance 13%; mean-reversion and leverage weakly identified, as expected.
- **Rough Bergomi** (non-Markovian fractional volatility, no tractable likelihood at all): the amortized posterior **recovers the Hurst roughness H with info-gain 0.42 — 42% of prior uncertainty removed — at SBC cov90 0.91** (IQN; 0.89 GBM); η info-gain 0.30; all coverages 0.85–0.92. Recovering the parameter that defines rough volatility, with calibrated uncertainty, from one 252-day path is the strongest "GBC does something structurally new in finance" result we have, and here the neural IQN is canonical (it samples the posterior; trees give fixed quantiles).

## 6. Multivariate: negative, then partially rescued

Three direct nonparametric portfolio-tail attempts all lost to multivariate GARCH (CCC/DCC), including a neural weight-input IQN that was ~2× worse — a network fed summary state never recovers w′Σw. We concede equity co-crash to explicit covariance models.

The rescue mirrors the univariate hybrid: DCC supplies the portfolio *scale*, a generative IQN learns only the standardized residual *shape*. Gross miscalibration disappears (PIT-KS 0.30 → 0.055–0.075, comparable to Gaussian), and the hybrid **wins the deep 1% tail in every weighting scheme** — Gaussian/DCC is ~2× too thin there (cov01 0.018–0.024 vs 0.01) while the hybrid is near nominal, best on concentrated books (top-1: 0.0085). Gaussian stays better at the moderate 5% tail. A crossover, not a loss.

## 7. Honest negatives and corrections logged this period

1. **A learned regime gate adds nothing** (+0.0% over always-nonparametric; the 4.4% per-day oracle gap is hindsight — predictability corr 0.16). Deployable rule: amortized nonparametric, or the residual-hybrid for a guaranteed ≥GARCH floor. The frontier score's role is monitoring.
2. **The −38% figure is retired.** Same-rows audit (102k identical rows): unit-matched GJR-GARCH-t beats the production IQN by 4.5–6.2% at every horizon (DM +12 to +18); recalibration halves the gap but GARCH still wins. Single-name daily equity belongs to leverage-GARCH.
3. **Trees vs the neural net, resolved honestly.** Raw: trees win (0.3650 vs 0.3551, DM 13.3) and the neural tail badly under-covers (breach99 3.2%). Tail-aware τ-sampling + monotone rearrangement + conformal recal: gap ~0.2% (0.3638 vs 0.3632, DM 3.03), tail fixed (0.92%). GBC is the framework; trees are the strongest tabular estimator; the tuned IQN is competitive and is required for §§5–6.
4. **Hierarchical/Gibbs own-history blends fail in both directions tried** (hurt 0.3–4.3% at every age). Full-scale ablation (1.32M rows, 720 names): the transfer edge is carried by own recent dynamics (realized vol above all); characteristics matter only at cold-start. Rich conditioning beats explicit hierarchy.
5. **Electricity artifact and Korea control** — §§2–3.

## 8. Paper status

The restructured draft is now a full paper: 10 sections, 5 contributions, 4 tables, 7 figures (generation script `make_figures_v2.py` / `go_figures.bat`; exact-value JSON hookup where available, verified headline numbers otherwise), and a reconciled bibliography (`refs_v3.bib`, 57 entries). Format follows the finance/econometrics standard — single-column, author–year natbib citations, JEL codes — which is what J. Financial Econometrics (OUP template at submission), J. Banking & Finance (Elsevier), and Quantitative Finance all use; IEEE format is not used in this field. The July-12 GRAFT-Q draft is preserved separately as the trading-appendix feeder. An Applications section (regulatory capital, misspecification monitor, trading regimes, scenario generation) sits before the conclusion. If length forces a split: contributions 3+4 → methods/Bayesian paper (Bayesian Analysis); 1+2+5 → applied paper.

## 9. Next steps (compute jobs, queued)

Credit/freight breach-independence repair (clustered exceptions) before claiming those universes; WRDS CRSP 2000–2024 for a true 2008 stress window and expanding calm-vs-stress split; Fissler–Ziegel joint (VaR, ES) scoring plus a certainty-equivalent/MEU translation of the ES edge into basis points of capital; the loss-in-the-exponent ablation (CRPS / tail-CRPS / Fissler–Ziegel / MEU); a leverage summary statistic to identify ρ in the SBC studies; and the live July-2026 forward holdout continues logging weekly.
