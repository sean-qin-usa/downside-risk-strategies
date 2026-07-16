# Quantile-by-Quantile P-vs-Q — Spec

*Sean Qin · GBC Downside-Risk Project · 2026-07-04 · companion to PQ_TRADE_BACKTEST.md §6*

## 1. The object

Today's trade compares two single numbers: K_Q = VIX² vs F_P = E[RV]. The extension compares two full *distributions* at every probability level. Define, for next-month market return r:

- **Q_P(τ | x_t)** — the IQN's conditional τ-quantile of r (physical measure, our machinery, per-day).
- **Q_Q(τ | t)** — the option market's τ-quantile of r under the risk-neutral measure, extracted from the IV surface.

The tradeable object is the **wedge curve** Δ_t(τ) = Q_P(τ|x_t) − Q_Q(τ|t), a *function* of τ, not a scalar. Today's VRP study collapses Δ to one number (its variance-weighted integral). The information the collapse throws away is *where on the distribution* the market overpays.

## 2. Getting Q_Q(τ) from the surface

Breeden–Litzenberger: the risk-neutral CDF is F_Q(k) = 1 + e^{rT} ∂C/∂K at strike k, so quantiles come from inverting the call-price curve. With only three moneyness points per tenor in hand (90/100/110 from iv_SPY.csv), fit a parsimonious skewed density rather than a nonparametric one:

1. Fit an SVI or quadratic-in-log-moneyness IV smile through the 3 points (extend the pull to 80–120% and 25Δ/10Δ if BBG access returns — the far left wing is where the payoff is).
2. Convert to call prices, differentiate → F_Q, invert on a τ-grid (τ ∈ {0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99}).
3. Sanity: the τ-integral of the implied variance must reproduce something between ATM IV² and VIX² (convexity check); the 30d fit should nest the Leg-C finding (ATM fair, wings rich).

## 3. Interpreting and trading the wedge

Three orthogonal wedge statistics, each with a natural instrument:

| statistic | meaning | instrument (SPX/XSP) |
|---|---|---|
| level: ∫Δ(τ)dτ ≈ width gap | today's VRP signal | short/long variance, straddle, VIX future |
| skew: Δ(0.1) − Δ(0.9) | market over/under-prices crash asymmetry vs IQN's predicted skew | risk reversal (sell put wing / buy call wing or reverse), put spreads |
| tail: Δ(0.01…0.05) | far-wing premium vs IQN+EVT tail | deep-OTM put spreads, VIX calls |

The Leg-C result (short at ATM-IV strike loses, short at VIX² strike wins) is a *one-day-resolution proof* that the premium is concentrated in the wings — i.e. almost all of ∫Δ comes from small τ. A GARCH cannot exploit this: its quantiles are scale × fixed t-quantiles, so its Δ(τ) is a one-parameter family — level and skew are mechanically linked. The IQN's Δ(τ) has independent degrees of freedom at each τ. **That is the structural edge claim, and it's testable:** if the IQN's extra degrees of freedom are real, per-τ signals should predict per-τ premia better than the GARCH-implied wedge does.

## 4. Evaluation before any trading

