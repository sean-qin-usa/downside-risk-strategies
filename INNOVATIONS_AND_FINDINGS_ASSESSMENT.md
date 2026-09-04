# GBC Program — Innovations & Findings Assessment (2026-08-15)

**The one-paragraph answer.** The program has produced one genuinely deployable engineering
innovation (the amortized residual-hybrid risk engine and its calibration stack), one
scientific finding with a real shot at changing how people frame the ML-vs-econometrics
question in risk (the misspecification frontier — which just survived a hostile code audit),
one clean capability result nothing parametric can match (likelihood-free SBC posteriors for
rough volatility), and a set of measured negative results that are themselves publishable
because they close questions people actually argue about (crash timing, portfolio tails,
generalized Bayes, model gating). The findings are significant; the engine and the monitor
are usable today; the crash-premium result is usable as risk discipline, not as alpha. The
threats that remain after this week are inference-presentation and completion work, not
validity of the core results.

---

## A. Methodological innovations

**A1. The amortized residual-hybrid engine** (GARCH scale × state-conditioned nonparametric
residual shape, EVT tail, conformal finish).
*Evidence:* beats every model banks actually run (HS, EWMA, GARCH-t, GJR-skew-t, FHS) with
date-level DM 4.4–8.3; co-best with CAViaR in the 90% MCS; best ES97.5 calibration
(−5.80 pred vs −5.76 realized while FHS/GARCH overstate by 8–11%); edge grows at h=10 and
holds in the 2020–22 stress window; FZ0 joint (VaR,ES) score confirms fat tails necessary and
shows the frontier direction on high-kurtosis names.
*Significance:* high — "FHS and above" by construction, with the division of labor
(parametric scale, nonparametric shape) argued a priori and confirmed everywhere.
*Usability:* **the most deployable asset in the program.** An internal-models VaR/ES
candidate plus a drop-in upgrade path from FHS. The 8–11% ES overstatement it removes is the
economically relevant number (with the desk-capital translation left properly unclaimed).
*Threats:* the pooled exception-test presentation (being restated per-asset + date-clustered
right now — audit confirmed the defect); the final hybrid+EVT+conformal object needs one
canonical results row; CAViaR tie must stay in the abstract-level honesty.

**A2. The misspecification frontier** (mk63 / |sk63| / jump5 rank score as a live meter of
when flexible-shape models beat GARCH).
*Evidence:* top-decile edge +2.71% (date-level DM 6.54), bulk ≈ 0; validated across four
universes (CRSP, FX incl. hyperinflation 12–14% with DM 2.9–3.8, 26 country indices corr
0.53, 43 cross-asset corr 0.43) with Korea-2026 as the sharpening negative control.
**Survived this week's audit:** the code lags every signal (`.shift(1)` — window is
{t−63,…,t−1}), features are causal, DM is date-aggregated with NW variance. The "fatal"
look-ahead attack was a paper-text bug (§3.7 wrote the wrong window), now fixed.
*Significance:* high if the two remaining hardening steps hold (timing-diagnostics table
S_{t−5}/lead-placebo; untouched 2000–2024 WRDS holdout). It is a *predictive theory of when
ML wins* — rarer and more useful than another horse race.
*Usability:* real — a model-risk surveillance dial computable on any asset with a GARCH fit.
The honest deployment rule matters: in the amortized setting run the flexible model always
(gating provably adds nothing); the score is a monitor, and a switch only for per-name
standalone models.

**A3. Amortization + cold start.** One model across hundreds of names; transfer beats
own-history benchmarks at every listing age (6–10% when young); day-one quantiles for IPOs
from characteristics; M5 external check at benchmark tier (SPL 0.269).
*Significance/usability:* the cold-start capability is unique in the battery and directly
monetizable (margining, limits, new listings). *Threat:* the claim must be scoped to the
amortized direct estimator (the hybrid needs a per-name σ̂; reviewers caught this) — a
wording fix plus, ideally, a small cold-start scale model.

