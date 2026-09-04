# next_indep_repair.py — Christoffersen independence repair for credit /
# freight (clustered exceptions). Registered next step (Jiang memo §9).
# NOT YET RUN.
#
# Diagnosis (frtb_winners + universal_sig, 2026-07-20): IG credit (52%
# accuracy, DM 30.6) and Baltic Dry (~15%, DM 9.4-9.6 across the two
# studies) FAIL breach-independence at 99% — breaches cluster. Hypothesis: the tail quantile doesn't widen fast enough after a
# first breach in these persistent/mean-reverting series.
#
# Repair tested here: BREACH-RESPONSIVE TAIL WIDENING (causal). After any
# day with a breach of the alpha-quantile, multiply the tail quantile by
# k > 1 for the next W days (decaying linearly). Grid-search (k, W) on the
# FIRST HALF of the test window only (calm/stress agnostic), evaluate
# Kupiec + Christoffersen + pinball on the SECOND half. Honest split: if
# the repair only works in-sample, report that.
#
# VERIFY BEFORE RUN:
#   Input CSV per asset: columns date, ret, q_alpha  (q_alpha = the
#   model's level-alpha quantile forecast for that date, negative).
#   Export from frtb_winners.py's per-asset forecast frames.
#
# Run: python next_indep_repair.py --input ig_oas_forecasts.csv --alpha 0.01

import argparse
import json

import numpy as np
import pandas as pd
from scipy import stats


def kupiec_p(breaches, n, alpha):
    x = int(breaches.sum())
    if n == 0:
        return np.nan
    pi = x / n
    if pi in (0, 1):
        return 0.0
    lr = -2 * (x * np.log(alpha / pi) + (n - x) * np.log((1 - alpha) / (1 - pi)))
    return float(1 - stats.chi2.cdf(lr, 1))


def christoffersen_p(breaches):
    b = breaches.astype(int)
    n00 = np.sum((b[:-1] == 0) & (b[1:] == 0))
    n01 = np.sum((b[:-1] == 0) & (b[1:] == 1))
    n10 = np.sum((b[:-1] == 1) & (b[1:] == 0))
    n11 = np.sum((b[:-1] == 1) & (b[1:] == 1))
    p01 = n01 / max(n00 + n01, 1)
    p11 = n11 / max(n10 + n11, 1)
    p = (n01 + n11) / max(n00 + n01 + n10 + n11, 1)
    def ll(pp, a, bb):
        return (a * np.log(max(1 - pp, 1e-12)) + bb * np.log(max(pp, 1e-12)))
    lr = -2 * (ll(p, n00 + n10, n01 + n11) - ll(p01, n00, n01) - ll(p11, n10, n11))
    return float(1 - stats.chi2.cdf(lr, 1))


def apply_repair(df, alpha, k, W):
    q = df["q_alpha"].values.copy()
    ret = df["ret"].values
    breach = np.zeros(len(q), bool)
    qw = q.copy()
    for t in range(len(q)):
        # widen if any breach in the last W days, decaying
        recent = breach[max(0, t - W):t]
        if recent.any():
            age = t - (max(0, t - W) + np.where(recent)[0].max())
            qw[t] = q[t] * (1 + (k - 1) * max(0, 1 - age / W))
        breach[t] = ret[t] <= qw[t]
    return qw, breach


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--alpha", type=float, default=0.01)
    ap.add_argument("--out", default="next_indep_repair.json")
    args = ap.parse_args()

    df = pd.read_csv(args.input, parse_dates=["date"]).sort_values("date")
    if not {"ret", "q_alpha"} <= set(df.columns):
        raise SystemExit("Input needs columns: date, ret, q_alpha")

    half = len(df) // 2
    tune, test = df.iloc[:half], df.iloc[half:]

    # baseline on test half
    b0 = (test["ret"].values <= test["q_alpha"].values)
    out = {"alpha": args.alpha,
           "baseline_test": {"breach_rate": float(b0.mean()),
                             "kupiec_p": kupiec_p(b0, len(b0), args.alpha),
                             "christoffersen_p": christoffersen_p(b0)}}

    best, best_score = None, -np.inf
    for k in (1.1, 1.2, 1.35, 1.5, 1.75):
        for W in (3, 5, 10, 20):
            _, b = apply_repair(tune, args.alpha, k, W)
            score = christoffersen_p(b) + kupiec_p(b, len(b), args.alpha)
            if score > best_score:
                best, best_score = (k, W), score
    k, W = best
    _, bt = apply_repair(test, args.alpha, k, W)
    out["repair"] = {"k": k, "W": W,
                     "test": {"breach_rate": float(bt.mean()),
                              "kupiec_p": kupiec_p(bt, len(bt), args.alpha),
                              "christoffersen_p": christoffersen_p(bt)}}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
    print("\nPass criterion: both p-values > 0.05 on the held-out half. If "
          "baseline passes too or repair fails out-of-sample, report honestly.")


if __name__ == "__main__":
    main()
