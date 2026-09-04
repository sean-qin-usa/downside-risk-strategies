# Beating Institution-Grade Models — Benchmark Ladder + Bloomberg Pull List

*Sean Qin · GBC Downside-Risk Project · 2026-07-03*
*Follow-up to RESEARCH_DIRECTIONS_V2.md, written after the amortization/transfer breakthrough (IQN beats per-ticker GARCH: in-sample 66% of 71 tickers p=0.0007; transfer 11/14 unseen p=0.09) and the capital-efficiency finding (calibration shape, not CRPS, drives dollars).*

---

## 1. What institutions actually run (the bar to clear)

"Simple GARCH" is the academic benchmark; desks and risk departments run richer models whose advantage is mostly **richer information sets** (intraday + options-implied), not fancier recursions. That asymmetry is the strategic point: **GARCH-family models can't easily ingest new information; the IQN eats features natively.** Every rung we add to the benchmark ladder also hands the IQN a new feature — so upgrading the benchmarks should widen, not shrink, the IQN's edge. If it doesn't, that's a finding too.

**Tier 1 — already done:** GARCH-t, EGARCH-t, GJR-t, RiskMetrics, CAViaR, FHS, EVT-POT, GP. Champion: EGARCH-t; best overall: Gibbs hybrid.

**Tier 2 — the institutional suite (proposed additions, roughly by importance):**

1. **FHS with EVT tails (FHS-EVT).** Banks' regulatory workhorse plus the McNeil–Frey tail. GARCH filter → standardized residuals → empirical body + GPD tail → rescale by today's vol. This is the closest thing to "what a bank's internal model actually produces." Cheap: composes two things we have (fix the low-vol GPD blow-up first).
2. **Realized GARCH / HEAVY (intraday-informed vol).** Hansen–Huang–Shek Realized GARCH and Shephard–Sheppard HEAVY use realized variance from intraday bars as the vol driver — the standard "institution upgrade" over daily GARCH, typically a large accuracy gain. Needs intraday data (see pull list). Also gives the IQN an RV feature on equal terms.
3. **Option-implied models.** The market's own risk forecast: (a) IV-scaled FHS (replace GARCH vol with 30d ATM implied vol); (b) implied-quantile benchmark from the vol surface (ATM IV + 25Δ risk reversal + butterfly → skewed distribution, e.g. via Corrado–Su or SVI fit). Forward-looking where all GARCH is backward-looking; this is what vol desks actually look at. Needs surface pulls.
4. **GAS / score-driven models (Creal–Koopman–Lucas).** The modern econometrics standard; t-GAS updates vol by the score of the t-likelihood, making it robust to outliers where GARCH overreacts. One pip install (`arch` doesn't have it; `pyflux`/hand-rolled — a day of work).
5. **RiskMetrics 2006 (Zumbach).** The successor to the λ=0.94 EWMA everyone still cites — multi-horizon EWMA cascade with fat tails. Trivial to implement, and it retires the "you only beat 1994 RiskMetrics" objection.
6. **DCC-GARCH + t-copula Monte Carlo (multivariate rung).** How MSCI RiskMetrics/Barra-style engines produce portfolio VaR: dynamic correlations + fat-tailed copula simulation. This is the institutional counterpart for the amortize-over-weights IQN (Q(τ|x,w)) — the right head-to-head for the multivariate direction.
7. **Basel FRTB framing (evaluation, not model).** Score everything on 97.5% ES (Fissler–Ziegel joint VaR-ES loss) and a stressed-window calibration, mirroring the regulatory regime. We already found calibration shape drives capital; this makes the capital result speak the regulator's language.

**The matched-information ablation (the paper's fairness spine):** run the IQN at each information tier — daily-only vs +RV vs +IV — against the benchmark native to that tier. Hypothesis: IQN ties at Tier 1 (proven), pulls ahead as information richens, because the pinball-trained network uses the *shape* information in IV skew/RV that variance recursions structurally discard. That's the "how does IQN beat institution-level models" story, stated as a testable claim.

---

## 2. Bloomberg pull list (prioritized — terminal access is the binding constraint)

Priority = perishable first (things only Bloomberg has, before expiry; WRDS arrives ~07-08 and covers some equity gaps).

**A. Options-implied (the biggest missing information class):**
- 30d/60d/90d ATM implied vol for SPY, QQQ, TLT, HYG, XLE + the largest single names in the 26/138 panel (`30DAY_IMPVOL_100.0%MNY_DF` etc.)
- **25Δ risk reversals and butterflies** (same tenors) — market-implied skew/kurtosis; the single best asymmetry feature and the input to the implied-quantile benchmark
- VIX term structure: UX1–UX8 futures (have some — extend history), VIX9D/VIX/VIX3M/VIX6M indices, **VVIX** (vol-of-vol), **SKEW** index
- **MOVE** (rates IV — the FI sleeve's missing vol input), OVX (oil), GVZ (gold); Deribit **DVOL** for BTC/ETH implied vol (free from Deribit if Bloomberg lacks it)

**B. Intraday bars (for Realized GARCH/HEAVY + RV features):**
- Bloomberg intraday history is only ~140–240 days — pull 5-min bars for the 7 core ETFs *now*, whatever depth is available; supplement equities via WRDS/TAQ next week; crypto hourly/minute is free from exchanges (already scripted)

**C. Credit & funding stress (crisis conditioning features):**
- CDX IG/HY on-the-run spreads + history (have CDX — extend); iTraxx Europe/Xover
- 5y single-name CDS for the largest panel names (if licensed)
- **SOFR-OIS / FRA-OIS spread**, 3m cross-currency basis (EURUSD, USDJPY), GC repo — funding stress is the classic tail predictor missing from our feature set
- HY–IG OAS differential (have components)

**D. Breadth/positioning (cheap, incremental):**
- % of S&P 500 above 200dma, advance-decline (Bloomberg has these as indices)
- Futures aggregate open interest + ETF short interest for the core sleeve
- AAII/put-call ratio (CBOE, free)

**E. Macro calendar (free, non-Bloomberg):** FOMC/CPI/NFP event dummies — event-day conditioning is a known VaR failure point and a trivially checkable IQN advantage (GARCH can't take a dummy).

**What NOT to spend terminal time on:** more daily equity closes (WRDS/stooq cover it), commodities breadth, anything with a free mirror.

---

## 3. How this feeds the three tracks

- **Model track:** IV-skew + RV features are the strongest remaining candidates to make the *standalone* IQN beat EGARCH at daily frequency (leverage feature already banked in the amortization win). Matched-information ablation is the headline experiment.
- **Theory track:** the Tier-2 suite enlarges the Gibbs ensemble's model space — a richer, more realistic test of state-dependent-η averaging, and the FRTB/ES scoring gives the "decision-aligned posterior" its regulatory loss function.
- **Breadth track:** DCC+copula is the named institutional opponent for Q(τ|x,w); implied-quantile benchmark connects to the option-pricing/MEU direction.

*Sequencing suggestion: Bloomberg pulls (A, B, C) this week before expiry → FHS-EVT + RiskMetrics-2006 + GAS on CPU (days) → Realized GARCH once intraday lands → implied-quantile benchmark + matched-information ablation as the next flagship experiment.*
