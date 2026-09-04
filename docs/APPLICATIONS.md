# Applications Beyond the Paper — Trading Signals and Other Uses

*Sean Qin · GBC Downside-Risk Project · 2026-07-03*
*Companion to RESEARCH_DIRECTIONS_V2.md and INSTITUTIONAL_BENCHMARKS_AND_DATA.md. Scope: what the trained conditional-distribution machinery (IQN, amortized panel IQN, Gibbs ensemble, confidence signal) can do outside the forecasting paper. These claims live under a different evidentiary standard than the paper — see §4.*

---

## 0. The honest frame

Our validated edge is in the **shape and scale** of the conditional loss distribution — width, asymmetry, tail thickness — not its **location**. Nothing we have demonstrates mean-return predictability, and daily mean prediction is close to hopeless anyway. So viable applications are those that monetize distributional information *without* requiring directional alpha: risk premia harvesting, position sizing, cross-sectional risk sorts, and risk-infrastructure uses. Anything that quietly assumes a mean edge should be treated as out of scope.

## 1. Trading signals (ranked by fit to existing results)

**1.1 P-vs-Q: volatility and skew risk premia (most direct).**
The IQN produces the real-world (P-measure) conditional distribution; the options market quotes the risk-neutral (Q) one. The wedge between them is the tradeable object:
- *Width vs implied vol:* when ATM IV is rich relative to forecast distribution width → short vol (variance-risk-premium harvesting); when forecast width exceeds implied → long vol / tail hedges.
- *Predicted skew vs risk reversals:* when the IQN's downside-vs-upside quantile asymmetry is fatter than the 25Δ risk reversal prices → buy puts/sell calls, and vice versa.
- The structural angle: we can compare P vs Q **quantile-by-quantile**, which is strictly more granular than variance-level desk models. No standard vol model produces a full conditional P-distribution to hold against the surface.
- Dependencies: the options-implied Bloomberg pulls (INSTITUTIONAL_BENCHMARKS_AND_DATA.md §2A) — the same series serve as benchmark, feature, and trade leg.

**1.2 Distribution-aware position sizing (highest Sharpe-per-effort, no alpha needed).**
Vol-targeting (Moreira–Muir 2017) improves Sharpe with zero mean forecast; we can do the tail-aware version:
- Scale exposure by forecast ES or P(loss > k%) instead of variance — direct read-offs from the quantile curve.
- Full-Kelly / fractional-Kelly sizing: E[log(1 + w·r)] computes as a marginal over τ-draws — literally the Polson–Ruggeri–Sokolov MEU machinery applied to sizing.
- Overlay the **confidence signal**: de-risk when ensemble disagreement spikes (validated: disagreement predicts IQN error). A regime filter no classical model can produce from its own internals.
- Evaluation: Sharpe/CEQ of tail-managed vs vol-managed vs unmanaged, same point-in-time discipline.

**1.3 Cross-sectional tail sorts (uses the flagship amortization result).**
The amortized 138-name IQN emits per-name conditional tail risk and predicted skew, daily, including for thin-history names (the transfer result). Sort the cross-section and form long-short portfolios on predicted left-tail risk / conditional skewness — the lottery-stock and skewness-anomaly literature (e.g. Bali–Cakici–Whitelaw) says these characteristics price. Novelty: GARCH cannot produce this signal for young names; we demonstrably can. Paper-adjacent but a separate contribution.

**1.4 Drawdown/crash-probability market timing (simplest, weakest).**
P(loss > k%) as a de-risking trigger. Cheap to test on existing outputs; expect modest results (timing off tail probabilities alone is well-mined). Include mainly as a baseline for 1.2.

## 2. Risk-infrastructure applications (no trading required)

- **Margin/collateral models.** CCPs and brokers set margins with VaR-type systems (SPAN-successors); the amortization argument applies verbatim — one conditional model margining every instrument, including newly listed ones. Same pitch as the flagship, different customer.
- **Coherent stress-scenario generation.** Sample joint tail scenarios from the conditional model (via Q(τ|x,w) or the copula route) instead of ad-hoc historical replays — internally consistent, state-conditional stress tests.
- **Market-making inventory risk.** Quantile forecasts of short-horizon P&L for spread/skew setting (natural fit with the HF-crypto direction and the Hilbert microstructure background).
- **Insurance/actuarial pricing.** The Gibbs-VaR literature (Syring–Hong–Martin) is already actuarial; conditional severity distributions via IQN is the obvious extension.

## 3. Outside finance proper

- **Growth-at-risk macro nowcasting (best academic analogue).** Adrian–Boyarchenko–Giannone, "Vulnerable Growth" (AER 2019): quantile regression of future GDP growth on financial conditions — the IMF's GaR framework. An IQN/GBC version (all quantiles jointly, nonlinear, amortized across countries) is a direct, publishable upgrade and squarely econometrics — strong fit for Prof. Jiang.
- **Electricity price/load tails.** Pinball loss is that field's lingua franca; energy markets have fat tails, seasonality, and abundant data — a friendly second domain to show generality.
- **Any pinball-scorable conditional distribution:** funding rates, realized-vol distributions, credit transitions — the machinery transfers unchanged wherever conditional *shape* carries information.

## 4. Evidentiary standard (read before trading anything)

Signal claims are NOT forecasting claims. Moving from CRPS/coverage to strategies changes the evaluation stack to Sharpe, certainty-equivalent return, max drawdown, turnover, and **transaction costs**, and makes backtest-overfitting the dominant risk (multiple-testing haircuts, e.g. deflated Sharpe ratio; strict OOS holdout; no strategy iteration on the test window). Keep the paper's forecasting results and any trading results in separate documents with separate standards — the paper's credibility should never underwrite a backtest.

*Sequencing: 1.2 sizing study is runnable today on existing outputs (CPU, an afternoon). 1.1 P-vs-Q needs this week's Bloomberg IV/risk-reversal pulls. 1.3 waits for the full-138 amortization run. §3 GaR is a thesis-scale spin-off to raise with Prof. Jiang.*
