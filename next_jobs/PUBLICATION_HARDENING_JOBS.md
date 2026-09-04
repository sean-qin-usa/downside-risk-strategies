# Publication-hardening job queue (created 2026-07-28)
Empirical runs needed to take Paper 1 to referee-proof. All are re-scoring /
re-runs of EXISTING pipelines — no new modeling. Run on host or ai2 (data in
C:\GBC_data; note 172 scripts still hardcode old Desktop path).

## J1 — FZ joint (VaR,ES) re-scoring of the FRTB battery  [highest priority]
Registered in paper (Sec. limitations). Score every battery model with the
FZ0 loss (Fissler–Ziegel) at (1%, 2.5%); re-run DM tests on FZ0 differences.
CAUTION: fz-and-gibbs-ablation memory records a past FZ0 SIGN BUG — reuse the
audited scorer, not a fresh implementation. Output: drop-in rows for
tab:frtb + one new table.

## J2 — Fill the "---" cells in tab:frtb
ES97.5 pred/realized, Breach99, Kupiec99 for GJR-skew-t, EWMA, HS. Same eval
harness, same 140-name/155k-obs panel. Paper currently flags these as "not
recorded in archived runs".

## J3 — Multiple-testing control
Romano–Wolf (or extend MCS) stepdown p-values for all pairwise headline DM
claims (battery + frontier deciles). Report alongside raw DM.

## J4 — 2008 stress window
Blocked on WRDS 2000–2024 CRSP request (registered). When data lands: re-run
battery + frontier on 2007–2009 window.

## J5 — Figure audit
Recompute the numbers behind all 7 pgfplots figures from results parquets;
diff vs hardcoded coordinates in gbc_downside_main.tex. (Pipeline diagram
fig:pipeline is schematic — exempt.)

## J6 — GPC upgrade of the Gibbs bands (feeds the continuation paper too)
Full Syring–Martin GPC iteration with moving-block bootstrap inner loop on
GARCH residuals at α=1%, 2.5%; compare coverage vs the one-step SD-matching
rule (paper reports 0.953–0.967). Also needed as the empirical seed of the
Gibbs continuation paper (see RESEARCH_IDEAS_BACKLOG.md).

## J7 — Code availability package
Freeze run configs (layer sizes, lr, seeds, walk-forward dates) into a
CONFIGS.md + zip the eval harness; paper's "reported with the code release"
promise points here.

## Paper 2 queue (parallel)
P1: regenerate the six fig_*.pdf from run artifacts (currently placeholders
in compiled PDF). P2: reconstruct refs_v2.bib (compiled with refs_v3
substitute). P3: OptionMetrics measured-cost columns (registered). P4:
delisting tails. P5: live-holdout first report (running since Jul 2026).
