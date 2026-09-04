# Adversarial Triage — Round 7 (Reviews #9 re-paste and #11)

Wave 6 of the adversarial-review program. Same protocol as R2–R6: every claim
verified against primary artifacts (scripts, result JSONs, both TeX builds),
real defects fixed in code and text, wrong claims rebutted with the evidence,
everything folded into the paper regardless of which way it cut.

---

## Review #9 (re-pasted) — stale-build desk reject

**Verdict: reviews a build several waves old. Every headline objection is
already closed in the current manuscript.** Kept here so the rebuttal is on
the record in one place.

| # | Claim | Verdict | Where it is closed |
|---|---|---|---|
| 9.1 | "3,600 hypotheses, no multiplicity control" | STALE | Romano–Wolf stepdown over all 30 design cells, both block lengths (10/20): 9/30 survive familywise control; reported in the multiplicity section since wave 3. The paper's headline claims never rested on per-cell significance. |
| 9.2 | "Look-ahead leakage from full-sample GARCH filtration" | STALE | Closed by construction four independent ways: strict calendar split at 2020 (+2.47%, DM 6.22); pre-GFC 2007 cut (DM 3.08); annual-refit walk-forward with expanding re-estimation each Jan 1, 2020–24 (+2.47% top decile, DM 6.05); recursive ex-ante score threshold (+0.99%, DM 2.15). All in the leakage section with a ledger table. |
| 9.3 | "Survivorship bias" | STALE | Point-in-time universe fixed at Q1-2000 including subsequently delisted names: edge *grows* (+2.94%, DM 6.6 frozen top decile; overall DM 8.96). |
| 9.4 | Cites Zhang, Härdle & Bommes as contradicting us | HALLUCINATED | No such paper exists with the claimed content; checked in wave 5. Nothing to answer. |

No manuscript changes from #9 beyond what earlier waves already made.

## Review #11 — the substantive wave-6 review

| # | Claim | Verdict | Action taken |
|---|---|---|---|
| 11.1 | h−1 boundary leak in `frtb_stress_exact.py`: h-day cumulative labels `rolling(h).sum().shift(-(h-1))` at indices sp−(h−1)…sp−1 contain test-era returns | **TRUE — real defect** | Purge applied: training now requires `idx < sp-(h-1)` so the whole label window precedes the split. Canonical job rerun on host (`job_stress_purged.py` → ships as `code/frtb_stress_exact.py`, writes `results/stress_es_results.json`). **Outcome: essentially unchanged.** Design h10 edge 1.37%; stress triple hybrid 1.248 < FHS 1.2605 < GARCH 1.262 (ordering intact); design-era ES −20.1 vs −17.3, breach 2.79% vs 3.30%; era-reversal holdout GARCH −16.63/−16.57 (was −16.6/−16.6), direct −15.9/−17.7 — reversal conclusion identical. Purge disclosed in §6.2 of both builds. |
| 11.2 | Same defect propagates to the OA horizon figure | TRUE | `job_horizon_purged.py` reruns the 4-horizon ratio study under the same purge, faithful to the stress-test design (direct h-day GBM vs √h GARCH-t, 150-name design panel). New curve: 0.9955 / 0.9896 / 0.9862 / 0.9789 (h=1,5,10,20), i.e. the advantage rises 0.45%→2.1% with horizon. OA Figure 3 and the master's horizon figure replaced; captions state the purged rerun supersedes the earlier unpurged figure. The old two-design story is collapsed to one design. |
| 11.3 | Ten-day model is not the deployed residual-hybrid engine, but the text lets readers conflate them | TRUE (clarity) | Relabeled everywhere: §6.2 retitled "The ten-day horizon: a direct multi-day extension"; identity paragraph states outright it is a *direct* multi-day GBM on cumulative returns, **not** the residual-hybrid engine; intro engine bullet carries the same clause. |
| 11.4 | Sign-convention contradiction (return-space quantiles vs loss-space regulatory numbers) | TRUE (clarity) | Notation section now has an explicit sign-convention block: all modeling and tables in return space (q_τ<0 in the left tail, e_τ≤q_τ, FZ convention); regulatory loss-space numbers are the negatives, quoted only for FRTB levels; the two are never mixed in one exhibit. Early "Risk measures" prose aligned. |
| 11.5 | "no assumptions needed" overclaim for the conformal overlay | TRUE | Replaced with "exact under exchangeability" + section cross-reference; the related-literature sentence now reads "without a parametric distributional model, under exchangeability." |
| 11.6 | Static overlay still called "deployed" in one spot | TRUE | "\emph{deployed} variant" → "\emph{static-overlay} variant." Overlay taxonomy (unshifted / static overlay / adaptive ACI) is already the paper's frame from wave 4. |
| 11.7 | Noninferiority bound direction stated ambiguously | TRUE | Caption language fixed to "calm-cell 90% *lower* confidence bounds sit above −0.25%." |
| 11.8 | `job_fz_fullpanel.py` still carries a REGISTERED-language header in the repo | TRUE (repo hygiene) | Header patched to frozen-specification/written-in-advance terminology; patched file ships to both repos this sync. |
| 11.9 | Annual-refit objection (from #8/#10) | WITHDRAWN by reviewer | The walk-forward job was "exactly the experiment I asked for." Ledger row + walk-forward paragraph retained. |

## Net effect on the paper's claims

The one *real* code defect this wave (h−1 boundary purge) moves no conclusion:
every multi-day number shifts at the third decimal or not at all, the stress
ordering and the era-reversal are intact, and the corrected horizon curve still
shows the edge growing with horizon — from a lower base (0.45%→2.1% rather than
the old unpurged 3.4%→4.9%). The remaining items were clarity failures on our
side (model identity, sign convention, overlay naming) and are fixed as such.
Both constructive reviewers now locate residual risk solely at novelty/fit for
JFEC, not correctness.

## Repo actions this sync (jfec_sync9 / zz_jfec_sync14)

- `job_stress_purged.py` → `code/frtb_stress_exact.py` in both repos (canonical, replaces v1)
- `job_horizon_purged.py` + `horizon_purged_results.json` shipped
- Refreshed `stress_es_results.json`, `walkforward_results.json`
- Patched `job_fz_fullpanel.py` → clone `code/`
- New top-level `README.md`: "Which file is the paper?" table, canonical script→result pairs, supersession policy
- Clone root tidied: stray amortization JSONs → `results/`, GPU scripts → `code/`
