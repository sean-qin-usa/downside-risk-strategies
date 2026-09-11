# Tradeable Strategies Catalogue
*What actually makes money, ranked by effect size — plus the model traits that convert to a tradeable edge, and what's currently being paper-checked. All figures backtest/net-of-cost unless flagged; treat as research, not promises.*

## Part A — Strategies, ranked by effect size

| # | Strategy | Vehicle | Net effect (Sharpe) | Capacity | Paper-checked? |
|---|---|---|---|---|---|
| 1 | **Cross-asset ETF VRP** (sell δ−0.12 puts across QQQ/TLT/GLD/HYG/FXE/USO/UNG, risk-weighted) | liquid ETF options | **combined 2.33** (IS 2.30 / OOS 4.46), CAGR 25% @10% vol, DD −12% | **$100M–$B (high)** | **NO** ⚠️ |
| 2 | **Weekly single-name VRP** (top-10% by VRP, 5–15 DTE, post at mid, de-risk 0.5×) | single-name options | **3.46 mid / 2.08 bid**, worst mo −1.4% | low–mid ($M) | **YES** (weekly-vrp-signal) |
| 3 | **Monthly single-name VRP** (top-10% VRP, 20–40 DTE) | single-name options | 2.38 mid / 0.51 bid | low ($M) | **YES** (monthly-vrp-signal) |
| 4 | **Index variance leg** (GJR-timed, regime-gated short var) | VIX futures / var swap | ~1.0–1.3, corr 0.15 to names book | high | NO |
| 5 | **EM-FX carry + regime-gate**, *crisis currencies only* ("when not to hold the carry") | NDF / FX options | **Turkey gated 0.88 (OOS 1.41 vs ungated −0.06), worst day −14.7%→−3.0%; Russia worst −22.8%→−2.2%.** Survived clean-carry + OOS robustness. BUT hurts well-behaved FX → broad-basket gate does NOT work | specialist / concentrated | NO — now credible for TRY/RUB; needs NDF access |
| 6 | Risk-reversal / skew harvest (sell put + buy call) | single-name options | 1.31 but directional/bull-tilted | mid | NO |

**The two biggest, most robust, and most scalable are #1 (cross-asset diversification, ~2.3) and #2 (weekly VRP, ~2 net).** Everything else is a diversifier or specialist add-on. The *combined* book (single-name VRP selection × cross-asset sleeves) targets a conservative portfolio Sharpe ~2.

## Part B — Usable model traits that beat GARCH / industry benchmarks in tradeable scenarios

These are *operational* advantages (not raw forecast accuracy) that translate into P&L. Tiered by honest effect size.

**Big tradeable effect (2–4×) — these are the real levers:**
- **Execution: post at mid vs cross the bid** — ~*doubles* Sharpe (0.67→1.13) on any put-writing strategy. It's a price, not a forecast — no look-ahead. The single largest clean lever found.
- **Regime-gating (stand-aside)** — flag "don't trade now" states and sit in cash. A parametric vol model (GARCH) scales *magnitude* but can't represent the *regime/shape* shift, so it can't gate the same way. **Robust findings (clean-carry, OOS-tested):** (a) the *Sharpe* benefit is **real but selective** — it works only where there's a learnable crisis regime (Turkey −0.15→0.88, OOS 1.41; Russia), and *hurts* well-behaved series (indiscriminate/broad-basket gating fails); (b) the *tail-reduction* is **universal and large** (EM-FX worst days cut 3–10×; VRP stress-gate). So: **gate selectively on crisis-prone assets for Sharpe; gate broadly only as a drawdown/tail control.**
- **Adaptive scaling / de-risk** — cut size 0.5× after the strategy's own down month (losses cluster; autocorr +0.27). Lifts the VRP book Sharpe and cuts drawdown (part of the production spec). Reacts to the strategy's *own* regime, which symmetric GARCH vol-scaling doesn't.
- **Cross-sectional selection** — rank the whole universe by VRP richness and trade only the top decile: ~*doubles* Sharpe (all-names ~1 → top-10% ~2–3). GARCH doesn't inform this; a consistent cross-sectional risk read does.

**Real but capability/sizing edges (not big Sharpe, but things GARCH literally can't do):**
- **Calibrated tail for risk-sizing, defined-risk caps, and ES capital (EVT + adaptive conformal)** — exact coverage → correct position sizing and margin. Beats the GARCH family on the regulatory 97.5% ES object (realized/predicted ES ratio 1.214, best of field; 99% VaR breach 1.45%→0.89%). This is a *capital-efficiency* edge, not a return edge.
- **Cold-start risk sizing (amortization)** — size positions on brand-new listings *from characteristics alone*, where GARCH can't run at all. On IPOs' first weeks the amortized model beats the only available benchmark (own short history) by **~5%** (ratio 0.944 at days 15–60). Lets a desk onboard new names to a book with proper day-1 risk. GARCH: N/A.
- **Self-assessed confidence** — the ensemble's disagreement predicts its *own* error (corr +0.11); size down on low-confidence days. A benchmark-free reliability signal GARCH cannot produce. *(Validated as a signal; not yet converted to a Sharpe number.)*

**Honest bottom line on traits:** the ones with *big tradeable effect* (execution, gating, de-risk, cross-sectional selection, diversification) are largely **model-light risk-premium levers** — they don't need the IQN. The IQN's *distinctive* traits (calibrated tail, cold-start sizing, confidence) are real and defensible but are **capability/sizing edges**, not sources of large Sharpe. Be clear-eyed: the trading P&L comes from the levers; the IQN adds risk-management robustness and cold-start coverage.

## Part C — Paper-check status and the gap
**Currently paper-checked** (live scheduled tasks generating tickets to `forward_signals/`):
- `monthly-vrp-signal` — monthly single-name VRP (strategy #3)
- `weekly-vrp-signal` — weekly single-name VRP (strategy #2)

**NOT paper-checked (gap):**
- **Cross-asset ETF book (strategy #1)** — the *highest-Sharpe and most scalable* strategy is **not being tracked**. This is the biggest gap.
- Index variance leg (#4), EM-FX carry-gate (#5).

**Recommendation:**
1. **Add a paper-check for the cross-asset ETF sleeve book (#1)** — highest priority; it's the scalable, robust one and it's untracked.
2. Add the index variance leg (#4) as the low-correlation diversifier.
3. Add EM-FX carry-gate (#5) **only after** the robustness test passes (in progress).

So today we paper-check 2 of ~5 tradeable strategies — and *not* the best one. Closing that is the single most useful operational step.
