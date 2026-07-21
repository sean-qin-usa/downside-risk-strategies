# GBC/IQN Research Ideas Backlog — living doc

**Convention: every conversation pass, append new ideas + update status here so nothing is lost.** Last updated 2026-07-19 (pass 2).
Status legend: ✅ done · 🔄 running/queued · 📋 ready to build · 🧊 needs data (marked) · 💡 idea.

---

## PASS-2 RESULTS (2026-07-19) — three ai2 jobs landed
- ✅ **Anti-strawman industry battery** (`industry_bench.py`, 239 names/188k days, single-name): **nonparametric WINS the full battery.** gbm 0.6423 (best) · iqn 0.6455 (+0.5%) · garch_t 0.6519 (+1.49%) · gjr_skewt 0.6564 (+2.2%) · histsim 0.6589 · ewma 0.6606 (+2.85%) · egarch_t 1.086 & fhs 1.363 (both badly miscalibrated — impls look mis-tuned, FIX before publishing). GBM+IQN hit 5% breach on target. → The 1-3% edge holds vs GJR-skewt/EGARCH/EWMA/FHS/HistSim, not just vanilla GARCH. Sean's anti-strawman demand answered.
- ✅ **Horizon edge GROWS** (`horizon.py`): GBM/GARCH-scaling ratio h1 0.966 → h5 0.964 → h10 0.960 → h20 0.951. Beats sqrt(h)-scaling at every horizon; ~5% better at 20d. Fat-tails-compound thesis confirmed.
- ✅ **Co-crash / joint-tail v1** (`joint_tail.py`, 25-name eq-wt largecap): **HONEST NEGATIVE for direct GBM.** pinball DCC 0.1709 < CCC 0.1719 < GBM 0.1752; crisis decile DCC 0.2933 < CCC 0.2969 < GBM 0.3035. Direct nonparam portfolio-quantile does NOT beat multivariate GARCH on a diversified basket (same lesson as diversified single-name). BUT DCC>CCC everywhere → correlation-spike matters, hypothesis intact. → NEXT: (a) concentrated/crisis portfolios where co-crash bites, (b) the elegant **v2 portfolio-weight-as-input IQN Q(τ|x,w)** is the real test, not direct-GBM v1.

### PASS-2b RESULTS (2026-07-19, later same session)
- ✅ **Gibbs overconfidence test** (`gibbs_coverage.py`, 80 names, τ=0.05 VaR): **Jiang's caution confirmed as a NUMBER.** Gibbs posterior SD vs true block-bootstrap SD → R_block = **1.64 on RAW returns** (Gibbs understates VaR uncertainty by ~60%), R_iid=1.19; on **GARCH residuals R_block=0.79** (overconfidence gone, slightly conservative). raw 1.64 ≫ resid 0.79 → naive Gibbs on raw returns is ~1.6× overconfident; working on standardized residuals restores honesty. **This is the plot that turns Jiang's caution into a result.** → build ACI comparison + block-ω calibration arm next.
- ✅ **Co-crash v2** (`joint_tail_v2.py`, K=2,3,5,10,25 by pairwise corr): **concentration hypothesis REJECTED (double-negative).** Direct GBM worse than CCC/DCC at every K, gap doesn't close with concentration, GBM over-breaches. Direct-GBM portfolio-quantile is a **confirmed dead end** for equity co-crash. Co-crash chapter needs the **neural weight-input IQN** or **genuinely crash-prone assets** (EM/crypto/sector-ETFs 2008/2020, needs Bloomberg).

