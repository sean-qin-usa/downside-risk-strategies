# Adversarial Triage — Round 8 (Review #12, wave 7)

Reviewer's verdict coming in: "Major Revision, but only narrowly — close to
Minor Revision"; the one item requiring a new empirical run was the strict
conformal split. Protocol as always: verify, fix, rebut with evidence, fold.

## 12.1 [MAJOR] "The calibration split is not held out from the full base model"

**Verified TRUE as a statement about the code**: `job_fz_fullpanel.py` fits
GARCH on `y[:sp]` (the whole 60% estimation period) while calibration is
`cp..sp`, so the filter's parameters saw the calibration returns. Shape learner
(trained `idx<cp`) and EVT tail (fit on pre-`cp` residuals) were already
strictly pre-calibration.

**But the imputation of consequence is wrong for the headline results, and the
requested rerun proves it.** Two structural facts:

1. **The accuracy layer never reads the calibration split.** The unshifted
   engine = filter × shape learner × EVT tail; the calibration window enters
   only through the conformal shift, which the accuracy layer does not use.
   And the filter is *shared with the GARCH benchmark* (also fit on `y[:sp]`),
   so every FZ0 contest pit identical information sets. There was nothing to
   leak *between* the compared models.
2. **The strict rerun** (`job_conformal_strict.py` → `fz_strict_results.json`;
   42s, same 200-name panel, identical test rows): engine rebuilt end-to-end
   with the filter fit only through `cp` (45% of sample), recursive filtration
   after, every estimated component then out-of-calibration — plus the control
   the comparison needs, a GARCH benchmark fit through the same `cp` boundary.

   | Comparison | 1% | 2.5% |
   |---|---|---|
   | Strict engine vs **matched-information** GARCH (both `cp`-fit) | **DM +4.97** | **DM +5.27** |
   | Original engine vs full-window GARCH (the paper's audit) | DM +4.15 | DM +4.53 |
   | Strict engine vs full-window GARCH | DM −0.74 | DM −2.42 |
   | Full-window GARCH vs its own `cp`-fit twin | DM +2.79 | DM +3.83 |

   Read together: under matched information the engine's advantage is fully
   intact (slightly larger than the original audit); the strict engine's gap to
   the full-window benchmark is the same size as the benchmark's own gap to its
   short-window twin — i.e., it is the price of a quarter less estimation data
   for the filter, not a leakage correction.
3. Where the critique **does** bite — the static overlay's shift, the one
   quantity computed from calibration outcomes — the strict split makes it
   wider (−0.51 vs −0.34) and its per-name Kupiec pass rate lower (33% vs 48%),
   consistent with the static overlay's already-disclosed conservatism. The
   adaptive form remains the deployment answer. Nothing new to withdraw.

**Folded into the paper** (both builds, Prop-1 scope paragraph): the
implementation gap stated plainly; the identical-information-sets argument; the
strict rerun's matched-benchmark DMs; the sample-size (not leakage)
attribution; the static-shift widening. Proposition 1 was already framed as
motivational, not asserted for deployment.

## 12.2 [MAJOR wording] Abstract overstated per-name calibration

TRUE. Fixed in both builds. Master abstract now: aggregate date-clustered
counts nominal at both levels + "per-name diagnostics disclose residual
cross-sectional calibration heterogeneity." JFEC abstract: "Aggregate
date-clustered exception counts stay nominal…" Contribution bullet aligned
("nominal on the aggregate date-clustered tests … per-name pass rates disclosed
as residual heterogeneity").

## 12.3 [MODERATE] Ten-day row inside "Panel A: the engine's record"

TRUE (front matter lagged the wave-6 relabeling). Fixed: Table 1 now has a
separate block "*Extension (a separate direct multi-day model — not the
engine)*" holding the ten-day row; caption and the pre-table paragraph say so;
abstract sentence now reads "a separate direct multi-day extension shows a
larger edge at ten days."

## 12.4 [MODERATE provenance] +0.65%/DM 0.22 vs the public JSON

TRUE — the number was carried from the unpurged run. Fix in two parts:
`job_stress_dm.py` recomputed the holdout h=10 panel under the identical purged
pipeline and wrote the exact quantities *into* `stress_es_results.json`
(edge_pct_direct_vs_garch = **0.489**, DM = **0.07**; vs FHS 0.57, DM 0.20),
replacing the holdout block with the recomputed one so the artifact is
self-consistent. Manuscript now quotes +0.49%, DM 0.07, NW lag 10 (and the
realized own-tail −17.8 aligned). Summary-table cell updated to DM 0.07.

## Also swept this wave

- `results/fz_fullpanel_results.json` note still said "registered" — patched to
  "pre-committed" (the reviewer's earlier terminology point, now closed in the
  artifact as well as the script).
- Conclusion tightened while restoring the p41 text boundary: triad removed
  ("decisively, significantly, and portably" → "decisively and portably"),
  redundant generative-extensions sentence cut, extensions inventory compressed
  and moved before Limitations so the paper ends on the oracle-gap sentence.
- New README row: `code/job_conformal_strict.py` → `results/fz_strict_results.json`.

## Net position after wave 7

The reviewer's one required run is done, with the control that makes it
interpretable. No headline number changed by more than provenance rounding
(+0.65→+0.49 on a tie that was always reported as a tie). The static overlay's
conservatism deepened slightly under the strict split — disclosed, consistent
with the existing taxonomy. Remaining referee surface: novelty/fit for JFEC.
