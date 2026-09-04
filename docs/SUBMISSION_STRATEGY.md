# Submission Strategy — Paper A (2026-09-03)

## 1. The big WINS, and whether the abstract states them

The abstract was rewritten today to be wins-led, three declarative results, ≤1 page of anyone's
time. Check each win against it:

| # | Win | Magnitude / evidence | In abstract now? |
|---|-----|----------------------|------------------|
| 1 | **Amortization + cold start** (one fit for hundreds of names; transfers to unseen names; beats own-history at every age; day-one IPO risk numbers) | 6–10% young-listing edge; 1.32M-row ablation; M5 external check | **Yes — "First, amortization"**, top billing |
| 2 | **Beats the deployed industry battery** (HS, RiskMetrics, GARCH-t, GJR-skew-t, FHS) | date-level DM 4.4–8.3; MCS co-best with CAViaR only | **Yes — "Second"** |
| 3 | **Capital-relevant ES calibration** (the practical headline) | removes 8–11% ES97.5 over-statement; exception counts consistent at both levels via EVT+conformal | **Yes — "Second"**, stated as capital |
| 4 | **The misspecification frontier** (a real-time score that says *when* the edge is large) | +2.7% top decile DM 6.5; 12–14% hyperinflation FX; geography across 4 universes | **Yes — "Third"** |
| 5 | Ten-day horizon + stress robustness | +1.4% at h=10; holds 2020–22 | Yes (one clause) |
| 6 | One-line deployment rule (run everywhere; score = dial) | gating provably unnecessary | **Yes — closing sentence** |

JFEC calibration point: JFEC 22(2) published Zhang–Zhang–Cucuringu–Qian, "Volatility
Forecasting with Machine Learning and Intraday Commonality" — ML + pooling across stocks +
transfer to unseen stocks as the headline ("universal volatility mechanism"). Our amortization
result is that paper's central claim, taken further (calibration, ES, exception tests, a
frontier theory, and deployment). The innovation bar for JFEC/IJF is met; what those journals
punish is inference sloppiness and scope sprawl, which is exactly what the last three weeks
of fixes addressed.

## 2. Losses framing (per Sean's direction)

The ledger (tab:winloss) is now two panels. **Panel A = the presented engine: only wins and
ties — its worst cell anywhere is a tie** (calm quintile ≈0 but never negative; CAViaR
statistical tie). There are no engine drawdown rows because the engine never materially loses
in any tested regime — that is itself now stated in the text. **Panel B is explicitly "not
the engine":** the standalone-net failure (why the engine is a hybrid), the calm-single-asset
scope condition, the Korea negative control (validates the frontier), and credit/freight
open-calibration items. Framed as boundary evidence and scope conditions that motivate the
design — which reads pro-engine — rather than as "our losses." Nothing hidden, nothing
self-sabotaging.

## 3. Readability for the target audience

Target reader = JFEC/IJF: econometricians and forecasting researchers who read
abstract → contributions → tables, and referee on inference validity. Current state: abstract
now three plain results; contributions are four numbered items all owned by this paper;
every number's test is defined once in the reading-guide; the ledger gives the skim-reader
the whole record in one table; the deployment box gives the practitioner the production loop
in ten lines; glossary demoted (register now matches the venue). Remaining readability debt:
the promised "Data and Forecast Evaluation Protocol" section with the sample-flow table
(720→200→140→45/40) — the single biggest remaining clarity item for a referee — and one
canonical results table unifying the battery variants.

## 4. Put-to-practice

Yes: §7 "Applications and deployment" now opens with the desk production loop (nightly 5-step
box: filter update → shared shape model → frozen tail → conformal → score-as-dial; annual
refit; new-listing path), followed by regulatory capital, the model-risk monitor, cold-start
use cases, and which desks the edge concerns. This is the section JFEC's "and it can be
implemented" expectation points at.

## 5. Research/validation still needed — WRDS-only world (no Bloomberg terminal)

Runnable now on this computer via WRDS + local data (all queued in autojobs):
- **2000–2013 confirmatory holdout** (job_wrds_holdout) — frozen spec on an untouched era;
  answers the forking-paths critique. THE most important remaining validation.
