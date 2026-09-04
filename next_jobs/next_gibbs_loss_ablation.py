# next_gibbs_loss_ablation.py — loss-in-the-exponent ablation for the
# Gibbs posterior over VaR. Registered next step (Jiang memo §9). NOT RUN.
#
# Question (generalized Bayes): does the choice of loss in
# exp{-omega * sum loss} change the honesty of the posterior on GARCH
# residuals? Losses (consistent for the tau-quantile — Gneiting form
# S = (1{z<=q} - tau)(g(q) - g(z)) with increasing g — except the
# deliberately inconsistent control arm, labeled as such):
#   pinball        g(x) = x            (canonical)
#   tail_pinball   pinball, tail obs upweighted (NOT consistent — kept as
#                  a deliberately mis-weighted control, label it so)
#   multi_tau      pinball averaged over a small tau-grid, each level
#                  evaluated at q + the empirical level offset (local
#                  CRPS proxy)
#   bounded_g      g(x) = arctan(x)    (consistent, bounded per-obs
#                  influence — the Gibbs-relevant variant: bounded
#                  influence is exactly what the Bernstein condition
#                  wants)
# Truth = moving-block bootstrap SD (gibbs_coverage.py convention:
# R = block SD / Gibbs SD; R>1 = overconfident).
#
# VERIFY BEFORE RUN:
#   Input CSV: columns name, date, z  (GARCH-t standardized residuals,
#   the same panel gibbs_coverage.py used on ai2 — 80+ CRSP names).
#
# Output: next_gibbs_loss_ablation.json — per-loss median/mean R across
# names. (omega-calibration per loss = follow-up once R landscape known.)
# Run: python next_gibbs_loss_ablation.py --input resid_panel.csv --tau 0.05

import argparse
import json

import numpy as np
import pandas as pd

RNG = np.random.default_rng(0)


def pinball(z, q, tau):
    u = z - q
    return np.where(u >= 0, tau * u, (tau - 1) * u)


def _consistent_g(z, q, tau, g):
    """Gneiting-class consistent quantile score S=(1{z<=q}-tau)(g(q)-g(z))."""
    return (np.where(z <= q, 1.0, 0.0) - tau) * (g(q) - g(z))


def _multi_tau(z, q, tau, halfwidth=0.02, k=5):
    """Pinball averaged over a small tau neighborhood, each level scored at
    q shifted by the empirical quantile offset — a local-CRPS proxy that
    still centers on the tau-quantile."""
    taus = np.linspace(max(tau - halfwidth, 0.005), tau + halfwidth, k)
    offs = np.quantile(z, taus) - np.quantile(z, tau)
    return np.mean([pinball(z, q + o, t) for o, t in zip(offs, taus)], axis=0)


LOSSES = {
    "pinball": lambda z, q, tau: pinball(z, q, tau),
    # NOT consistent — deliberately mis-weighted control arm:
    "tail_pinball_CONTROL": lambda z, q, tau:
        pinball(z, q, tau) * (1 + 3 * (z <= q)),
    "multi_tau": _multi_tau,
    "bounded_g": lambda z, q, tau: _consistent_g(z, q, tau, np.arctan),
}


def gibbs_posterior_sd(z, tau, loss_fn, omega=1.0, grid_n=400):
    """Posterior over the tau-quantile level q via exp(-omega*sum loss)."""
    lo, hi = np.quantile(z, [0.001, 0.30])
    grid = np.linspace(lo, hi, grid_n)
    ll = np.array([-omega * np.sum(loss_fn(z, q, tau)) for q in grid])
    ll -= ll.max()
    w = np.exp(ll)
    w /= w.sum()
    mu = np.sum(w * grid)
    return float(np.sqrt(np.sum(w * (grid - mu) ** 2)))


def block_bootstrap_sd(z, tau, block=20, B=300):
    n = len(z)
    ests = []
    for _ in range(B):
        idx = []
        while len(idx) < n:
            s = RNG.integers(0, n - block)
            idx.extend(range(s, s + block))
        ests.append(np.quantile(z[np.array(idx[:n])], tau))
    return float(np.std(ests))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--tau", type=float, default=0.05)
    ap.add_argument("--max-names", type=int, default=80)
    ap.add_argument("--out", default="next_gibbs_loss_ablation.json")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    if not {"name", "z"} <= set(df.columns):
        raise SystemExit("Input needs columns: name, date, z")

    out = {"tau": args.tau, "losses": {k: {"R": []} for k in LOSSES}}
    names = df["name"].unique()[: args.max_names]
    for nm in names:
        z = df.loc[df["name"] == nm, "z"].dropna().values
        if len(z) < 500:
            continue
        sd_true = block_bootstrap_sd(z, args.tau)
        for lname, lfn in LOSSES.items():
            sd_g = gibbs_posterior_sd(z, args.tau, lfn)
            out["losses"][lname]["R"].append(sd_true / max(sd_g, 1e-12))

    for lname, d in out["losses"].items():
        R = np.array(d["R"])
        d.update(median_R=float(np.median(R)), mean_R=float(np.mean(R)),
                 n=len(R))
        del d["R"]

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
    print("\nInterpretation: R>1 overconfident, R<1 conservative; the loss "
          "whose raw omega=1 posterior sits closest to R=1 needs the least "
          "calibration — that is the generalized-Bayes result.")


if __name__ == "__main__":
    main()
