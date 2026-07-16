# Research Directions v2 — Model Improvements, Theory, and New Questions

*Sean Qin · GBC Downside-Risk Project · 2026-07-03*
*Companion to RESEARCH_DIRECTIONS.md (the five applied directions: amortization, self-aware model, multivariate, HF crypto, MEU). This memo covers the theory side: polishing the IQN/GBC itself, the multivariate/dimensionality problem, the Gibbs posterior (origins → finance), and broadening beyond tail risk.*

---

## 1. Polishing the IQN/GBC (the "not that polished" critique)

The critique is fair: our IQN is a plain MLP with uniform-τ pinball loss, post-hoc rearrangement, and hand-tuned hyperparameters. Each of these has a known better answer in the literature. Roughly in order of payoff-per-effort:

**1.1 Non-crossing by construction, not by rearrangement.**
Monotone rearrangement (Chernozhukov et al. 2010) fixes crossing after the fact, but a network that is *monotone in τ by architecture* is cleaner and trains better: parameterize Q(τ|x) = Q(τ₀|x) + ∫ softplus(g_θ(s,x)) ds, or use the incremental-quantile trick (predict the τ₀ quantile plus nonnegative increments). This removes a reviewer objection and an entire post-processing step. Low effort, real polish.

**1.2 Learned τ-proposals instead of uniform τ (FQF-style).**
Our tail-weighted mixture G_λ is a hand-designed answer to "where should the network spend capacity on the τ axis?" The Fully-parameterized Quantile Function line (Yang et al. 2019, successor to IQN in the RL literature) *learns* where to place the τ probes. A middle ground: keep fixed λ for evaluation honesty but learn the tail-mixture shape on a validation split inside each window.

**1.3 Hybrid IQN body + EVT tail.**
The IQN is data-starved exactly where we care most (τ > 0.99). Splice: IQN for τ ∈ (0, 0.95], GPD tail extrapolation (McNeil–Frey style) beyond, with the splice point and GPD parameters conditioned on x (the network can output ξ(x), β(x)). This directly targets the known EVT-POT blow-up bug and the far-tail weakness, and it's a *methodological contribution*: "conditionally-parameterized EVT tails on a neural quantile body" is publishable on its own.

**1.4 The two levers already identified in the capstone.**
(a) Signed-shock / leverage feature — the entire EGARCH win came from asymmetry; give the IQN the same information (lagged signed return, r⁻ₜ = min(rₜ,0), or the EGARCH news-impact term itself). (b) GARCH-residual IQN done cleanly — let GARCH model the scale, IQN model the standardized shape. These are the cheapest possible tests of "was the loss architectural or informational."

**1.5 Epistemic uncertainty on the network itself.**
The proposal's honest disclaimer — we model aleatoric but not epistemic uncertainty — can be *fixed* rather than disclaimed: deep ensembles (we already run them for the confidence signal; promote them to the predictive distribution via ensemble-mixed quantiles), or a Bayesian last layer. This also strengthens the self-aware-model story: disagreement is then a principled posterior quantity, not a heuristic.

**1.6 Conformal calibration wrapper.**
Adaptive conformal inference (Gibbs & Candès 2021) on top of the IQN gives *finite-sample* coverage guarantees online, even under distribution shift — the strongest possible answer to "is it calibrated under stress?" and it composes with any of the above. Cheap, and referee-proof.

**1.7 Training-budget honesty.**
The K=3 vs K=5 artifact in the capstone shows results are sensitive to compute budget. Polish = a documented, fixed training protocol (epochs, early stopping, seeds, warm-start rule) with an ablation table. Boring but this is most of what "polished" means to a referee.

---

## 2. Multivariate / dimensionality: the real open problem

**Why it's hard:** pinball loss has no vector analogue because ℝᵏ has no total order. Everything univariate about IQN breaks at k > 1. Three routes, increasing ambition:

**2.1 Amortize over portfolio weights (the cheap, clever route).**
We don't need the full k-dimensional law — we need the loss distribution of *portfolios*. So learn Q(τ | xₜ, w) with the weight vector w as an input, training over randomly sampled weights each batch. One network then prices the downside of *every* portfolio on the simplex, which implicitly encodes the dependence structure that matters (tail co-movement shows up as: quantiles of concentrated w's don't diversify away). This sidesteps optimal transport entirely, reuses our exact machinery, and the evaluation is unchanged (each w gives a univariate loss series). It also connects directly to the amortization study already underway — same trick, different conditioning variable. **This is the direction I'd lead with.**

**2.2 Marginals + copula factorization.**
IQN marginals per asset (or per sleeve) + a parametric/nonparametric copula on the PIT-transformed residuals, refit per window. Interpretable ("which pairs crash together"), modular, and the IQN's PIT outputs are exactly the copula's inputs — the architecture is already half-built. Weakness: copula choice is its own misspecification risk; the honest version compares 2–3 copulas.

