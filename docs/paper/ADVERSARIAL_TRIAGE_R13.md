# Adversarial Triage — Round 13 (Review #18: REJECT recommendation, 20 ranked attacks)

The most serious review in the program. It recommended reject and rested on
two code-level catches. **Both were verified against the primary artifacts,
both were real, both are fixed, and the headline survives.** Every number
below was rerun on the host, not argued from priors.

## [FATAL #1] Design-era headline frontier formed deciles with global `pd.qcut`

**Verified real.** The score inputs are causal (rolling kurtosis `.shift(1)`),
but `pd.qcut` over the whole pooled test panel makes top-decile *membership*
depend on the full-sample score distribution, including future dates. Confirmed
in `job_romanowolf_v2.py:65`, `job_calendar_split.py:67`, `job_walkforward.py:80`,
`job_nurel.py:96`. The manuscript already handled this for the 2000--2013
*holdout* (frozen-constant + expanding prior-only threshold) but never for the
design-era headline figure — exactly the gap the attack named.

**Action.** New job `job_causal_frontier.py` reran the design-era top decile
under three cutoff rules on the identical 200-name / 221.6k-row panel and the
11-$\tau$ accuracy engine (`causal_frontier_results.json`):

| rule | top-decile edge | DM | membership overlap w/ A |
|---|---|---|---|
| A global qcut (shipped) | +2.96% | 10.1 | — |
| B expanding prior-only 90th-pct threshold (as deployed, 250-date burn-in) | **+2.45%** | **8.3** | **0.86** |
| C within-date cross-sectional decile (NOT the deployed rule) | +0.26% | 2.2 | 0.10 |

The only look-ahead was the *threshold*; a strictly past-only threshold leaves
86% of membership unchanged and holds the edge at +2.45% (DM 8.3) — essentially
the headline. C is weak because it forces 10% occupancy every date incl. calm
cross-sections: the frontier ranks the *absolute* misspecification level, not
within-day rank. Consistent with the point-in-time universe already in the paper
(+2.94%, DM 6.6). **Folded into both builds** as "The decile boundary is causal
too," after the timing diagnostics.

## [MAJOR #4] MCS eliminated argmax(raw mean loss), not the standardized statistic

**Verified real.** `frtb_table_canonical.py:233` had `worst=surv[argmax(means)]`
— eliminates the largest *raw* mean loss, not the Hansen--Lunde--Nason range
statistic the test statistic `TR2` is built on.

**Action.** Fixed to `worst = argmax_i max_j (means_i-means_j)/sqrt(var_ij)`
(the signed standardized HLN range-elimination rule). Reran Table 6
(`frtb_table_results.json`): best model `resid_hybrid_ML` (0.3551);
**90% MCS = {resid_hybrid_ML}, sole survivor — UNCHANGED.** The old raw-mean
rule coincided with the standardized order because the models are well
separated. Correctness fix; the paper's claim ("the 90% MCS contains the raw
hybrid alone") stands, no text change to the claim. DM battery within run-to-run
GBM noise (<=0.2) of the cited values.

## [#11] Online-appendix cross-references off by one

**Verified real.** The win/loss summary table was moved into the JFEC online
appendix as Table OA.1 in a prior wave (R11), shifting every later table up by
one, but the hard-coded citations were not all updated. Actual numbering:
OA.1 winloss, OA.2 double-sort, OA.3 decision, OA.4 Holm. Figures and algorithms
were already correct.

**Action (submission build).** double-sort 1x (OA.1->OA.2), decision 2x
(OA.2->OA.3), Holm 2x (OA.3->OA.4). **Reading build:** its companion appendix is
glossary+proofs only (no OA tables), so the two dangling "Table OA.3" pointers
were dropped; the prose already states the survivor set. Zero OA.N refs remain
dangling in the reading copy.

## [#19] Kupiec pass-rate figure GJR bar predated the skew-t correction

**Verified real** (the caption itself admitted it). Extended
`frtb_table_canonical.py` to emit per-name Kupiec-99 pass rates for the canonical
model set (skew-t GJR included) so the figure is regenerated from the same models
as Table 6. [Bars + caption updated from `passrate99_perasset`; see below.]

## [#5] Paper-wide multiplicity

Per-family control was already thorough (Romano--Wolf over the 3x10 grid; Holm
over the 93-comparison universe). Added an explicit paper-wide stance to both
builds: the guard against selection is **replication, not one joint correction** —
the headline is FWER-controlled within its grid, pre-registered and reproduced on
the untouched holdout, and recovered under a causal cutoff, so it does not hang on
a single surviving test; exploratory single-instrument universes are labeled as
such and carry their own adjustment.

## [#6] GAS "surrogate"

**Verified.** GAS at 1% is a one-factor PZC-2019-style model FZ0-estimated per
name; its 1% gap (meanFZ0 2.232 vs engine 2.147) is inflated by a few names whose
optimizers destabilize. Reframed in both builds: the accuracy claim **rests on the
GARCH-t (DM 4.8) and FHS (DM 4.9) margins**; the GAS comparison (DM 9.6 at 1%, 6.2
at 2.5%) is "indicative only," instability named, three-start re-estimate settles
the stable 2.5% comparison near DM 5.9.

## [#7] "Residual degree of freedom" a-priori rhetoric

**Verified already removed** (softened in R12). The only "degrees of freedom" left
in either build is the legitimate Student-t usage in Proposition 2. No action.

## [#20] Referee-dialogue "objection->reversal->slogan" prose

Prior waves (R11/R12) removed the bulk. Remaining clear slogan "the low
correlation is the point, not a weakness" -> plain statement in both builds. Other
grep hits were false positives ("point-in-time", "pointwise") or honest disclosure
of the conformal concession, left as-is.

## Status

The review's two headline code-level catches (#1, #4) are both verified real and
fixed; the headline survives a strictly causal decile cutoff (+2.45%, DM 8.3, 86%
overlap) and the sole-MCS-survivor conclusion is unchanged under the corrected
rule. Text/reference fixes (#11, #19) and framing (#5/#6/#7/#20) done in both
builds. Both repos to be synced; both builds to be recompiled and page-checked.
