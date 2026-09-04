# next_roughvol_leverage.py — leverage summary statistic to identify rho
# in the Heston / rough-Bergomi SBC studies. Registered next step (Jiang
# memo §9). NOT YET RUN — this is a PATCH MODULE for the ai2 scripts.
#
# Motivation (heston_sbc.py results): rho (leverage) info-gain was only
# 0.7-2.3% — the 10 path summaries contain no leverage information. The
# leverage effect IS identifiable from a path via the cross-correlation of
# returns with FUTURE absolute returns / realized variance. Adding these
# summaries should raise rho info-gain; SBC coverage must stay ~nominal.
#
# HOW TO APPLY (on ai2):
#   1. from next_roughvol_leverage import leverage_summaries
#   2. In heston_sbc.py / roughvol_sbc.py, extend the summary vector:
#        S = np.concatenate([existing_summaries(path),
#                            leverage_summaries(path)])
#   3. Re-run the SBC pipeline unchanged. Compare rho info_gain and cov90
#      to the archived runs (heston: 0.7-2.3%; rBergomi rho: 0.17).
#
# Registered prediction: rho info-gain rises materially (leverage corr is
# the standard estimator of rho's sign/magnitude); if coverage degrades,
# the added summaries are too noisy at 252 days — also a reportable result.

import numpy as np


def leverage_summaries(r, lags=(1, 2, 5, 10)):
    """Leverage cross-correlations corr(r_t, |r_{t+k}|) and corr(r_t,
    r_{t+k}^2) for k in lags, plus a pooled short-horizon version.

    r : 1-D array of daily log returns (one simulated or real path).
    Returns: np.array of 2*len(lags)+1 summaries, NaN-safe.
    """
    r = np.asarray(r, float)
    r = r - r.mean()
    out = []
    for k in lags:
        a, b = r[:-k], np.abs(r[k:])
        c, d = r[:-k], r[k:] ** 2
        out.append(_corr(a, b))
        out.append(_corr(c, d))
    # pooled 1..5-day leverage (single robust number)
    pooled = np.mean([_corr(r[:-k], np.abs(r[k:])) for k in range(1, 6)])
    out.append(pooled)
    return np.array(out)


def _corr(x, y):
    sx, sy = x.std(), y.std()
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return float(np.mean((x - x.mean()) * (y - y.mean())) / (sx * sy))


if __name__ == "__main__":
    # smoke test on synthetic leverage: negative shocks raise future vol
    rng = np.random.default_rng(0)
    n = 252
    vol = np.ones(n) * 0.01
    r = np.zeros(n)
    for t in range(1, n):
        vol[t] = 0.01 + 0.85 * (vol[t - 1] - 0.01) + 0.4 * max(0, -r[t - 1])
        r[t] = vol[t] * rng.standard_normal()
    s = leverage_summaries(r)
    print("summaries:", np.round(s, 3))
    print("expected: negative corr(r_t, |r_{t+k}|) at short lags "
          "(leverage present) — check sign before deploying.")