- **Timing-diagnostics table** (job_timing_diag) — lag1/lag5/contaminated-lag0/lead-placebo.
- **Finished-engine per-asset exception restatement** (job_perasset_v2).
- Full-panel FZ (VaR,ES) re-scoring (next_fz_scoring exists; needs battery forecast export).
- Protocol section + canonical table (writing, no data needed).
- CRSP delisting: done. Measured option costs: local OptionMetrics extracts already on disk.

Bloomberg-dependent and now **frozen as static exhibits** (fine for submission; label the
sample end dates): the FX/country/cross-asset geography, Korea control, crypto. These cannot
be refreshed or extended — do not promise updates to them in-text. The intraday frontier
stays tick-data-blocked. Nothing submission-gating depends on Bloomberg.

## 6. One paper for JFEC and IJF, or two versions?

One master paper, two light "skins" — and strictly sequential submission (simultaneous
submission of the same paper is an ethics violation everywhere; tailoring does not change
that). The two journals want the same evidence with different emphasis:
- **JFEC skin** (submit here first): lead with the econometrics — the frontier as a testable
  theory of parametric misspecification, formal results, inference discipline (date-level DM,
  MCS spec, per-asset backtests), engine as the applied payoff. Single-column OUP format.
- **IJF skin** (if JFEC declines): lead with forecasting practice — amortized forecasting,
  cold start, M5 external validation, the deployment loop, ES calibration; frontier as the
  organizing empirical regularity. IJF loves honest negative results and reproducibility.
The differences are: abstract emphasis, intro ordering, and which robustness lives in
appendix — ~1 day of work per skin, one results base, no forked analyses.

## 7. Journal list (large pass, roughly in descending prestige within each block)

**Primary targets:** Journal of Financial Econometrics (JFEC); International Journal of
Forecasting (IJF).
**Strong fits, similar tier:** Journal of Econometrics; Journal of Business & Economic
Statistics (JBES); Journal of Applied Econometrics; Journal of Empirical Finance; Journal of
Banking & Finance; Journal of Financial Markets; JFQA (economics-of-premium angle needed).
**Statistics side (conformal/SBC/calibration lead):** Annals of Applied Statistics; JASA
(Applications & Case Studies); Econometrics and Statistics; Journal of Time Series Analysis;
Studies in Nonlinear Dynamics & Econometrics (SNDE); Econometric Reviews (more survey/theory).
**Quant-finance journals (very good fit, faster):** Quantitative Finance; Journal of Financial
Data Science (JFDS — tailor-made for this paper); Journal of Risk; Journal of Forecasting
(Wiley — distinct from IJF, publishes exactly this genre); Journal of Computational Finance;
Applied Mathematical Finance; Journal of Risk and Financial Management (JRFM — MDPI, fast,
lower prestige); Digital Finance; Algorithmic Finance.
**Practitioner (visibility, fast, less "publication" weight):** Journal of Portfolio
Management; Journal of Derivatives; Journal of Investment Strategies (Risk.net); Risk
magazine (Cutting Edge section — short technical note version).
**Fast/short-format options:** Finance Research Letters (strong impact factor, 2,500-word
format — a frontier-only note); Economics Letters (a one-result letter, e.g. the frontier).
**Backstops (broad-scope, higher acceptance):** International Review of Financial Analysis;
North American Journal of Economics and Finance; Global Finance Journal; Journal of Financial
Stability (systemic angle); Expert Systems with Applications (ML-applied, indexing-friendly).
**Immediately, regardless of target:** post to SSRN + arXiv (q-fin.RM) for a timestamp and
circulation; neither counts as prior publication for any journal above.

Strategy: JFEC → IJF → Quantitative Finance / JFDS → Journal of Forecasting → Journal of
Risk → backstops. In parallel (different content, no overlap violation): a short
frontier-only letter to Finance Research Letters is a legitimate separate mini-paper if you
want an early win — but only if its result set is disjoint from the main paper's submission.
