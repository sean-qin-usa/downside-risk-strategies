# Adversarial Triage — Round 9 (Review #13, wave 8) + the de-AI prose pass

Reviewer's own verdict: "Minor Revision / borderline publishable after
revision… I no longer see a credible path to rejecting the central
misspecification-frontier result on econometric validity grounds." Two fixes
requested, two cleanups suggested, plus Sean's directives this wave (100-word
abstract, resume bullets, AI-prose audit).

## 13.1 Cross-universe multiplicity (the one substantive item)

Reviewer computed Bonferroni 0.05/93 over the instrument-level looks and
predicted USDEGP and Kenya survive while Sri Lanka and USDARS do not. We did it
properly rather than by the suggested sentence alone: recovered all 93
per-instrument DMs from the archived run logs (24 FX + 26 indices + 43
cross-asset — the reviewer's exact family), computed one-sided p-values and a
full Holm step-down at familywise 5%.

**Result (Online Appendix Table OA.3):** eight numerical survivors — PJM
power, Baltic Dry, VIX, V2X, VVIX, USDEGP (p=7.2e-5), Kenya (2.2e-4), wheat
(2.2e-4). MOVE (6.4e-4), Sri Lanka (6.9e-4), gasoline, USDARS (2.1e-3),
Pakistan, Nigeria all fail, exactly bracketing the reviewer's calculations.
Bonferroni gives the identical set. **PJM is reported as an artifact, not a
survivor** — the paper's own cross-asset audit had already reclassified
electricity as a log-return artifact on near-zero prices (refit on
differences, GARCH wins), so the text quotes *seven* real survivors. Main text
adds the exploratory-framing paragraph the reviewer requested: instrument
rows are exploratory; the pooled crisis-FX comparison (DM 4.12, p≈1.9e-5,
survives anything) and the kurtosis–edge gradients are the replication
evidence. Table 7's frontier-index footnote flags that only Kenya survives.

## 13.2 Strict-calibration audit reproducibility

Renamed to the reviewer's suggested names: `code/job_fz_strict_calibration.py`
→ `results/fz_strict_calibration_results.json` (script's output path updated;
JSON note carries the rename provenance; logic identical to the wave-7 run).
The DM 5.0/5.3 paragraph now cites the artifact filenames inline, the Data and
Code section names them, and the README pairs the strict audit with
`job_fz_fullpanel.py` explicitly labeled as the original-construction audit.

## 13.3 CAViaR "machine zero" rhetoric

Removed. The pooled-rejection comparison is replaced with the same-standard
statement: pooled asset-day tests ignore cross-sectional dependence and
overstate rejection for every model, ours included; the date-clustered
restatement is the reading the paper trusts. The capability asymmetry (one
level per fit, no ES, no cold start) and the honest DM 0.59 tie stand.

## 13.4 "Industry-standard-and-above" heading

Downgraded everywhere: the contribution heading is now "An FRTB-aligned risk
engine"; "meets and beats the industry standard" → "beats the market-risk
forecasting benchmarks banks commonly run"; "deployable at industry
standards" → "deployable in practice." The descriptive uses (defining the
empirical bar as beating HS/FHS) remain, as they claim nothing about us.

## Sean's items this wave

- **Abstract:** one exactly-100-word abstract now in BOTH builds (the reading
  copy's 380-word abstract is gone; no repo/submission mismatch remains). Title
  unchanged.
- **Resume bullets:** docs/RESUME_BULLETS.md (full, compact, one-liner).
- **"Are we using GBC?"** The lit paragraph now says outright: the deployed
  shape model is the trees; the IQN is a benchmark; GBC is the framework
  lineage; sampling/posteriors are out of scope.
- **AI-prose pass:** full protocol run and fixed in place — em-dashes 220→119
  (main)/106 (submission), no prose paragraph above 3; doubled statements
  removed; report in docs/PROSE_CHECK_REPORT_R1.md. Master build is now 40pp;
  submission text ends on p41 as required.
- **Paper map:** docs/PAPER_MAP.md — plain-language section-by-section
  breakdown with the five-link logic chain.

## Status after wave 8

All four of Review #13's items are closed at or above the requested strength.
Per the reviewer's own advice — and ours since wave 6 — the experiment program
now stops: remaining risk is novelty/editorial fit, which no further audit
changes.
