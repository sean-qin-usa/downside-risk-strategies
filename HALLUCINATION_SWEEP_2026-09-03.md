# Paper A — Hallucination & Number Sweep vs the Memory Record (2026-09-03)

Method: every quantitative claim in `paper_A_frontier.tex` cross-checked against the result
memories (three-way-flagship, misspec-frontier + its ai2 results JSON + audited script,
frtb-industry-benchmark, crosscountry-singleasset, amort-agecurve, regime-gate, gibbs,
fz-ablation, m5) and, where available, the raw results JSONs and the audited source scripts.

## Verdict: no fabricated results found. Three provenance defects found and fixed.

**Verified clean (exact match to recorded results):** the three-way flagship table
(0.6543/0.6447/0.6478; calm→turbulent gap 0.0059→0.0247); frontier deciles (+2.46 kurtosis,
+2.37 asymmetry, +0.90 jump; DM 6.54 top / 1.41 bottom / 6.74 top-two / 5.67 overall;
top-decile kurt ≈25, |skew| ≈4); the full FX / country / cross-asset geography table
(ARS 0.880 DM 2.86, EGP 0.857 DM 3.80, crisis pool DM 4.12, majors −13.7, EM −9.5;
developed/emerging/frontier 1.007/1.012/0.993 with kurt 4.7/5.3/10.0, the four frontier wins
incl. DMs, corr 0.53; 13/43 cross-asset, corr 0.43; Philippines and carbon/corn
counterexamples); Korea 23/23 GARCH with DM −2.5..−5; the FRTB battery (every pinball, ES,
breach, Kupiec, and DM value; EVT variant values; CAViaR tie 0.3461/0.3460 DM 0.59; IQN v1
0.3650/DM 13.3/breach 3.2% and v2-recal 0.3638 vs 0.3632/DM 3.03/0.92%); ten-day + stress
numbers (−19.4/−15.4, −19.05/−17.70, 0.0265/0.033, stress 1.247<1.2605<1.262); horizon curve
0.966→0.951; amortization (6–10% young, 1.32M rows/720 names/288 held out, ablation +1.0%
realized-vol / +0.5% chars, blends hurt 1.003–1.043, M5 0.269); gate futility (0.3987 vs
0.4000, predicted-edge corr +0.16, 4.4% oracle gap); Gibbs 1.6×/1.19/0.79; electricity
artifact DMs (−2.55/−2.73); EVT-hurts list (VVIX/V2X/MOVE).

**Provenance defects fixed this pass:**
1. *IG credit 52% (DM 30.6) vs Table 3's 0.960 (DM 2.3):* both are real, from different
   batteries (FRTB-grade single-asset fits vs the lean hybrid-vs-GARCH sweep). §5.3 and the
   new ledger table now say so explicitly; the batteries are flagged non-interchangeable.
2. *CAViaR levels (0.3460) vs Table 4 (0.3551):* different common sample; a clarifying
   parenthesis added — rankings comparable, levels not.
3. *Baltic DM:* §5.3 cited 9.4 (the lean sweep's 9.36) in an FRTB-battery sentence; the
   FRTB-grade value is 9.63 → corrected to 9.6 with the ledger consistent.

**Unverifiable from the record but low-risk (left in, noted):** the synthetic boundary-check
constants (regret match 3.5×10⁻⁵, ν̂=6.8, <0.5% total regret) — the script ships with the
release; the 90.5% gate-routing share and the 59–79% transfer win-rate — plausibly from the
respective result files but not in a memory note; verify when the repo results are packaged.

**Also this pass (scope/worldview per Sean):** the "Magnitudes" wall replaced by a
wins/ties/losses ledger table (tab:winloss) with per-row DM and status; the cross-field
glossary demoted to `paper_A_online_appendix.tex` (a one-line pointer remains); "honesty
rules" → "reporting conventions"; VIX stays flagged suggestive. The paper's claim set now
maps 1:1 onto the title/abstract (frontier + engine + amortization + theory), with Paper B
material referenced only as context.

**Unexplored branches still promised in-text (submission gates, unchanged):** full-panel FZ
re-scoring; per-asset exception restatement for the finished (EVT+conformal) engine — base
models already restated 2026-08-15; the 2000–2024 WRDS untouched holdout; the frontier
timing-diagnostics table (S_{t−1}/S_{t−5}/lead placebo); protocol section + sample-flow
table; one canonical results table; MEU capital translation; intraday frontier (tick-blocked).
