# Paper direction — generative quantile models for downside risk

Broad framing (agreed): the paper is about BEATING THE INDUSTRY STANDARD for downside-risk forecasting, with GBC (generative/neural quantile methods, Polson-Sokolov) as the flagship methodology and the misspecification frontier as the organizing empirical principle. It need not be GBC-only; the applied "beat the banks / FRTB" results and the GBC-thesis results are two pillars of one story.

Working title: "When and why distribution-free and generative quantile models beat the industry standard for downside risk."

## The one-sentence thesis
A single measurable quantity — the local misspecification of the parametric conditional tail (post-GARCH residual kurtosis) — governs when distribution-free / generative quantile methods beat the industry-standard parametric VaR/ES; where that misspecification is high they win decisively and with statistical significance, where it is low the parametric model is as good or better, and generative (GBC) methods additionally deliver two things parametric models cannot: honest uncertainty on the risk number and likelihood-free calibration of intractable models.

## Five contributions (crisp)
1. The misspecification frontier — a live, measurable axis (post-GARCH residual excess kurtosis) that predicts, with Diebold-Mariano / Model Confidence Set significance, when nonparametric quantiles beat GARCH-t. Validated across four universes: CRSP US equities (top-decile +2.71%, DM 6.5), FX (hyperinflation tier pooled DM 4.1), 26 countries (developed->frontier, corr 0.53), 43 cross-asset instruments (corr 0.43).
2. An industry-standard-and-above risk engine — the residual-hybrid (GARCH vol x conditional residual quantile) + EVT tail + conformal recalibration: co-best with CAViaR in the Model Confidence Set, beats GARCH-t/FHS/EWMA/HS/GJR-skew-t with DM significance, best ES97.5 calibration, and the only model to pass Kupiec + Christoffersen at both 99% and 97.5%. Holds at the FRTB 10-day horizon and in the 2020/2022 stress window.
3. Honest uncertainty on VaR/ES — a generative / Gibbs posterior over the conditional (VaR, ES) with calibrated credible bands, which no standard model (GARCH, CAViaR, the hybrid) provides. Resolves Prof. Jiang's caution empirically: naive i.i.d. Gibbs under-covers (dependence -> effective sample size << n); the workhorse fix is block-bootstrap on GARCH residuals (calibrated for VaR and 2.5% ES, block~=iid confirming dependence is neutralized in residual space), with adaptive conformal for coverage under drift. Two supporting refinements, each stated with its caveat: an omega-calibrated Gibbs band (omega solved to match the block-bootstrap SD — inherits calibration by construction, a recipe not independent proof) and an EVT/POT interval for the sparse 99% ES tail (0.86->0.89, closer to nominal but within ~1 SE).
4. Likelihood-free calibration of intractable models — GBC recovers well-calibrated posteriors (SBC coverage ~ nominal) for Heston and rough-volatility (non-Markovian, no tractable likelihood) from a single price path, identifying vol-of-vol and roughness. The capability GARCH/MLE structurally cannot do.
5. A generative joint-tail sampler — one weight-input IQN that samples the predictive downside of any portfolio on the simplex, calibrated across weights (a representational contribution). Reported as a two-step arc: (a) a NAIVE generative sampler that must learn scale and shape jointly from summary state fails badly (PIT-KS 0.30, tail far too thin); (b) a covariance-ingesting HYBRID — DCC supplies the portfolio scale, the generative net learns only the shape of the standardized residual — restores calibration (PIT-KS 0.30->0.06, on par with a Gaussian copula) and is directionally better-calibrated in the 1% deep tail, most clearly on concentrated portfolios (top-name 1% breach 0.85% vs target 1% vs Gaussian's thin 1.8%). Hedge explicitly: the 1% comparison rests on ~10-11 tail events per weighting scheme, so it is suggestive-not-decisive and rides on the consistent direction across five schemes + 20 random draws, not any single number; at the moderate 5% tail a Gaussian is better (the hybrid is a touch conservative). Framing: not "GBC fails at multivariate" but "naive joint generation fails, the scale/shape split rescues calibration and points to a deep-tail edge under concentration."

## Section outline
1. Introduction — the gap (parametric VaR/ES mis-specifies the conditional tail in identifiable regimes; FRTB uses HS/FHS + ES97.5, not bare GARCH); the frontier thesis; contributions.
2. Background — VaR/ES, FRTB internal-models ES97.5 + exception backtests; GARCH/FHS/CAViaR/EVT; quantile regression; GBC (generative Bayesian computation); generalized Bayes / Gibbs posteriors (Jiang); adaptive conformal inference.
3. Methods — (3.1) residual-hybrid estimator (trees and neural IQN; EVT tail; conformal recal); (3.2) the GBC estimator proper (neural IQN generative quantile/transport map; amortization; likelihood-free posterior); (3.3) the misspecification score + regime gate; (3.4) generative posterior on (VaR, ES).
4. The misspecification frontier — the organizing empirical result across the four universes, with significance.
5. Beating the industry standard (FRTB) — full battery, ES97.5, Kupiec/Christoffersen at 99% & 97.5%, DM/MCS; 10-day + stress; ES-capital implications.
6. Honest uncertainty on the risk number — the generative/Gibbs posterior coverage result (the Jiang chapter).
7. Likelihood-free inference — Heston + rough-vol SBC; roughness/vol-of-vol recovery; SBC coverage.
8. Multivariate / generative joint tail — honest negatives for direct/neural co-crash (summary-feature joint generation and neural co-crash lose to DCC); then the covariance-ingesting scale/shape hybrid as the partial rescue (calibration restored, suggestive deep-tail edge under concentration, hedged on tail-event count). The arc IS the contribution: it localizes exactly where and why generation fails multivariate, and the recipe that fixes calibration.
9. Applications — FRTB capital efficiency; the misspecification-monitor product; trading regimes (crisis FX, vol indices, credit, frontier equities); scenario generation / stress testing via SBC.
10. Conclusion + limitations — trees >= neural on tabular; some credit/freight calibration gaps; intraday data-blocked; power was an artifact (corrected).

## Two-paper option (if one is too broad)
- Paper A (applied, finance/risk journal): contributions 1, 2, 5 (naive-negative + hybrid-rescue arc) + applications. "An industry-standard-and-above ES engine and the misspecification frontier."
- Paper B (methods/Bayesian, GBC thesis): contributions 3, 4 + the neural IQN + Jiang's Gibbs framing. "Generative Bayesian computation for honest downside-risk uncertainty and likelihood-free volatility calibration."
Recommended: develop as one broad paper first; split only if length forces it. Paper B is the one that most directly answers the thesis with Prof. Jiang.

## Honest framing rules (so reviewers can't sink it)
- The winning tabular estimator is gradient-boosted trees, not the neural net; call GBC the framework and report trees as the strongest estimator, with the neural IQN competitive after tail-aware training + monotone output.
- Residual kurtosis is necessary but not sufficient (carbon/CORN counterexamples; Baltic Dry wins at low kurtosis via limit-moves) — present the frontier as a strong regularity, not a law.
- Report the co-crash negatives and the electricity artifact correction explicitly; for the joint-sampler rescue, state the ~10-tail-event limitation up front rather than leaning on any single scheme's 1% number.
- The uncertainty chapter's headline is the block-bootstrap-on-residuals result; present omega-calibrated Gibbs and EVT ES as supporting refinements with their caveats (engineered SD-match; within-1-SE improvement), not as independent proofs.

## Target venues
- Finance/econometrics: Journal of Financial Econometrics, Journal of Banking & Finance, Quantitative Finance, Journal of Risk.
- Bayesian/methods: Bayesian Analysis (the GBC/Gibbs chapter), plus ML-for-finance workshops (NeurIPS/ICML).

## Open items to strengthen before submission
- Fix credit/freight independence-backtest failures; refit power correctly (done: it's GARCH's).
- WRDS 2000-2024 CRSP for a true 2008 stress window + expanding-split calm-vs-stress.
- Tail-aware neural IQN to close the tree gap on the headline table (v2 already narrowed it).
- Fissler-Ziegel joint (VaR, ES) scoring; MEU / certainty-equivalent-bps translation of the ES edge (Polson MEU machinery).
- Intraday/high-frequency needs a tick-data / exchange source (Bloomberg bdib stores ~1 day for the composite crypto tickers).
- Loss-in-the-exponent ablation for the Gibbs posterior (CRPS / tail-CRPS / Fissler-Ziegel / MEU).
