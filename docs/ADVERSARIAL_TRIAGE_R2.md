# Adversarial review #2 — triage (2026-09-04)

Unlike review #1 (every quote fabricated), review #2 read the repository. Several attacks
check out against our own result files and produced real fixes. Verdicts below; every
claim was verified against the primary artifact before any action.

## Verdicts

1. FZ0 "lowest at both levels" (FATAL claim) — TRUE AS STATED, FIXED BY SCOPING.
   Verified in fz_fullpanel_results.json: at 2.5% the DEPLOYED variant (conformal shift on)
   scores 1.86765 vs GARCH-t 1.85420, DM -1.97 (deployed loses); the accuracy layer
   (no shift) scores 1.85065 and wins (DM 4.23). At 1% the shift is inactive and the engine
   wins outright (DM 4.1). The paper's body already disclosed the give-back but the
   headline/ledger attributed the win to "the engine" undifferentiated. FIXED everywhere:
   intro contribution, ledger row, FZ body paragraph (now also disclosing the top-decile
   deployed deficit DM -7.1), conclusion, README, cover letter. New sentence pins the rule:
   every "lowest FZ0" headline refers to the accuracy layer; the deployed variant's 2.5%
   concession is the quantified price of its coverage margin. The claim was never false at
   1%; at 2.5% it was true only for the accuracy layer, and now says so.

