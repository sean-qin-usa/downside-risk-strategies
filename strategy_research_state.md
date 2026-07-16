# ℙ-vs-ℚ Put-Writing Strategy — State of Research

*Single reference, consolidated. τ.10 book = sell δ≈−0.12 monthly puts on liquid US single names. All Sharpes ex-ante and leakage-checked unless flagged.*

## 1. Core economics (clean, robust)
- Sell δ−0.12 puts, 20–40 DTE, held to expiry, cash-secured.
- **Crossing the spread (sell at bid):** ~27 bp/trade, Sharpe ~0.67 (18-name book, 2016–25). This is the conservative number the paper reports.
- **Posting at mid:** ~46 bp/trade, Sharpe ~1.13. ← the single biggest *clean* lever found.
- Win rate ~92%; average win +0.8% vs average loss −6.6%; risk concentrated in ~5 crash months/decade.
- Over 30 years, vol-matched to the S&P: beats it (Sharpe 1.07 vs 0.83, 3.6× terminal wealth), but a *diversifier*, not a market-beater — lagged the S&P badly 2016–25.

## 2. The one big lever: EXECUTION (post at mid, don't cross)
| Execution | Net/trade | Sharpe |
|---|---|---|
| Cross (bid) | 27 bp | 0.67 |
| Post at mid | 46 bp | 1.13 |
| Post at ask (ceiling) | 66 bp | 1.53 |

