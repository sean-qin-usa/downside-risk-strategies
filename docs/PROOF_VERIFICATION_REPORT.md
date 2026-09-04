# Proof & Equation Verification Report — `gbc_downside_main.tex`

**Date:** 2026-08-03
**Scope:** Every displayed equation and all four formal results (two lemmas, two propositions) in the Methods section (lines 376–1150). No new theorems or proofs appear after line 1150; later sections only reference these results.

**Verification method (five independent passes):**

1. My own line-by-line re-derivation + numerical checks in Python (SciPy).
2. Independent fresh-context auditor A ("re-derive everything, state missing hypotheses").
3. Independent fresh-context auditor B (adversarial: "try to break each proof," with Monte-Carlo reproductions).
4. **ChatGPT** (Plus, High reasoning) — driven in-browser, section-by-section, ran its own code.
5. **Gemini** (Pro, Extended thinking) — driven in-browser, section-by-section.

The five passes converge. Headline finding: **no result is mathematically false, and nothing is hallucinated.** The underlying mathematics is sound and the numbers reproduce exactly. What the audit found is a set of *missing hypotheses* and *terse steps* that a top journal referee would flag, plus **one genuine factual error in a prose remark** and **one overclaim about continuity**. All are fixable without changing any result.

---

## 1. Consensus verdict table

| # | Result | Me | Auditor A | Auditor B | ChatGPT | Gemini | Consensus |
|---|--------|----|-----------|-----------|---------|--------|-----------|
| L1 | Pinball regret identity | Correct, terse | Correct-but-terse | Cannot break | GAP (atom/derivative) | Correct-but-terse | **Correct; justify the derivative step; add finite-mean hypothesis** |
| P1 | Split-conformal validity | Correct, terse | Correct-but-terse (missing hyp.) | **Broke upper bound with ties** | ERROR (ties + endpoint) | GAP (no-ties) | **Correct given a no-ties/continuity hypothesis — which is currently missing** |
| P2 | Tail wedge (kurtosis) | Correct | Correct (remark has error) | Partial (τ*<½ not shown) | Terse (τ* fine via min) | GAP (τ*<½) | **Result correct; add one line that τ* ∈ (0,½) by intersecting with ½** |
| L2 | Generative sampler | Correct, terse | Correct-but-terse | Cannot break | Correct-but-terse | Correct | **Correct; make the inverse-of-inverse step explicit** |
| Eq | EVT/GPD splice (eq:evt) | Correct algebra; splice caveat | Correct; splice caveat | Correct; splice caveat | ERROR *for the conditional splice*; algebra correct | ERROR (continuity flawed) | **Algebra correct; "splices continuously" overclaims — see §4** |
| Rk | Crossover remark (rem:crossover) | — | **ERROR** | (numeric) | **ERROR (τc ≈ 0.0179)** | **ERROR (τc ≈ 0.0179)** | **Factual error: fix the wording — see §3** |
| Eq | Pinball, GARCH-t, IQN, Gibbs, score | Correct | Correct | Correct | — | — | **All correct** |

Numerical claims that were re-checked and reproduce exactly: unit-variance `t_3` quantiles (5%: −1.36 vs normal −1.64; 1%: −2.62 vs normal −2.33); the pinball regret identity vs Monte Carlo; the `t_3`-vs-normal crossover level (all three code-running checkers independently returned **τc ≈ 0.01794**).

---

## 2. The four proofs — detailed findings

### L1 — Pinball regret identity `\label{lem:regret}`
**Correct.** `dS/dq = F(q) − τ` and integrating gives the identity; the quadratic sandwich follows from `m ≤ f ≤ M`. Two things a referee will demand:

- The derivative step is written as "by dominated convergence," but `ρ_τ` is not differentiable at 0. The correct justification is the Lipschitz bound `|ρ_τ(Z−q) − ρ_τ(Z−q′)| ≤ max(τ,1−τ)|q−q′|` (dominated *difference quotients*). At an atom the one-sided derivatives differ: `S′_−(q)=F(q⁻)−τ`, `S′_+(q)=F(q)−τ`; since the result is then integrated, atoms are a null set, so **the identity itself needs no continuity assumption** — worth stating as a strength.
- The quadratic bound's step `F(u)−τ = F(u)−F(q_F)` needs `F(q_F)=τ`, which is *supplied* by the density hypothesis (absolute continuity ⇒ `F` continuous). One clause fixes it.
- Add the standing hypothesis `E|Z| < ∞` so `S(q)` is finite.
- Fix the nonnegativity wording: as written it only literally covers `q > q_F`; state the `q < q_F` case (reversed orientation) too.

