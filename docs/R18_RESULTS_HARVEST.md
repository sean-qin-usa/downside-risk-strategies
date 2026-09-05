# Review #18 host-rerun harvest (verified, not assumed)

## [FATAL #1] Causal decile rule -- causal_frontier_results.json (200 names, 221.6k rows, 11-tau accuracy engine)
- A global qcut (shipped):   top +2.964%  DM 10.12  (bottom -0.17%, DM -1.12; overall +0.341%, DM 5.09)
- B expanding prior-only 90th-pct threshold (as-deployed, 250-date burn-in):
      top +2.45%  DM 8.28   (n_defined 171.6k; overall_defined +0.34%, DM 4.37)
- C within-date cross-sectional decile (NOT deployed): top +0.259%  DM 2.17
- overlap A_top vs B_top = 0.862   (86% of top-decile membership unchanged under causal cutoff)
- overlap A_top vs C_top = 0.10
VERDICT: headline survives a strictly causal cutoff. Score inputs already causal (.shift(1)); only
look-ahead was the threshold, and past-only threshold reproduces it (86% overlap, +2.45%/DM 8.3).
Within-date (C) weak because it forces 10% daily occupancy incl calm cross-sections -> frontier is about
ABSOLUTE misspecification level, not within-day rank. Consistent w/ point-in-time universe (+2.94/DM 6.6).
Engine note: this panel uses the 11-tau FZ0 accuracy engine, so A=+2.96% here vs +2.46% pooled in
fig:frontier (standalone-frontier convention); the A-vs-B-vs-C comparison is within one engine.

## [MAJOR #4] MCS elimination-rule fix -- frtb_table_results.json (140 names, 155k rows, 1108 dates)
Corrected rule: worst = argmax_i max_j (means_i-means_j)/sqrt(var_ij)  [HLN standardized range]
- best_model = resid_hybrid_ML (avg pinball 0.3551)
- MCS_90 = {resid_hybrid_ML}  SOLE SURVIVOR  (UNCHANGED from old argmax(means) rule)
- all 8 others eliminated at p=0.0
- DM vs best: garch_t 4.92, gjr_skewt 4.95, fhs 6.05, fhs_pername 5.13, fhs_roll500 5.70,
  hybrid_EVT 6.20, hist_sim 7.52, ewma_rm 8.64
- pooled Kupiec99 p: fhs 0.79 (pass), gjr_skewt 0.0617 (pass at 99%), garch_t 0.026,
  resid_hybrid_ML 0.0 (raw, over-breaches -> WHY EVT tail exists), hybrid_EVT 0.0003
VERDICT: correctness fix; sole-survivor conclusion UNCHANGED. Old raw-mean rule coincided w/ standardized
order because models are well separated. Fold in as honest repro fix, claim stands.
