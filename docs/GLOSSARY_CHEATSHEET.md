# GBC Project — Cheatsheet & Glossary
*Plain-language reference for every symbol and term used across the paper and research. Written for someone new to finance **or** statistics. Skim the section you need.*

---

## 1. Symbols at a glance

| Symbol | Say it | What it means here |
|---|---|---|
| **τ** | "tau" | A probability level for a quantile. τ=0.05 = the 5%-worst outcome; τ=0.50 = the median. We forecast the whole distribution at several τ's. |
| **δ** | "delta" | An option's sensitivity to the stock price; loosely, the market's estimated probability the option finishes in-the-money. We sell puts at δ≈−0.12 (~12%-ish chance of being exercised). Negative for puts. |
| **σ** | "sigma" | Volatility — how much something moves. Usually annualized (e.g. σ=0.30 = 30%/yr). |
| **η** | "eta" | A learning-rate / "temperature" knob in model-averaging (see *Gibbs*). Bigger η = react faster to recent performance. |
| **h** | — | Forecast **horizon** in trading days (h = 5, 10, 21, 42, 63 ≈ 1 week to 3 months). |
| **√h** | "root-h" | Square-root-of-time scaling: risk over h days ≈ 1-day risk × √h (a baseline assumption models refine). |
| **K** | — | Two uses: (1) an option's **strike price**; (2) the number of neural nets in an **ensemble** (K=3, K=5). Context tells which. |
| **S** | — | The **spot** (current) price of the underlying stock/ETF. |
| **p05, p50, p95** | — | The forecast return at the 5th / 50th / 95th percentile. p05 = a bad-case (downside) outcome, p50 = middle, p95 = good-case. |
| **bp** | "bips" / basis points | 1 bp = 0.01%. "46 bp/trade" = 0.46% profit per trade. |
| **DTE** | — | **Days to expiration** of an option. Weekly ≈ 5–15 DTE, monthly ≈ 20–40 DTE. |

---

## 2. Options & trading basics

- **Option** — a contract. A **put** gives its owner the right to *sell* the stock at the strike; a **call**, to *buy*. We mostly **sell puts** (collect the premium, take on the risk).
- **Strike (K)** — the fixed price in the contract.
- **Expiry / expiration** — the date the option ends; **held to expiry** = we keep it to the end rather than closing early.
- **Premium** — the price paid for the option; what the seller collects up front.
- **Moneyness** — where the strike sits vs the stock price. **OTM** (out-of-the-money) = strike below spot for a put (the cheap, "insurance" puts we sell); **ATM** = at spot; **ITM** = already in profit for the holder.
- **Bid / Ask / Mid / Spread** — the **bid** is the highest price a buyer will pay; the **ask** (offer) the lowest a seller will accept; the **mid** = halfway between; the **spread** = ask − bid (a transaction cost). "Post at mid" = try to trade at the midpoint; "cross to bid" = accept the worse price to trade immediately.
- **Cash-secured** — we set aside enough cash to cover assignment, so no leverage/margin risk. Returns are quoted on this full amount (conservative).
- **Assignment** — if a put we sold finishes in-the-money, we're obligated to buy the stock at the strike (the loss scenario).
- **Roll** — closing an expiring option and opening a new one; a monthly strategy "rolls" ~12×/yr, a weekly one ~52×/yr.
- **Settlement** — computing the final payoff at expiry. We reconstruct it from the stock's price move (via a Black–Scholes inversion) so stock splits don't corrupt it.

---

## 3. Volatility & the core idea (P vs Q)

- **Implied volatility (IV)** — the volatility *baked into an option's price*; the market's expectation of future movement. Higher IV = pricier option.
- **Realized volatility (RV)** — how much the stock *actually* moved (measured from history, e.g. trailing 21 days).
- **VRP — Variance/Volatility Risk Premium** — the gap **IV − RV**. Historically IV > RV: options are priced as if the world is scarier than it usually turns out. Selling that gap is the core edge. **We sell puts on the names with the biggest VRP.**
- **ℙ vs ℚ ("P vs Q")** — two views of the future. **ℙ (physical)** = what actually tends to happen (from data/statistics). **ℚ (risk-neutral)** = what option *prices* imply. The premium lives in the gap between them (ℚ prices more fear than ℙ delivers). The name of the whole strategy.
- **Skew** — puts (downside protection) cost more than calls; the "fear" is asymmetric, concentrated on the downside.
- **Term structure** — how IV varies with expiry (short-dated vs long-dated). Inverted term structure (short > long) signals stress.
- **VIX / VIX3M** — market-wide 30-day / 3-month expected volatility indices ("the fear gauge").
- **Variance swap** — a cleaner instrument that pays the difference between implied and realized variance directly; conceptually the purest way to harvest VRP.

---

## 4. Strategy & performance terms