**2.3 True vector quantiles via optimal transport.**
Carlier–Chernozhukov–Galichon vector quantile regression defines the conditional quantile as a monotone (gradient-of-convex) transport map from Uniform([0,1]ᵏ) to Y|x; neural versions parameterize the map as the gradient of an input-convex neural network (Pegoraro et al. 2024; conditional generative quantile networks via OT). This is the principled generalization of the IQN — literally "IQN where τ becomes a vector" — and it is Polson's own stated future direction for GBC. High effort, genuinely novel in the finance application (joint crash structure, contagion), thesis-chapter scale. Note the Gibbs-posterior world has its own multivariate quantile answer via geometric quantiles (Bhattacharya & Martin 2022), which gives a theory hook connecting this to Prof. Jiang's framework.

Dimensionality within the univariate model is the same theme smaller: block-PCA already won (~30% CRPS); the next steps are supervised dimension reduction (train the projection end-to-end as the network's first layer with an orthogonality penalty) vs. the current unsupervised PCA — an ablation that tests whether *learned* summaries beat *fixed* ones, which is exactly the "sufficient summary statistics" question in Polson's GBC papers.

---

## 3. The Gibbs posterior: where it came from, what it's for, how to push it

**3.1 Original usage (the answer to your question).**
Jiang & Tanner (2008, *Annals of Statistics*): "Gibbs posterior for variable selection in high-dimensional classification and data mining." The object is π(θ) ∝ exp{−n·η·R̂ₙ(θ)}·prior(θ), where R̂ₙ is an *empirical risk* (there: classification error), not a negative log-likelihood. The motivation was **robustness to model misspecification**: the ordinary Bayesian posterior is only trustworthy if the likelihood is right, whereas the Gibbs posterior concentrates on the *risk minimizer* regardless of the true data-generating process. Original setting: i.i.d.-style classification with K ≫ n candidate variables, statistical-mechanics roots (hence "Gibbs"), MCMC implementation. So: **not econometrics and not finance — statistical learning theory / data mining.** The parallel econometrics lineage is Chernozhukov & Hong (2003), "An MCMC Approach to Classical Estimation": the same exp(−criterion) object built from GMM/minimum-distance objectives ("Laplace-type estimators") — that's how the idea entered econometrics. The two lines have since merged into the "generalized Bayes" literature.

**3.2 What we've already done with it.**
Our capstone's online model averaging — weights ∝ exp(−η·trailing CRPS) — is a Gibbs posterior over *model space* rather than parameter space, updated online. It won the tournament (CRPS 0.7430 vs EGARCH 0.7436). That's currently our best result and it is *directly* in the Jiang lineage, which makes it the natural centerpiece to deepen.

**3.3 The open problem that adapting it to finance exposes: η with dependent, nonstationary data.**
Everything in the Jiang–Tanner theory (and most of the calibration literature since) assumes i.i.d. or exchangeable data. Financial returns are neither: dependent (mixing), heavy-tailed, and regime-switching. Concretely researchable gaps, all empirical-first but each with a theory hook for Prof. Jiang:

- **η calibration under dependence.** Syring & Martin's Generalized Posterior Calibration tunes η by bootstrap so credible sets attain frequentist coverage — but the bootstrap must respect serial dependence (block/stationary bootstrap). "GPC with block bootstrap for time-series risk functionals" is, as far as I found, unexplored. This is a well-posed, publishable question and squarely in the mentor's wheelhouse.
- **Time-varying / state-dependent η.** In our ensemble, η controls how aggressively weights chase recent performance. A fixed η is wrong across regimes: calm markets favor slow adaptation, crises favor fast. Making η(xₜ) state-dependent (or learning it online, e.g. by running a small Gibbs posterior *over η itself*) turns the capstone hack into a method. The online-learning literature (exponential weights / Hedge, Vovk's aggregating algorithm) gives regret bounds for exactly this weighting scheme — connecting Gibbs-posterior averaging to prediction-with-expert-advice guarantees would be a genuinely nice theory bridge, and regret bounds hold *without* i.i.d. assumptions, which is precisely what finance needs.
- **Which risk in the exponent?** We used trailing CRPS. Alternatives change what the posterior "believes in": tail-weighted CRPS (weights chase tail skill), joint VaR–ES scores (Fissler–Ziegel — the only elicitable pair, and Basel-relevant), or utility-based loss (ties to the MEU direction). An ablation over the exponent's loss function is cheap and no one has done it in this setting.
- **Gibbs posterior directly on the risk functional.** Syring–Hong–Martin (2019) already build a Gibbs posterior *on VaR itself* — inference on the quantile with credible intervals, no likelihood. Extending that from unconditional VaR to *conditional* VaR (our setting), and from VaR to (VaR, ES) jointly, would put honest uncertainty bands on our risk forecasts — something none of our current models (IQN included) provide. This may be the single best "further the hypothesis" project: it fuses the mentor's framework with our exact application, and Bhattacharya & Martin's multivariate-quantile Gibbs posterior extends it toward direction 2.3.

**3.4 Finance vs. econometrics, sharpened.** In econometrics the Gibbs posterior is mostly a *computational device* (Chernozhukov–Hong: MCMC to avoid optimizing nasty objectives) or a *robustness device* (Jiang–Tanner: misspecification). In finance the pitch is different and stronger: the loss function in the exponent can be the *economically correct* one (CRPS, tail loss, regulatory capital, utility) — so the posterior concentrates on the model/parameter that is best *for the decision you face*, not best-fitting. "Decision-aligned posteriors for risk management" is a framing that doesn't exist yet as a paper and covers everything in 3.3.

---

## 4. Beyond tail risk — and what GBC was originally for

**Original focus:** GBC (Polson & Sokolov, "Generative AI for Bayesian Computation" 2023; MEU paper 2024; GP-surrogate paper 2026) was never about tail risk. It's a general *likelihood-free posterior sampler*: train a quantile network on simulated (θ, y) pairs so that feeding it uniforms yields posterior draws — an ABC replacement. Their showcase applications were simulation-based inference (epidemic models, satellite drag, traffic), decision theory (maximum expected utility as a quantile marginal), and surrogates for expensive computer experiments. **Tail risk was *our* application, not theirs.** So broadening isn't drift — it's returning the tool to its native generality with finance-shaped problems:

- **Full-distribution objects we already produce but don't use.** The trained IQN gives the whole conditional law, so anything that is a functional of it is free: Expected Shortfall term structures, probability of k%-drawdown, upside/downside asymmetry (Q(0.9)+Q(0.1) skew measures), option-style payoff pricing E[f(L)] by averaging f over τ-draws. One model, many outputs — a "conditional distribution engine," with tail risk as one consumer.
- **True simulation-based GBC in finance (closest to Polson's original).** Calibrate a structural model with intractable likelihood — Heston/rough-volatility, Hawkes order-flow, agent-based models — by simulating (θ, price-path features) pairs and training the IQN to sample the posterior over θ. This is *literally* the original GBC use-case, applied where finance genuinely lacks likelihoods. It would also fix our data-scarcity complaint: simulated training pairs are unlimited (your Polson point from the proposal review).
- **Decision layer / MEU.** Portfolio choice or capital allocation where the expected utility is computed as a quantile marginal (Polson–Ruggeri–Sokolov 2024). Converts "0.1% CRPS edge" into basis points of certainty-equivalent return — the industry-credible metric.
- **Anything with a conditional distribution and pinball-scorable outcome:** realized-volatility distributions (not just points), credit spread changes, funding-rate distributions in crypto, order-flow imbalance. The machinery transfers unchanged; the question is where the *conditional shape* (not just scale) carries economic information — the daily study suggests shape-learning pays exactly where classical scale models are misspecified.

---

## 5. Recommended portfolio (what I'd actually pitch to Prof. Jiang)

Three tracks, orthogonal risks, all reusing existing infrastructure:

1. **Model track (polish + win):** 1.4 leverage feature + 1.1 monotone architecture + 1.3 EVT tail splice, evaluated on the existing pipeline; then HF crypto where the data advantage flips. Goal: a *decisive* standalone IQN result somewhere.
2. **Theory track (the Jiang paper):** Gibbs posterior for conditional (VaR, ES) with η calibrated under dependence (block-bootstrap GPC) + state-dependent η in the online ensemble, significance-tested. Goal: turn the capstone's winning hack into the paper's methodological core. This is the strongest thesis-chapter candidate because it's mentor-aligned and no one has done it.
3. **Breadth track (GBC as it was meant):** amortized-over-weights portfolio quantiles (2.1) as the pragmatic multivariate answer, and one simulation-based-inference demo (rough-vol calibration) to show the Bayesian half of GBC working in finance. Goal: reframe from "a tail-risk model" to "a conditional-distribution engine for finance."

Key references: Jiang & Tanner (2008, AoS) · Chernozhukov & Hong (2003, J. Econometrics) · Syring & Martin (2019+, GPC; 2019 SSRN Gibbs-VaR with Hong) · Bhattacharya & Martin (2022, multivariate quantiles) · Martin & Syring (2022, direct Gibbs on risk minimizers) · Polson & Sokolov (2023 Generative AI for Bayesian Computation; 2024 MEU; 2026 GP-surrogate) · Carlier–Chernozhukov–Galichon (VQR) · Yang et al. (2019, FQF) · Gibbs & Candès (2021, adaptive conformal) · Fissler & Ziegel (2016, elicitability of (VaR,ES)).
