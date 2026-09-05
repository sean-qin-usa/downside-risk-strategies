# Adversarial Triage — Round 14 (Review #19: REJECT -> MAJOR REVISION)

The reviewer downgraded from reject to major revision and explicitly withdrew the
three leakage/selection attacks (common-calendar, causal cutoff, annual walk-forward
all preserve the top decile; Romano-Wolf + Holm now in the appendix). "The central
numerical frontier is no longer the vulnerable part." Remaining case: over-claimed
mechanism + package-integrity bugs. All verified against artifacts; fixed win-or-lose.

## Mechanism (the #1 ask) -- experiment run, result goes AGAINST our prior claim

[#1] "The score reads departure from the fitted law, not raw tail mass." REFUTED by a
discriminating test (job_mechanism.py, mechanism_results.json). The nu-relative
normalization is 0.971-correlated with raw kurtosis (82.5% top-decile overlap), so it
cannot separate the hypotheses; the discriminating tests settle it against model-relative:
- Fama-MacBeth (edge on z(raw)+z(nurel), within-date): raw t=+7.8, nurel t=-5.2 (negative
  incremental content controlling for raw).
- Double-sort: within the top raw-kurt quintile the edge FALLS with nu, +1.9% (fat-tailed
  low-nu) -> +1.5% (thin-tailed) -- opposite of the model-relative prediction.
- Discordant: top-raw-not-nurel +1.23% (DM 4.4, sig); top-nurel-not-raw +0.35% (DM 0.5, NS).
Rewrote the paragraph to report this straight: the frontier is the absolute level of recent
tail activity, not departure from the fitted law; normalizing by nu adds nothing. Frontier
itself untouched.

[#2/#9/#14] Narrowed/de-verdicted in both builds: "shape not staleness" -> annual refit
removes the aggregate gap (overall +0.32%, DM 0.8, NOT detectable) but not the conditional
concentration, so staleness is not necessary (not "shape identified"); "economic argument
for adoption" -> proper-score reductions, not monetary welfare; deleted the punchline
verdicts (crisis/leakage, names-that-die, asymmetric-in-capability, cheap-while-it-waits).

## Package lock (the #2 ask) -- all fixed

[#4] frtb_caviar.py MCS elimination argmax(means) -> HLN standardized range. Rerun:
90% MCS = {hybrid_GBM, caviar_sav} -- "contains exactly these two" CONFIRMED; DM caviar
0.59 -> 0.4 (p 0.28 -> 0.34), reconciled in both builds + OA winloss table.
[#5] Production ES recipe: "ES from the GPD closed form below the splice" -> "VaR and ES
both read from the coherent min-envelope curve Q* (VaR at the alpha node, ES its numerical
tail integral)" in the reading-copy production box AND the OA production loop.
[#6] Kupiec text 81% -> 84% (canonical passrate99 = 0.843; matches the figure); Christoffersen
86% left (not disputed).
[#13] OA byline: Sean Qin -> Sean Qin and Wenxin Jiang.
[#3] "pre-registered" (my own R18 multiplicity sentence) -> "specified before the run";
consistent with the paper's stated position that no third-party registry exists.

## Not done this pass (flagged for the revision, lower-ranked)
[#7] GAS is a single-start Nelder-Mead; already demoted to "indicative only" (R18). A robust
multi-start ES-CAViaR/PZC battery is a revision-scale addition; SAV-CAViaR already provides
the strong semiparametric comparator (the co-best tie). [#8] point-in-time drops 36/200; the
prose now states the estimand is the 164 that clear the fitting floors, but full 36-name
characteristics + intention-to-treat bounds are future work.

## Status
Both builds compile clean, no undefined refs; JFEC body ends p41 (within limit); reading copy
39pp; OA 16pp. code/frtb_caviar.py fixed, job_mechanism.py added, results regenerated.