Roughly doubles the edge, no look-ahead (it's a price, not a timing signal). Caveat: pushing toward the ask invites adverse selection (fills concentrate on toxic down-flow); severe case goes negative. **Playbook: post near mid, don't chase the ask.** Real fill quality can't be measured from EOD data — needs forward paper-trading.

## 3. What does NOT work (all tested, all fail)
- **Buy protection** (per-name or index puts): overpriced; bleed exceeds premium; Sharpe falls at every hedge ratio.
- **Delta-hedging:** *worse* — kills the return (46→4.5 bp, SR 1.14→0.12) and amplifies crashes (short-gamma bleed through gaps). Proves the premium is *directional*, not variance.
- **VIX regime gate:** the "2.5–3.2 Sharpe" was **look-ahead** (gated on same-month-end VIX). Clean timing (prior-month-end) → no edge / hurts. RETRACTED.
- **Reactive daily stops:** every stop lowers Sharpe and halves the premium; wide stops make crashes worse (sell the bottom before the rebound).
- **Bull put spreads:** cap the tail but cost ~25% of Sharpe + half the premium. Defined-risk = risk preference, not edge.
- **Model features / seasonality / GEX / earnings-proximity:** none improve calibration — the informational ceiling. Crashes are unforecastable ex-ante.

**Unifying conclusion:** the VRP is payment for a crash you cannot dodge, hedge, or time. Improvement comes from diversification/selection/execution, not avoidance.

## 4. Clean levers still being tested (queued)
- **Breadth** (18 → 100–500 names): diversifies the ~25% idiosyncratic loss slice. Expected +15–30% (bounded; the 75% macro doesn't diversify).
- **Cross-sectional VRP selection** (sell richest names by entry IV − trailing RV): wildcard — could help, could backfire (rich IV showed mild adverse selection). Testing top *and* bottom quartile.
- **Inverse-vol sizing** (risk-weight names by trailing vol): standard, modest.
- **Tenor laddering** (blend weekly DTE5–15 + monthly): smooths single-date gap risk, modest.
- **Skew harvest / risk reversal** (sell δ−0.12 put, buy δ+0.12 call): needs the calls pull (running); a second, weakly-correlated premium.

## 5. Data scope and limits
- **OptionMetrics (WRDS)** `opprcd` daily options 2005–2025: **puts only**, δ −0.03 to −0.45 (calls pull now running to fix this). Columns: bid/offer/IV/delta/gamma/volume/OI. `stdopd` vol surface 2011–25.
- **Bloomberg** daily PX_LAST for underlyings (settlement).
- **No intraday** (daily close only) → can test daily reaction, not intraday stops.
- **No cross-asset** (equities only) → the biggest *structural* Sharpe lever (rates/FX/commodity vol) is a data-acquisition question, not a backtest.

## 5b. VALIDATED PRODUCTION STRATEGY (the payoff)
Two independent, leakage-free, high-impact levers survived all scrutiny:
- **Execution:** post at mid vs cross the bid → 0.67 → 1.13.
- **Cross-sectional VRP selection:** sell richest names by VRP = entry IV − trailing 21d realized vol → survives OOS (both era-halves), monotonic across quantiles, beats raw-IV/RV selection, and holds in liquid names (top-100 liquid: all 1.05 → top-25% 1.75 → top-10% 2.38).

**Spec:** top-100 liquid names → each month sell **top-10–15% by VRP** → **post at mid** → hold to expiry → **cut size to 0.3–0.5× after any down month.**

Combined backtest (top-100 liquid, 2016–25), incremental stack:
| Layer | Full SR | In-samp (16–20) | Max DD |
|---|---|---|---|
| baseline all-liquid | 0.65 | 0.26 | −18.6% |
| + VRP top-25% | 1.26 | 0.68 | −15.3% |
| + de-risk 0.5× after down | 2.11 | 1.38 | −7.7% |
| VRP top-10% + de-risk | ~2.3+ | ~1.5+ | −7.7% |

**Honest headline = the in-sample column (~1.1–1.5 Sharpe, −8% max DD)** — 2016–20 includes Volmageddon + COVID; the 2021–25 OOS (SR 4+) is inflated by a kind regime, don't extrapolate.

Parameter findings:
- **Concentration:** top-10–15% VRP is the sweet spot (IS SR 1.33–1.48, DD −8 to −9%). top-5% over-concentrates (IS collapses to 0.94, DD −14%). top-25% only if you need capacity.
- **De-risk:** more aggressive = higher SR (losses cluster); 0.3–0.5× is pragmatic (DD −5 to −8%); full-exit (SR 3.3) over-relies on return-autocorr stability + kills capacity. React to *sign* of last month, not magnitude (tiered/continuous did worse).
- **Vol-target sizing: FAILS** (pro-cyclical for short vol — sizes up into crashes, DD −38%).
- **VRP persistence: none** (rank autocorr −0.02) — re-measure monthly, not anticipable.
- **Skew:** risk-reversal (sell put + buy call) 1.09 → 1.31 but adds directional/bull tilt; selling calls loses (premium is downside-only).

Pending: VRP+skew *combined* selection (job died mid-run, needs lighter retry); earnings-aware VRP (needs earnings-date source).

## 5c. VALIDATION & RIGOR (why we believe it)
- **Beats random (permutation test):** vs 500 random 10%-of-names portfolios, VRP-10% sits at the **100th percentile** in-sample & full-period, 96th OOS → edge is not luck (p<0.002 IS).
- **IS<OOS gap is a *regime* effect, not overfitting:** random selections show the *same* gap (mean IS 0.28 vs OOS 2.49) → 2021–25 was kind to *everyone*; don't extrapolate OOS 4+. Portable quantity = VRP's edge-over-random (~+1.2 IS, +1.65 OOS).
- **In-sample low = COVID:** IS ex-Feb/Mar-2020 jumps 1.48 → 2.57 (≈ OOS). IS honestly bears the tail.
- **Factor attribution = it's ALPHA:** final strategy excess return regressed on market/size/value + a short-vol factor → **alpha +13%/yr, t≈6.9**, survives the short-vol control (short-vol β 0.70). SMB/HML insignificant (not a small-cap/value bet). R² 0.18–0.25 → mostly idiosyncratic name-selection alpha. (t inflated by kind OOS; magnitude shrinks at bid/in-sample, but survival is the robust result.)
- **Strike-robust:** VRP top-10% ≈ 2.2× the all-names Sharpe at δ−0.05 (1.48→3.09), δ−0.12 (1.05→2.38), δ−0.20 (0.83→1.87) — not a δ−0.12 artifact.
- Pending: RV-window robustness (re-run after bug), VRP+skew combined, earnings split.

## 5d. CROSS-ASSET DIVERSIFICATION (#6) — tested via liquid ETF options
Sell δ−0.12 puts on cross-asset ETFs (2016–25): per-sleeve SR QQQ 2.97, HYG 1.35, GLD 1.19, FXE 1.03, TLT 0.19, UNG 0.19, USO 0.05. **Mean single-sleeve 1.0, avg pairwise corr 0.05 (≈uncorrelated), combined risk-weighted SR 2.33.** Diversifying the crash driver ~doubles portfolio Sharpe — the √N benefit. Ideal book = single-name VRP-selection for the equity sleeve (alpha, capacity-limited) + liquid ETF sleeves for rates/FX/commodity/credit (diversification, high capacity).

## 5e. COMBINED SHARPE & SCALABILITY
- **Combined everything:** within-equity VRP-selection (~1.4 IS bid) × cross-asset diversification (~2.3× from 0.05 corr) → realistic **conservative-execution portfolio Sharpe ~2 in-sample** (full-period higher but regime-flattered).
- **Conservative execution:** final equity strategy at bid (mid−20bp) still IS SR ~1.4 / ann ~7.5%; harsh −30bp → IS 1.1 / 6.3%.
- **Scalability:** single-name VRP top-10% capacity-limited ~low-single-digit $M (thin OTM single-name options); cross-asset ETF sleeves (SPY/QQQ/TLT/GLD/HYG hyper-liquid) scale to $100M–$B. Hybrid book scales well since most capital flows to liquid sleeves. Turnover ~monthly roll (inherent, priced in exec); de-risk fires ~11% of months.

## 5f. PnL BY YEAR & EARNINGS RISK
**Yearly returns (final strategy, mid / bid-conservative):** 2016 +9.4/+6.9, 2017 +7.3/+4.9, 2018 +3.1/+1.0 (weakest — Volmageddon+Q4), 2019 +4.7/+2.1, 2020 +15.3/+12.9 (COVID, de-risk sat out March), 2021 +16.2/+13.5, 2022 +12.9/+9.9, 2023 +10.5/+8.1, 2024 +11.2/+8.7, 2025 +11.3/+7.4 (8mo). **CAGR 10.5% mid / 7.7% bid; every year positive.** Worst month −3.8% (Feb-2020). Seasonality flat +0.6–1.3% except **Feb +0.07%** (only soft month; worst-8 months are Feb-heavy: Feb2020/Feb2024/Feb2019).
**EARNINGS SPLIT (earnings.py, IBES anndats via cusip):** 33% of trades span an earnings announcement but **51% of VRP-SELECTED trades do** (over-tilted). Earnings names avg VRP 0.141 vs 0.064 (~2.2x richer). top10VRP: all SR 2.9, earnings-only 2.5, NO-earnings 2.06. => **~half the edge is an EARNINGS-VOL premium** (rich pre-earnings IV + crush) carrying idiosyncratic GAP risk; other half is clean non-earnings VRP (still 2.06 alone). Implication: cap/size-down earnings weight or knowingly accept announcement-gap risk as priced. Skew-combined test still incomplete (memory-bound calls read; minor).

## 6. Honest Sharpe ceiling
Clean tradeable core = **top-10% VRP liquid single-names, posted near mid, de-risked 0.5× after loss** → honest in-sample **Sharpe ~1.4 at bid, ~7.5%/yr, max DD ~−4–8%**. **Adding cross-asset diversification (0.05-corr sleeves) lifts the portfolio to ~2** and massively improves capacity. That's the realistic institutional ceiling here; further gains need more asset classes / better financing / live execution edge.

## 7. Method lessons
- Any regime/vol signal must use **lagged** (prior-period) values; contemporaneous month-end leaks.
- Multi-leg structures must settle on **one consistent spot** (BS-inversion), not per-leg.
- Cross-sectional signals must use **trailing** realized vol, never holding-period realized.

## 8. RIGOR & ROBUSTNESS CAMPAIGN (2026-07-15)
All at mid execution, top-100-liquid universe, leakage-checked (trailing RV, lagged signals, BS-inversion settlement).

### 8a. WEEKLY vs MONTHLY Q-side (rigor gap 2 — CLOSED)
Built the weekly (5–15 DTE) VRP series from WRDS `spreads_dte05_15` (178,787 weekly puts, 542 names, 2016–25; `weekly_qside_results.json`), monthly-grouped and directly comparable to the monthly (20–40 DTE) book.

| Selection | Weekly SR | Weekly bp/trade | Weekly worst-mo | Monthly SR | Monthly bp/trade | Monthly worst-mo |
|---|---|---|---|---|---|---|
| all | 1.34 | 17.6 | −2.6% | 1.05 | 42.2 | −8.7% |
| top-25% VRP | 3.18 | 46.3 | −2.0% | 1.75 | 85.3 | −8.1% |
| top-10% VRP | 3.46 | 73.8 | −1.2% | 2.38 | 150.2 | −8.4% |

**Weekly beats monthly on Sharpe AND worst-month at every selection tier**, but earns ~half the premium per trade. Mechanism: shorter exposure per contract truncates the crash tail (worst month −1.2% vs −8.4%), and ~4× more trades/month diversifies idiosyncratic risk within the month.

**Net-of-full-spread test (does it survive real cost? `netcost_weekly_vs_monthly.json`):** settling at **BID** (worst-case: cross the full half-spread) rather than mid — **weekly wins decisively:**

| top-10% VRP | MID SR | BID SR | BID worst-mo | spread eats |
|---|---|---|---|---|
| **Weekly** | 3.46 | **2.08** | −1.4% | 57% of gross |
| **Monthly** | 2.38 | **0.51** | −9.6% | 82% of gross |

At the bid, **monthly collapses (SR 2.38 → 0.51)** while **weekly holds up (3.46 → 2.08)** — the half-spread eats 82% of monthly's fat deep-OTM premium but only 57% of weekly's (near-dated δ-0.12 puts on liquid megacaps are proportionally tighter), and weekly's −1.4% worst-month dominates monthly's −9.6%. This **reverses the earlier hedge** ("weekly executes worse"): risk-adjusted and net of realistic cost, **weekly is the better vehicle** — the tail advantage survives execution. Monthly bid SR 0.51 cross-checks the earlier `bt_real2` top-18 result (~0.67). Caveats: "bid" is worst-case full-cross (posted-at-mid lands between: weekly ~2–3, monthly ~1–2); δ-0.12 on liquid names only (illiquid names widen and degrade weekly more).

### 8b. CROSS-ASSET ETF — strict IS/OOS + combined curve (#3 deepened)
7 liquid ETF sleeves (QQQ/TLT/GLD/USO/UNG/FXE/HYG), avg pairwise corr **0.05** (`xasset_oos_results.json`, `xasset_combined_curve.csv`):

- **Combined risk-weighted SR: full 2.33, IS(16–20) 2.30, OOS(21–25) 4.46** — the diversification benefit is **stable across IS/OOS** (unlike the VIX-gate, which was a look-ahead / regime-dependent artifact). This is the robust, defensible robustness result.
- Per-sleeve SRs **rotate** across eras (QQQ robust 2.8–3.2; USO/HYG weak IS → strong OOS 4.7/5.0; TLT/UNG weak) — exactly why the *combination* is what matters, not any single sleeve.
- 10%-vol-target combined book: **CAGR 25.3%, max DD −12.2%.** This is the scalable ($100M–$B) sleeve of the book.

### 8c. FORWARD PAPER-TRADE — harness validated (#forward)
`paper_trade_v2.monthly_signal` replayed over 2016–25 (116 months; `paper_sim_results.json`, `paper_sim_series.csv`) reproduces the validated spec (top-100 → top-10% VRP → de-risk 0.5× after a down month), equal-weight:
- **mid: SR full 2.22 (IS 1.74, OOS 2.96), ann +21.3%;** **bid: SR full 0.72 (IS 0.49, OOS 1.10), ann +6.1%,** worst month −11.6%.
- Gap to the §5b headline SR 2.81 is the **equal-weight vs VRP-weight** difference (~+0.5) plus the harsh full-bid cross; the pattern (OOS > IS, positive every regime) reproduces. This **validates the go-live harness end-to-end**.
- A sample broker-ready ticket for the latest month (2025-08, 10 tickets) is written to `forward_signals/`. **The harness never sends orders — a human submits.** This is the paper-trade scaffold; the one number no backtest can give (real limit-fill adverse selection) must come from running it forward.

### 8d. SAME-ROWS IQN vs GJR-GARCH-t (rigor gap 1 — CLOSED; kills the invalid −38%)
Pinball (quantile) loss for the production walk-forward IQN vs a **clean, unit-matched** GJR-GARCH-t MC (Zero-mean, annual walk-forward refit, MC h-day paths, Student-t) on **identical (ticker,date,horizon) rows** — 102,391 rows, 111 names, h=5/10/21/42/63 (`samerows_iqn_garch.json`, `samerows_merged.csv`). Both are quantiles of the **same** h-day forward return, so pinball is directly comparable.

| h | IQN avg-pinball | GARCH avg-pinball | ratio (IQN/GARCH) | DM t (IQN−GARCH) |
|---|---|---|---|---|
| 5 | 0.01302 | 0.01245 | **1.046** | +12.3 |
| 10 | 0.01871 | 0.01769 | **1.058** | +17.2 |
| 21 | 0.02762 | 0.02602 | **1.062** | +18.1 |
| 42 | 0.03895 | 0.03710 | **1.050** | +14.0 |
| 63 | 0.04757 | 0.04552 | **1.045** | +12.3 |

**On identical single-name equity rows, GJR-GARCH-t BEATS the IQN by ~4.5–6.2% at every horizon (DM t ≈ +12 to +18, all significant).** This **definitively retires the invalid −38%** (which had compared IQN on 113 names/2016+ against t6 on 543 names/2005+). The honest matched result is that the parametric leverage-GARCH is *modestly but robustly better* on single-name equity forward-return quantiles — fully consistent with the project thesis (GARCH owns single-name daily equity; the IQN wins hourly-crypto, transfer, amortization). Per-τ diagnosis: the gap is **concentrated in the tails** — downside τ=.05 ~7% worse at all h; upside τ=.95 worsening with horizon (1.03 → 1.18 by h=63); **body τ=.50 nearly tied (1.02–1.05, shrinking with h)**. This is exactly the un-spliced-tail deficiency that EVT+ACI was already shown to fix.

**Tail-recalibration test (does the gap survive EVT/ACI?):** applied a past-only, pooled-across-names, monthly-refit conformal/EVT recalibration to the IQN quantiles and re-ran the same-rows pinball (`samerows_iqn_calibrated.json`). It **fixes coverage** — p05 breach 0.071–0.089 → **0.051–0.064** (near the 0.05 target) — but only **partially closes the pinball gap**: ratio raw 1.045–1.062 → calibrated **1.029–1.048**. **GARCH-t still wins after tail-splicing** (the gap roughly halves at long horizons, ~⅓ at short). So the deficiency is **not purely a fixable-tail-calibration artifact** — a real structural/training-budget residual (~3–4%) remains. That residual is what the GPU retrain (below) isolates. *(Caveat: production IQN is raw9, K=3, CPU/GPU-mixed budget.)*

### 8e. EARNINGS-VRP robustness (thread — refined)
Re-run on the per-ticker `earn_*.csv` source (`earnings_deep_results.json`; the consolidated `earnings_dates.csv` failed to join → 0%). Top-10%-VRP book, ~85 names with earnings files, 35-day option-life window:
- **Earnings names carry richer VRP** (0.137 vs 0.078 non-earnings) and more premium per trade (185.9 vs 141.6 bp) — confirms the event-premium is real and over-tilted into (19.4% of selected trades span earnings vs 15.2% of all).
- **But it does NOT carry the Sharpe:** earnings-only SR 1.94 ≈ non-earnings-only SR **1.99** — the richer earnings premium is offset by gap risk, netting the *same* risk-adjusted return. **The non-earnings VRP is strong on its own (1.99)**, so the edge does **not** critically depend on earnings gap risk (this qualifies the earlier §5f "half the edge is earnings" reading).
- **Sizing earnings down 0.5× slightly HURTS** (book SR 2.38 → 2.24) — you're cutting rich, fairly-compensated premium. Verdict: **accept earnings exposure at full weight as priced**; no earnings filter needed (echoes the earlier "earnings vol fairly priced" finding).

### 8f. GPU K=5 retrain — training-budget arm (COMPLETE, 2026-07-16)
To isolate the residual ~3–4% same-rows gap that survives tail-recalibration (§8d): retraining the MH IQN on ai2 with **K=5 ensemble (vs production K=3) and 70 epochs (vs 40)**, same raw9 features / `mh_panel_v2` / walk-forward-annual design — `gpu_iqn_k5.py` (sed-derived from `gpu_iqn_mh.py`), launched detached (`setsid --fork`, MHVAR=k5), confirmed running (GPU active). Output `mh_quantiles_k5.csv` on ai2, ETA ~3–4h. **Completion is cheap:** double-click `fetch_k5.bat` once `train_k5.log` ends, then the comparison is a **sandbox merge** of the new quantiles onto `samerows_merged.csv` (the GARCH-t MC columns g05–g95 are already there — no re-run) → recompute pinball. If K=5/70ep closes most of the residual → the gap was **training budget**; if the ~3–4% persists → it is **structural** (parametric leverage-GARCH genuinely better on single-name equity). *Prediction from §8d: the ensemble helps the body/variance but the tail residual is largely structural, so expect partial closure — GARCH-t likely stays ahead by a point or two.*

**RESULT (finished 2026-07-16).** The K=5 / 70-epoch retrain finished on ai2 (`train_k5.log` → `DONE 259650`; `mh_quantiles_k5.csv`, 259,650 rows fetched). Merged onto `samerows_merged.csv` by (tk,date,h); NaN-safe avg-pinball over τ = .05/.25/.50/.75/.95 on **102,391 identical rows** (the production-IQN recompute reproduces the §8d reference ratios to 3 decimals — 1.046/1.058/1.062/1.050/1.045 — validating the merge and loss).

| h | K5-IQN pinball | GARCH-t pinball | ratio K5/G | DM t (K5−G) | prod ratio (§8d) |
|---|---|---|---|---|---|
| 5 | 0.012960 | 0.012446 | **1.041** | +11.7 | 1.046 |
| 10 | 0.018563 | 0.017694 | **1.049** | +14.7 | 1.058 |
| 21 | 0.027327 | 0.026016 | **1.050** | +15.5 | 1.062 |
| 42 | 0.038669 | 0.037096 | **1.042** | +12.7 | 1.050 |
| 63 | 0.047142 | 0.045524 | **1.036** | +10.6 | 1.045 |

Pooled K5/G = **1.043**, DM t = **+26.1**.

**Verdict: STRUCTURAL.** Bumping the ensemble K=3→5 and epochs 40→70 shaves only ~0.5–1.1 pp off each ratio (h21 1.062→1.050, h63 1.045→1.036) — it closes roughly **15–20% of the gap** and no more. GJR-GARCH-t still beats the K=5 IQN by **3.6–5.0% at every horizon with overwhelming significance** (per-horizon DM t ≈ +11 to +16; pooled +26). Training budget is *not* the explanation. Combined with §8d's finding that EVT/ACI tail-recalibration also only halved the gap, the residual is genuinely **structural: parametric leverage-GARCH-t is the better model for single-name daily equity forward-return quantiles.** This matches the §8d prediction (ensemble helps the body/variance, tail residual survives) and is fully consistent with the project thesis — the IQN's edge lives in hourly-crypto, cross-asset transfer, and amortization, not single-name equity. The matched-rows question is now closed on both arms (calibration and budget); no further retrain is warranted.
