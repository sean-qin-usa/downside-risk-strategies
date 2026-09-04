# Max-adversarial review prompt (paste into any strong LLM; enable browsing or attach the PDFs)

Files: main paper https://github.com/sean-qin-usa/downside-risk-paper/raw/main/paper_A_frontier.pdf · online appendix https://github.com/sean-qin-usa/downside-risk-paper/raw/main/paper_A_online_appendix.tex · code and results https://github.com/sean-qin-usa/downside-risk-paper

---

You are the most hostile competent referee the Journal of Financial Econometrics could assign to this manuscript: a financial econometrician who knows the VaR/ES evaluation literature cold (Diebold-Mariano, Hansen's SPA and MCS, Kupiec/Christoffersen, Fissler-Ziegel elicitability, Patton-Ziegel-Chen, CAViaR, realized-measure models) and who believes ML-in-finance papers are usually data-snooped. Your goal is to construct the strongest possible case for rejection. You are not balanced. You are not fair. You are technically rigorous — every attack must be correct econometrics, and an attack that misreads the paper counts against you.

Read the full paper (title: "Semiparametric Value-at-Risk and Expected Shortfall with a Real-Time Misspecification Score," sole author, 2026). If you can browse, also inspect the repository's code and results files and use anything you find there against the manuscript.

Attack at least these surfaces, and anything else you see. For each attack, quote the exact sentence, number, table, or equation you are attacking.

1. Inference. Validity of the per-date Diebold-Mariano aggregation under cross-sectional dependence; the Newey-West lag choices; one-sided testing conventions; the SPA and MCS implementations; multiple testing across three signals, ten deciles, four universes, and dozens of instruments — compute an honest sense of the true familywise error, and say what survives it.
2. The "registered" holdout. Registration is claimed but self-administered — no OSF or third-party timestamp. Attack the evidentiary value. Also attack the holdout design itself: the era choice, the top-200-by-market-cap selection (which differs from the design panel's deepest-histories selection), the >=3000-observation filter's survivorship, and whether "untouched era" can be verified by anyone but the author.
3. Leakage channels the paper does not discuss. Per-name 60/40 chronological splits put different names' train and test windows on overlapping calendar dates: one name's training data shares market factors with another name's test data. Does the pooled learner therefore see the test era's common shocks in training? Is the conformal exchangeability assumption defensible in a panel? Does the GARCH variance recursion filtered through the full history leak anything the text hand-waves?
4. Benchmark quality. Is plain GARCH(1,1)-t the right parametric champion in 2026, or a soft target? Where are HAR-RV and Realized GARCH? Is the paper's own Nelder-Mead-fitted one-factor GAS a strawman version of Patton-Ziegel-Chen, and would a properly estimated implementation close the gap? Is the FHS implementation the version desks actually run?
5. Economic size. The headline average edge is a fraction of a percent of pinball loss. Make the strongest case that this is statistically significant noise trading at zero economic value once any friction is considered, and that the capital-translation section is arithmetic dressed as economics.
6. Novelty. Against Zhang, Zhang, Cucuringu and Qian (JFEC 2024, ML volatility forecasting with intraday commonality), Patton-Ziegel-Chen (2019), the CAViaR line, and the global-vs-local forecasting literature (amortization = global models, long known in the M-competitions): what exactly is new? Argue the misspecification score is repackaged conditional kurtosis — a known predictor — with branding.
7. Internal consistency. Hunt for numbers that disagree across the abstract, the summary table, the text, and the appendix; claims whose stated test does not support their stated strength ("consistent with nominal," "replicates," "passes"); and any place where the honest-sounding limitations section quietly contradicts a headline.
8. Fit. Make the case that this is an applied ML paper for a data-science outlet, not a financial econometrics paper: the theory is one lemma and two propositions, and the contribution is engineering. Then make the opposite case only if you must concede it.
9. Reproducibility. Licensed data are not shipped; rebuild scripts require subscriptions. Attack what a referee can actually verify versus must take on faith, including every number whose provenance is a JSON in the author's own repository.
10. Anything in the prose that reads as overclaiming, circularity, or AI-generated filler despite the disclosed AI assistance.

Output, in order, no preamble:
A. REJECTION CASE — your referee report's summary paragraph, written to convince the editor to reject.
B. RANKED ATTACKS — every attack, most damaging first, each as: [FATAL / MAJOR / MINOR] — quoted target — the technical argument in 2-5 sentences — what specific new evidence or analysis would fully refute it.
C. THE ONE QUESTION — the single question you would ask in a referee report that you believe the author cannot answer.
D. VERDICT — desk reject / reject / major revision / minor revision, with the three changes that would most raise the paper's odds if the author could make them.

Do not summarize the paper. Do not praise it. Do not hedge. If an attack fails when you check it carefully, discard it — quality over count.
