# Semiparametric Value-at-Risk and Expected Shortfall with a Real-Time Misspecification Score

## Which file is the paper?

There is **one manuscript**, in two formats:

| File | What it is |
|---|---|
| **[`paper_A_frontier.pdf`](paper_A_frontier.pdf)** | **The paper — read this one.** Single-spaced, figures and tables inline. ("frontier" in the filename is historical, from an earlier working title.) |
| [`submission/paper_A_jfec.pdf`](submission/paper_A_jfec.pdf) | The **same manuscript** in the Journal of Financial Econometrics review format: double-spaced, endnotes, floats collected at the end with "[Table N about here]" markers. This is the file submitted to the journal. |
| [`submission/paper_A_jfec_online_appendix.pdf`](submission/paper_A_jfec_online_appendix.pdf) | Online appendix to the submission (algorithms, supplementary figures and tables, proofs deferred from the main text). |

LaTeX sources sit next to each PDF; the bibliography is [`refs_v3.bib`](refs_v3.bib).

## What the paper shows

A single measurable quantity — the excess kurtosis and asymmetry of recent GARCH-standardized residuals — orders when flexible-shape quantile methods beat parametric VaR/ES. Where the score is high, an amortized nonparametric engine wins decisively (top decile +2.7% pinball, DM 6.5; replicated on an untouched 2000–2013 holdout under a frozen specification with predictions written in advance, under strict calendar splits, under a true annual-refit walk-forward, and in a point-in-time universe that keeps delisted names); where it is low the advantage shrinks toward zero — the score orders the magnitude of the edge (top decile ≈ 7× the calm region), never a detectable loss. The engine passes the aggregate date-clustered exception tests at both regulatory levels through a 2008-crisis window, and its accuracy layer attains the lowest joint (VaR, ES) FZ0 score at both levels on the full panel.

## Repository layout

| Location | Contents |
|---|---|
| `paper_A_frontier.pdf` / `.tex` | The paper (reading format) |
| `submission/` | Journal-format build + online appendix (see `submission/README.md`) |
| `refs_v3.bib` | Bibliography |
| `paper_A_online_appendix.tex` | Glossary appendix for the reading version |
| `code/` | Analysis scripts. Every number in the paper traces to one script here; each script documents its data inputs at the top |
| `results/` | Derived statistics as JSON — one file per script run; these are the numbers quoted in the paper |
| `docs/` | Research notes, review syntheses, cover letter |
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

Superseded implementations (for example the pre-correction skew-t and the three-node ES approximation) are preserved in the repository history, not in the working tree; `code/frtb_bench.py` carries its correction history in the header.

## Data and licensing

Return data derive from CRSP/WRDS and Bloomberg under the author's licenses and are **not** redistributed — no raw data files are tracked. Every WRDS-based panel rebuilds from the documented queries in `code/` for any licensed subscriber; Bloomberg-based exhibits are preserved as-run (terminal access ended mid-2026). A synthetic end-to-end example (`code/toy_example.py`) runs the full pipeline without licensed data.
