# Adversarial reviews #5 and #6 - triage (2026-09-04, third wave)

Review #5: re-read of the second-wave build, verdict Major Revision on one narrowed
ground (ES statistics). Review #6: fresh hostile A-D. Every checkable claim verified
before action; the big one changed the paper.

## The ES audit (R5 #1) - TRUE, AND WORSE THAN CLAIMED. CLAIMS WITHDRAWN.
Confirmed: ES975_pred was the equal-weight mean of Q(.005), Q(.01), Q(.025) - not the
tail integral. Reviewer's normal-case error (2.2%) reproduced exactly in a self-test.
Rebuilt the entire battery in ONE run (job_frtb_table.py -> frtb_table_results.json)
with true ES: closed forms (t, normal), 200-node Hansen integration, GPD closed form,
matched 20-node midpoint for empirical models. RESULT: under the exact integral the
predicted-vs-own-tail wedge roughly doubles for everyone (GARCH-t 18.4%, pooled FHS
21.6%, EVT engine 16.8%, raw hybrid 9.3%) and no longer separates the engine from the
field. ACTIONS: the 8-11% over-statement claim and the ENTIRE capital-release table
(6.4/4.9/14.6bp) are WITHDRAWN from abstract, intro, ledger, Section 6, and the
applications section, with the withdrawal explained in-text and credited to audit;
the ES columns are relabeled a model-dependent diagnostic; FZ0 carries the ES
comparison (as the reviewer himself proposed). Table 6 is now generated wholly from
the one-run artifact - also killing R5 #4 (spliced-row provenance; the old "fourth
decimal" sentence is gone with it). R6's "pro-cyclical 14.6%" attack dies with the
table it attacked.

## Other verdicts
- Equivalence margin not equivalence (R5 #2) - TRUE. The +/-0.25% margin definition
  was replaced: "tie" now means failure to reject only, explicitly not equivalence;
  the one genuine TOST that passes is stated as one (CAViaR: 90% CI [-0.05%,+0.11%]
  inside +/-0.25%); "pays nothing to hold it" removed.
- Cold start conflation (R5 #3 = R6 FATAL #1) - TRUE. Scoped everywhere: the day-one
  forecaster is the characteristics-only amortized model (no scale filter); the
  residual-hybrid attaches once a per-name scale filter is estimable; "one fit
  replaces per-asset estimation" now says "of the innovation shape (the scale filter
  remains the industry's per-name recursion)"; "a GARCH cannot be estimated" below
  250 days corrected to "below our 750-observation fitting floor... a practical
  floor, not a mathematical impossibility." R6's "mathematical impossibility" attack
  is answered by the scoping, not contested.
- GAS single-start (R5 #5) - RE-RUN. Three starts, maxiter 300, convergence flags:
  at 2.5% the comparison reproduces (DM 5.9 vs 5.95 single-start; flags 100%); at 1%
  the wider search destabilizes the filter for a few names (exploding FZ0 on test) -
  reported in-text as the reason the benchmark stays deliberately lightweight and
  appendix-grade. gas_polish_results.json ships.
- FZ0 "bait-and-switch" (R6 FATAL #2) - superseded: the adaptive-shift result
  already ties GARCH-t on deployed 2.5% FZ0; top-decile cost disclosed.
- CAViaR (R6 MAJOR) - answered previously (capabilities + backtest failures + TOST).
- Latency (R6 MINOR) - existing measurement (median 0 / mean 2-4 days, back-loaded
  edge) already in paper; no change.
- Frontier language - one conceptual adjustment adopted: the PIT result shows the
  score predicts the MAGNITUDE of the advantage (top ~7x bottom), not a hard zero
  below; the paper already discloses the positive calm-cell PIT edge.

## Provenance note
The canonical one-run table changes some pooled exception cells (common trimmed
sample): the EVT variant's pooled breach is 0.91% (conservative side) and pooled
Kupiec rejects from over-coverage. The table note now says pooled p-values at 155k
obs reject at +/-0.1 point deviations in either direction and are reported, not
leaned on; the regulatory reading remains the per-asset and date-clustered
restatements (which pass at both levels) and the 2008-era battery.
