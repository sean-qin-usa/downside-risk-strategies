# When NOT to Be Short — the P−Q Wedge as a Short-Vol Veto

*Sean Qin · GBC Downside-Risk Project · 2026-07-04 · companion to PQ_TRADE_BACKTEST.md and PQ_QUANTILE_EXTENSION_SPEC.md. Trading evidentiary standards apply (APPLICATIONS.md §4).*

## 1. Why the veto is the *right* reading of the backtest

The backtest's honest summary was: timing the VRP with ln(K_Q/F_P) adds no statistically significant *mean* over always-short (s2−s0 NW-t ≈ 1.5–1.8), but transforms the *tail* — skew −4.15 → −1.51, positive in all six subperiods including 2008-09 and 2020, exposure cut to 0.41 entering Lehman and net long entering COVID.

That is not the signature of a return-enhancing signal. It is exactly the signature of a **veto**: a signal that can't tell you when selling vol is *extra* good, but can tell you when it's *bad*. Restated economically: the unconditional VRP (t = 5.2, the most replicated fact in the asset-pricing literature) is the strategy; the P−Q wedge's job is only to identify the minority of months when the insurance premium you're collecting is below actuarial value — when K_Q is thin relative to what the P-model says variance (and especially its tail) will be. Sell always, *except* then.

The veto framing also buys three methodological advantages over s1/s2:

1. **A weaker, more defensible claim.** s2 going net long variance into COVID is a great anecdote but a hard claim (long-vol timing). The veto only requires the signal to identify bad-selling regimes — stepping aside, never flipping. This is also what a desk would actually do.
2. **Less multiple-testing exposure.** One binary rule with one threshold, against ~50 model×strategy×leg combinations behind the SR-1.35 headline. The p-hacking haircut in §5 of the backtest mostly doesn't apply.
3. **Cleaner evaluation.** The test is a difference in conditional means: short-var returns in vetoed vs non-vetoed months. No sizing function, no vol-scaling choices.

## 2. Candidate veto rules (pre-register before testing)

Ordered from what today's outputs support to what needs the IQN extension:

- **V1 — fair-value veto:** stand aside when lr = ln(K_Q/F_P) < 0 (GJR-t): implied strike at or below the P-forecast means you are being paid less than the model's actuarial value — no premium to harvest. The zero threshold is a priori, not tuned.
- **V2 — trailing-quantile veto:** stand aside when standardized lr is in its bottom trailing quintile (reuses the s3 machinery but one-sided: s3's long side is dropped).
- **V3 — confidence veto (stacks on V1/V2):** stand aside when ensemble disagreement is in its top trailing decile — the capstone validated that disagreement predicts model error; when the P-side doesn't know, the wedge is noise. This one is GBC-native: no GARCH desk can produce it.
- **V4 — tail-ratio veto (the IQN-native rule, needs the quantile extension):** the seller's ruin lives in the τ > 0.95 region, but lr compares *expected variances*. The right actuarial comparison is premium per unit of predicted tail: veto when (K_Q − F_P) / ES_P^{0.95}(x_t) falls below its trailing floor. Leg C proved the premium is concentrated in Q-wings; V4 vetoes precisely when the P-wing eats it. Equivalent wedge statistic: veto on thin Δ(0.01…0.05) from PQ_QUANTILE_EXTENSION_SPEC.md §3.

## 3. Evaluation protocol

On the existing 377-month Leg-A dataset (code `GBC_data/code/pq_trade/`, results parquets in hand — this is an afternoon of CPU):

1. **Veto quality:** mean short-var return in vetoed vs non-vetoed months (want: vetoed ≪ non-vetoed, ideally negative), NW paired test; **crash capture** = fraction of the bottom-decile always-short months that the rule vetoed; false-veto rate = fraction of vetoed months where always-short was actually fine.
2. **Portfolio delta:** short-except-veto vs always-short: Sharpe, skew, max drawdown, 08-09 and 2020 sub-Sharpes, % time invested. Expected shape from the s1/s2 evidence: similar mean, drastically better skew/DD.
3. **Honesty checks:** thresholds fixed ex-ante (V1's zero, V2's quintile, V3's decile — written here, before running); all windows trailing; one-day lag on every signal (the same-bar canary from the backtest); report the vetoed-month list so the 2008/2020 story is auditable month by month.
4. **Holdout:** confirm on the 26-name single-stock panel (per-name IV vs per-name P-forecast, where IV history exists) or a paper-trading window — the backtest's own §5 discipline.

## 4. What "P vs Q" means (one-paragraph reference)

**P** is the physical (real-world) probability measure: the actual frequencies of outcomes, which is what any model estimated on historical returns — GARCH, GJR, the IQN — forecasts. **Q** is the risk-neutral measure: the probabilities *implied by option prices* when you treat prices as discounted expected payoffs. Q is not a forecast — it is P distorted by risk premia, because insurance sellers demand compensation: crash states get up-weighted, so implied variance sits above true expected variance on average. VIX² is a Q-expectation of next-month variance; the GJR forecast is the P-expectation; their persistent gap *is* the variance risk premium (t = 5.2 in our sample), and its fluctuations are the timing/veto signal. Selling variance = selling insurance at the Q-price while bearing the P-risk; the veto fires when the Q-price stops exceeding the P-actuarial value. Leg C's lesson refines this: the premium isn't "IV is too high" at the money — it lives in Q's *convexity and left wing* (VIX² > ATM IV²), which is why the IQN's P-*tail* is aimed at exactly the right part of the distribution.

## 5. Sequencing

V1–V3 are runnable now on existing outputs (one script, reuse `bt_monthly` parquets). V4 waits on the Q_Q(τ) extractor (quantile-extension spec step 1). If V1–V3 results hold, the veto — not the sized strategy — becomes the headline trading claim: *"the P−Q wedge doesn't beat the VRP; it tells you when to decline it."*