### PASS-2c RESULTS (2026-07-19) — Bloomberg cross-country studies recovered + hybrid
- ✅ **Cross-country single-asset (Bloomberg, real data)**: Korea-deep (23 assets/9 types), FX (24 pairs), crypto (5), universal (42 instruments) ALL COMPLETED. **GARCH-t wins standalone almost everywhere** incl. Korea 2026 crisis (ratios >1). Nonparam wins ONLY hyperinflation FX: **USDARS −12%, USDEGP −14%**, USDNGN −2%. Universal: GBM within 2% of best on 33/43, within 5% on all 43, wins outright only BTC. → Nonparam edge is NOT universal-crisis; it's amortized + extreme-misspecification. Use a **regime/misfit gate**, not "always nonparam."
- ✅ **GARCH-residual HYBRID amortized** (garch_gbm_hybrid.py, 200 names): q=mu+sigma·Qz(τ|state). **Beats GARCH at every vol quintile** (+0.3% overall, +0.62% turbulent) — nests GARCH, never worse. But does NOT beat raw amortized GBM (raw-GBM already best, 0.3953). Hybrid = the "never-underperform-GARCH" construction; in amortized regime raw-GBM achieves it more simply.
- 🔄 **Standalone per-name hybrid** (garch_hybrid_standalone.py) RUNNING on ai2: GARCH-t vs FHS_full vs FHS_recent per name — tests the "never worse than GARCH on a single asset" floor + fixes battery FHS calibration.

**Answer to "is nonparam the best for crises / a universal standard?":** No standalone — GARCH-t/qr win single-asset incl. crisis assets. Yes in amortized + extreme-misspec (ARS/EGP, turbulence quintile ~4×, longer horizons). The residual-hybrid gives a provable "≥ GARCH everywhere" floor. Regime detector: have vol-quintile + post-GARCH-residual-kurtosis misfit metric → gate GARCH↔nonparam.

### PASS-2d RESULTS (2026-07-19) — misspecification defined + detector latency
- ✅ **Standalone residual-hybrid** (garch_hybrid_standalone.py): FHS_full == GARCH-t EXACTLY (0.3971) → "never worse than GARCH" floor confirmed; but only ties on avg equities (resid excess kurt 15.9 already absorbed by t). Win needs shape DRIFT.
- ✅ **Misspecification frontier** (misspec_frontier.py) — DEFINES "high misspecification": edge ~0 in bottom 9 deciles, jumps to **+2.46% in top decile of recent residual excess-kurtosis (mk63)** and **+2.37% top decile residual asymmetry (skew63)**. It's the residual SHAPE being locally extreme (not vol level, not static fat tails). overall edge only +0.44% because it's a tail-decile phenomenon (corrs 0.05-0.10). → "scenario where nonparam wins" = live top-decile residual-shape-extremity, computable on ANY asset (generalizes Korea/ARS/EGP).
- ✅ **Detector latency** (detector_latency.py, 6871 onsets): detectors fire MEDIAN 0 / MEAN 2-5 day lag (EWMA λ=0.97 sweet spot: mean 2.4d, recall 0.73; std5 recall 0.999 but median 4d; precision ~0.45 = 2.25× base). **KEY: edge is BACK-LOADED** — grows with action lag (L0 0.000 → L5 +0.0045) because nonparam's advantage accumulates DEEPER into turbulence, not at onset. So 2-4 day detector lag is HARMLESS. But calm-day edge is −0.0021 → MUST gate (always-nonparam loses when calm).

**Answers:** "What is high misspecification?" = top-decile recent residual excess-kurtosis or asymmetry (GARCH-t's fixed-shape assumption locally broken). "Scenarios beyond Korea?" = any asset/day in that top decile; +2.4%. "How fast is the detector by lag?" = median 0, mean 2-4 days, and latency barely matters because the edge is back-loaded; the binding constraint is gating (don't run nonparam when calm), not speed.

