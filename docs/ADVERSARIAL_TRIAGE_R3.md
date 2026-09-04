# Adversarial reviews #3 and #4 — triage (2026-09-04, second wave)

Review #3: fresh max-hostility referee against the armored build. Review #4: a re-read
of the armored build + repo, verdict moved Reject -> Major Revision with a priority
list. Both were verified claim-by-claim before action.

## The scoreboard first
Review #4 concedes the armor held: calendar splits (2020 + pre-GFC 2007), Romano-Wolf
FWER, and the point-in-time universe "successfully neutralize" the leakage,
multiplicity, and survivorship attacks. The frontier core is no longer contested by
either review. The remaining attacks target the deployed variant's FZ0 concession,
benchmark implementation details, provenance language, and overclaims.

## Verdicts and actions

1. REPO CONTRADICTS PAPER on the skew-t correction (R4, submission-blocking) — TRUE,
   FIXED. The paper reported the corrected GJR row while public code/frtb_bench.py
   still carried the defect and frtb_bench_results.json the old numbers. Fixed:
   code/frtb_bench.py replaced by the corrected battery (Hansen inverse CDF validated
   against arch's SkewStudent.ppf and the symmetric limit; correction history in the
   header), frtb_bench_v2_results.json shipped alongside, pre-correction artifact
   preserved in git history, and the availability section now states exactly this.

2. Deployed-variant FZ0 loss at 2.5% (R3 FATAL #1) — DISCLOSED BY US, NOW ALSO
   ATTACKED CONSTRUCTIVELY. The framing answer is already in the paper (the shift is
   a chosen conservatism margin; every "lowest FZ0" claim scoped to the accuracy
   layer; regulators score breach counts, not FZ0). The constructive answer is
   queued: job_fz_aci.py tests an ADAPTIVE pooled shift (Gibbs-Candes style, daily
   update from panel breach frequency, warm start at the static value, gamma 0.02
   and 0.05). If it restores nominal 97.5% coverage without losing FZ0 to GARCH-t,
   the concession disappears and R3's "one question" has a direct answer. Results
   fold in win or lose.

3. CAViaR parity / Occam (R3 FATAL #2) — ANSWERED WITH CAPABILITIES + BACKTESTS.
   New text: SAV-CAViaR models one quantile level per fit, produces no ES (the FRTB
   metric) without an ad-hoc stage, cannot price a new listing, and its pooled
   exception tests reject at machine zero at both levels in the same battery, while
   the EVT-tailed engine sits at p=0.02-0.07 pooled and passes per-asset and
   date-clustered restatements. The accuracy tie is between a specialized
   single-level autoregression and one shared model carrying the whole deployment
   brief. (R3's own refutation request — "evidence that SAV-CAViaR fails regulatory
   exception backtesting where the hybrid passes" — was already in
   frtb_caviar_results.json.)

4. Ten-day capital release fails in 2008 (R3 MAJOR) — ALREADY DISCLOSED; NOW CAVEATED
   IN-ROW. The 14.6% row is labeled "(2014-24 regime only)" inside the table; the
   abstract never carried it; the era-reversal paragraph stands. The h=1 rows are
   the era-robust component and say so.

5. Prop 1 ornamental under dependence (R3 MAJOR) — PARTLY BOUGHT. Title now reads
   "split-conformal validity under exchangeability"; scope paragraph cites
   Chernozhukov-Wuthrich-Zhu (COLT 2018) for dependence-valid constructions and
   Gibbs-Candes ACI as the deployment escalation; the empirical audit remains the
   arbiter. Not demoted to a remark: the proposition motivates a stage the engine
   actually uses, and its scope is stated in the statement itself.

6. Frozen-threshold holdout loses significance (R3 MAJOR) — TRUE AND DISCLOSED BY US;
   REFEREE-REQUESTED VARIANT QUEUED. job_holdout_recthr.py implements the recursive
   ex-ante rule (expanding pooled 90th percentile over strictly earlier dates,
   250-date burn-in, no design-era constant, no test-era ranks). Occupancy
   self-adapts to the era, which restores the power the frozen constant lost.

7. Per-name FHS not the bank implementation (R4) — TRUE, QUEUED. The battery's fhs
   row is the pooled variant (the code comment even said "approximate"). 
   job_fhs_pername.py adds per-name train-constant AND per-name rolling-500d causal
   FHS on the identical panel. Results enter the battery table win or lose.

8. "Registered" language + TUNING_GRID_PREREG mismatch (R4) — TRUE, FIXED. The cited
   prereg file was a different study's trading grid — removed from the availability
   statement and from the paper repo. All evidentiary uses of "registered" renamed
   to frozen-specification / pre-committed, with a new sentence saying explicitly
   why: no third-party timestamp exists, the claim is diffability, not notarization.
   The availability statement now points to the actual frozen artifact
   (code/job_wrds_holdout.py header, containing the written-in-advance predictions).
   "Confirmatory holdout" renamed "untouched-era holdout" throughout; the
   point-in-time run is the operational replication.

9. Overclaims (R4) — DELETED OR NARROWED. "Worst outcome anywhere is a tie / costs
   nothing" -> bounded-equivalence phrasing with the FZ0 concession named; "~2-3%
   wrong on that name" -> conditional average over the region, twice; "capital
   arithmetic and maximum-expected-utility arithmetic coincide" -> illustrative
   certainty-equivalent reading, not a derived optimality result; abstract
   "over-charges capital" -> "would mechanically inflate an ES-driven capital
   component"; availability "every table and figure" -> scoped to WRDS-based
   exhibits with Bloomberg exhibits preserved as-run.

10. GAS single-start/no-convergence-check (R4) — ACKNOWLEDGED, UNCHANGED. The paper
    claims only "a one-factor FZ-score-driven benchmark in the style of PZC," which
    is what it is. Multi-start polish stays on the backlog.

11. Bloomberg exhibits frozen (R3 MINOR) — DISCLOSED; availability language now
    scopes reproducibility to WRDS-based exhibits explicitly.

12. Contribution order — REWEIGHTED per author's call: amortization/cold-start (the
    unlosable claim) now leads the contributions list, matching the abstract's
    order; industry battery second; frontier third; theory fourth.

## Newly queued jobs (fold on landing, win or lose)
- job_fz_aci.py        -> fz_aci_results.json        (adaptive shift: coverage without the FZ0 loss?)
- job_fhs_pername.py   -> fhs_pername_results.json   (bank-exact FHS rows)
- job_holdout_recthr.py-> holdout_recthr_results.json (recursive ex-ante threshold)