- **Short vol / put-writing** — the strategy: repeatedly sell insurance (puts), collect premium, absorb occasional crashes.
- **Sharpe ratio (SR)** — return per unit of risk (annualized). Rough reading: <1 modest, ~1–2 good, >2 excellent — *but* backtest Sharpes overstate live results. Our honest tradeable core is ~1–2.
- **Drawdown / Max DD** — the worst peak-to-trough loss. "Worst month" is the single ugliest month.
- **De-risk (0.5× after a down month)** — cut position size in half following any losing month; losses cluster, so this trims the tail.
- **Cross-sectional selection** — each period, rank all names and trade only the best-ranked slice (e.g. **top-10% by VRP**). "Cross-sectional" = comparing names *against each other at one time*.
- **Sleeve** — one component of a diversified book (e.g. the QQQ sleeve, the gold sleeve). Low-correlated sleeves combine into a higher-Sharpe portfolio.
- **Capacity** — how much money a strategy can hold before its own trading moves prices. Single-name puts = low capacity; liquid ETFs = high.
- **Alpha** — return *not* explained by known risk factors (market, size, value, short-vol) — i.e. genuine skill. Ours ≈ +13%/yr, t≈6.9 (statistically strong).

---

## 5. Forecasting & statistics terms

- **Distribution / quantile** — instead of one guess, we forecast the *whole range* of outcomes. A **quantile** is a cut point: the τ=0.05 quantile is the value only 5% of outcomes fall below.
- **Pinball loss (quantile loss)** — the scoring rule for a single quantile forecast; penalizes being on the wrong side asymmetrically. Lower = better. Our main model-comparison metric.
- **CRPS** — a score for a *whole* distribution forecast (roughly, averaged pinball across all τ). Lower = better.
- **Coverage / calibration** — does a "5% quantile" actually get breached ~5% of the time? If yes, it's **calibrated**. Fixing coverage was what the tail-recalibration did.
- **GARCH family** — classic statistical volatility models. **GJR-GARCH** and **EGARCH** add a *leverage effect* (down-moves raise volatility more than up-moves). The **-t** suffix = fat-tailed (Student-t) errors, for crash realism. This is the tough benchmark to beat.
- **IQN (Implicit Quantile Network)** — our neural network that outputs the full return distribution (any τ) conditioned on features. The "GBC/learned" side of the project.
- **Walk-forward** — train only on the past, predict the next block, roll forward. Prevents cheating with future data.
- **In-sample (IS) vs out-of-sample (OOS)** — IS = data the model/strategy was tuned on; OOS = fresh data it never saw. OOS is the honest test.
- **Look-ahead / leakage** — accidentally using information you wouldn't have had in real time (e.g. month-end VIX to decide a start-of-month trade). It fakes great results; we hunt and kill it (the "VIX gate" was retracted for this).
- **EVT / GPD (Extreme Value Theory / Generalized Pareto)** — statistics of rare extremes; used to model the far tail (crashes) that ordinary fits miss.
- **Conformal / ACI (Adaptive Conformal Inference)** — a method that adjusts quantiles using recent errors so coverage lands exactly on target, with no distributional assumptions.
- **Diebold–Mariano (DM) test** — checks whether one model's forecasts are *significantly* better than another's. A DM t of ±12–18 = a very confident difference.
- **MCS (Model Confidence Set)** — the set of models that are statistically tied for best.
- **Permutation / random-portfolio test** — compare the real strategy to hundreds of random ones; if it beats ~all of them, the edge isn't luck.
- **Gibbs posterior / Gibbs model-averaging** — a way to blend several models by weighting each by exp(−η × its accumulated error). Best models get exponentially more weight; it updates online as new data arrives. *(The name comes from the Gibbs–Boltzmann distribution in physics — see the note below.)*

---

## 6. Project shorthands you'll see

- **τ.10 book / "top-10% VRP"** — the production strategy: sell puts on the richest-10%-VRP names.
- **raw9 / K=3 / K=5** — the IQN's feature set (9 raw features) and ensemble size (3 or 5 nets averaged).
- **"the −38%"** — a *retired, invalid* figure that once claimed the IQN beat GARCH by 38% (it compared mismatched data). The corrected same-rows result is GARCH ~5% *ahead*.
- **h-day forward return** — the return from today to h trading days later; what the risk models forecast the distribution of.
- **mid / bid numbers** — a result "at mid" assumes good fills; "at bid" assumes worst-case fills. Reality is between.

---

## 7. Two conceptual notes

**Is the "Gibbs" method connected to physics?** Yes — directly. The Gibbs–Boltzmann distribution in statistical mechanics weights each physical state by exp(−Energy / temperature). Our model-averaging weights each model by exp(−η × accumulated forecast error): *error plays the role of energy, and 1/η the role of temperature.* It's the same mathematical object, and in machine learning it's also known as **exponential-weights / multiplicative-weights / "Hedge"** (prediction with expert advice). So the intuition from physical systems *does* translate: low-"energy" (low-error) models dominate the mixture, and the "temperature" η controls how sharply. Implementation is a few lines: keep a running loss per model, set weight ∝ exp(−η·loss), predict the weighted blend, update each period.

**Do we have "great prediction power"?** Be precise about *which* prediction. We are **good at forecasting the risk distribution** (after EVT/ACI the quantiles are calibrated — a "5% bad day" really is ~5%). We are **poor at predicting direction or timing crashes** (return R² is only a few percent, and every crash-prediction feature we tried failed — the "informational ceiling"). The money is **not** from foresight; it's a **risk premium** — getting paid to hold a risk others avoid. On *time trends*: the raw premium has **decayed** (base-strategy Sharpe fell across decades ~1.8 → ~0.5 as the trade got crowded), so in premium terms we were "better before." Recent backtest Sharpes look high, but that's a *kind-regime* effect (random strategies also scored high 2021–25), not improved skill. Honest forward expectation is the lower, conservative number.