Per-τ premium is directly measurable without pricing a single option: realized coverage. For each τ, the historical frequency of {r < Q_Q(τ)} minus τ estimates the premium the market pays at that quantile (Carr–Wu logic quantile-by-quantile). Then run the same predictive-regression protocol as the VRP study, per τ: does standardized Δ_t(τ) predict the subsequent τ-level payoff (e.g. the return of the τ-strike put spread)? Score with the Fissler–Ziegel joint VaR-ES loss at each τ to stay elicitability-honest. Gate position size with the ensemble-disagreement confidence signal (validated in the capstone: disagreement predicts IQN error — de-risk the whole wedge book when the model doesn't know).

## 5. Build order (reuses existing pipeline)

1. Surface → Q_Q(τ) extractor on iv_SPY.csv history (2012–2026, ~3,600 days). CPU, a day.
2. IQN retrained with the leverage feature on market returns (already planned in the model track) → Q_P(τ|x) on the same dates.
3. Wedge dataset Δ_t(τ) + per-τ coverage/premium table 2012–2026. This alone is a finding (which τ carries the premium) regardless of trading.
4. Per-τ predictive regressions + the three wedge-statistic strategies vs their scalar-VRP baselines (the GJR-t s2 from PQ_TRADE_BACKTEST.md is the null to beat).
5. Only then: instrument-level backtest with real option prices (needs bid/ask surface history — WRDS OptionMetrics when access arrives, which also fixes the 3-point-smile limitation).

Risks: 3-point smiles under-identify the wing (mitigate: parametric fit + WRDS later); overlapping 30d horizons at daily frequency need HAC everywhere; multiple testing multiplies fast across τ — pre-register the τ-grid and statistics above before running step 4.

## 6. Deferred — gated on data access

**Needs WRDS (~07-08; OptionMetrics is the priority):** real 10Δ/25Δ wing quotes to replace the extrapolated left wing of the 3-point smile fit; actual option bid/ask history → tradable put-spread/risk-reversal backtests (step 5); TAQ intraday → HAR-RV/Realized-GARCH-grade P-side; CRSP for the cross-sectional version.

**Needs Bloomberg login (run_bbg_check.bat pending):** re-pull 25Δ/10Δ risk reversals + butterflies and 60/90d tenors (fields returned empty on 07-02 pull); extended iv_* single-name surfaces; live VIX/UX quotes for pq_live_signal.py; MOVE-conditioned FI variant; DVOL for the crypto version.

**Runs today on free/archived data (no dependency):** everything in PQ_TRADE_BACKTEST.md, the Q_Q(τ) extractor (step 1, done), the IQN Q_P(τ|x) walk-forward (step 2), wedge dataset + per-τ coverage tests (steps 3–4 at monthly resolution).

## 7. First-pass results (2026-07-04, steps 1–4 executed)

Code `pq_07_qq_extract.py` (Q_Q), `pq_08_iqn_pq.py` (walk-forward NumPy-IQN, 54 quarterly refits 2013–2026, warm-started, leverage + term-structure features), `pq_09_wedge.py` (tests). Results `results/pq_trade/{qq_coverage,wedge_tests}.json`, `wedge_dataset.parquet`.

**Step 1 (solid).** Q_Q(τ) extraction validated: convexity ordering ATM IV² < fitted totvar < VIX² on 98% of days. Per-τ premium (n=174 non-overlap months): realized breaches Q_Q(0.05) only 1.7% (prem +3.3%, ~2se), Q_Q(0.25) 17.9% (+7.1%, ~2.2se), median 35.8% (+14.2%, ~3.7se — mixes equity drift), while 0.90/0.95/0.99 are priced fairly. **The entire wedge is on the downside half.**

**Steps 2–4 (infrastructure done; P-side not yet paper-grade).** The quick CPU IQN retrofit to the 21d horizon is materially miscalibrated — physical coverage 0.107 at τ=.01, 0.685 at τ=.95 (too narrow) — worse at the tails than a GJR-t(ν=6) baseline. Consequently no per-τ wedge-timing signal survives multiple testing (best cells t≈2.0 at τ≥.90 across 18 tests; expected under the null). Unconditional digital-put-sell premia are significant at τ=.50/.75/.90 (t 2.9–4.2) but drift-contaminated at central τ.

**Conclusion:** the pipeline (surface→Q_Q, walk-forward Q_P, wedge, per-τ harness) is built end-to-end; the binding constraint is P-side quantile calibration at the 21-day horizon. Before any wedge-trading claim: retrain with the tail mixture G_λ, K≥5 ensemble, block-sampled batches for overlapping targets, EVT tail splice (RESEARCH_DIRECTIONS_V2 §1.3–1.4), on GPU — then rerun pq_09 unchanged.

## 8. Update after Bloomberg reactivation (2026-07-04 evening)

Re-pull landed (see data/raw/PQ_PULL_SUMMARY.txt): 5-point smiles (90/95/100/105/110% mny, 3 tenors) for SPX **2005+** and 8 ETFs 2012+; UX1–UX8 futures from **2004** (+volume/OI); vol-index family from 2004. 25Δ/10Δ and BVOL routes are entitlement-blocked and 80/120% fields don't exist — true wings remain WRDS-gated.

`pq_07b_qq_spx.py`: Q_Q re-extracted from the SPX 5-point smile (least-squares quadratic, median fit residual 0.9 vol-pts), 5,408 days, 257 non-overlapping months **including the GFC**. Premium by τ (τ − coverage): 0.05 → **+4.2%** (se 1.4, t≈3.1); 0.10 → +3.4%; 0.25 → +4.8%; 0.50 → +11.1%; 0.75 → +10.4%; 0.90/0.95/0.99 → ≈0. The downside-concentration result strengthens with the longer, crisis-inclusive sample.

GPU package staged in Drive `gpu_pq/` (gpu_iqn21.py, make_features_gpu.py, RUN_PQ_GPU.sh) and locally in `code/pq_trade/gpu/` with pq21_features.csv — run on ai2, output `pq_iqn_quantiles_gpu.csv` drops back into pq_09 unchanged. Next data tasks: rebuild Leg B on 2004+ futures (adds 2008–2009 to the tradeable-instrument test); 60d/3M tenor term-structure of the wedge.

## 10. Powered tests: pooled 8-ETF panel + GFC-inclusive futures leg (2026-07-04, late)

**Pooled panel (`pq_14_panel.py`, 1,288 asset-months, 8 ETFs × 2012–2026, month-clustered NW inference).** Per-τ digital premium, pooled: τ=0.01 +0.7% (t=2.9), **τ=0.05 +3.5% (t=8.0)**, τ=0.10 +3.6% (t=3.5), τ=0.25 +5.0% (t=2.9), τ=0.50 +7.5% (t=3.5), τ=0.75 +3.9% (t=2.3), τ≥0.90 ≈ 0 with τ=0.99 slightly *negative* (−0.5%, t=−2.5 — market may underprice the far right wing, or a 5-point-smile fit artifact; check on WRDS). Cross-asset pooling makes the downside-half concentration decisive. **First significant timing cell:** wedge-timed digital at **τ=0.25: +4.1%/month, t=3.21** (survives a 9-cell Bonferroni at 5%), using only a parametric GJR-t(6) P-side — the lower-quartile strike is where the wedge is both measurable and priced. Economically this is the put-spread sweet spot.

**Futures leg on full 2004–2026 UX history (`pq_13_legB2004.py`, 5,553 days incl. GFC).** The timed strategies now clear significance where the 2010-start version was flat: RM2006-s2 SR 0.50 (NW-t 2.77), EWMA-s2 0.44 (t 2.48), vs always-short SR 0.36 (t 1.94); the 2004–09 subperiod (SR 1.1–1.3 for timed vs 0.67 unconditional) is where the signal earns its keep — crisis avoidance again.

## 9. GPU retrain + regime-transfer results (2026-07-04 night)

**GPU IQN (K=5, two-sided tail mixture, stride-21 sampling; trained on ai2's 2070 in ~2 min).** Left-tail calibration dramatically improved vs the CPU quick version (coverage at τ=.01: .107→.037; τ=.05: .208→.094; τ=.25: .396→.220); upper half still too narrow (.95→.795). Wedge-timing rerun (`wedge_tests_gpu.json`): still no per-τ signal survives (best cell t=1.34, confidence-gated), including for the GJR baseline. With n=149 non-overlapping months, detecting corr≈.05 signals is hopeless — **the binding constraint has shifted from calibration to statistical power.** Power routes: the 8-ETF surface panel (cross-sectional pooling ×8), daily overlapping observations with HAC/block bootstrap, or WRDS option returns (real per-τ P&L, 1996+).

**Regime-transfer matrix (`pq_12_regime_matrix.py`, HAR-21d, expanding point-in-time VIX terciles, 377 months).** QLIKE, rows=train regime, cols=test regime:

| train\test | calm | mid | stress |
|---|---|---|---|
| all | −3.294 | −2.766 | −1.853 |
| calm | −3.344 | −2.546 | **−0.650** |
| mid | −3.350 | −2.752 | −1.629 |
| stress | −3.190 | −2.725 | −1.841 |

Findings: (T1) matched-regime training beats all-data only marginally (paired t: calm −1.61, stress −1.67 — suggestive, not significant). (T2) **transfer is violently asymmetric**: stress-trained models degrade mildly in calm markets (ΔQLIKE ≈ 0.15, log-bias +0.57 = conservative), while calm-trained models fail catastrophically in stress (ΔQLIKE ≈ 1.19 vs stress-trained; log-bias −0.92 → they forecast ~40% of realized variance, understating crisis risk by ~60%). The sharp thesis: **stress observations are irreplaceable, calm observations are nearly redundant** — any training set containing crises performs within noise of optimal in crises; any set without them is lethal, and in the dangerous direction (they are exactly the models that scream "sell vol" before a blow-up). Connects to the paper's transfer/amortization narrative (breadth of training distribution > recency/quantity — cf. splits study: regime-matched HAR SR 0.97 vs 0.74 contiguous-10y) and to state-dependent-η Gibbs weighting (regime-aware model averaging).