### P1 — Split-conformal validity `\label{prop:conformal}`
**Correct, but a required hypothesis is missing — this is the most important fix.** Under exchangeability *and a.s. distinct residuals*, the rank of `e_{n+1}` is uniform on `{1,…,n+1}`, coverage `= ⌈(n+1)τ⌉/(n+1) ∈ [τ, τ+1/(n+1))`.

- **Missing no-ties/continuity assumption.** Auditor B and both external models broke the *upper* bound by forcing ties (with identical residuals coverage → 1). Add "continuous error distribution (a.s. distinct residuals), or randomized tie-breaking."
- **Endpoint caveat (ChatGPT + Auditor B):** if `⌈(n+1)τ⌉ = n+1` (τ near 1), the order statistic of `n` calibration points is undefined; adopt the convention `c_τ = +∞` there. Relevant because the shift is applied per level across the whole curve, including upper levels.
- The upper bound is actually **strict** (`< τ + 1/(n+1)`); keeping `≤` is true but never attained. Coverage is **marginal**, not conditional on `s` — worth one clause given the pooled-state setup.

### P2 — Tail wedge under kurtosis misspecification `\label{prop:wedge}`
**Correct.** Regular variation of the unit-variance `t_ν` tail gives `Q_ν(τ) = −(c_ν/τ)^{1/ν}(1+o(1))`; the unit-variance rescaling changes only the constant `c_ν`, not the tail index `ν`, so the ratio diverges and the ordering holds for small τ.

