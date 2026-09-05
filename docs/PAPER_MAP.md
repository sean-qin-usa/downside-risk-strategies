# The paper in plain language — section by section

One sentence for the whole thing: **banks model risk with a formula that assumes
the shape of surprise returns is fixed; we built a model that learns the shape
from data across hundreds of stocks at once, showed it beats what banks run,
and — the real contribution — built a live score that tells you when learning
the shape matters and when it doesn't.**

| § | What it does | Why it's there |
|---|---|---|
| Abstract + 1. Introduction | States the three results (amortization, the engine, the frontier) and, before anything else, the honest scope: on ~90% of days the engine merely ties the standard model; the payoff is concentrated. | A referee's first suspicion is overclaiming. The intro leads with the tie so the concentrated win is credible. |
| 1.1 Contributions | Three numbered claims with their section homes. | Standard econometrics-paper furniture; lets a referee check the paper delivers exactly what it lists. |
| 2. Related work | Positions against GARCH-family econometrics, ML quantile methods, GBC, CAViaR/GAS, conformal prediction. States plainly: trees are what we deploy; GBC is the framework lineage; the IQN is a benchmark. | Answers "what's new vs. Polson–Sokolov, Engle, Patton" before it's asked. |
| 3. Methods (the engine) | The four-stage pipeline: GARCH scale filter → one pooled gradient-boosted residual-quantile model (trained once across all names) → extreme-value tail beyond the data → optional conformal coverage overlay. Proposition 1 (conformal validity) is stated as motivation, with its assumptions' failure in time series disclosed. | Each stage fixes a measured failure of the previous one; the section proves the engine is engineering, not alchemy. |
| 3.3 Amortization/ablation | Shows one pooled fit transfers to unseen names, beats own-history models at every listing age, and prices day-one IPOs; ablations show which features carry it. | This is the "no per-asset model can do this" capability claim. |
| 4. The misspecification score | Defines the score (excess kurtosis + asymmetry + jump indicator of recent GARCH residuals), its timing (strictly lagged), and the simulation showing when the score should NOT work. | The paper's theory piece: a measurable quantity that predicts the ML edge. The negative simulation is armor against "you'd find this anywhere." |
| 5. The frontier (US equities) | The 3×10 decile grid: the edge concentrates in the top score decile (+2.7%, DM 6.5), ~7× the calm region; Romano–Wolf keeps 9/30 cells; gating/switching is shown to add nothing. | The headline empirical result, with multiplicity priced and the "why not switch models daily" question closed. |
| 5.x Leakage & holdout | Strict calendar splits, annual walk-forward, the frozen-spec 2000–2013 holdout with predictions written in advance, point-in-time universe with delistings, recursive real-time threshold. | The reviewer-proof core: every look-ahead objection answered by construction, not assertion. |
| 5.y Across universes | FX (crisis-tier pooled DM 4.12), country indices, cross-asset; Holm over all 93 instrument looks (7 real survivors); Korea 2026 as negative control. | Shows the score travels, prices the breadth of the search, and shows a crash without shape-break is correctly a GARCH win. |
| 6. FRTB battery | The engine vs everything banks run + CAViaR/GAS on one panel: lowest joint VaR/ES score at both levels for the accuracy layer, exception tests pass date-clustered through 2008, conformal overlay's cost quantified, strict-calibration audit, ten-day direct extension (not the engine) with era caveat. | The "would this survive a risk desk" section; every concession (CAViaR tie, static-overlay cost, per-name heterogeneity) is printed, not hidden. |
| 7. Applications | Model-risk monitor, cold-start pricing for new listings. | What a desk does with it on Monday. |
| 8. Conclusion + limitations | Restates the frontier reading and lists what's unresolved (credit/freight calibration, intraday, trees-vs-IQN). | Ends on the discipline point: day-level model-switching is mostly noise. |
| Online Appendix | Algorithms, supplementary figures/tables (incl. the Holm table OA.3), the two-regime simulation, proofs. | Everything a referee needs but the page limit excludes. |

**The logic chain to check:** (1) fixed-shape assumption is sometimes locally
wrong → (2) a lagged, observable score measures how wrong → (3) where the score
is high, a pooled learned shape beats the fixed one, decisively and
replicably → (4) where it's low, no harm done → (5) so deploy the engine
everywhere and read the score as a risk monitor. Every section serves one link.
