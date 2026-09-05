# Adversarial Triage — Round 11 (Review #16: canonical coherence + editorial) & authorship

Review #16 re-read the public `main` after wave 9. Verdict: science is
JFEC-level; two things left — make the coherent Q* the *canonical* code (not
just an audit arm), and finish the JFEC editorial pass. Both done.

## 1. Coherent Q* is now canonical (the one real technical item)

The audit had shown coherence, but `frtb_table.py` and `job_fz_fullpanel.py`
still shipped VaR = min(body, EVT) with ES from the GPD closed form. Both
scripts now assemble one monotonized min-envelope curve
Q*(u) = min(body, EVT) on a 20-node sub-α grid, take VaR at the α node
(re-anchored to the curve endpoint), and read ES as the numerical integral of
that same Q*. The GPD-closed-form ES convention is retired.

**Reran on host; the result strengthened, as the audit predicted:**
- Table 6 (`frtb_table_results.json`): hybrid+EVT ES −6.90 → −6.92 (a
  third-decimal move — the min-envelope binds on 38% of tail nodes but the two
  branches are close in the averaged tail, so ES barely shifts); raw hybrid
  best pinball 0.3551, sole 90% MCS survivor; DMs vs hybrid refreshed
  (GARCH-t 4.94, GJR 4.96, FHS pooled 6.12, per-name 5.17, rolling 5.68,
  HS 7.50, EWMA 8.65).
- Full-panel FZ0 (`fz_fullpanel_results.json`): the accuracy layer's edge
  **grew** — vs GARCH-t DM 4.0 → **4.8** at 1%, 4.4 → **5.1** at 2.5%; vs FHS
  4.9 at 1%; vs GAS 9.6 / 6.2. Engine FZ0 1% 2.147, 2.5% 1.849.

Text updated: eq. (hybrid) already carried the R[·] rearrangement form from
wave 9; Table 6 tablenote now says "numerical tail integral" and describes the
min-envelope curve (dropped "GPD closed form for the EVT tail" and "exact
integral"); FZ0 DMs refreshed in the battery paragraph and the OA summary row.

## 2. Four smaller technical items

- **"necessary but not sufficient" → "predictive but neither necessary nor
  sufficient"** everywhere (three sites incl. conclusion): the carbon/corn and
  Baltic-freight examples prove exactly non-necessity and non-sufficiency.
- **IQN sampler claim** fixed: dropped "a capability no tree ensemble or GARCH
  filter provides"; now "the network learns one continuous quantile map, so
  draws come by inverse transform without a fitted grid (a GARCH-t or FHS
  model also simulates)."
- **Lemma 1 statement**: "equality iff F ≡ τ on the interval" → "iff
  F(u) = τ for Lebesgue-almost every u" (master, OA proofs, matches the a.e.
  proof).
- **"only valid normalizer"** softened to "a finite-window null
  normalization, which stays well defined when the fitted ν ≤ 4."

## 3. Editorial / de-AI pass

- **Deleted** the self-incriminating Methods sentence ("For a finance-journal
  submission the algorithm boxes… can migrate to an appendix unchanged").
- **Self-referential meta-language removed**: "the paper is deliberate about
  which to use" → "we use trees for accuracy and the network when draws are
  needed"; "the exposition follows three reporting conventions fixed in
  advance" → "we fix three reporting conventions"; "the paper makes it as one"
  → "we make it as one"; "the choices … are deliberate" → plain reasons.
- **Punchline heading** "trees for accuracy, networks for generation" →
  "gradient boosting and neural quantile networks."
- **Marketing phrases** neutralized: "FHS and above" → "nests FHS";
  "the one rival the engine only ties" → "ties"; "holding it costs at most a
  rounding error while it collects +2.7%" → plain magnitude statement;
  abstract closer "orders its magnitude everywhere" → "strongly orders the
  magnitude … in the equity panel and across several external-market
  exercises."
- **Mechanism arc** ("Why one should expect this to work before seeing data",
  the closed inevitability argument) rewritten as a short "Motivation for the
  design" paragraph — states the statistical reasons, drops the retro-fitted
  "each choice had to be this one" rhetoric.
- **Abstract** opens declaratively ("We develop…") and reduced advertising.
- **Em-dashes**: 220 (wave 7) → **37 master / 32 submission / 0 online
  appendix**. Converted to commas, colons, semicolons, and parentheses;
  numeric en-dash ranges (DM 4.4--8.3) untouched.

## 4. Authorship (Sean's directive)

Both title pages now list **Sean Qin** (first author, corresponding) **and
Wenxin Jiang**. Acknowledgments shifted from "I thank Professor Wenxin Jiang
… all errors are mine" to "we … all errors are ours"; AI-assistance note now
plural ("the authors designed the research … and are responsible").
**Gate before submission**: Prof. Jiang must explicitly consent to
co-authorship — ScholarOne requires all named authors to approve. If she
prefers to remain an acknowledged advisor, it is a one-line revert.

## Status

Review #16's two blocking items (canonical coherence, editorial pass) are
closed; the coherent rerun strengthened the FZ0 result. All three documents
compile clean; submission text ends p41; reading copy 38pp.