2. Holdout deciles via pd.qcut over the full test era (FATAL claim) — TRUE, ARMOR RUN.
   Verified in job_wrds_holdout.py: frontier() computes qcut boundaries from the whole
   holdout test sample. The deciles never touch a forecast or a loss (conditional-sort
   convention), but "a desk could have used this rule in real time" was not supported.
   FIX: (a) disclosure sentence added to the holdout paragraph; (b) job_holdout_frozen.py
   re-runs top/bottom buckets with NUMERIC thresholds frozen from the design era (pooled
   design test-sample decile edges applied as constants; membership then depends only on
   the name's own past 63 days + a constant); (c) job_calsplit2007.py adds a strict
   2007-01-01 calendar cut inside the holdout so the GFC is entirely out of training.
   Results fold into the paper win or lose.

3. frtb_bench.py skew-t defect (FATAL claim) — TRUE, CONFIRMED IN CODE, RE-RUN QUEUED.
   Verified: skewt_ppf(t,nu_,la_) never uses la_ (always the symmetric standardized t) and
   params.get('nu',8) always returns 8 because arch names the skew-t dof 'eta'. The
   "GJR-skew-t" benchmark was therefore GJR-vol x symmetric t(8), mean term also omitted.
   FIX: job_frtb_skewt.py re-runs the full battery with the true Hansen (1994) inverse CDF
   (validated against the symmetric-t limit exactly and against arch's SkewStudent.ppf to
   1e-4, plus a 200k-draw simulation check), fitted eta/lambda per name, mean included.
   Table tab:frtb updates from frtb_bench_v2_results.json when it lands, with a disclosure
   note. Also caught by this audit: the caption said "7 quantile levels"; the battery
   averages 12. Fixed.

4. Horizon +1.4% vs ratio 0.9600->4.0% "provenance clash" (MAJOR) — FALSE, BUT DEFUSED.
   The +0.4%->+1.4% pair traces exactly to frtb_stress_results.json (h1: 0.3586 vs 0.3570;
   h10: 1.1603 vs 1.1438 = 1.42%; the same sentence quotes that file's stress-window
   pinballs verbatim). The 0.9662/0.9600/0.9507 ratios are a DIFFERENT study
   (horizon_results.json: fresh quantile model trained per horizon), shown only in the
   online appendix. No number is wrong; the two designs were not labeled as two designs.
   FIXED: a sentence now names both designs, their estimands, and why the numbers do not
   compare.

5. Stress-ledger row "t 0.2 / 0.4" (MAJOR) — TRUE, FIXED.
   Verified in frtb_holdout_results.json: 0.17@99 is the engine; 0.35@97.5 is the EVT tail
   WITHOUT the shift; the deployed variant at 97.5 is -1.09 (conservative direction,
   breach 2.21% vs 2.5%). Row now reports all three with variant labels.

6. MCS B=800 vs stated B=1,000 (MAJOR) — TRUE, FIXED.
   frtb_caviar.py: def mcs(...,B=800). The main battery (frtb_bench.py) uses B=1000.
   Conventions note now states both.

7. Zhang citation "wrong authors" (MAJOR) — FALSE FOR THE PAPER, TRUE FOR A SIDE DOC.
   refs_v3.bib zhang2024commonality is correct (Zhang, Zhang, Cucuringu, Qian, JFEC 2024)
   and the paper cites via \citet. The wrong authorship ("Zhang, Haerdle and Bommes")
   appeared in ADVERSARIAL_REVIEW_PROMPT.md — my own prompt document, not the manuscript.
   Fixed there.

8. TUNING_GRID_PREREG.md 404 in the paper repo (MAJOR) — TRUE, FIXED.
   The file lives in the strategies repo docs/; the paper repo referenced it without
   carrying it. Copied into the paper repo this sync.

9. Registration has no independent timestamp (MAJOR) — CONCEDED HONESTLY (unchanged from
   R1 triage): the paper claims diffability, not notarization; OSF for future work.
   The frozen-threshold and calendar-cut re-runs reduce what registration must carry:
   the strongest results now hold under rules a hostile reader can recompute from
   public constants.

10. Survivorship of the holdout SQL (MAJOR) — PARTLY TRUE, ARMOR QUEUED.
    The >=3000-obs filter + full-window mcap ranking do condition on survival; the paper
    said the RANKING comparison is unaffected (both models score the same names) and that
    stands. The sharper "selection on later information" point is answered by
    job_pit_universe.py: top 200 by Q1-2000 mcap, no minimum-history filter, delisting
    returns appended, names ride to their delisting date; fitting floors applied
    symmetrically and attrition reported. New protocol subsection carries the design;
    numbers fold on landing.

11. Per-name 60/40 calendar leakage (MAJOR) — CONCEDED IN PRINCIPLE, KILLED IN FACT.
    New subsection concedes the channel exactly as stated ("a per-asset split cannot by
    itself support a causal reading of a pooled model's edge"), then reports the strict
    calendar split: everything re-estimated pre-2020, test 2020+ for all names, top decile
    +2.47% DM 6.22 over 1,258 dates (design split: +2.7%, DM 6.5). Overall +0.71% DM 1.87.
    The 2007-cut variant (GFC fully out of training) is queued as the second barrel.

12. Multiplicity math / 163-test family (MAJOR) — PARTLY BOUGHT, FORMALIZED.
    The review's Bonferroni arithmetic mixes universes with different date counts and
    dependence structures; Bonferroni over dependent cells is the wrong tool. What we owe
    is FWER over the frontier grid, and job_romanowolf_v2.py delivers Romano-Wolf
    step-down over all 30 (signal x decile) cells with a stationary bootstrap over dates
    (blk 10 B=2000, blk 20 B=1000 sensitivity). v1 crashed on a datetime hashing bug;
    v2 fixed (numpy searchsorted). Cells that lose significance get named in the text —
    committed policy sentence already in the subsection. Cross-universe instruments
    (FX/indices) remain per-universe claims with disclosed families.

13. Conformal "finite-sample guarantee" language (MAJOR) — PARTLY TRUE, TIGHTENED.
    The body already scoped the proposition ("motivates the construction... evidence is
    empirical"); three deployment-facing uses of "finite-sample guarantee" did not carry
    the qualifier. All now read exchangeability-based / coverage margin, pointing to the
    scope paragraph.

14. Tie-not-loss needs an equivalence margin (MAJOR) — BOUGHT, IMPLEMENTED.
    Conventions now define the label: "tie" is used only where per-date DM cannot reject
    zero at two-sided 10% AND the point edge is inside +/-0.25% of the benchmark loss.
    Checked against the rows that use the label (calm quintile, CAViaR, era-rerun): all
    satisfy both bounds.

15. Placeholder DOI / ANONYMIZED repo URL (MAJOR) — TRUE, FIXED.
    Availability section now names the real public repository; the fake Zenodo URL is
    replaced by a plain statement that the archival DOI is minted at acceptance. Also
    fixed "authors'" -> "author's" (sole author).

16. Benchmark field weak (GAS 1-start/80-iter; no HAR-RV/Realized GARCH) (MAJOR) —
    UNCHANGED FROM R1: honestly labeled, appendix-grade GAS; realized-measure models
    remain the disclosed information-set boundary (TAQ backlog). The corrected skew-t
    strengthens the parametric field. No text change beyond what R1 already added.

17. FRTB capital arithmetic omits stressed-ES/LH/NMRF/PLA (MAJOR) — ALREADY SCOPED:
    the section is labeled illustrative, modelled-component-only. No change.

18. "Audit script outcome-seeking prose" (MINOR) — COSMETIC, ACCEPTED: comments in
    audit scripts assert what they verify; the assertions are the content. No change.

## The one question ("independently timestamped artifact + why qcut in confirmatory code")
Answer on the record: no independent timestamp exists for the holdout registration —
diffability is the claim, OSF is the future practice — and the qcut choice was the
conditional-sort convention, now audited in-paper and re-run under frozen design-era
thresholds and a 2007 calendar cut. If those runs land supportive, the confirmatory
result no longer leans on trust at all; if they land adverse, they get reported with
the same prominence. That is the whole policy.

## Armor results (all five ran 2026-09-04; folded into both builds)
- Romano-Wolf FWER (romanowolf_results.json): 9 of 30 cells survive 5% FWER under BOTH
  block lengths, including all three top deciles (mk63_d10 t=9.4, skew63_d10 t=9.2,
  jump5_d10 t=5.1, adj p<0.001) plus mk63_d9 (adj p=.022), skew63_d9/d7, jump5_d1/d3/d4.
  Every mid-grid cell with unadjusted t~2 dies (mk63_d6 2.34, jump5_d7 2.08, skew63_d1
  2.01). The paper's claims rest on survivors; the losers are named in the text. WIN.
- Calendar split 2020 (calendar_split_results.json): top decile +2.47% DM 6.22 over
  1,258 dates; overall +0.71% DM 1.87. No calendar overlap anywhere. WIN.
- Calendar split 2007 (calsplit2007_results.json): GFC entirely out of training;
  overall +0.29% DM 3.08 over 1,762 dates; qcut profile keeps its shape (top three
  deciles +0.45..1.04 vs +0.06..0.09 bottom three); frozen top cell underpowered
  (3.4% occupancy, +0.85%, DM 0.7) - reported as such. WIN overall, thin-cell caveat.
- Frozen-threshold holdout (holdout_frozen_results.json): threshold shape survives the
  real-time rule (bins 8/9/10: +0.82/+0.92/+1.02 vs ~0 below); top-bin point edge
  LARGER than qcut's (+1.02 vs +0.89) but cell thins to 3.3% occupancy and DM drops
  to 1.11 (NW-lag insensitive 5-44). Reported honestly; the PIT run is the decisive
  frozen-rule test. MIXED, disclosed.
- Point-in-time universe (pit_universe_results.json): THE STRONGEST REPLICATION.
  Top 200 by Q1-2000 mcap, no history filter, 79 delisting returns ridden, 164/200
  clear symmetric fitting floors. Overall +0.58% DM 8.96 (2,692 dates); frozen top
  bucket +2.94% DM 6.6; bottom +0.44% DM 5.4. The survivor tilt was biasing the
  reported edge DOWN. Survivorship attack now works for us. WIN.
- Corrected skew-t battery (frtb_bench_v2_results.json): GJR row 0.3574 -> 0.3562,
  now passes both 99% tests (Kupiec .062, Christoffersen .103); hybrid margin DM
  5.73 -> 4.52; every other row reproduces to the 4th decimal; MCS still {hybrid}
  alone. Median fitted eta 4.2, lambda -0.015 (61% negative skew). Table 6 updated
  with a correction note crediting adversarial review. WIN (honest correction).
