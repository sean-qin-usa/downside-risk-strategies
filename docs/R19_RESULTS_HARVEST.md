# Review #19 host-rerun harvest (verified, folded in win-or-lose)

## [R19 #1 MAJOR] Mechanism identification -- mechanism_results.json (200 names, 221.6k rows)
The reviewer's central question, answered with a DISCRIMINATING test. Result goes AGAINST the paper's prior claim.
- Spearman(raw mk63, nu-relative) = 0.971 ; top-decile overlap = 0.825 (reproduces reviewer)
- edge top raw   = +2.98% (DM 10.5) ; edge top nu-relative = +3.01% (DM 8.6)  [rank-preserving, cannot separate]
- Fama-MacBeth (within-date cross-sectional, edge on z(raw)+z(nurel)):
      beta_raw   = +0.00655  t = +7.76
      beta_nurel = -0.00239  t = -5.23   <-- nu-relative has NEGATIVE incremental content controlling for raw
- Double-sort edge% [raw-kurt quintile rows x fitted-nu quintile cols]: within top raw quintile (rawQ4),
      edge FALLS with nu: 1.90 (nuQ0 fat-tailed) -> 1.46 (nuQ4 thin-tailed) -- OPPOSITE of model-relative prediction
- Discordant: top-raw-not-nurel edge = +1.23% (DM 4.36, significant); top-nurel-not-raw = +0.35% (DM 0.52, NS)
VERDICT: the predictive content is RAW tail activity, NOT model-relative (nu-adjusted) misspecification.
Paper's "the score reads departure from the fitted law, not raw tail mass" is REFUTED and has been rewritten
to report this straight. The frontier itself is untouched (raw score still predicts the edge, +2.7% DM 6.5).

## [R19 #4 MAJOR] CAViaR-extension MCS -- frtb_caviar_results.json (90 names, 99.7k rows), corrected rule
- Fixed frtb_caviar.py:131 worst=argmax(means) -> HLN standardized range (same as frtb_table).
- Rerun: 90% MCS = {hybrid_GBM, caviar_sav}  -- "contains exactly these two" CONFIRMED under corrected rule.
- pinball: caviar_sav 0.3461, hybrid_GBM 0.3460 (matches paper); DM caviar_sav vs best = 0.4 (p=0.34).
  Paper's "DM 0.59, p=0.28" -> updated to "DM 0.4, p=0.34" (main text x2 + OA winloss table).
VERDICT: correctness fix; co-best-with-CAViaR conclusion unchanged; DM reconciled to canonical run.
