# Adversarial Triage -- Round 15 (Review #20: REJECT at 8e1fd77, 22 ranked attacks)

The one substantive question the reviewer asked: does the DEPLOYED composite score
(not mk63 alone) actually earn its OOS edge, and is the content raw tail activity or
model-relative departure? Both were run against artifacts and folded in win-or-lose.

## FATAL #1 -- "the deployed composite score was never evaluated" -- ANSWERED

The reviewer is correct that the frontier program sorted each signal separately and the
+2.7% headline was mk63 alone, while Algorithm 4 / OA.2 deploys the MAX of the three
signal percentiles. Built and evaluated the exact deployed object (job_composite.py,
composite_results.json; 200 names, 221.6k test rows):

- composite score (max of the three trailing-panel percentiles, RE-DECILED) top decile:
  +2.79% (DM 8.9), a clean 10% cell; deciles 1-9 flat in [-0.3%, +0.35%].
- causal expanding prior-only 90th-pct cutoff on the composite (as deployed): +2.72% (DM 9.0).
- components alone: mk63 +2.98% (DM 10.5) | skew63 +2.78% (DM 9.9) | jump5 +1.96% (DM 7.6).
- literal max-of-decile-RANKS==10 = union of the three top deciles: 19.3% occupancy, +1.72%;
  reported as the union (not a 10% cell), which is why we headline the re-deciled score.

VERDICT: the object the paper deploys IS evaluated and reproduces the frontier. New paragraph
"The deployed composite" added to both builds; Algorithm 4 / OA.2 step (iii) rewritten from
the ambiguous "rank of the maximum" to "the maximum of the three percentiles, re-ranked into
deciles" so the algorithm text matches exactly what was evaluated.

## FATAL #2 -- model-relative vs raw -- REAFFIRMED from R19 (already conceded and defended)

Settled in R19 by the discriminating tests (job_mechanism.py): the nu-relative normalization
has negative incremental content controlling for raw kurtosis (Fama-MacBeth t_nurel = -5.2),
so the content is the absolute level of recent tail activity, i.e. trailing kurtosis of the
STANDARDIZED residuals -- a first-order departure from the fitted t_nu shape -- and only the
finer per-name nu-normalization is rejected. Title thesis defended precisely, not overclaimed.

## Text fixes this round (all four verified against the sources, applied to both builds)

- [#3] "governs" -> "predicts" (score is predictive, not a structural law).
- [#7] conformal "carries the guarantee" -> "is motivated by" (split conformal is exact only
  under exchangeability, which daily returns violate; already flagged in-text).
- [#8] false "infinite-variance kurtosis" claim -> correct asymptotic statement (sample kurtosis
  of a t_nu has finite variance for nu > 8; the estimator noise argument restated correctly).
- [#13] day-level trading-timing sentence removed (unsupported by the oracle-gap result).

## Already handled in prior rounds (reaffirmed, not re-litigated)

- [#4] CAViaR MCS: HLN standardized-range elimination (R19); 90% MCS = {hybrid_GBM, caviar_sav},
  DM 0.4 p 0.34. [#5] "pre-registered" softened to "specified before the run" (R19).
- [#9] production ES reads the coherent min-envelope Q* tail integral (R14). [#10] shape-not-
  staleness de-verdicted; annual refit removes the aggregate gap but not the conditional
  concentration (R14). [#18] Kupiec 81->84% to match the canonical skew-t figure (R14).

## [#21] reproducibility / path leak -- FIXED for the replication package; broader item flagged

code/job_wrds_holdout.py scrubbed: personal WRDS username -> os.environ['WRDS_USERNAME'] with a
placeholder default; hard-coded C:\Users\OWNER project path -> os.environ.get('GBC_PROJECT_DIR',
script dir); Windows PGPASSFILE line dropped (the wrds package reads the standard pgpass). Header
documents the two env vars. The curated replication repo (downside-risk-paper/code) now carries
the scrubbed file. BROADER FINDING for Sean's decision: the same WRDS username string appears in
many non-curated scripts across the strategies repo (code/, autojobs/, _github_public/); it is a
login name not a password, but it should not sit in any public repo -- resolve by the planned
private-flip of downside-risk-strategies and/or a repo-wide string scrub before going public.

## Lower-ranked / revision-scale (acknowledged, not blocking)

[#6] holdout decile detail, [#11] PZC multi-start battery, [#12] monetary-welfare economic case,
[#14] the 36 dropped names (intention-to-treat bounds), [#15] multiplicity across the score menu,
[#19] novelty positioning, [#20] journal-fit framing, [#22] residual AI-prose cadence -- each is
a revision-scale addition or a framing choice, none contradicts an artifact.

## Status
All three builds compile clean, no undefined refs. Reading copy 39pp; OA 16pp. JFEC submission
text now runs to the top of p42 (40 full pages of text p2-p41 plus the ~130-word limitations
paragraph); within the soft "typically not exceed 40 double-spaced pages" limit; conclusion and
composite paragraph tightened losslessly to hold the length. code/job_wrds_holdout.py scrubbed;
job_composite.py + composite_results.json shipped.
