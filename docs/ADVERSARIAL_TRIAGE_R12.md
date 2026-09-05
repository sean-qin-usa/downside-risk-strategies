# Adversarial Triage — Round 12 (Review #17: prose/tone audit)

Review #17 re-read the full source and put the manuscript at ~4.5/10 on
"AI-polished sounding" (down from 7--8), with the correct diagnosis: the
signal is rhetorical scaffolding and referee-response narration, not
em-dashes or vocabulary. Four technical text fixes plus a structural de-AI
pass, all applied to both builds.

## Technical text fixes (the must-do list)

1. **Stale FZ sentence** — "with ES from the fitted GPD tail" was a real
   code/text mismatch after the coherent-canonical change; now "with VaR and
   ES read from the coherent min-envelope curve Q*."
2. **"exact integral" → "numerical integral"** everywhere (four sites): it is
   a 20-node midpoint approximation, not exact.
3. **"uniquely able to sample"** removed from the intro; the IQN's distinction
   is now stated as direct drawing from a learned continuous quantile map (the
   Background already conceded GARCH-t/FHS also simulate).
4. **"necessity-not-sufficiency"** last occurrence → "neither necessary nor
   sufficient."
5. **Raw-mk63 "residual degree of freedom itself"** softened; the interpretation
   now leans on the frontier evidence and the t_ν-relative normalization, not
   the a-priori rhetoric.

## Structural de-AI pass

- **Thesis subheading deleted**; folded into the introduction as ordinary
  prose, with "wins decisively / never a detectable loss" de-pitched to
  "large and significant advantage / no detectable loss."
- **Six-part GBC comparison** (the "(1) Base measure … (6) Scope discipline"
  parallel list — a strong LLM marker) rewritten as two ordinary paragraphs.
- **Conversational GARCH questions** ("how big is a typical move today?… how
  likely is a move five times that?") and the "one-line logic" finishing-stage
  slogans replaced with plain description of what each stage estimates.
- **Applications de-pitched**: "A desk should therefore run the engine always"
  → "The gating experiment provides no evidence that day-level switching
  improves on continuous use of the flexible model"; "holding it is cheap …
  edge accrues automatically" removed.
- **"It fails, instructively."** deleted (gating paragraph).
- **Conclusion limitations** rewritten from eight staccato one-sentence
  verdicts into two flowing paragraphs (estimator/evidence limits; boundaries
  and future work).
- **Referee-response phrasing** neutralized: "the strongest replication in the
  paper" → "addresses survivorship directly"; "once the family is priced" →
  "under familywise control"; "whose omission would flatter our model" → "the
  strongest available comparator for the accuracy claim."
- **Abstract** de-pitched (the "Amortization:" colon-fragment became a
  sentence; "prices day-one listings" → "produces day-one risk forecasts for
  newly listed assets"), retrimmed to exactly 100 words.

## Em-dashes

220 (wave 7) → **0 prose em-dashes** in all three documents. What remains: the
title-page `Draft --- \today` and three table missing-value placeholders, both
conventional. Numeric en-dash ranges (DM 4.4--8.3, 2014--2024) untouched
throughout.

## Status

All three documents compile clean; submission text ends p41; reading copy
38pp. Review #17's technical mismatches are closed and its structural markers
(Thesis heading, six-part list, desk-should language, staccato conclusion,
referee narration) are gone. Its own note was that after these edits the paper
would "read much closer to an ordinary well-edited JFEC empirical paper."
