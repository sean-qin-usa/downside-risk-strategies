---
title: "The Paper Split — a three-paper program"
subtitle: "Resolving gbc_downside_main.tex against the existing GRAFT-Q (IQN) paper"
date: "3 August 2026"
---

# The situation, stated plainly

You do not have one over-stuffed paper. You have **two overlapping manuscripts** that both stake a claim to the same core machinery:

- **`graftq_main_v2.tex` — GRAFT-Q** ("EVT Tails on a Neural Quantile Body"): a horizon-conditioned **implicit quantile network (IQN)** → **EVT tail graft** → **cross-sectional conformal** layer, on ~543 US single names, multi-horizon, calibration-focused, plus the **variance-risk-premium / crash-insurance economics** and a trading system. *This is the "original IQN paper."*
- **`gbc_downside_main.tex` — the downside paper**: a GARCH-residual → nonparametric-shape (GBM trees **or** IQN) → **EVT tail** → **conformal** engine, plus the misspecification frontier, the FRTB battery, honest-uncertainty (Gibbs) bands, likelihood-free SBC on Heston/rough-Bergomi, and a multivariate negative.

The overlap is not cosmetic: **both papers use IQN, both use an EVT graft, both use cross-sectional conformal.** If you submit them as-is to overlapping audiences, an editor will see two papers re-deriving the same method and reach for the salami-slicing / self-plagiarism objection. The split therefore has to be designed as a **coherent three-paper program with one clear owner for each piece of machinery**, not as an isolated cut of the downside paper.

# The answer to "what about the original IQN paper?"

**GRAFT-Q keeps the IQN.** It is the natural methods anchor: it is built around the neural quantile surface, it names and defines the EVT-graft-with-splice-continuity, it defines the cross-sectional conformal layer, and it carries the economic payload (the P–Q crash-premium result) that gives it a thesis no other paper duplicates. So:

- The neural **IQN estimator**, **horizon conditioning**, the **EVT graft**, and the **cross-sectional conformal** layer are **owned by GRAFT-Q**. The other two papers *cite* GRAFT-Q for these and never re-derive them as novel.
- The downside paper's methods section stops presenting IQN/EVT/conformal as its own contribution. Paper A uses **GBM trees** as its estimator (which it already argues are the better *point* estimator anyway), so it depends on the shared machinery only through a citation. Paper B uses the IQN as an amortized *posterior* map — a genuinely different use — and cites GRAFT-Q/Polson for the estimator while claiming only the likelihood-free application.

That single decision removes the double-claim and lets all three papers stand on distinct estimands.

# The three-paper program

## Paper 1 — GRAFT-Q (already drafted; the IQN paper)

Keep essentially as is; it is the most finished and has the sharpest single thesis.

- **Thesis:** a calibrated neural quantile *term structure* for single-name equities, whose left-tail miscalibration is an **informational** ceiling (not architectural) repaired by an EVT graft, and which — precisely *because* it forecasts the physical measure well — exposes that model-timed crash insurance still loses money (the P–Q put-wing premium).
- **Owns:** IQN-in-finance, horizon conditioning, EVT graft + splice continuity, cross-sectional conformal, VRP/crash economics, the trading system.
- **Target:** Journal of Financial Econometrics or Journal of Empirical Finance (the economics gives it more reach than a pure forecasting venue).
- **Action:** minor — align notation/citations with Papers A/B; make it the explicit methods reference the others point to. Consider trimming the trading appendix to a companion note if a referee finds it distracting.

## Paper A — the frontier + deployable engine (from the downside split)

The strongest, most novel empirical contribution in the downside manuscript.

- **Working title:** *"When does flexible-shape beat GARCH? The misspecification frontier and a deployable ≥-industry-standard engine."*
- **Thesis:** the nonparametric edge over GARCH-*t* is **not universal** — it is a thin, *ex-ante predictable* frontier (top-decile local misspecification, turbulent-vol regimes, and cold-start), and a GARCH-residual → tree-shape → EVT → conformal engine plus a live misspecification *meter* captures it while never underperforming the FRTB industry standard.
- **Estimator:** **GBM trees** (best point accuracy, no GPU). IQN mentioned once, cited to GRAFT-Q, as the sampling alternative.
- **Pulls from `gbc_downside_main.tex`:** Background/industry benchmark (§2), the tree half of Methods (§3), the **misspecification frontier** (§4, incl. within-universe + cross-country), the **FRTB battery** (§5), the **amortized cold-start / transfer** results (currently inside §3), and Applications (§9).
- **Theory kept:** the **regret-identity lemma** (it *organizes* the frontier: regret is quadratic in the quantile wedge, so the edge must concentrate where the wedge is largest) and the **tail-wedge proposition** (why kurtosis misspecification creates that wedge). Conformal proposition → cite GRAFT-Q. Sampler lemma → not needed here.
- **Target:** International Journal of Forecasting or JFEC.

## Paper B — likelihood-free inference & honest uncertainty (from the downside split)

The "GBC-core" thesis paper — the direction the project has been pushing toward.

