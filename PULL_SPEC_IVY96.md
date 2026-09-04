# IvyDB 1996+ Re-Pull Spec — Crash-Premium Asset-Pricing Paper

*2026-08-06. Pre-registered pull design (filters pinned before any return is computed, per TUNING_GRID_PREREG convention). Entitlements verified 2026-08-06: optionm_all (full 1996–), CRSP + wrdsapps_link_crsp_optionm, comp_na_daily_all, TAQ-msec.*

## Design goals
1. **Survivorship-free cross-sectional universe** — all optionable US common stocks 1996–2025, not the current ticker list. Universe defined by the OptionMetrics–CRSP link, filtered to CRSP shrcd 10/11, exchcd 1/2/3.
2. **Both flags, full delta range** — calls and puts, |δ| ∈ [0.02, 0.98]. The old pull (2005+, puts only, δ −0.45..−0.03) was self-imposed.
3. **Monthly formation-date snapshots, not full daily panels** — Goyal–Saretto/Cao–Han convention: portfolios formed on the first trading day after the standard (3rd-Friday) expiry, holding next-month-expiry contracts. Cuts volume ~21× vs daily; daily paths for *held* contracts are a deferred stage-2 pull (needed only for delta-hedged variants; hold-to-expiry P&L needs entry quote + CRSP terminal price).
4. **Resumable, per-year, gzip CSV** — same conventions as `wrds_pull_run2.py` (skip-if-exists, pgpass auth, host-side).

## Tables and filters (pinned)

| Stage | Table | Filter | Purpose |
|---|---|---|---|
| A1 | `optionm.securd` | all US | secid master |
| A2 | `wrdsapps.opcrsphist` | all | secid→permno link (score ≤ 2 kept) |
| A3 | `crsp.dsenames` | shrcd 10/11, exchcd 1/2/3 | common-stock filter |
| B | `optionm.opprcd{yr}` 1996–2025 | date ∈ formation dates; DTE 15–50; cp_flag both; δ: puts [−0.98,−0.02], calls [0.02,0.98]; best_bid ≥ 0 | formation snapshots |
| C | `optionm.stdopd{yr}` 1996–2025 | days ∈ {10,30,60,91}, both flags | Q-surface / Q−P wedge |
| D | `crsp.dsf` + `crsp.dsedelist` | permnos in universe | returns, terminal prices, delisting returns |
| E | `optionm.zerocd` | all | risk-free curve |
| F | `optionm.distrd` | universe secids | dividends/splits (option-return adjustment) |
| G | `comp.fundq` (rdq) via ccmxpf_lnkhist | universe | earnings dates |

Formation dates: first trading day strictly after the 3rd Friday of each month, from the `crsp.dsi` calendar (computed in-script, not hardcoded).

## Quality screens (applied at load, not in SQL — keep raw pull unfiltered beyond the above)
Standard OptionMetrics hygiene, recorded here so the paper can cite one place: drop bid = 0 or bid ≥ offer; drop mid < $0.125; drop nonstandard settlement (`ss_flag` ≠ 0); moneyness/arbitrage violations flagged not dropped; volume/OI kept as columns for liquidity subsetting, never as a pre-filter.

## Size guardrails
Snapshot pull ≈ 12 dates/yr × 0.3–1.5M rows ≈ 4–18M rows/yr → ~0.2–1 GB/yr gzip. Full 30-yr pull ~10–20 GB → **write to `C:\GBC_data\data\wrds\ivy96\`** (C: was full — verify free space or point OUT at the BOX mount used by chain-archive).

## Explicitly deferred (stage 2)
Daily quote paths for held contracts (delta-hedged returns); TAQ realized variance; call-side skew-harvest legs pre-2005.

## Script
`wrds_pull_ivy96.py` — host-side, resumable. Run: `python wrds_pull_ivy96.py` (uses pgpass; ~hours, per-year progress printed).
