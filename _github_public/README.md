# Downside-Risk: Amortized Conditional-Quantile Forecasting

Research code and results for amortized (transfer) conditional-quantile estimation of
financial downside risk, with Prof. Wenxin Jiang (Northwestern).

## Key finding — amortization edge vs listing age
A single cross-sectionally-trained ("amortized") quantile model, conditioned on characteristics,
beats a name's own return history at every listing age — largest when the name is brand-new
(~6.4% lower pinball at days 15-30) and still ahead (~2.6%) at maturity. Cold-start (<250 days,
where GARCH cannot fit) is the regime where the amortized model is the only option.
A naive age-weighted blend toward own-history does NOT help; the amortized model should be
treated as a prior (Gibbs / partial-pooling), not shrunk toward the weaker own-empirical.

## Contents
- `code/` — neural IQN + amortized gradient-boosted quantile training and evaluation
- `results/` — pinball-loss results by listing-age bucket and history length (held-out CRSP names)

Trading applications are maintained separately and are not part of this repository.