- On `τ* ∈ (0,½)`: the asymptotics give ordering below *some* `δ>0`. The proposition only claims *existence* of a `τ*` in `(0,½)`, which follows immediately by taking **`τ* < min(δ, ½)`** (ChatGPT's nuance). Gemini/Auditor B flagged this as a gap because the proof doesn't *locate* the crossover — but locating it isn't claimed. Add the one-line `min(·,½)` remark and the point is airtight.
- State explicitly `ν₁, ν₂ > 2` (finite variance) and cite the RV quantile-inversion (de Haan–Ferreira / Karamata).

### L2 — Generative sampler validity `\label{lem:sampler}`
**Correct.** Standard inverse-transform. Two terse spots to expand: (i) `P(τ ≤ a) = a` because `τ ∼ U(0,1)` (unstated); (ii) name the step that the generalized inverse of a nondecreasing left-continuous quantile function returns the function itself (the Galois "inverse-of-inverse" duality) — that last step *is* the content and is currently hand-waved as "which equals that supremum." Left-continuity + monotonicity are jointly sufficient; no error.

---

## 3. The one genuine error: the crossover remark `\label{rem:crossover}`

The remark states the deployable levels **"τ ≤ 0.025 sit below the empirical crossover."** This is **numerically false.** All three code-running checkers put the `t_3`-vs-normal quantile crossover at **τc ≈ 0.0179 (1.79%)**. Therefore:

- `τ = 0.01` is below the crossover (fat tail more extreme) ✓
- `τ = 0.02` and `τ = 0.025` are **above** it — there the unit-variance `t_3` quantile is *less* extreme than the normal (at 2.5%: −1.837 vs −1.960).

The rhetorical point (that whole-distribution/CRPS scoring can rank a fat-tail model *below* a thin-tail one at these levels) is stated for exactly the level where it does not hold at 2.5%. **Fix:** reword to "the deepest deployable level (τ = 0.01) sits below the crossover (≈ 1.79%), while τ = 0.025 straddles it." The surrounding argument is unaffected.

---

## 4. The one overclaim: EVT "splices continuously" (eq:evt)

The **algebra is correct**: solving `τ = p₀(1+ξ(x−u)/β)^{−1/ξ}` gives `q_EVT(τ) = −[u + (β/ξ)((τ/p₀)^{−ξ} − 1)]`, and `q_EVT(p₀) = −u`. So the EVT curve is continuous *at its own endpoint*. But the paper says it "splices continuously into the Stage-2 curve," and the Stage-2 body quantile at `p₀` is the **state-conditional** `q̃(p₀|s)`, whereas `u` is fixed at the **unconditional** empirical loss quantile. These coincide only if `u = −q̃(p₀|s)` for every `s`, which generally fails. **Fix:** either (a) anchor the threshold at the body model's own `p₀`-quantile, `u(s) = −q̃(p₀|s)`, or (b) downgrade the wording to "continuous at the EVT endpoint; approximately continuous with the body up to the gap `−u − q̃(p₀|s)`." Add the standing GPD hypotheses `β>0`, `1+ξ(x−u)/β>0`, and the `ξ→0` (exponential) limit.

---

## 5. Everything else checks out

- `eq:pinball` (check loss), `eq:garch` (GARCH-t recursion), `eq:shapeERM`, `eq:hybrid`, `eq:iqn` (cosine embedding — verbatim Dabney 2018 IQN), `eq:gibbs` (Gibbs/generalized-Bayes posterior), and `eq:score` (windowed excess-kurtosis / skewness moments): **all correct.**
- The Gibbs `ω` one-step rescaling rule (`posterior variance ∝ 1/ω`, so `ω ← ω·(SD_post/se_boot)²` lands the SD in one step) was numerically confirmed and is honestly hedged to the approximately-Gaussian regime.

---

## 6. How top journals want this structured (and where to aim)

Based on the current author guidelines (2024–2026) of Annals of Statistics, JASA T&M, JRSS-B, Biometrika, Journal of Econometrics, and Journal of Financial Econometrics:

- **This is not an Annals-of-Statistics paper.** AoS wants deep theorems *as the payload*; four elementary (though correct and useful) formal results wrapped around a ~70%-empirical risk-forecasting study reads as "thin theory + application" there. The natural homes are **Journal of Financial Econometrics** or **Journal of Econometrics** (best fit for a VaR/ES downside-risk paper with strong empirics and supporting theory), or a **sharpened JASA Theory & Methods** version if the results are recast as methodological guarantees. Your own in-file FORMAT NOTE already targets JFEC/JBF/Quantitative Finance, which is consistent.
- **Proof placement:** the dominant convention (explicit in JRSS-B: "development of mathematical expressions… presented in appendixes, only the relevant equations in the body") is to **state each result in the main text next to its assumptions, and defer full proofs to an appendix or online supplement.** Keep at most a one-line proof sketch inline for the headline result. → I have expanded the proofs and moved the rigorous versions to a new **Appendix B (Proofs)**, leaving compact statements + sketches in the Methods body.
- **Code:** never printed in the paper. JRSS-B and JASA now effectively *require* a public replication repository with a **Zenodo DOI cited in the main text**, plus a Data/Code Availability Statement; JFEC runs a replicability review as a condition of acceptance. Your algorithm boxes stay; add a one-paragraph availability statement pointing at the repo+DOI.
- **Figures/charts:** normal even in theory-forward papers, but *confirmatory and compact* — keep 1–4 core figures/tables in the body (the pipeline diagram and the frontier/decile results), push extended simulation grids and robustness tables to a supplement. A theory-forward paper is ~10–25% empirical; a methods paper 40–70%. At ~70% empirical you are squarely a *methods/econometrics* paper, which is fine for JFEC/JoE and argues against trimming the empirics to chase a pure-theory venue.

Sources: imstat.org (AoS manuscript prep & supplement instructions); academic.oup.com/jrsssb, /biomet, /jfec (general instructions); tandfonline.com JASA reproducibility (2024); sciencedirect.com Journal of Econometrics guide for authors.

---

## 7. Bottom line

Nothing in the paper's mathematics is invented or wrong. Priority fixes before submission, in order:

1. **Reword `rem:crossover`** — the "τ ≤ 0.025 below the crossover" claim is false; crossover ≈ 1.79%. *(genuine error)*
2. **Add the no-ties/continuity hypothesis to `prop:conformal`** (and the `⌈(n+1)τ⌉=n+1` endpoint convention). *(missing hypothesis that breaks the stated upper bound)*
3. **Soften/repair the EVT "splices continuously" claim** (unconditional `u` vs state-conditional body). *(overclaim)*
4. **Expand the two terse proofs** (`lem:regret` derivative justification + finite-mean; `lem:sampler` inverse-of-inverse step) and **add the `τ* < min(δ,½)` line** to `prop:wedge`.
5. **Move full proofs to Appendix B**, keep statements + sketches inline; add a code/data availability statement.

Items 1–5 are implemented in the companion edit to `gbc_downside_main.tex` (see the new Appendix B and the inline fixes).
