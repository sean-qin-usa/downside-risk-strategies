# Paper portfolio map — which result lives in which paper
2026-07-21. Purpose: three writing efforts now exist; this doc fixes what
belongs where, so no result is double-claimed and none is orphaned.

## Paper 1 — "When and Why Distribution-Free and Generative Quantile Models Beat the Industry Standard for Downside Risk" (NEW, compiled on Overleaf)
The broad flagship. Thesis = the misspecification frontier + what only
generative methods can do. Status: full draft, 18pp compiled, figures
native TikZ, refs_v3.bib.

Owns: misspec frontier (deciles + DM, four universes, Korea control);
FRTB battery (residual-hybrid + EVT + conformal, CAViaR tie, ES97.5
capital, 10-day horizon/stress); uncertainty bands on (VaR, ES)
(1.6× Gibbs overconfidence, block bootstrap, ACI, EVT interval); Heston
+ rough-Bergomi SBC; joint-tail negatives + scale/shape crossover;
gate negative; amortization ablation + failed hierarchy blends
(compressed, §3.2); the −38% retirement (one paragraph, intro).

Venue: J. Financial Econometrics / JBF / Quantitative Finance.
Split option (only if referees force it): Paper 1A applied
(frontier + FRTB + multivariate), Paper 1B methods/Bayesian
(uncertainty + SBC, the thesis chapter with Prof. Jiang → Bayesian
Analysis).

## Paper 2 — "EVT Tails on a Neural Quantile Body … and the Price of Crash Insurance" (graftq_main.tex, Jul 12, KEPT AS ITS OWN PAPER)
Single-universe deep dive + economics. Status: full draft in PQ
Research → Paper; measured-cost columns pending OptionMetrics.

Owns: 543-name multi-horizon IQN calibration (body exact, left tail 2×
thin, EVT splice repair — THE detailed calibration anatomy); the
idiosyncratic-event informational ceiling; crash-insurance negative
(525 trigger months, −1.7%/mo, t=−1.9; demand-based pricing
interpretation); the entire VRP trading system (sell_10, switcher,
master book SR 1.44, Kelly, negative catalog); dimension-reduction and
NaN-imputation results.

Venue: Journal of Derivatives / JFQA-style applied, or split the
trading appendix to a practitioner journal.

## Overlap rules (so the two don't collide)
- The EVT tail splice appears in both: Paper 2 owns the DISCOVERY and
  anatomy (calibration repair on the 543-name IQN); Paper 1 uses it as a
  COMPONENT of the FRTB engine and must cite Paper 2 for it.
- IQN architecture: Paper 2 owns the multi-horizon design; Paper 1 owns
  the tail-aware/monotone/conformal fixes and trees-vs-net comparison.
- Walk-forward + purge/embargo protocol: described fully once (Paper 2),
  cited from Paper 1.
- Neither paper claims the other's headline. Cross-cite as companion
  papers.

## Orphaned results — RESOLVED 2026-07-21 (all placed in Paper 1)
- Hourly-crypto IQN win (~0.6%, DM p<1e-7) → Paper 1 §4.2 "A frequency
  corollary" (frontier has a frequency dimension; daily crypto stays
  GARCH's).
- Ensemble-disagreement self-confidence (corr +0.11) → Paper 1 §6.2
  (benchmark-free first-line reliability screen).
- M5 benchmark (leakage-safe SPL 0.269) + transfer win rate 59–79% →
  Paper 1 §3.2 (external checks on the amortized machinery).
- Regime-detector latency (median 0 / mean 2–4 days, edge back-loaded)
  → Paper 1 §4.3 parenthetical.
- Edge-concentration/three-way regime table already in Paper 1 §4.3.
- Full future-directions program now in Paper 1 conclusion (FZ+MEU,
  loss-in-exponent, leverage-ρ, Hawkes/jump SBC, vector quantile
  regression, WRDS 2008, intraday frontier).

## Memo lineage
Weekly Jiang memos track Paper 1's research line. GRAFT-Q/trading
progress reports separately if resumed (live forward holdout feeds
Paper 2's registered exhibits).
