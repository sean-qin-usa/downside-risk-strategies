# AI-prose check — run against the manuscript (wave 8)

Protocol: docs/PROSE_CHECK_PROMPT.md, executed on `paper_A_frontier.tex`
(the same body text as the submission build). Findings were **fixed in place**,
not just listed; both builds and the online appendix carry the fixes.

## PATTERN COUNTS (before → after)

| # | Tell | Before | After |
|---|---|---|---|
| 1 | Triadic incantations ("decisively, significantly, and portably") | 1 | 0 |
| 2 | "not merely X…" reversal templates | 0 | 0 |
| 3 | Sentence-initial Crucially/Importantly/Notably/… | 0 | 0 |
| 4 | Inflated vocab (leverage*/showcase/delve/landscape/holistic/comprehensive/seamless/pivotal/underscore/framework†) | 0 | 0 |
| 5 | Uniform sentence rhythm | localized | reduced in rewritten paragraphs |
| 6 | Self-narrating transitions ("Having established…", "Taken together…") | 0 | 0 |
| 7 | Hedging boilerplate ("it is important to note", "may potentially") | 0 | 0 |
| 8 | **Em-dashes** | **220** | **119** (main), 106 (submission build), none above 3 per prose paragraph |
| 9 | Conclusion grandeur ("paves the way", "opens avenues") | 0 | 0 |
| 10 | Ornamental anaphora | 0 | 0 |
| 12 | aforementioned/whilst/utilize/plethora/myriad/realm | 0 | 0 |

\* "leverage" appears only as the GJR *leverage effect* — a technical term, not the verb.
† "framework" appears once, correctly ("GBC as the framework, trees as the strongest estimator").
"robust" appears 6×, all technical (serial-correlation-robust SEs, robust stylized fact) except one
promotional use ("the robust engine") — removed.

## What was actually rewritten (the em-dash pass)

Twenty-plus paragraphs rewritten by hand, worst first: the abstract (2 dash
pairs → 0), the two-communities opener (7→1), the misreading paragraph (7→1,
including deletion of a clause that restated the same concession twice), the
GBC lit paragraph (4→0, plus removal of a doubled definition of the Gibbs
posterior and an explicit "what is deployed: the trees" sentence), the
contribution bullets (10→2), amortization (8→2), the FZ full-panel narrative
(9→3), the untouched-era holdout (8→2), the simulation (7→2), the CAViaR
caveats (7→2), the summary-of-results paragraph (5→0), the Romano–Wolf
paragraph (5→1), the gating paragraph (5→1), the GBC-deltas list (5→0), the
cross-asset audit paragraph (5→1), and the conclusion (tightened twice; now
ends on the oracle-gap sentence). Dashes that remain are mostly in the notation
glossary (a standard "$r_t$ — return" format) and single asides in technical
paragraphs, which is ordinary academic usage.

## Substantive catches made during the pass

1. The Gibbs-posterior definition appeared twice in one sentence (parenthetical
   + dash clause) — a classic generation artifact. Fixed.
2. The 2.5% coverage-shift concession was stated twice in one paragraph. Fixed.
3. The new OA Holm table initially listed PJM power as a survivor, but the
   paper's own cross-asset audit had already reclassified electricity as a
   log-return artifact on near-zero prices. Table and text now report seven
   real survivors with PJM flagged as the artifact — the kind of internal
   contradiction a referee hunts for, caught before it shipped.

## VERDICT

Before the pass, a suspicious referee would have flagged the em-dash density
(220 across 40 pages, with 10-dash paragraphs) and a handful of doubled
statements; everything else on the tell list was already clean, because the
claims are number-dense and the register is unusually concrete. After the pass
the highest-leverage remaining risk is not style but structure: the paper's
completeness (many audits, many robustness runs) is itself the residual "not
written by a hurried human" signal, and that is defensible — it is what the
adversarial-review process actually produced. Recommended reading order for a
final human pass: abstract, intro, conclusion, then the FZ battery narrative.
