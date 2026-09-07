# Cover letter — Journal of Financial Econometrics (draft)

Dear Editors,

Please consider the enclosed manuscript, "Semiparametric Value-at-Risk and Expected Shortfall with a Real-Time Misspecification Score," for publication in the Journal of Financial Econometrics.

The paper asks when flexible-shape quantile methods actually improve on the parametric models that banks run, and answers with a measurable quantity: a real-time score built from the excess kurtosis and asymmetry of recent GARCH-standardized residuals. Where the score is high, an amortized nonparametric engine beats GARCH-t by 2.98% of pinball loss (per-date Diebold–Mariano 10.5) and by 12–14% on hyperinflation currencies; where it is low the advantage shrinks toward zero — the score orders the magnitude of the edge, and no cell shows a detectable loss. Three features of the evidence may interest your referees in particular. First, the design was frozen and its predictions written down in advance before we pulled an untouched 2000–2013 CRSP panel; the frontier replicated (top decile +0.9%, DM 2.2), and the paper reports its pre-committed failures with the same prominence as its wins — the ten-day horizon advantage, for example, is shown to be era-dependent. Second, the deployed engine passes Kupiec and Christoffersen backtests at both regulatory levels, per asset and under date clustering, through a test window spanning the 2008 crisis; its accuracy layer attains the lowest Fissler–Ziegel joint (VaR, ES) score at both regulatory levels on the full panel against GARCH-t, filtered historical simulation, and a score-driven GAS benchmark in the style of Patton, Ziegel, and Chen (2019); and the paper reports, rather than hides, the static conformal stage's joint-score concession at 2.5% — which its adaptive form removes. Third, one estimator amortized across hundreds of names replaces per-asset estimation and forecasts tail risk for new listings with no history (in its characteristics-only form), and is shown to be a precondition for the frontier result rather than a convenience: state-conditioning a single name's history collapses its effective sample and underperforms. Relative to the closest recent work in this journal (Jiang, Hu, and Yu 2022, on single-index expectile models; Luo, Xue, and Izzeldin 2025, on predictor selection for joint tail forecasting), the object here is different: not a new model or a new predictor set, but the observable state-dependence of relative model performance and a decomposition of its source.

The manuscript is not under consideration elsewhere, and the results have not been published previously. Following the journal's submission format, all tables and figures are collected at the end of the manuscript; the main text runs to approximately 43 double-spaced pages, so the compiled length reflects the end-collected floats and the reference list rather than the length of the text. A public replication package accompanies the paper; licensed data (CRSP, Bloomberg) are rebuilt from documented queries rather than redistributed. I have no conflicts of interest to declare.

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
- JFEC (OUP) submission via ScholarOne; single-blind (anonymization NOT required per JFEC General Instructions, so author block, acknowledgments, and the GitHub link stay). Prepare: title page with JEL codes (C14, C52, C58); abstract ≤ 100 words (JFEC house limit — current abstract is 99 words, compliant, no numerals); keywords (5, within the 2–6 limit); notes as endnotes (already set via \let\footnote\endnote, per the "footnotes at the end" rule); data availability statement (drafted in-paper); and the online appendix uploaded as a separate file. Manuscript is ~43 double-spaced text pages (within the "typically ≤ 40" soft cap); the compiled 58pp reflects endfloat collecting floats at the end — worth a one-line note to the editor so page count isn't misread.
- Sequential submission only: JFEC first; IJF re-skin (forecasting-first framing) if rejected. Never simultaneous.
- On acceptance: de-anonymize the repository link and mint the Zenodo DOI already stubbed in the data-availability section.
