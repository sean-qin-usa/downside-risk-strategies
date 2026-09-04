# Cover letter — Journal of Financial Econometrics (draft)

Dear Editors,

Please consider the enclosed manuscript, "Downside Risk at the Misspecification Frontier: A Real-Time Score for When Nonparametric Models Beat Industry-Standard VaR and ES," for publication in the Journal of Financial Econometrics.

The paper asks when flexible-shape quantile methods actually improve on the parametric models that banks run, and answers with a measurable quantity: a real-time score built from the excess kurtosis and asymmetry of recent GARCH-standardized residuals. Where the score is high, an amortized nonparametric engine beats GARCH-t by 2.7% of pinball loss (per-date Diebold–Mariano 6.5) and by 12–14% on hyperinflation currencies; where it is low, the two are statistically indistinguishable. Three features of the evidence may interest your referees in particular. First, the design was frozen and its predictions registered before we pulled an untouched 2000–2013 CRSP panel; the frontier replicated (top decile +0.9%, DM 2.2), and the paper reports its registered failures with the same prominence as its wins — the ten-day horizon advantage, for example, is shown to be era-dependent. Second, the deployed engine passes Kupiec and Christoffersen backtests at both regulatory levels, per asset and under date clustering, through a test window spanning the 2008 crisis; its accuracy layer attains the lowest Fissler–Ziegel joint (VaR, ES) score at both regulatory levels on the full panel against GARCH-t, filtered historical simulation, and a score-driven GAS benchmark in the style of Patton, Ziegel, and Chen (2019); and the paper prices, rather than hides, the conformal stage's joint-score concession at 2.5%. Third, one estimator amortized across hundreds of names replaces per-asset estimation, prices new listings with no history, and is shown to be a precondition for the frontier result rather than a convenience: state-conditioning a single name's history collapses its effective sample and underperforms.

The manuscript is not under consideration elsewhere, and the results have not been published previously. A public replication package accompanies the paper; licensed data (CRSP, Bloomberg) are rebuilt from documented queries rather than redistributed. I have no conflicts of interest to declare.

Thank you for your consideration.

Sincerely,
Sean Qin

---

## Suggested referees (working list — verify current affiliations before submission)

- Andrew J. Patton (Duke) — dynamic semiparametric (VaR, ES) models; forecast evaluation. The paper benchmarks against and extends his FZ-loss framework.
- Johanna F. Ziegel (ETH Zurich) — elicitability and joint scoring of risk measures; directly relevant to the FZ0 evaluation design.
- Simone Manganelli (ECB) — CAViaR; the paper's strongest academic rival model and a natural evaluator of the comparison.
- Kevin Sheppard (Oxford) — volatility modeling, MCS/bootstrap inference software and methodology.
- Dacheng Xiu (Chicago Booth) — machine learning in asset pricing and volatility; speaks to the amortized-learner contribution.

Names to consider excluding (conflicts): none known.

## Notes for submission mechanics
- JFEC (OUP) submission via ScholarOne; single-blind. Prepare: title page with JEL codes (C14, C22, C52, C58, G17, G28), abstract ≤ 150 words (current abstract may need trimming to house limit — check), data availability statement (already drafted in-paper), and the online appendix as a separate file.
- Sequential submission only: JFEC first; IJF re-skin (forecasting-first framing) if rejected. Never simultaneous.
- On acceptance: de-anonymize the repository link and mint the Zenodo DOI already stubbed in the data-availability section.
