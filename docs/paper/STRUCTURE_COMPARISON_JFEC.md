# Our paper vs. published JFEC/JoE structure (2026-09-04)

Exemplars checked directly: Zhang, Härdle & Bommes (JFEC 22(2) 2024, "Volatility Forecasting with Machine Learning and Intraday Commonality" — full section list) and Caporin et al. (JFEC 24(4) 2026, "Realized-VAR" — abstract norm), plus Patton–Ziegel–Chen (JoE 2019), the closest methods relative, from the published paper.

## What JFEC papers look like

Zhang et al. runs seven terse, noun-phrase sections: Related Literature; Data and RV; Commonality Estimation; Methodology; Experiments; Forecasting Daily RVs with Intraday RVs; Conclusion. No claim-sentence headings, no boxed practitioner material, no glossaries. PZC 2019 is the same shape with a theory core: Introduction; Dynamic models; Estimation theory; Simulation; Empirical analysis; Conclusion — roughly 45 published pages including appendix, with about eight tables and four figures. Caporin et al.'s abstract is 105 words, which confirms the ~100-word rule is a norm rather than a cliff, and that ours (97-word version stored for the build) is exactly in range.

## Where we now match

Heading register (after tonight's sweep: The ledger. / Conventions. / An absorption test. / Robustness of the dial. / Ex ante use of the score.), abstract length option, table and figure counts (6 tables, ~8 figures — inside the JFEC range), evaluation machinery (per-date DM, MCS, SPA, FZ0 — the exact toolkit JFEC referees use themselves), and a replication package that exceeds the journal's 2023 policy.

## Where we still differ, and what the JFEC build changes

Length is the one real outlier: 36 compact pages ≈ 55+ double-spaced against a ~40-page norm. Two sections are practitioner-shaped in a way JFEC papers compress: §2 (Background and industry benchmark — fold its FRTB context into the introduction and the battery section) and §7 (Applications and deployment — the boxed production loop and the trading-implications material read as an industry report; keep regulatory capital and cold start, move the box and the rest to the online appendix). The toy example, the algorithm boxes beyond Algorithm 1, the double-sort table, and the timing/pass-rate/horizon figures are online-appendix material in journal terms — every one is referenced from the text, so nothing is lost from the record. The in-introduction ledger table is unusual for JFEC but is our differentiator; it stays, possibly trimmed to Panel A. Target after cuts: ~38 double-spaced pages, 4 tables and 4 figures in the main text.

## Bottom line

Nothing structural separates us from the journal's register anymore except length, and the length plan is mechanical: compress §2, thin §7, move the named exhibits to the online appendix, swap the 100-word abstract. That is the whole remaining JFEC build.