**A4. GRAFT-Q calibration stack** (tail-aware Beta(0.3,0.3) τ-sampling + monotone
rearrangement + EVT graft in the model's own probability coordinates + conformal).
*Evidence:* raw neural 99% breach 3.2% → 0.92%; 5% coverage 0.056–0.063 and 1% 0.012–0.014
at every horizon; body exact.
*Significance:* the recipe that makes neural quantiles *calibrated* on financial panels —
each ingredient forced by a documented failure. Usable as a checklist by anyone deploying
distributional nets. *Threat:* the splice/ordering must be written as one coherent object
(reviewer's point 1.6 — a specification-writing task).

**A5. The conformal panel finding (this week).** Per-date cross-sectional split conformal is
finite-sample valid but loose in thin cross-sections; the lagged deployable version *fails*
(factor dependence makes effective n ≈ #dates; the h-day outcome lag makes calibration
stale); adaptive (ACI-style) updating restores nominal (0.0506 and 0.0509 at the 5% target
on two panels; 0.031→0.014 at 1%).
*Significance:* a small but genuinely novel design rule — "in financial panels, conformal
must be adaptive; the split guarantee is a diagnostic" — with the failure mechanism
decomposed. Publishable as a section, useful to anyone doing conformal prediction on markets.

**A6. Likelihood-free amortized posteriors + SBC for intractable volatility models.**
Heston and rough-Bergomi posteriors that are well-calibrated by simulation-based calibration
(rough-vol Hurst: 42% prior-uncertainty reduction, SBC coverage 0.91) — where MLE/GARCH have
no access at all.
*Significance:* the cleanest "this capability did not exist" result in the program; the lead
of Paper B. *Usability:* calibrating scenario generators for stress design — more academic
than desk-level, but real.

**A7. Honest uncertainty on the risk number.** Block-bootstrap + EVT intervals on GARCH
residuals hit 0.89–0.95 coverage at a 0.90 target for (VaR, ES); ACI is the most stable arm
under drift; and the Gibbs-posterior diagnostic *measures* why naive generalized Bayes fails
on returns (1.6× overconfident raw; i.i.d.-bootstrap comparison isolates serial dependence;
residual space repairs it; the loss exponent must be pinball — expectile collapses coverage
to 0.1–0.4).
*Significance:* VaR with a standard error is something desks simply don't have; the Gibbs
result settles a methodological question with a number. *Usability:* immediate.

---

## B. Empirical findings

**B1. The idiosyncratic-event ceiling.** Single-name left-tail miscalibration is
informational, not architectural: the failure is one-sided, loss reweighting can't fix it,
and the events are discrete idiosyncratic news. The honest fix is statistical (EVT for
frequency), not a bigger network. *This is the program's organizing insight* — it predicts
where model capacity pays (shape, term structure, amortization) and where it cannot (crash
timing).

**B2. The crash premium survives a genuine forecast.** The model's distinctive fat-tail
shape signal has *no* crash-prediction skill (AUC 0.39–0.47 at every scale tested); such
predictability as exists is volatility, matched by GARCH (0.78–0.84 both). And buying puts
conditional on the signal that *does* forecast risk loses in every decile (ETFs −64%
overall, −32% top decile; single names −50%, top decile ≈ 0 with the highest realized crash
rate). A model that cannot time crashes can still price their frequency — and pricing
frequency identifies the premium without being able to trade against it. *Significance:*
this turns the VRP literature's unconditional statement into a conditional one and relocates
the premium's source to risk-bearing capacity. *Usability:* the deployable side is selling /
warehousing with model-driven tail control (switcher book: net SR 1.1–1.16, best crisis
profile; measured-cost bound SR 1.10 mid → 0.71 full-bid on 1,433 tickets, hit rate
invariant) — and an explicit warning that crash-alpha products don't work.

**B3. The frontier's geography.** GARCH-t wins nearly everywhere standalone — including the
Korea 2026 crisis (a price crash is not residual misspecification). The flexible-shape edge
lives at top-decile residual-shape extremity, hyperinflation FX, turbulence (4× calm→turbulent),
and long horizons (~5% at h=20 vs √h-scaling). High kurtosis is necessary, not sufficient
(carbon/corn tie). This is a *map*, not a slogan — and it is falsifiable day by day.

**B4. Trees vs nets, honestly.** GBM is ~0.75% better as a point estimator on tabular state;
the net's value is sampling/amortized posteriors. A practitioner selection rule, not a fight.

**B5. Survivorship closes cleanly.** The CRSP delisting merge finds exactly one true
in-sample delisting on the 111-name panel (BBBY, +0.305 exchange value); every statistic
moves <2bp. Survivorship enters through optionable-universe entry, not terminal returns.

**B6. Trigger counts are benchmark-shape-specific.** The 525-vs-6 firing gap measures the
original benchmark's fitted innovation shape, not a stable GARCH-class property (a re-fit
GJR-t with ν≈4.5 fires more than the IQN). Correctly demoted to illustration; nothing rests
on it.

---

## C. Negative results that are findings

Gating is futile (the 4.4% per-day oracle gap is realization noise — a discipline-check for
the whole model-switching literature); direct nonparametric portfolio tails lose to DCC three
ways (equity co-crash conceded); naive Gibbs is 1.6× overconfident and the exponent must be
pinball; hierarchical own-history blends hurt at every age; model-timed crash insurance
loses; electricity and same-universe "wins" were artifacts, caught and retired. Each is
documented with the same discipline as the positives — reviewers consistently cite this as
the program's biggest stylistic asset.

---

## D. What this week's external audit changed

Three AI referees (my read + Gemini + ChatGPT) attacked the drafts. Outcome: the *findings*
survived; the *presentation and inference wrapping* took real hits, most now fixed or in
flight. Specifically: frontier timing verified clean in code (paper text corrected); DM/MCS
implementation verified valid (date-level, NW, stationary-bootstrap MCS — now documented in
the paper); pooled Kupiec confirmed invalid → per-asset + date-clustered restatement running
now; model-dependent "realized ES" comparator → FZ full-panel is the ranking criterion and a
submission gate; VIX cross-asset "win" downgraded to suggestive; protocol-reconstructability
section and one-canonical-table restructure remain to be written; the 2000–2024 WRDS panel is
the untouched confirmatory holdout that answers the forking-paths critique.

## E. Bottom line

**Significant?** Yes, on three axes: a deployable engine that beats the actual industry
standard with the strongest rigor stack in this literature's neighborhood (MCS + DM + proper
scores + exception tests + pre-registration); a falsifiable theory of *when* flexible-shape
models pay; and negative results that close live questions. **Usable?** The engine, monitor,
uncertainty bands, and cold-start are usable now by a risk desk; the premium work is usable
as sizing/tail discipline for a vol book (not as a buy-side signal); the SBC machinery is
usable for scenario-generator calibration. **What stands between here and publication** is
finite and known: the per-asset backtest restatement (running), the FZ full-panel and
protocol section, the holdout confirmation, and the reconciliation sweep — completion work,
not conceptual risk.