### PASS-2e RESULTS (2026-07-19) — deployable gate + neural co-crash
- ✅ **Neural weight-input IQN co-crash v3** (neural_wiqn.py, GPU): THIRD co-crash NEGATIVE. Q(τ|state,w) ~2× WORSE than CCC/DCC at every weighting (wiqn ~0.34 vs ~0.17); never learned diversification/covariance from summary feats. Lesson across v1/v2/v3: explicit covariance (GARCH/DCC) beats nonparam over summary state for equity portfolio tails → concede in paper.
- ✅ **Learned regime gate v1 (classifier)**: adds NOTHING over always-amortized-nonparam (both 0.3987 vs garch 0.40, +0.33%). Routed BACKWARDS by misspec decile (0.995→0.565) because pinball is an average driven by rare tail days, not win-frequency.
- ✅ **Regime gate v2 (regressor on edge)**: fixed the backwards routing (flat deciles, corr +0.16) but SAME result — optimal policy gates 99.7% to nonparam = always-on. **The 4.4% oracle gap is UNREACHABLE**: per-day model advantage is dominated by the unpredictable realization (which day the tail lands), not predictable state.
- **CONVERGED RECOMMENDATION:** use amortized nonparam as the standard (no gate needed — rarely underperforms); residual-hybrid for a guaranteed ≥GARCH floor. Don't oversell per-day switching (oracle gap is a hindsight artifact).

### PASS-2f RESULTS (2026-07-19) — FRTB "industry standard and above" + rigor layer
GARCH is NOT the bank standard: Basel FRTB uses ES97.5 + Historical Simulation / GARCH-Filtered-HS (FHS), exception-backtested (Kupiec/Christoffersen). Built the residual-hybrid against that real bar with full significance testing.
- ✅ **frtb_bench.py** (140 names, 155k rows): resid_hybrid_ML vs HS, EWMA/RiskMetrics, GARCH-t, GJR-skew-t, GARCH-FHS. **Sole survivor of the 90% Model Confidence Set** (all others eliminated p=0); beats every model by Diebold-Mariano (DM 4.4-8.3, p≈0); BEST ES97.5 calibration (pred −5.80 vs realized −5.76). Nuance: 99% exceptions slightly hot (1.19%) → fails Kupiec.
- ✅ **frtb_hybrid_evt.py** — the finisher: ML body + **Peaks-Over-Threshold GPD left tail** (τ≤0.025). breach99 1.04%, **Kupiec p=0.10 PASS + Christoffersen p=0.20 PASS** (only model that passes both), still beats GARCH-t (DM 3.9) & FHS (DM 4.28) on pinball. Costs 0.0003 pinball vs raw hybrid.
- **FLAGSHIP:** hybrid_EVT statistically dominates the full FRTB industry battery on ES/pinball AND is the only model to pass the FRTB 99% exception backtests → genuine "industry-standard-and-above." Rigor layer (Kupiec/Christoffersen/DM/MCS) now implemented and reusable.
- Also confirms: FHS/GARCH-FHS calibration bug from the earlier industry battery was the impl — clean FHS here is well-behaved (pinball 0.3562, just loses to the hybrid).

### PASS-2g — GAP AUDIT ("did we miss anything?", 2026-07-20) — YES, three things
- ⚠️ **CAViaR ties the hybrid** (frtb_caviar.py): Engle-Manganelli SAV-CAViaR pinball 0.3461 ≈ hybrid_GBM 0.3460 (DM 0.59, p=0.28); 90% MCS = {caviar, hybrid_GBM}. Earlier "sole survivor" was because CAViaR was absent. Hybrid still beats GARCH-t/FHS/EVT w/ significance but is CO-BEST with CAViaR. Report honestly.
- ⚠️ **Neural IQN (the literal GBC method) LOSES to trees** (frtb_neural.py): hybrid_IQN 0.3650 vs hybrid_GBM 0.3551 (DM 13.29); raw neural tail under-covers badly (breach99 3.2%, ES pred −3.75 vs −5.52). EVT tail fixes calibration but still trails trees (0.3587). → Frame GBC as FRAMEWORK, trees as estimator; OR fix net (tail-aware τ sampling, monotone output, full amortization).
- ⚠️ **97.5% level miscalibrated for ALL models**: over-breach ~2.8% vs 2.5%, all fail Kupiec/Christoffersen@97.5%. EVT tail helped 99% only. → extend recal to 97.5% (the FRTB ES quantile).

