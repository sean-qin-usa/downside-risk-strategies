# Cushioning Deep-Dive — Findings

*P-vs-Q downside put-writing (τ.10 book). Session of 2026-07-14. All numbers are ex-ante unless flagged.*

## The question
Sharpe is dominated by ~5 crash months per decade. Can we **cushion** those months — buy protection, hedge, or stand down — without paying away the premium? We already knew crashes are **unforecastable** (features, calendar, earnings, dealer-gamma all failed). So the target was structural cushioning, not prediction.

## What we tested, and what happened

**1. Buy protection (defined risk).** Per-name protective puts *and* a portfolio-level index put overlay.
Result: **fails.** Constant crash insurance is overpriced (this is literally the paper's thesis). The index-put overlay bled −0.54%/month (~−6.5%/yr), swamping the +1.8%/yr base leg; Sharpe fell at every hedge ratio (0.59 → 0.36 → 0.03 → negative). It cuts the tail (Mar-2020 −4.5% → −2.0%) but costs more than the whole premium.

**2. Delta-hedge the short puts.** Daily-rebalanced BS delta, split-consistent price path, 1 bp/rebalance cost.
Result: **fails worse.** Average return 46.5 → 4.5 bp, Sharpe 1.14 → 0.12, and it made Mar-2020 *worse* (−481 → −849 bp). A short put is **short gamma**: hedging means selling as the stock falls and buying as it rises, realizing losses proportional to realized variance — which explodes in a crash. Deeper point: **the premium is the directional downside-risk premium**, so hedging away the delta hedges away the return, leaving a 4.5 bp variance crumb.

**3. Regime standdown (stand down when VIX elevated).**
Result: **looked spectacular, then proved to be a look-ahead artifact.**
- With contaminated timing (gate month M on month-M's *end*-of-month VIX): Sharpe 0.70 → 2.5–3.2. Exciting, and wrong.
- The bug: end-of-month VIX already "knows" a crash spiked vol that month, so the gate skipped exactly the bad months using information unavailable at entry.
- With **clean timing** (gate on the VIX known at entry — prior month-end): the edge collapses.

| VIX>18 gate | Clean (tradeable) | Look-ahead |
|---|---|---|
| Index leg, full | **0.67** (vs 1.07 baseline — hurts) | 1.85 |
| Index leg, pre-2016 | **0.48** (vs 1.32 — badly hurts) | 1.65 |
| Single-name mid, 2016+ | **1.19** (vs 1.13 — no edge) | 3.16 |

The clean gate catches *some* crash months (e.g. Mar-2020, which follows an already-elevated Feb) but misses the onset shocks (Volmageddon, Oct-2018) and over-sits the calm post-spike recovery months that pay well — netting to roughly zero benefit. *(Caught because the dial-down test used entry-time VIX and disagreed with the gate scripts.)*

## The one real lever: execution
Not a cushion, but the biggest realistic improvement found — and it has **no look-ahead** (it's a per-trade price, not a timing signal). Selling by **posting at the mid** instead of **crossing to the bid**:

| Execution | Net/trade | Sharpe |
|---|---|---|
| Cross (sell at bid) — our baseline | 27 bp | 0.67 |
| Post at mid (fair value) | 46 bp | 1.13 |
| Post at ask (ceiling, unrealistic) | 66 bp | 1.53 |

Roughly doubles the tradeable edge. Caveat: pushing toward the ask invites adverse selection (fills concentrate in toxic down-flow); in the severe case the edge goes negative. Realistic target: post near mid, don't chase the ask. The one number no backtest can give — *your* actual fill quality — needs a forward paper-trade.

## Unifying conclusion
**You cannot cushion the punch; you can only be paid for taking it.** Insurance is overpriced, delta-hedging removes the premium and amplifies crashes, and regime-timing requires knowing the future. This is the deepest confirmation of the ℙ-vs-ℚ thesis: **the variance risk premium is compensation for a crash you genuinely cannot dodge ex-ante.** The honest levers are (a) *execution* (post at mid), (b) *diversification/sizing* to survive the tail, and (c) *position size* set so the unavoidable crash months are tolerable — not avoidance.

## Implications
- **Paper:** the headline economics are conservative (reports 27 bp crossing); patiently-executed is ~46 bp. The "no cushion works" result is itself a clean, publishable finding that reinforces the crash-premium interpretation.
- **Live trading:** do *not* deploy a VIX gate — it doesn't survive honest timing. Focus on execution quality and tail-tolerant sizing. Validate execution via forward paper-trading before capital.
- **Method note:** any regime/VIX gate must use lagged (prior-period) values; contemporaneous month-end values leak.
