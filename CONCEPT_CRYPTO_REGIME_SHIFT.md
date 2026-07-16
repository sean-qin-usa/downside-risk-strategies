# Concept Note: Did Institutionalization Break the Crypto Cycle?
*Side-paper concept, July 2026. Companion to RESEARCH_DIRECTIONS_V2 (HF-crypto direction). Status: idea only — not competing with the GBC/IQN flagship.*

## One-line pitch
Test formally whether the Jan-2024 spot-ETF approvals flipped crypto from the Liu–Tsyvinski regime (macro-disconnected; driven by attention, sentiment, momentum, and the halving cycle) to a macro/liquidity-driven risk asset — a structural-break + time-varying-exposure + announcement-response paper with a clean event date.

## Why now / why us
- The benchmark result (Liu & Tsyvinski, RFS 2021: crypto has ~zero exposure to macro, equity, FX, commodity factors) is estimated on pre-2020 data. Post-2020 announcement studies (FOMC/CPI), the NY Fed "Bitcoin–Macro Disconnect" staff report, and the 2025–26 divergence (Michigan sentiment at record lows while BTC holds on ETF flows) all suggest the regime changed — but the formal test is currently owned by practitioner research (Galaxy, Grayscale, Fidelity, Amberdata), not journals.
- Clean identification event: ETF approval (Jan 2024), with a supporting shift in market microstructure (57% of BTC volume now in US hours; ETF flows >10x daily mined supply).
- Connects to our machinery: regime-dependent conditional distributions are exactly what the IQN captures; this paper is a natural motivation/application for the HF-crypto direction and can share its data pipeline (exchange intraday data already scripted; DVOL free from Deribit).

## Core empirical design
1. **Time-varying macro betas.** Rolling/DCC and formal structural-break tests (Bai–Perron; Andrews) on BTC/ETH exposure to equity factor, global M2/liquidity proxies, rates, dollar. H0: break at ETF approval, not at halvings.
2. **Announcement studies.** High-frequency (5-min) responses to FOMC/CPI/NFP pre- vs post-2024. Complements, not repeats, the existing announcement literature: the contribution is the *change* in response, not the response.
3. **Sentiment horse race.** Attention/sentiment measures (Google SVI, social sentiment, Michigan for the retail channel) vs macro surprises in explaining returns and *conditional distribution shape* (IQN quantiles) across regimes. Hypothesis: sentiment loads on tails/skew pre-2024; macro loads on scale post-2024.
4. **Cycle component (descriptive only).** Halving-cycle patterns presented as stylized facts with explicit n=4 caveat — never as identification. Frame via supply-flow arithmetic (mined supply vs ETF flow), which does not need many cycles.

## What we deliberately do NOT do
- No pump-and-dump content (JFQA paper + ML-detection literature have saturated it).
- No new bubble-dating (PSY/LPPL literature saturated).
- No claim to predict cycle tops/bottoms.

## Honest risks
- Descriptive empirical work, far from the econometrics core; referees may say "two regressions and an event."
- Announcement literature is crowded; the wedge must stay "regime change," not "crypto reacts to CPI."
- Cycle strand is attackable on n=4 regardless of framing — keep it stylized-facts only.
- One event date = one experiment; robustness needs placebo breaks and alt event dates (futures 2017, COVID 2020).

## Verdict / next step
Worth a 2–3 week feasibility pass *after* MCS + robustness on the flagship: pull the macro-surprise series and ETF flow data, run the Bai–Perron breaks, and see if the break lands where the story says. If it does, this is a solid field-journal paper (JIMF, JBF, Finance Research Letters for a short version) and a ready-made application chapter for the HF-crypto IQN work.

## Key references
- Liu & Tsyvinski (2021), "Risks and Returns of Cryptocurrency," *RFS* 34(6).
- Liu, Tsyvinski & Wu (2022), crypto factor model, *JF*.
- Li, Shin & Wang (2021), "Cryptocurrency Pump-and-Dump Schemes," *JFQA* (excluded strand).
- Benigno & Rosa, "The Bitcoin–Macro Disconnect," NY Fed Staff Report 1052.
- Corbet et al. / Ben Omrane et al., macro-announcement effects on crypto (FRL; Int. Rev. Econ. Finance 2025).
- Practitioner regime pieces: Grayscale 2026 Outlook; Amberdata "End of the Four-Year Cycle"; Fidelity drawdown-structure note.