### PASS-2h — ALL FOUR GAPS CLOSED (2026-07-20)
- ✅ **Tail-aware monotone neural IQN v2** (frtb_neural_v2.py): fixed the tail (breach99 0.92% vs v1 3.2%), narrowed pinball gap to trees from ~1% to ~0.5%; after conformal recal IQN_v2_recal 0.3638 ≈ GBM_recal 0.3632 (DM 3.03). Neural GBC now competitive & calibrated; trees still marginally best (expected on tabular). Report both.
- ✅ **97.5% calibration fixed** (split-conformal recal): recalibrated hybrids PASS Kupiec@97.5% (GBM_recal 0.24, IQN_v2_recal 0.15) vs 0.0 for all un-recalibrated; IQN_v2_recal also passes Christoffersen@97.5%. Deploy = conformal-recalibrated hybrid (EVT tail @99% + conformal @97.5%).
- ✅ **Misspec-frontier significance** (misspec_significance.py, per-date DM): top mk63 decile +2.71% DM 6.54 p≈0 (SIGNIFICANT); bottom decile +0.19% DM 1.41 p=0.08 (NOT sig). Confirms the frontier win is real.
- ✅ **Gibbs ACI arm** (gibbs_aci.py): at 5% ACI realized 5.03% (best) + most stable rolling coverage (max-dev 0.042 vs garch 0.059, naive 0.074); at 1% ACI≈garch, both beat naive. Confirms honest-uncertainty-under-drift = ACI, not fixed Gibbs.

**Remaining (lower priority):** DM/MCS on hyperinflation-FX (needs host+Bloomberg rerun — FX per-day losses not cached); 10-day ES + stressed-window (2008/2020) FRTB faithfulness; simulation-based calibration of intractable models (Heston/rough-vol) = the full-GBC likelihood-free application.

