# Adversarial reviews #7 and #8 - triage (2026-09-04, fourth wave)

Review #7: constructive re-read, Major Revision, 8 items + a "cannot attack anymore"
list covering every prior wave's fix. Review #8: hostile A-D; three of its five
attacks target text already removed or answered (14.6% capital - withdrawn last wave;
FZ0 deployed - adaptive-shift resolution in print; CAViaR - capabilities defense in
print), two are new.

## R7 items, all actioned
1. Ten-day ES still a 3/5-node proxy - TRUE, RECOMPUTED (his preferred option).
   job_stress_es.py: uniform exact ES in BOTH eras (closed-form t for sqrt-h GARCH,
   exact empirical z-tail mean for FHS, 20-node sub-alpha GBM integral for the
   direct model). Design era: hybrid still closest to its own tail (-20.0/-17.2 vs
   GARCH -21.1/-15.4) with best ten-day breach (2.83% vs 3.30%). Holdout era: the
   era-reversal caveat SURVIVES the correction - GARCH sqrt-h exactly calibrated
   (-16.63 pred vs -16.57 realized) while the direct tail still under-states
   (-15.9 vs -18.0). Passage rewritten with exact-integral numbers and the own-tail
   diagnostic caveat; "capital" language removed from the ten-day discussion
   ("tail severity").
2. FRTB linearity + "meets and exceeds the FRTB standard" - FIXED. The linearity
   sentence now lists what IMA capital actually involves (liquidity horizons,
   stressed ES, NMRF, aggregation, backtesting+PLA eligibility) and states no
   one-for-one mapping exists or is claimed. Section renamed "The FRTB-aligned
   forecasting battery"; conclusion now claims beating common market-risk
   forecasting benchmarks at FRTB-relevant levels, explicitly not IMA approval.
3. tie/costless/never-worse leftovers - FIXED. Ledger calm row is now "noninferior
   (no detectable loss)" with the bottom-decile 90% CI bound stated; winloss caption
   rewritten; thesis subsection no longer claims "a tie, not a loss."
4. Gradient not switch - ADOPTED. Abstract, thesis, README, SSRN abstract, and the
   100-word abstract now state the score orders the MAGNITUDE of the advantage
   (top decile ~7x the calm region, itself never a detectable loss); the hard
   "zero below / win above" dichotomy is gone.
5. Production-loop box cold start - FIXED. New-listing step now routes to the
   separate characteristics-only forecaster until a scale filter is estimable,
   then attaches the residual-hybrid; "no history required" removed.
6. Repo "registered" leftovers - SWEPT. README, cover letter (which also carried a
   STALE TITLE - now fixed), SSRN long abstract, job_fz_fullpanel.py header, and
   job_wrds_holdout.py header (now states the terminology choice explicitly).
7. "ES calibration" phrasing - FIXED in the passrates caption ("joint FZ0 score").
8. Conclusion generative prose - SHORTENED to a scope disclaimer.

## R8 new attacks
- Infinite-variance kurtosis thermometer (their FATAL) - the quoted noise
  disclosure is OUR OWN sentence; added the attenuation argument in place:
  misclassification across bucket boundaries biases measured top-bucket edges
  DOWN, so noise works against the frontier, not for it; jump/asymmetry signals
  corroborate under FWER; Hill-type variant named as the robustness extension.
- EVT splice discontinuity (MINOR) - already disclosed in the text; monotonicity
  is enforced by the pointwise minimum and rearrangement; dynamic POT noted as an
  extension. No change beyond what stands.
- Unified-configuration demand (their ONE QUESTION) - answered directly in the FZ
  section: the accuracy layer IS the unified configuration (lowest FZ0 at both
  levels AND passes per-asset + date-clustered exception restatements at both
  levels; only the hypersensitive pooled 155k-obs Kupiec at 97.5% is against it).

## Standing
R7's "cannot attack anymore" list now covers: skew-t, FHS strawman, one-day ES,
table/JSON provenance, holdout ranking, survivorship, multiplicity, GAS framing,
capital release. Remaining exposure per R7 is novelty and journal fit - an
editorial question, not a validation question.
