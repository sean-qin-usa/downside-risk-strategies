# Adversarial review #1 — triage (2026-09-04)

## Reliability note, first
Every "quoted" passage in this review is fabricated: the paper contains no "Section 3.1" sentence of that form, no "lag L=5" (ours is NW lag 10, stated), no 2023-2025 holdout (ours is 2000-2013), no acronym "RTMS", no "0.24%", no "-4.12%/-3.85%" pair, no "unprecedented accuracy", and one lemma/two propositions are real but not as described. The reviewer evidently reviewed an imagined paper. Attack CLASSES are triaged on merit anyway.

## Verdicts

1. Calendar-overlap leakage — REAL CLASS, PARTLY WRONG ON FACTS, NOW DOUBLE-ARMORED.
   Facts: both panels select near-complete histories, so per-name split points already fall on nearly the same calendar dates (the unbalanced-inception scenario in the review's "one question" barely exists in these universes). Sentence added to the protocol section. Definitive answer queued: job_calendar_split.py — strict single calendar cut (train < 2020-01-01 for everything incl. GARCH fits, pooled learner, tail; test 2020+ for all names). If the frontier profile survives, the channel is dead.
   Also wrong in the attack: "GARCH recursion filtered over full history leaks future volatility states into training features" — the recursion at time t uses returns up to t-1 only; parameters are fit on train only. No forward information enters any training feature.

2. Inference/multiplicity — HALF WRONG, HALF WORTH BUYING.
   Wrong half: per-date aggregation is the cross-sectional-dependence FIX (collapse the cross-section per date, then HAC over dates; effective n = #dates), not the sin; lag is 10 not 5; MCS/SPA already use stationary block bootstrap over dates.
   Bought half: formal FWER over the full grid was our thinnest armor → job_romanowolf.py queued: Romano-Wolf step-down over all 30 (signal x decile) hypotheses, stationary bootstrap over dates (preserves cross-hypothesis dependence), B=2000. Mechanics validated on synthetic data (planted effects recovered exactly; nulls rejected).

3. Registration evidentiary value + survivorship — FAIR POINT, HONESTLY HANDLED.
   Added to the paper: the holdout pipeline is line-for-line diffable against the public design-era pipeline (real, checkable claim; stronger than an honor pledge, weaker than OSF — future registrations go through OSF, noted for Paper B). Survivorship: acknowledged in the protocol with the correct scope — the comparison is relative on the same names, so the filter tilts the universe, not the model ranking. The review's "top 200 selected after the holdout period" is factually wrong (selection is within-era by market cap, disclosed).

4. Benchmarks — PARTLY FAIR, PARTLY ANSWERED.
   HAR-RV/Realized GARCH absence: known gap, TAQ-based battery remains backlogged; the paper's scope defense is that the battery covers what desks run plus CAViaR and a GAS variant. GAS-strawman: fair to a point — ours is honestly labeled and appendix-grade; a gradient-polished PZC implementation is a legitimate strengthening (backlogged). FHS: ours is the standard filtered variant; "aged-volatility scaling" is not the standard desk description.

5. Economic size — ANSWERED IN-PAPER.
   The average edge being small is the paper's own thesis (concentration, tie-not-loss); the engine changes the reported risk number, not positions, and monitor churn is 0.68 entries/name-year (measured). Capital section is labeled illustrative arithmetic, modelled component only. A transaction-cost simulation of hedge rebalancing is a possible future note, not a gap in the claims made.

6. Novelty ("repackaged kurtosis") — ANSWERED BY DESIGN + TWO RESULTS.
   The score is not a feature of the engine (the engine's inputs contain no kurtosis terms); it is a monitor that predicts WHERE the engine wins. The absorption study (reweighted-FHS fails, DM -11) and the double sort (vol alone carries nothing) already answer "just append a 4th-moment feature."

7. Internal contradictions — FABRICATED.
   The specific number pairs and phrases do not exist. The genuine era-dependence (10-day result) is disclosed by the paper itself, in its own voice.

8. Theory-thin / fit — POSITIONING RISK, ACCEPTED.
   JFEC publishes empirical ML (Zhang et al. 2024). The cover letter frames the contribution as evaluation-rigorous empirics; if an editor wants more theory, that is a revision conversation, not a hidden defect.

9. Reproducibility — PARTLY DONE, KEEP.
   toy_example.py (synthetic end-to-end) is already in the availability statement; licensed-data rebuild is the field's standard posture and JFEC's own policy allows the exemption request.

## Actions taken tonight
- Protocol section: +2 defenses (diffability of the frozen pipeline; split-date alignment + survivorship scope), both builds, compiled clean (36pp / 49pp).
- Queued: job_calendar_split.py (leakage kill-shot), job_romanowolf.py (FWER over the whole grid).
- Next fold: if both come back supportive, one sentence each in the frontier section; if either comes back adverse, it gets reported with the same prominence as a win — same rule as always.
