# Adversarial Triage — Round 10 (Review #14: the math/code audit, wave 9)

The deepest review of the program: a line-level audit of the formal claims
against the implementation. Verdict coming in: back to Major Revision on two
grounds — "mk63 is not yet a model-relative statistic" and "the implemented
hybrid is not obviously one coherent distribution" — plus a list of exact math
errors and a prose-architecture critique. Every item verified, and the two
required experiments RUN and PASSED.

## The two decisive experiments

### 14.3 ν-relative misspecification score (`job_nurel.py` → `nurel_results.json`)

Objection verified TRUE as stated: mk63 is raw sample kurtosis, and a
correctly specified $t_{\nu_i}$ implies different null kurtosis per name.
The requested normalization was run properly: each observation's mk63
converted to a percentile of the *simulated* null distribution of 63-window
sample excess kurtosis under that name's own fitted $t_{\nu_i}$ (21-point ν
grid from 2.6 to 50 — extended *below* 4 because the panel's median fitted ν
is 3.9, where population kurtosis does not exist and the reviewer's
$6/(\nu-4)$ formula is undefined; the finite-window simulated null is the
only valid normalizer, a point now in the paper).

**Result: the frontier fully survives.** Normalized-score top decile +2.99%
(DM 8.5) vs raw +2.97% (DM 10.5) on the same 200-name panel; deciles 1–8 at
zero; decile 9 +0.66 (DM 4.6); 82% top-decile overlap (Spearman 0.97 — the
normalization genuinely re-ranks, and the frontier holds). "Misspecification
score" is now the defended name. Folded as its own paragraph in the frontier
section.

### 14.2 Hybrid coherence (`job_coherent.py` → `coherent_results.json`)

Objection verified TRUE: the displayed equation showed an indicator splice
while the code takes a min envelope, and ES came from the GPD closed form.
The audit: define the implemented curve Q*(u) = min(body, EVT) on the EVT
domain, monotonize by rearrangement, read **both** VaR and ES from that one
curve (ES as the exact 20-node integral), rerun FZ0, and measure how often
the body branch binds.

**Result: the envelope is real (body binds on 38% of tail nodes — so the
displayed equation was wrong and is now fixed to the min-envelope form with
rearrangement operator R[·]), and coherence costs nothing**: coherent-ES FZ0
1.849 vs shipped 1.851 at 2.5% (coherent marginally BETTER, DM 5.3),
engine-over-GARCH DM 4.8 at both levels, and the splice threshold is
immaterial (p0 ∈ {1.5%, 2.5%, 5%}: DM 4.6–4.8). Equation \eqref{eq:hybrid}
rewritten; audit numbers in the text.

## Conformal implementation = theorem (14.4) + adaptive under strict (14.5)

- All conformal shifts now use the exact ⌈(n+1)τ⌉ order statistic of
  Proposition 1 (was interpolated np.quantile) in `job_fz_fullpanel.py`,
  `job_fz_strict_calibration.py`, `job_fz_aci.py`; all three rerun. Quoted
  numbers refreshed (static concession DM −2.0 → −1.6, now insignificant
  two-sided; pass rates 47/72/69; GAS 6.9–9.3; strict matched-information DMs
  5.1/5.4).
- ACI run **under the strict split** (γ=0.05, warm start at the strict static
  shift): walks the shift −0.51 → −0.20, per-name pass 34% → 57%, GARCH gap
  DM −3.2 (static) → −1.5 (insignificant two-sided). "Adaptive remains the
  answer" replaced by the established version with these numbers.

## Math fixes (14.1 + formal-result audit)

- **W1 claim deleted** (it was wrong: integrated pinball is CRPS/2, not a
  Wasserstein objective; the two true facts are now stated separately).
- **DM sign convention unified**: orientation stated (benchmark − engine,
  positive favors the engine; per-use orientation for benchmark-vs-benchmark
  rows); one-sided 1.645 headline convention reconciled.
- **Lemma 1 main-text proof**: missing absolute values restored
  (m|u−q| ≤ |F(u)−τ| ≤ M|u−q|, a.e.); appendix was already correct.
- **Tail-wedge proposition retitled** "tail-shape misspecification" (kurtosis
  doesn't exist for ν ≤ 4, which the proposition's ν > 2 range allows).
- **Sampler proof added** to both proofs appendices (the "four formal
  results" count is now true); the "only member with an exact sampler" claim
  narrowed to the defensible version (continuous quantile map ⇒ direct
  inverse-transform sampling; GARCH-t/FHS also simulate).
- **EVT language**: "must follow" → MDA-conditions approximation; ξ<1
  condition for the ES formula stated with the code guard noted.
- **CRPS wording** ("weights quantile levels uniformly — a 1% tail is 1% of
  the integral"); "forecast error" → "quantile loss"; simulation "must
  reflect" → "is consistent with".
- **Headline-edge provenance**: +2.46 (pooled asset-day) vs +2.71
  (equal-date) vs +2.69 (timing-diagnostics lag) defined once in the
  frontier tablenote.

## Prose architecture (the de-AI items)

Status column deleted from the summary table (no more "win (survivorship
armor)" scoreboard — three columns, results speak for themselves); "armor"
count now 0; ALL referee/audit narration removed ("adversarial audit",
"a referee could ask for", "decided it", "settles it" → neutral method
statements; grep count for adversarial/referee: 0/0); triad scaffolds
dissolved (the "Three X" announcers are gone; only the tablenote's factual
"Three top-decile conventions" remains); thermometer/arbiter/treatment
metaphors stripped (frontier and engine retained); abstract opens
declaratively ("We develop…", "Against standard benchmark models it reduces
quantile loss…" — advertising verbs gone, still exactly 100 words);
em-dashes now 109 (master) / 96 (submission), from 220 two waves ago.

## Also this wave

- JFEC structure survey (92 papers, 2008–2025) delivered: ~5% carry a
  "Robustness"-titled main-text section; 60–70% of post-2018 papers defer to
  online appendices; median 6 main sections. Restructure decision deferred to
  Sean ("targeted now, tell me how others do" — done).
- Duplicate `\section{Proofs}` heading in the OA removed.
- Timing/absorption/monitor/context paragraphs compressed to restore the
  40-page text boundary (submission text ends on p41; reading copy now 40pp).

## Net position

Both of the reviewer's decision experiments passed with the headline intact.
The engine's displayed math now IS the implemented model; the conformal code
now IS the proposition's rule; the score's name is now earned, not asserted.
Files: `job_nurel.py`, `job_coherent.py`, and the three rerun conformal jobs
ship as canonical artifacts with their JSONs.
