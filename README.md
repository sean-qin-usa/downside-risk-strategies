# Semiparametric Value-at-Risk and Expected Shortfall with a Real-Time Misspecification Score

## The paper

The manuscript is [`submission/paper_A_jfec.pdf`](submission/paper_A_jfec.pdf) — the version prepared for the *Journal of Financial Econometrics* (double-spaced, endnotes, floats collected at the end with "[Table N about here]" markers, as the journal's review format requires). Its LaTeX source is [`submission/paper_A_jfec.tex`](submission/paper_A_jfec.tex) and the bibliography is [`refs_v3.bib`](refs_v3.bib).

| File | What it is |
|---|---|
| [`submission/paper_A_jfec.pdf`](submission/paper_A_jfec.pdf) | The manuscript, in journal review format. |
| [`submission/paper_A_jfec_online_appendix.pdf`](submission/paper_A_jfec_online_appendix.pdf) | Online appendix (algorithms, supplementary figures and tables, and proofs deferred from the main text). |
| [`docs/gbc_downside_main.pdf`](docs/gbc_downside_main.pdf) | A convenience copy of the current submission PDF, kept in `docs/` for quick reference. |

An earlier single-spaced reading build (`paper_A_frontier.*`) has been retired: it predated the reframing of the paper and no longer matched the submission in either its numbers or its front matter. The submission build above is now the single source of truth; the retired build remains in the repository history for anyone who needs it.

## Revisions since the September 7 submission

The manuscript in this repository is ahead of the version under review (R32, commit `25266fb`). The changes, each ledgered sentence by sentence in [`docs/CHANGE_LEDGER_R34.md`](docs/CHANGE_LEDGER_R34.md), are: a same-rows comparison against standalone McNeil-Frey GARCH-EVT, per name and with a pooled tail (Sections 1.2, 4.1 and 5.1, Figure 2, and a new Online Appendix section; `job_garch_evt.py`); every model in the comparison set re-scored on the identical 221,600 test rows with the Giacomini-White conditional-predictive-ability regression, Murphy diagrams, the Engle-Manganelli dynamic quantile test and a 90% Model Confidence Set (`job_bench_all.py`, Online Appendix); equation (5) and Stages 3 to 4 restated in the order the code runs them, with the GPD estimator named and the symbol collisions removed; Christoffersen conditional coverage reported at 97.5% as well as 99%; and a committed result file for the residual-hybrid annual-refit walk-forward. No number in the submitted tables changed by more than rounding.

## What the paper shows

A single measurable quantity — the excess kurtosis and asymmetry of recent GARCH-standardized residuals — orders when flexible-shape quantile methods beat parametric VaR/ES. Where the score is high, an amortized nonparametric estimator wins decisively (top decile +3.0% pinball, DM 10.5; replicated on an untouched 2000–2013 holdout under a frozen specification with predictions written in advance, under strict calendar splits, under a true annual-refit walk-forward, and in a point-in-time universe that keeps delisted names); where it is low the advantage shrinks toward zero. The score orders the magnitude of the edge, which is concentrated in the top decile, never a detectable loss.

The paper's central result is a decomposition of that top-decile edge. Measured against a jump-robust GARCH that does not overstate its variance after a single large shock, the +3.0% edge falls to roughly +0.3% to +0.5% (DM 2.5 to 4.7), so most of the advantage is the standard filter's post-shock scale error and a smaller but statistically significant part is conditional-shape value that a robust scale does not remove. The estimator passes the aggregate date-clustered exception tests at both regulatory levels through a 2008-crisis window, and its accuracy layer attains the lowest joint (VaR, ES) FZ0 score against GARCH-t and FHS at both levels on the full panel.

## Repository layout

| Location | Contents |
|---|---|
| `submission/` | Journal-format build and online appendix (see `submission/README.md`) |
| `refs_v3.bib` | Bibliography |
| `code/` | Analysis scripts. Every number in the paper traces to one script here; each script documents its data inputs at the top |
| `results/` | Derived statistics as JSON — one file per script run; these are the numbers quoted in the paper |
| `docs/` | Research notes, review syntheses, cover letter, and a convenience copy of the submission PDF |
| `figures/` | Exported charts |

### Canonical script → result pairs (the ones the paper's tables cite)

| Script | Output | Feeds |
|---|---|---|
| `code/frtb_table.py` | `results/frtb_table_results.json` | Table 6 (battery, exact tail-integral ES) |
| `code/frtb_stress_exact.py` | `results/stress_es_results.json` | Ten-day sections, both eras (boundary-purged; `code/job_stress_dm.py` adds the stored out-of-era edge and DM) |
| `code/job_wrds_holdout.py` | `results/holdout_frontier_results.json` | Untouched-era holdout (frozen spec; its header carries the written-in-advance predictions) |
| `code/job_fz_strict_calibration.py` | `results/fz_strict_calibration_results.json` | Strict-split conformal/FZ audit (engine filter estimation stopped before the calibration window) with the matched-information GARCH control; companion to `code/job_fz_fullpanel.py`, which is the original-construction audit (filter fit through the full pre-test history) |
| `code/job_nurel.py` | `results/nurel_results.json` | ν-relative misspecification-score test: mk63 percentile-normalized against each name's simulated fitted-t null; frontier re-sorted |
| `code/job_coherent.py` | `results/coherent_results.json` | Coherent-curve audit: min-envelope hybrid monotonized, ES as the exact integral of the same curve, body-branch binding frequency, p0 splice sensitivity |
| `code/job_frontier_robust.py` | `results/frontier_robust_results.json` | Scale-versus-shape decomposition: the top-decile edge re-measured against a jump-robust (bounded-news) GARCH |

Superseded implementations (for example the pre-correction skew-t and the three-node ES approximation) are preserved in the repository history, not in the working tree; `code/frtb_bench.py` carries its correction history in the header.

## Data and licensing

Return data derive from CRSP/WRDS and Bloomberg under the author's licenses and are **not** redistributed — no raw data files are tracked. Every WRDS-based panel rebuilds from the documented queries in `code/` for any licensed subscriber; Bloomberg-based exhibits are preserved as-run (terminal access ended mid-2026). A synthetic end-to-end example (`code/toy_example.py`) runs the full pipeline without licensed data.
