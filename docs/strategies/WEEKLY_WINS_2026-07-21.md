# GBC Project — Week Summary & Presentation Guide
Date: July 21, 2026 (addendum July 24) · Covers: full project state through the paper-canonicalization pass

## Addendum (Jul 22–24): papers finalized and canonicalized
- **Canonical Drive home for both papers**: GBC root → "Papers — CANONICAL (GBC broad + GRAFT-Q)" — polished tex for both papers, both bibliographies, portfolio map, and Paper 2's four chart exhibits. Everything outside this folder is superseded drafts.
- **Coverage audit closed**: every significant result from the whole project is now in a paper (last two gaps fixed: the Gibbs model-average win → Paper 1 §6; cold-start-in-practice → Paper 1 §9 Applications + abstract billing for amortization).
- **Paper 2 exhibits are real charts, chosen by inspection**: cumulative-PnL timelines (timing overlay + exact stored timed series, 1996–2026) and the switcher operating dashboard including the trade-volume timeline (350→550 positions/month) and rolling win rate. Eleven candidate charts rejected — pure-VRP books or charts contradicting paper numbers.
- **Full-document readability pass** on both papers: every technical term glossed at first use (MCS, DM, Kupiec/Christoffersen, FHS, CAViaR, EVT/GPD, conformal, Gibbs posterior, SBC, Hurst/rough vol, DCC, PIT, VRP, P-vs-Q, …) so a PM, statistician, or ML researcher reads end-to-end without leaving the page.
- **Two queued jobs have since RUN** (results to fold into Paper 1 next pass): Fissler–Ziegel joint (VaR, ES) scoring — fat tails are strictly necessary (normal-innovation models lose with DM≈6), fat-tailed models tie on large caps, hybrid+EVT directionally best on high-kurtosis names; and the Gibbs loss-in-the-exponent ablation — the exponent must be the pinball loss (an expectile loss mis-centers the posterior; coverage collapses to 0.1–0.4). Both strengthen Paper 1 §5/§6.
- Remaining mechanical steps: Overleaf recompile of both (Paper 2 needs its 4 PNGs uploaded alongside — pq_timing_overlay, pq_exact_timing, pq_model_stability, trading_dashboard2, all in the local GBC Project folder); credit/freight repair + leverage-ρ jobs still queued.
Audience: Sean — what to present, in what order, with exact numbers.

## The one-slide story

**A single live score — the excess kurtosis/asymmetry of recent GARCH residuals — predicts when distribution-free quantile models beat the industry standard. Where it's high they win big and significantly; elsewhere the parametric model holds. An engine built on that principle beats everything banks run under FRTB rules, and the generative version adds two things no bank model has: calibrated uncertainty on the risk number, and posteriors for models with no likelihood.**

## Present in this order (win → number → significance)

1. **The misspecification frontier** (the intellectual core). Top decile of the residual-shape score: **+2.71%** pinball edge, DM 6.54, p≈0; bottom decile +0.19%, not significant — exactly the predicted pattern. Same axis works across four universes: hyperinflation FX **+12–14%** (tier-pooled DM 4.1), frontier equity indices 4 significant wins (corr 0.53 with kurtosis), 13/43 cross-asset wins (corr 0.43). Killer control: Korea's 2026 crash — GARCH wins all 23 assets because a *price* crash isn't *residual* misspecification.
2. **The FRTB engine** (the product). Residual-hybrid + EVT tail + conformal: beats GARCH-t/FHS/EWMA/HS/GJR-skew-t with DM 4.4–8.3; co-best with CAViaR (say this plainly — it buys credibility); **the only entrant passing exception tests at both levels**.
3. **The capital number** (for practitioners this is the headline). FHS and GARCH-t **over-state ES97.5 by 8–11%** — direct capital over-charge — while the hybrid is nearly exact (−5.80 pred vs −5.76 realized). At the FRTB 10-day horizon GARCH √h-scaling over-states worse (−19.4 vs −15.4) and the edge grows to +1.4%.
4. **Rough-vol likelihood-free posterior** (the "only GBC can do this" moment). Recovers the Hurst roughness H from one 252-day path: **42% of prior uncertainty removed, SBC coverage 0.91** — calibrated, for a model with no tractable likelihood. Heston same story (vol-of-vol info-gain 36.5%).
5. **Honest uncertainty on (VaR, ES)**. Naive Gibbs on raw returns is **1.6× overconfident** (measured); on GARCH residuals honesty returns (0.79); block bootstrap + EVT interval deliver 0.89–0.95 coverage vs 0.90 target. Plus the free screen: ensemble disagreement correlates +0.11 with the model's own error.
6. **The negatives — present them, they're the credibility engine.** GJR-GARCH-t beats our net 4.5–6.2% on single-name equity (retired the bogus −38%); DCC wins equity co-crash three ways (but our scale/shape hybrid fixes the deep 1% tail: Gaussian ~2× too many breaches, hybrid on target); a learned regime gate adds exactly 0.0%; hierarchical blends hurt; electricity "win" was an artifact; Korea control above.

## Supporting wins (mention if asked)
Amortized transfer beats own-history at every age (+6–10% young; benchmark is own EWMA-t/empirical, not full GARCH); cold-start it's the only option; transfer win rate 59–79%; M5 external benchmark SPL 0.269. Hourly crypto: IQN beats the full ladder (~0.6%, DM p<1e-7) — the frequency dimension of the frontier. Edge ×4 calm→turbulent quintile, both nonparametric models win every quintile. VIX: clean calibrated win (DM 1.74, passes both Christoffersen levels).

## Paper status (both on Drive; portfolio map in PAPER_PORTFOLIO.md)
- **Paper 1 — "When and Why Distribution-Free and Generative Quantile Models Beat the Industry Standard"**: full draft, compiled on Overleaf, 18pp, 0 errors, native TikZ figures, 57-entry bib, finance-standard format + JEL. Today: absorbed all remaining orphan results (hourly crypto, ensemble signal, M5, transfer rate, detector latency) + full future-directions program. Needs: one recompile, Table 2 width fix.
- **Paper 2 — GRAFT-Q v2 (revised scope)**: trading section now model-driven strategies only (P–Q wedge signal, GARCH×IQN switcher SR 1.1–1.16 with the best crisis profile, switcher-book Kelly table, model-timed crash-insurance negative −1.7%/mo t=−1.9). Pure-VRP books (master book SR 1.44 etc.) moved out to the separate trading report. Same-rows GJR audit added; companion cross-references in.

## Future directions (registered in Paper 1's conclusion; scripts queued in next_jobs/)
Ready to run (scripts written, need host/ai2): Fissler–Ziegel joint scoring + MEU capital translation; loss-in-the-exponent ablation (incl. the bounded-influence score — the Bernstein-relevant arm); credit/freight independence repair; leverage summary for ρ. Data-blocked: WRDS 2000–2024 (2008 stress window), tick data (intraday frontier). Next modeling targets: Hawkes/jump-diffusion SBC; vector quantile regression for the multivariate tail. Live forward holdout continues logging weekly.

## One-line honesty rules if challenged
Trees, not the neural net, are the best tabular estimator (the net earns its place by sampling and likelihood-free inference — and is competitive after the tail-aware fix, 0.3638 vs 0.3632). Kurtosis is necessary-not-sufficient (carbon/corn). Credit/freight accuracy edges (52%/15%) have unresolved breach clustering — don't claim them as wins.
