# Adversarial reviews #9 and #10 - triage (2026-09-04, fifth wave)

Review #9: hostile desk-reject that reviewed a STALE BUILD - every one of its
"required changes" was already in the paper it claims to attack (calendar splits:
done, DM 6.22/3.08; Romano-Wolf: done, 9/30 survive; point-in-time universe with
delistings: done, edge grows to +2.94 DM 6.6; recursive GARCH filtration: parameters
were always train-only with a forward recursion, and the walk-forward below removes
even the staleness variant; per-name/rolling FHS: done; multi-start GAS: done;
"Zhang, Haerdle, Bommes" is the reviewer's hallucinated citation - the real
Zhang-Zhang-Cucuringu-Qian entry is verified in the bib; the quoted "navigating the
complex landscape" prose does not exist in the paper). No new content; no action
beyond this note.

Review #10 (constructive re-read): three substantive items, all actioned.

1. WALK-FORWARD MISMATCH (their top priority) - TRUE and now RESOLVED WITH THE
   EXPERIMENT THEY ASKED FOR. The evaluated protocol froze all stages once per
   split while Algorithm 1 recommended annual refits, leaving stale-GARCH as an
   alternative explanation for the score. job_walkforward.py runs the true annual
   walk-forward (per-name GARCH refit on expanding data at each Jan-1 cutoff
   2020-24; residuals, mk63, and pooled learner all rebuilt per cutoff). RESULT:
   top decile +2.47%, DM 6.05 (NW lags 5-44: 6.6-5.4), indistinguishable from the
   frozen-fit frontier; overall compresses to +0.32% (DM 0.8) because refits help
   the benchmark in the bulk. The frontier measures SHAPE, not staleness - the
   cleanest mechanism demonstration in the paper. Algorithm 1, the pipeline
   caption, and the protocol section now state evaluated-vs-production schedules
   explicitly, and the result is reported with the other splits.

2. "DEPLOYED ENGINE" INCLUDES A HARMFUL STAGE - ADOPTED THEIR REDEFINITION.
   The engine is now: core = residual hybrid + EVT (the accuracy layer); static
   conformal = OPTIONAL conservative coverage overlay (its costs quantified);
   adaptive = the overlay form that removes the overall FZ0 cost. Abstracts,
   contribution list, and production loop all updated. "Passes the per-asset
   restatements" narrowed everywhere to what 81%/86% supports: "passes the
   aggregate date-clustered test, with per-name diagnostics showing residual
   cross-sectional heterogeneity."

3. TEN-DAY PUBLIC ARTIFACTS STILL THREE-NODE - TRUE, CANONICALIZED. The repo now
   ships code/frtb_table.py -> results/frtb_table_results.json (Table 6) and
   code/frtb_stress_exact.py -> results/stress_es_results.json (ten-day, both
   eras); code/frtb_bench.py carries an explicit SUPERSEDED-for-Table-6 header;
   the stale frtb_stress.py, frtb_stress_results.json, and frtb_bench_results.json
   are removed from the working tree (preserved in git history, as the paper
   says). The availability section names the canonical pairs.

4. Tie wording - final pass done ("statistically indistinguishable /
   noninferior where tested"; "ties" reserved for shown equivalence).
5. Theory framing - softened to motivation: the lemma/proposition motivate
   looking where trailing shape diagnostics are extreme; the mk63-to-edge link
   is stated as established empirically, not theoretically.

## Where this leaves the record
Ten reviews, five waves. Every validation-design attack now has either a
by-construction refutation (calendar splits, walk-forward, recursive threshold,
PIT universe, FWER) or an honest quantified concession (overlay costs, era
dependence, pooled-test hypersensitivity). Both constructive reviewers place the
remaining risk on novelty and fit - the editor's question.