### PASS-2j — BLOOMBERG BACK ON: executing the plan (2026-07-20)
Host runner live; Bloomberg signed in. Pulling per BLOOMBERG_DATA_PLAN.md.
- ✅ **P1 Crisis-FX significance** (fx_sig.py, host): **crisis-FX win is now DM-SIGNIFICANT.** USDARS ratio 0.880 DM 2.86 p=0.002 ✓, USDEGP 0.857 DM 3.80 p=0.0001 ✓, fx_crisis tier **pooled DM 4.12 p≈0** ✓. Majors pooled DM −13.71, EM −9.46 (GARCH sig better, expected). resid_kurt FIXED: crisis mean 1915 (ARS 3298/EGP 1920/NGN 3357/UAH 4103) vs majors 39 vs EM 8 — the wins are the extreme-misspec cases (confirms frontier mechanism on FX). over_time now computes (TRY peak 414). File fx_sig.json.
- ✅ **P1 Korea-deep + significance** (korea_sig.py, 23 assets): GARCH SIGNIFICANTLY beats nonparam on EVERY Korean asset, full + 2026 crisis (DM −2.5 to −5.0). WHY: Korean resid_kurt only 4-13 (fixed) — far below nonparam threshold. A dramatic price crash ≠ high residual-misspec. Corrects "nonparam wins Korea crisis" (it doesn't).
- ✅ **P2 Cross-country stability GRADIENT** (cross_country.py, 26 indices): CLEAN gradient mediated by residual kurtosis. developed (kurt 4.7, 0 sig wins) → emerging (5.3, 0) → **frontier (10.0, 4 SIGNIFICANT nonparam wins: Sri Lanka DM 3.5, Kenya 3.5, Pakistan 2.4, Nigeria 2.1)**. **corr(log resid_kurt, edge)=0.53.** Answers "does edge scale first→third world?" YES, via residual misspecification. Frontier indices = genuine nonparam regime; developed/emerging = GARCH's.
- ✅ **P2 Universal cross-asset + significance** (universal_sig.py, 43 instruments, lean): nonparam residual-hybrid SIGNIFICANTLY beats GARCH-t on **13/43**, concentrated in vol indices (VIX/VVIX/V2X 3/3), freight (Baltic Dry −15%, DM 9.4), electricity (ERCOT; PJM 0.03 = ARTIFACT to refit), credit (IG −4%), MOVE, SPX/NDX. GARCH wins fx-major/crypto/rates/metals/most-ags. corr(log resid_kurt, edge)=0.43. Cross-asset misspec-frontier table for the paper. (vol indices were already IN this set → P3 vol-index item DONE here.)
- ⚠️ **P3 crypto HOURLY BLOCKED** (crypto_hourly.py): Bloomberg `bdib` returns only 24 bars/coin for XBTUSD/XETUSD/etc — intraday history not stored for these composite crypto Curncy tickers. Intraday/HF needs a different source (exchange API / tick data vendor) or proper intraday-permissioned tickers. Same limit will hit intraday-equity (tasks 15-17) via bdib. → mark intraday as data-blocked.
- ✅ **MASTER SYNTHESIS** (pass-2k): all asset classes placed on the single edge-vs-residual-kurtosis frontier (CRSP + FX + 26 countries + 43 cross-asset). See MASTER_FRONTIER memo/figure.
- 📋 NEXT (host, when wanted): refit PJM/power on price-diffs; add EVT tail + Kupiec/Christoffersen to the universal winners (vol/freight/credit) for the full FRTB-grade cross-asset table; WRDS 2000-24 CRSP for a 2008 stressed window.

### PASS-2i — all non-Bloomberg work + Bloomberg plan (2026-07-20)
- ✅ **Heston SBC (FULL GBC flagship, non-Bloomberg/simulation)**: likelihood-free amortized posterior over Heston params from 40k simulated paths. SBC coverage ≈ nominal (cov80 0.79, cov90 0.87); info-gain ξ 36%, θ 13% (strong), κ/ρ weak. GARCH/MLE CAN'T do this. IQN≈GBM (both work; IQN is the generative one). Neural-GBC showcase + capability story.
- ✅ **FRTB 10-day + stress (non-Bloomberg CRSP)**: nonparam edge HOLDS/GROWS at 10-day horizon (h1 ~0.4% → h10 ~1.4%) and in the 2020/2022 stress window; GARCH sqrt-scaling over-states 10-day ES (−19.4 vs real −15.4, over-charges capital), hybrid well-calibrated + best breach975. (Calm bucket empty — temporal split artifact; needs expanding split / longer WRDS panel.)
- ✅ **BLOOMBERG_DATA_PLAN.md** (GBC Project + Drive): maps every blocked path (FX-crisis significance P1, Korea-deep P1, universal FRTB flagship P2, cross-country gradient P2, crypto/intraday/vol P3) w/ exact tickers/fields/history + non-Bloomberg WRDS/FRED fallbacks. One-session pull order.
- Non-Bloomberg backlog now essentially exhausted; further big steps need Bloomberg (see plan) or a longer WRDS CRSP pull (2000-2024, adds 2008) — WRDS is non-Bloomberg.

**Pass-2b next actions:**

**Pass-2b next actions:** (1) Gibbs test v2 — add ACI coverage arm + explicit block-ω-calibrated Gibbs (predict both nominal); (2) portfolio-weight-as-input **neural** IQN Q(τ|x,w) — the real co-crash test now that direct-GBM is ruled out; (3) fix EGARCH/FHS calibration + industry_bench_v2 (+CAViaR/EVT/POT +Kupiec/Christoffersen +DM/MCS); (4) crisis-asset co-crash needs Bloomberg/EM data.

---

## A. The four "big, non-marginal" win directions (2026-07-19)
Single-name daily pinball stays marginal (~1-2%); GARCH is genuinely good there. The real wins:

1. **Multivariate / joint-tail / co-crash — biggest untapped win.** Incumbents (GARCH, copula-GARCH, CCC) model joint extreme moves poorly — they can't capture correlations spiking to ~1 in a crash (2008, COVID, Korea 2026 circuit-breakers). A generative/conditional quantile net could beat them *materially* on portfolio VaR/ES.
   - ✅ `joint_tail.py` — v1 DONE (ai2, 2026-07-19): direct GBM portfolio-quantile vs CCC/DCC-GARCH on 25-name eq-wt largecap. **HONEST NEGATIVE**: GARCH wins the diversified basket (DCC 0.1709 < CCC 0.1719 < GBM 0.1752, same in crisis decile). DCC>CCC confirms corr-spike matters. Lesson: largecap diversifies away co-crash → need concentrated/crisis baskets + the v2 weight-input IQN.
   - 📋 v2 (the ELEGANT version, from RESEARCH_DIRECTIONS_V2 §2.2, "the direction I'd lead with"): **portfolio-weight-as-input IQN** — learn Q(τ | xₜ, **w**) with weight vector w sampled each batch; one network prices the downside of *every* portfolio on the simplex; tail co-movement shows up as concentrated-w quantiles not diversifying away. Sidesteps optimal transport, reuses amortization machinery.
   - 💡 Vector quantile regression / ICNN (Carlier–Chernozhukov–Galichon; Pegoraro et al. 2024) — the principled "IQN where τ is a vector"; thesis-scale. Gibbs-world analog: geometric quantiles (Bhattacharya & Martin 2022) → theory hook to Jiang.

2. **Regulatory ES / capital — small pinball, big dollars.** A 2% better 97.5% ES in a crisis = basis points of Basel capital across a book. Frame wins in ES/capital terms (Polson MEU machinery computes expected utility as a quantile marginal → certainty-equivalent bps).
   - 🔄 industry battery reports 97.5% ES + VaR breach; 📋 add Fissler–Ziegel joint (VaR,ES) score, Basel capital translation.

3. **Extreme-misspecification domains — already big (10%+), not marginal.** Crisis FX (ARS +14%, TRY +2.4%), electricity/PJM (+8%), and (predicted) Korea KOSDAQ/EcoPro 2026. Regime result: edge ~4× larger in turbulent quintile (✅ edge_regime). Headline: "we beat GARCH *a lot exactly when it matters* — crises, circuit-breakers, panics," not "1% on average."
   - 🧊 Korea deep + cross-country FX/index crisis-window studies — NEED BLOOMBERG (or WRDS-Global substitute).

4. **Capabilities GARCH can't do at all** — strongest kind of non-marginal.
   - ✅ Cold-start (~5%, GARCH N/A <250 days); ✅ one-model-for-thousands (amortized, no per-name refit).
   - 📋 **Simulation-based calibration of intractable models** (Heston, rough-vol, Hawkes order-flow) — GBC's ORIGINAL pitch (likelihood-free). Train IQN on simulated (θ, path-summary) pairs → invert to posterior over params. GARCH can't do this. Genuinely novel finance application.

## B. Slipped-through high-value ideas (mined from RESEARCH_DIRECTIONS_V2, 2026-07-19)
- 💡 **Block-PCA dimension reduction already won ~30% CRPS** — a NON-MARGINAL win that got buried. Next: **supervised vs unsupervised** dim reduction (learn the projection end-to-end as the net's first layer w/ orthogonality penalty vs fixed PCA) — the "sufficient summary statistics" question in Polson's GBC papers.
- 📋 **Gibbs posterior on conditional (VaR, ES)** (extends Syring–Hong–Martin 2019 from unconditional VaR → conditional, and VaR → (VaR,ES) jointly) — puts honest UNCERTAINTY BANDS on risk forecasts, which NO current model (IQN included) provides. Doc calls this "the single best further-the-hypothesis project"; fuses Jiang's Gibbs framework with our application.
- 💡 **Loss-function-in-the-exponent ablation** for the Gibbs posterior: trailing CRPS vs tail-weighted CRPS vs Fissler–Ziegel (VaR,ES) joint score vs utility-based (MEU). Cheap, nobody's done it in this setting.
- 💡 Self-aware model / confidence (ensemble disagreement predicts own error, corr +0.11) — convert to a Sharpe/sizing number (validated as signal, not yet a number).
- 💡 MEU / capital allocation as a quantile marginal (Polson–Ruggeri–Sokolov 2024) — converts CRPS edge → certainty-equivalent bps.
- 💡 High-frequency crypto (hourly) — where IQN already won ~0.6%; extend.

## C. Rigor / anti-strawman upgrades (2026-07-19)
- ✅ **Industry-standard battery** (`industry_bench.py`, ai2, DONE 2026-07-19): amortized GBM+IQN BEAT GARCH-t, GJR-skew-t, EGARCH-t, EWMA, FHS, HistSim on 239 names. gbm 0.6423 best, iqn +0.5%, garch_t +1.49%, gjr_skewt +2.2%. (EGARCH/FHS miscalibrated — FIX impls.)
- 📋 Add **CAViaR** (Engle–Manganelli — the direct conditional-VaR quantile benchmark) + **EVT/POT** (extreme tails).
- 📋 Add **Kupiec (unconditional coverage) + Christoffersen (independence) VaR backtests**, and **Diebold–Mariano + Model Confidence Set (MCS)** significance on all pinball comparisons. Without these the comparisons aren't publishable.

## D. Study status (2026-07-19)
✅ full-scale amortization (age-curve + ablation, 720 names); ✅ Gibbs/amortized-as-prior (negative — conditioning already captures it); ✅ neural IQN vs GBM (GBM ~0.75% better on tabular); ✅ feature ablation (own recent vol carries the edge); ✅ edge-concentration by vol regime (~4× in turbulence); ✅ three-way GARCH/GBM/IQN by regime (both beat GARCH everywhere); ✅ M5-uncertainty (leakage-safe SPL 0.269, benchmark tier).
✅ industry battery (nonparam wins full battery); ✅ horizon (edge grows to ~5% at h=20); ✅ joint_tail v1 (negative on diversified basket, DCC>CCC). 🔄 universal cross-asset benchmark (host, partial — Bloomberg cut).
🧊 NEEDS BLOOMBERG (deferred/marked): Korea-deep multi-data-type + 2026 crisis window; FX-over-time stability gradient; cross-market stability gradient; crypto tier.

## E. Data status / needs
- ✅ HAVE: CRSP panel (on ai2 + local, 1.3M rows / 720 names); M5 competition (local + ai2).
- 🔄 WRDS (works w/o Bloomberg): pull a LONGER/bigger CRSP US panel (2000-2024, incl. 2008 + 2020 crises, more names) for richer amortization/crisis/battery; **Compustat Global** for INTERNATIONAL equities/indices → cross-country stability gradient WITHOUT Bloomberg (substitute).
- 🧊 NEEDS BLOOMBERG: single-name Korea/EM tickers, FX pairs, crypto, vol indices (VKOSPI), intraday. → substitute via WRDS-Global / open source where possible.
- 📋 OPEN SOURCE to fetch: Fama–French factors (Ken French), FRED (rates/macro), GEFCom2014 electricity (3rd competition, not yet downloaded), realized-vol library.

## F. Cross-cutting programs
- 📋 **All-country in-depth program** (Korea-deep template → stratified developed→frontier, many data types + crisis-window slices) — via WRDS-Global now, Bloomberg later.
- 📋 **True 4-model amortization proof**: GARCH | GBM | IQN | GBC(sim-based) side-by-side, industry battery + significance tests, across assets/horizons/regimes.
