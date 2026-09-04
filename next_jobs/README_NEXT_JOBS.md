# next_jobs — queued compute jobs for the paper's registered next steps
Created 2026-07-21. These implement §9 of the Jul 6–20 Jiang memo. The
sandbox VM was unavailable, so none of these have been executed — they are
written to run on the host (Bloomberg box) or ai2 (ssh steveqin@ai2),
following the project convention: each job reads clearly-documented
inputs, writes a single result JSON, and prints a summary table.

| Script | Registered next step | Input needed | Where to run |
|---|---|---|---|
| next_fz_scoring.py | Fissler–Ziegel joint (VaR,ES) scoring + DM across the FRTB battery | per-observation forecast export from frtb_bench.py (see header) | ai2 |
| next_gibbs_loss_ablation.py | loss-in-the-exponent ablation (pinball / tail-pinball / CRPS / FZ) for the Gibbs posterior | GARCH-standardized residual panel CSV | ai2 or host |
| next_indep_repair.py | credit/freight Christoffersen independence repair (breach-responsive tail) | per-date forecast/return series for IG OAS + Baltic Dry | host (Bloomberg) |
| next_roughvol_leverage.py | leverage summary statistic to identify ρ in Heston/rough-vol SBC | patch for heston_sbc.py / roughvol_sbc.py on ai2 | ai2 (GPU) |

WRDS items (2000–2024 CRSP for the 2008 stress window; OptionMetrics
spreads) are data requests, not scripts — see DATA_NEEDS.md.

IMPORTANT: every script has a "VERIFY BEFORE RUN" block at the top listing
the assumptions about input file layout. Nothing in these files has been
validated against the real data — check column names against your exports
before queueing.
