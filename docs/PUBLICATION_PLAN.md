# GBC Project — Publication Plan
*Draft memo: what to publish, where, and how. For discussion with Prof. Jiang. Venue fit and acceptance are uncertain and ultimately the advisor's call; treat this as a menu, not a promise. All strategy numbers are backtests and must be framed as such (no performance claims).*

---

## 1. There are two separable papers

The work splits cleanly into a **methods/forecasting paper** and an **empirical/trading paper**. They can be published independently; the methods paper is the stronger academic contribution and the natural fit for a statistics advisor.

### Paper A — Forecasting methods (the GBC / IQN paper) — *lead paper*
**Working title:** *"When do neural conditional-quantile networks beat GARCH for downside risk? A regime map across assets, horizons, and data regimes."*

**The honest, defensible thesis (this is a feature, not a weakness):**
- On **single-name equity, daily–multi-day**, a leverage GARCH-t is the benchmark to beat, and a walk-forward Implicit Quantile Network (IQN) does **not** beat it — GARCH is ~4.5–6.2% better in pinball loss on identical rows (DM t = +12 to +18). *(This corrects an earlier mismatched-data comparison.)*
- The IQN **wins decisively where classical GARCH is weak**: (i) **intraday crypto** (hourly, DM t ≈ −5.2, p ≈ 10⁻⁷, beats a full clean ladder incl. FHS); (ii) **transfer to unseen / young / newly-listed assets** (amortization — GARCH structurally cannot fit a no-history asset); (iii) a **maturing / regime-shifting** vol environment (long-run crypto).
- A **frozen-cutoff experiment** shows the neural tail is training-regime-dependent (a calm-trained net is crash-blind) while GARCH is stable across cutoffs — motivating an **EVT + adaptive-conformal (ACI) tail splice** that calibrates coverage exactly.
- Methodological contributions: the **amortized/transfer quantile forecaster**, the **regime map** (a clear statement of *where* flexible models pay off), and the **EVT/ACI calibration layer**.

**Why this is publishable (and good):** rigorous, honest horse-races with DM tests, model-confidence-set logic, calibration/coverage, and a clean identification of the boundary condition. Forecasting and econometrics journals explicitly value credible negative/nuanced results — an overclaiming "neural beats everything" paper would be *weaker* and less believable.

### Paper B — Empirical / trading (the VRP paper) — *second output*
**Working title:** *"Harvesting the cross-sectional variance risk premium: execution, tenor, and diversification."*

**Thesis:** the tradeable edge is a **risk premium**, not a forecasting edge — cross-sectional VRP selection (sell puts on the richest implied-minus-realized names), **execution** (post at mid vs cross the spread nearly doubles the Sharpe), **weekly beats monthly net of realistic spread**, and **cross-asset ETF sleeves** (corr ≈ 0.05) roughly double the portfolio Sharpe. Factor attribution shows the selection adds alpha beyond a short-vol factor.

**Audience:** practitioner/empirical-finance, not statistics. Better as a separate submission than bolted onto Paper A.

---

## 2. Where to publish

### Step 0 — Working paper first (do this regardless of journal)
- **arXiv** under **q-fin** (q-fin.ST Statistical Finance, q-fin.RM Risk Management, q-fin.TR Trading/Microstructure, q-fin.CP Computational Finance) + cross-list **stat.ML**. Establishes a public timestamp and invites feedback.
- **SSRN** (Financial Economics Network) — the standard circulation venue in finance; how most people will actually find and cite it.
- Do this *after* the advisor signs off on framing, and *before* journal submission.

### Paper A — target journals (ranked by fit)
1. **International Journal of Forecasting (IJF)** — best fit. Prizes rigorous forecast comparisons, DM/MCS tests, calibration, and honest results across regimes. This is the natural home.
2. **Journal of Financial Econometrics** (Oxford) or **Journal of Applied Econometrics** — if you want a more econometrics-theory framing.
3. **Journal of Risk** or **Quantitative Finance** — if the tail-calibration (EVT/ACI, VaR/ES) becomes the headline.
4. **Journal of Forecasting** (Wiley) — solid alternative to IJF.
- *ML venues (NeurIPS/ICML/AISTATS or their time-series / ML-for-finance workshops)* are an option for the amortized-quantile method, but top-tier ML tends to reward "neural wins" narratives; the honest regime-boundary story lands better in forecasting/econometrics. A workshop paper is a reasonable low-cost parallel shot.

### Paper B — target journals
1. **Journal of Portfolio Management (JPM)** — practitioner, strategy-focused.
2. **The Journal of Derivatives** — options/VRP is squarely in scope.
3. **Financial Analysts Journal (FAJ)** — higher bar, broad practitioner+academic.
4. **Journal of Alternative Investments** / **Journal of Futures Markets** — good alternatives.

### Conferences / early exposure
- **SoFiE** (Society for Financial Econometrics) and **CFE** (Computational and Financial Econometrics) meetings — ideal for Paper A.
- Student research competitions / poster sessions for early feedback and CV value.

---

## 3. What's still needed to be submission-ready

**Paper A:**
- Finish the **K=5 training-budget arm** (running) — confirms the equity gap is structural, not budget. *(Auto-completing via a scheduled check.)*
- Re-run **MCS** (model confidence set) on the matched equity rows and formally on the crypto ladder.
- Tidy the **EVT/ACI** section into a clean, reproducible calibration protocol with coverage tables.
- One **reproducibility appendix** (walk-forward protocol, leakage controls, unit-matching, seeds).

**Paper B:**
- Lock the **net-of-cost** results (weekly vs monthly at bid — done) and add a realistic **capacity/turnover** discussion.
- **Forward paper-trade** log (the monthly + weekly scheduled signals) to report *live-fill* evidence — a strong differentiator vs pure backtests.
- Frame all Sharpes as **in-sample honest / regime-caveated** (the OOS 4+ is a kind-regime artifact — say so).

---

## 4. Recommended sequence
1. Advisor meeting: agree Paper A framing + author order.
2. Draft Paper A (methods + regime map + calibration), fold in the K=5 result.
3. Post arXiv + SSRN working paper.
4. Submit Paper A to IJF; in parallel, draft Paper B for JPM/J. of Derivatives.
5. Present at SoFiE/CFE or a student session for feedback before/after submission.

*Caveat: journal fit and acceptance are uncertain and depend on execution and reviewers; the advisor should drive final venue choice. Nothing here is a guarantee of publication or of trading performance.*