- **Working title:** *"Honest uncertainty for intractable volatility models: amortized quantile posteriors, simulation-based calibration, and where they fail."*
- **Thesis:** generative/amortized quantile inference yields **well-calibrated posteriors** for stochastic-volatility models that MLE/GARCH cannot (rough-volatility Hurst recovery especially), validated by SBC — **but** on real *multivariate* returns the generative joint sampler fails honestly (DCC wins). A map of where likelihood-free inference earns its keep in finance and where it does not.
- **Pulls from `gbc_downside_main.tex`:** Honest-uncertainty / Gibbs (§6, incl. the 1.6× raw-return overconfidence that residual space repairs), Likelihood-free / SBC (§7, Heston + rough-Bergomi, the Hurst info-gain and SBC coverage, and the negative generative joint sampler), and the multivariate-tail negative (§8).
- **Estimator:** IQN as the amortized posterior map, **cited** to GRAFT-Q/Polson; the contribution is the likelihood-free *application* + the SBC audit + the honesty diagnostics, not the estimator.
- **Theory kept:** the **generative-sampler lemma** (validity of inverse-transform sampling from the fitted quantile map — the object SBC consumes). Gibbs/generalized-posterior construction stays as method.
- **Target:** Bayesian Analysis, Journal of Computational & Graphical Statistics, or Quantitative Finance.

# Method-ownership map (the de-confliction table)

| Machinery / result | Owner | The other papers |
|---|---|---|
| IQN estimator + horizon conditioning | **GRAFT-Q** | A cites (uses trees); B cites (uses as posterior map) |
| EVT tail graft + splice continuity | **GRAFT-Q** | A cites, reports only cross-asset regulatory use |
| Cross-sectional conformal layer + validity proof | **GRAFT-Q** | A cites |
| Misspecification frontier score + results | **Paper A** | — |
| FRTB battery (MCS, Kupiec, Christoffersen) | **Paper A** | — |
| Amortized cold-start / transfer | **Paper A** | B may reference the amortization idea |
| Regret identity + tail-wedge propositions | **Paper A** | — |
| Gibbs honest-uncertainty + 1.6× diagnostic | **Paper B** | — |
| SBC + Heston/rough-Bergomi + Hurst recovery | **Paper B** | — |
| Multivariate negative (DCC wins) | **Paper B** | — |
| Generative-sampler lemma | **Paper B** | GRAFT-Q may reference |
| VRP / crash economics + trading system | **GRAFT-Q** | — |

Every cell has exactly one owner; every other appearance is a citation. That is what defeats the salami objection.

# Where the Appendix B proofs go

The four proofs I expanded now distribute cleanly: **regret identity + tail wedge → Paper A** (they underwrite the frontier); **split-conformal validity → GRAFT-Q** (it owns conformal); **generative sampler → Paper B** (it underwrites SBC). The crossover remark and its fix travel with the tail-wedge into Paper A. The EVT continuity fix travels with the graft into GRAFT-Q.

# The one strategic choice for you

The only real fork is **Paper B's home**:

1. **Recommended — Paper B stands alone** (3-paper program). It has a distinct estimand (parameter inference for stochastic-vol models), a distinct venue (Bayesian/comp-stats), and a distinct audience. Folding it elsewhere would mix an equity-*forecasting* paper with a stochastic-vol-*inference* paper.
2. **Alternative — fold Paper B into GRAFT-Q.** GRAFT-Q already frames itself against the Polson GBC baseline and uses IQN, so the SBC/rough-vol material is thematically adjacent. Downside: GRAFT-Q is already long (it carries a trading appendix), and the estimands differ; the result would be a sprawling paper with the same focus problem you are trying to escape. I recommend against it.

Unless you say otherwise, I will assume the **3-paper program**.

# Migration checklist (keyed to `gbc_downside_main.tex`)

To generate the two new skeletons from the current file:

- **→ Paper A:** §1 Introduction (re-scoped to the frontier thesis), §2 Background/benchmark (1196), §3 Methods *trees half* + cold-start (376–1195, dropping the IQN derivation to a cited paragraph), §4 Frontier (1196), §5 FRTB (1431), §9 Applications (1879); Appendix proofs = regret + wedge; Glossary subset.
- **→ Paper B:** §6 Honest uncertainty (1590), §7 Likelihood-free/SBC (1745), §8 Multivariate (1811); Appendix proof = sampler; the Gibbs posterior machinery from §3.7 (posterior methods); Glossary subset.
- **→ GRAFT-Q (already there):** no migration; receives the conformal proof and becomes the cited methods anchor. Add one paragraph in each of A and B: "the neural estimator, EVT graft, and conformal layer are developed in [GRAFT-Q]; here we [use trees / use it as a posterior map]."
- **Shared front-matter both new papers need:** the pinball-loss/notation subsection (§3.1), the industry-model nesting paragraph, and the walk-forward/purge/embargo protocol — these are common and can be stated compactly in each with a cross-reference.

# Bottom line

Keep GRAFT-Q as the IQN paper and the methods anchor. Split the downside manuscript into **Paper A** (the frontier + cold-start + FRTB, trees, → IJF/JFEC) and **Paper B** (likelihood-free SBC + honest uncertainty + multivariate negative, → Bayesian Analysis/JCGS/QF). One owner per piece of machinery, everyone else cites. Three sharp papers, zero double-claims, and each with a single sentence you can point a referee to.
