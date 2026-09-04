# Semiparametric Value-at-Risk and Expected Shortfall with a Real-Time Misspecification Score

A semiparametric VaR/ES engine — parametric scale, amortized flexible tails — and a real-time misspecification score for when it beats industry-standard risk models.

**Current live draft: [paper_A_frontier.pdf](paper_A_frontier.pdf)** ([LaTeX source](paper_A_frontier.tex) · [bibliography](refs_v3.bib))

The draft at the link above is the working version and is updated continuously; dated snapshots live in `paper/archive_pdfs/`.

## What the paper shows

A single measurable quantity — the excess kurtosis and asymmetry of recent GARCH-standardized residuals — governs when flexible-shape quantile methods beat parametric VaR/ES. Where that misspecification score is high, an amortized nonparametric engine wins decisively (top decile +2.7% pinball, DM 6.5; replicated on an untouched 2000–2013 holdout under registered predictions); where it is low, the engine and the parametric model tie. The engine passes Kupiec and Christoffersen backtests at both regulatory levels through a 2008-crisis test window and attains the lowest joint (VaR, ES) FZ0 score on the full panel.

## Repository layout

| Folder | Contents |
|---|---|
| `paper/` | Other manuscripts (online appendix, companion drafts) and `archive_pdfs/` with dated snapshots |
| `code/` | Study and job scripts (standalone; each documents its data inputs at the top) |
| `results/` | Derived statistics as JSON — every number in the paper traces to one of these |
| `logs/` | Run consoles and pipeline logs |
| `docs/` | Research notes, review syntheses, submission strategy, cover letter |
| `figures/` | Exported charts |
| `tools/` | Utility scripts |
| `autojobs/`, `ai2jobs/` | Job-runner queues (consumed jobs move to `done/`) |
| `live_paper/` | Live data-capture pipeline (options-surface archive, watchlist) |

## Data and licensing

Return data derive from CRSP/WRDS and Bloomberg under the author's licenses and are **not** redistributed here — no raw data files are tracked. Every panel rebuilds from the documented queries in `code/` for any licensed subscriber, and the paper's Data and evaluation protocol section states the exact filters and sample flow. A synthetic end-to-end example (`code/toy_example.py`) runs the full pipeline without licensed data.
