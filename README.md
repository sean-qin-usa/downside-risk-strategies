# Downside-risk research working repository

Working repository for "Semiparametric Value-at-Risk and Expected Shortfall with a Real-Time Misspecification Score" (Sean Qin, submitted to the *Journal of Financial Econometrics*, September 2026) and for the wider research program it grew out of. The replication package that the manuscript cites is the separate repository [downside-risk-paper](https://github.com/sean-qin-usa/downside-risk-paper); this one holds the job scripts, result files, drafts and notes behind it.

## The paper

The current manuscript is `paper/jfec/paper_A_jfec.pdf`, in the journal's review format, double spaced with endnotes and with the tables and figures collected at the end under "[Table N about here]" markers. The online appendix is `paper/jfec/paper_A_jfec_online_appendix.pdf`. LaTeX sources and `refs_v3.bib` sit beside them; the figures are drawn in pgfplots inside the source, so the two `.tex` files and the bibliography are all a build needs.

The version under review is tagged `r32-submitted`. The text in the repository is ahead of it, and every change since then is recorded sentence by sentence in `docs/paper/CHANGE_LEDGER_R34.md`. The revisions add a same-rows comparison against standalone McNeil-Frey GARCH-EVT, per name and with a pooled tail (Sections 1.2, 4.1 and 5.1, Figure 2 and a new online appendix section, from `code/paper/job_garch_evt.py`); re-score every model in the comparison set on the same 221,600 test rows with the Giacomini-White conditional predictive ability regression, Murphy diagrams, the Engle-Manganelli dynamic quantile test and a 90% model confidence set (`code/paper/job_bench_all.py`, online appendix); restate equation (5) and Stages 3 to 4 in the order the code runs them, with the GPD estimator named and two symbol collisions removed; report Christoffersen conditional coverage at 97.5% as well as 99%; and commit a result file for the residual-hybrid annual-refit walk-forward. None of the post-submission runs moved a number in the submitted tables by more than rounding, and the frontier results replicate against every benchmark added since. Standalone GARCH-EVT shows no frontier and loses to the estimator in the top decile and on the joint score, the conditional-predictive-ability regression and the Murphy diagrams confirm the ordering, and the point-in-time, calendar-split and annual-refit checks stand. One claim was narrowed rather than strengthened. The abstract's joint (VaR, ES) sentence is now stated against GARCH-t and FHS, because on the full comparison set GJR-GARCH-skew-t at both levels and the Taylor model at 2.5% are within noise of the estimator.

## What the paper finds

A score built from the excess kurtosis and asymmetry of recent GARCH-standardized residuals predicts when a flexible-shape quantile estimator improves on a parametric VaR/ES model. In the top score decile the pooled gradient-boosted estimator beats GARCH-t by 3.0% of pinball loss (DM 10.5), and the pattern holds on an untouched 2000 to 2013 panel under a frozen specification, under strict calendar splits, under an annual-refit walk-forward, and in a point-in-time universe that keeps delisted names. Outside the top decile the advantage shrinks toward zero and no region shows a loss.

Measured against a jump-robust GARCH that caps how far one shock propagates into the variance, the top-decile edge falls to between 0.3% and 0.5% (DM 2.5 to 4.7). Most of the advantage is therefore the standard filter's post-shock scale error; the part that survives a robust scale is conditional-shape information. The estimator passes the date-clustered exception tests at both regulatory levels through the 2008 window, and on the full panel its accuracy layer has a lower joint (VaR, ES) FZ0 score than GARCH-t and every FHS variant at both levels. On the full comparison set it is within noise of GJR-GARCH-skew-t at both levels and of the Taylor ES-CAViaR model at 2.5%; on pinball, SAV-CAViaR shows the same frontier and ties the estimator in every score region.

## Layout

| Location | Contents |
|---|---|
| `paper/jfec/` | Manuscript, online appendix, bibliography, cover letter, SSRN abstract, generated table bodies (`tables/`) |
| `paper/archive_pdfs/`, `paper/drive_upload/` | Dated builds, including the pair uploaded to Drive on September 5 |
| `paper/` (other files) | Earlier drafts of this paper and the two companion papers (`gbc_downside_main.tex`, `graftq_main_v2.tex`, `paper_B_likelihoodfree.tex`) |
| `code/paper/` | The scripts behind this paper: frontier, FRTB battery, holdouts, benchmarks, table generators, `toy_example.py` |
| `code/amortization/` | The amortization and IQN study (one pooled fit across names, transfer to unseen names, age curve) |
| `code/gbc/` | Gibbs and generative posterior work, simulation-based calibration (paper B) |
| `code/strategies/` | Option-selling backtests, execution studies, signal generation, the crash section of the GRAFT-Q draft |
| `code/data/` | WRDS and TAQ pulls, realized-measure builds, delisting merges, inspection and diagnostic scripts |
| `results/<group>/` | Result files as JSON, one per script run, grouped the same way as `code/`. The numbers in the paper come from `results/paper/` |
| `docs/paper/` | Change ledger, adversarial review rounds, journal requirements, submission notes, cover letter |
| `docs/strategies/`, `docs/program/` | Strategy catalogue and specs; memos and research directions for the program as a whole |
| `figures/` | Exported charts from the strategy side |
| `tools/edits/` | The edit scripts for the ledgered text revisions (`r34_*`, `r36_*`, `r38_*`, `r40_*`) |
| `tools/bats/`, `tools/sync/` | Runner helpers and the earlier PowerShell sync scripts; `tools/strip_claude_trailers.pl` is the commit-message filter |
| `autojobs/`, `ai2jobs/`, `auto_runner.bat`, `START_RUNNER_CLICK_ME.bat` | The batch runner. `auto_runner.bat` executes each `.bat` dropped in `autojobs/` and moves it to `autojobs/done/`; `ai2jobs/` holds the jobs that ran on the ai2 GPU host |
| `live_paper/`, `forward_signals/`, `next_jobs/`, `competitions/`, `logs/` | Live-trading paper trade, forward signal records, queued jobs, forecasting competition entries (M5, GEFCom), run logs |

Job scripts take the project root from the `GBC_PROJ` (or `GBC_PROJECT_DIR`) environment variable and default to the Windows working folder; they write their result JSON there, and the file is moved into `results/<group>/` when it is committed. Table bodies are regenerated with `python code/paper/make_tables_garch_evt.py` and `python code/paper/make_tables_bench_all.py`.

## Scripts behind the tables

| Script | Result file | Used for |
|---|---|---|
| `code/paper/frtb_table_canonical.py` | `results/paper/frtb_table_results.json` | The twelve-level FRTB battery with exact tail-integral ES (Table 3) |
| `code/paper/job_composite.py` | `results/paper/composite_holdout_results.json` | The score frontier on the 200-name panel (Table 1) |
| `code/paper/job_fz_fullpanel.py` | `results/paper/fz_fullpanel_results.json` | Full-panel FZ0 joint loss (Figure 2) |
| `code/paper/job_fz_strict_calibration.py` | `results/paper/fz_strict_calibration_results.json` | Strict-split conformal and FZ audit with the matched-information GARCH control |
| `code/paper/frtb_stress_exact.py`, `code/paper/job_stress_dm.py` | `results/paper/stress_es_results.json` | Ten-day sections in both eras with the boundary purge |
| `code/paper/job_wrds_holdout.py` | `results/paper/holdout_frontier_results.json` | The 2000 to 2013 holdout under the frozen specification (Figure 1) |
| `code/paper/job_pit_universe.py` | `results/paper/pit_universe_results.json` | Point-in-time universe with delisting returns |
| `code/paper/job_calendar_split.py`, `code/paper/job_walkforward.py` | `results/paper/calendar_split_results.json`, `results/paper/walkforward_results.json` | Calendar splits and the annual-refit walk-forward |
| `code/paper/job_nurel.py`, `code/paper/job_mechanism.py` | `results/paper/nurel_results.json`, `results/paper/mechanism_results.json` | The nu-relative score and the Fama-MacBeth mechanism test |
| `code/paper/job_coherent.py` | `results/paper/coherent_results.json` | Monotonized curve audit and ES as the integral of the same curve |
| `code/paper/job_frontier_robust.py` | `results/paper/frontier_robust_results.json` | The jump-robust GARCH decomposition of the top-decile edge (Section 4): the frontier rebuilt on a bounded-news filter at three- and four-sigma caps |
| `code/paper/job_scaleshape_canonical.py` | `results/paper/scaleshape_canonical_results.json` | Realized-variance scale decomposition on large caps |
| `code/paper/job_pzc_taylor.py` | `results/paper/pzc_taylor_results.json` | GAS-FZ and ES-CAViaR benchmarks |
| `code/paper/job_perasset_v2.py` | `results/paper/perasset_v2_results.json` | Per-asset exception tests at 99% and 97.5% |
| `code/paper/job_garch_evt.py`, `code/paper/job_holdout_garch_evt.py` | `results/paper/garch_evt_results.json`, `results/paper/holdout_garch_evt_results.json` | McNeil-Frey GARCH-EVT on the same rows, design era and holdout |
| `code/paper/job_bench_all.py` | `results/paper/bench_all_results.json` | Every benchmark on the same rows: pinball frontier, FZ0, CPA, DQ, Murphy, model confidence sets (online appendix Tables OA.10 to OA.12) |
| `code/paper/job_walkforward_hybrid.py` | `results/paper/walkforward_hybrid_results.json` | Residual-hybrid annual refit |

Superseded implementations are kept in the history and removed from the working tree. `code/paper/frtb_bench.py` records its own correction history in the header. `code/paper/toy_example.py` runs the whole pipeline on synthetic data and needs no licensed input.

## Data

Returns come from CRSP through WRDS and from Bloomberg under the author's licenses and are not redistributed; no data file is tracked. The WRDS panels rebuild from the queries documented in the scripts for any subscriber. The Bloomberg exhibits are kept as run, since terminal access ended in mid-2026.
