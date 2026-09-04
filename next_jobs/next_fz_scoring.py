# next_fz_scoring.py — Fissler-Ziegel joint (VaR, ES) scoring + per-date DM
# Registered next step (Jiang memo Jul 6-20, §9). NOT YET RUN.
#
# VERIFY BEFORE RUN:
#   Input = per-observation forecast export, one row per (date, name, model):
#     columns: date, name, model, ret, var_alpha, es_alpha
#   where var_alpha/es_alpha are the level-ALPHA forecasts (negative numbers
#   for losses, same sign convention as ret). Export these from frtb_bench.py
#   (it already computes them internally; add a to_csv of the forecast frame).
#
# Scoring: the FZ0 loss (Fissler & Ziegel 2016), in the Patton-Ziegel-Chen
# (2019, J. Econometrics) form, strictly consistent for the (VaR, ES) pair
# at level alpha with left-tail negative convention (e < v < 0):
#   L(v, e, r) = -(1/(alpha*e)) * 1{r<=v} * (v - r) + v/e + log(-e) - 1
# LOWER IS BETTER. (Sweep note 2026-07-21: an earlier draft of this file
# had the negated form, which would have REVERSED the model ranking —
# verify against a hand-computed example before trusting output.)
#
# Output: next_fz_results.json — per-model mean FZ0 + per-date DM vs baseline.
# Run:    python next_fz_scoring.py --input frtb_forecasts.csv --alpha 0.025

import argparse
import json

import numpy as np
import pandas as pd


def fz0_loss(v, e, r, alpha):
    v = np.minimum(v, -1e-8)          # guard: VaR must be < 0
    e = np.minimum(e, v - 1e-8)       # guard: ES < VaR
    hit = (r <= v).astype(float)
    return (-(1.0 / (alpha * e)) * hit * (v - r) + v / e + np.log(-e) - 1.0)


def per_date_dm(df, loss_a, loss_b):
    """Newey-West per-date Diebold-Mariano on daily mean loss differentials."""
    d = (df[loss_a] - df[loss_b]).groupby(df["date"]).mean().values
    T = len(d)
    dbar = d.mean()
    L = int(np.floor(1.5 * T ** (1 / 3)))
    # Newey-West long-run variance
    s = np.sum((d - dbar) ** 2) / T
    for k in range(1, L + 1):
        w = 1 - k / (L + 1)
        s += 2 * w * np.sum((d[k:] - dbar) * (d[:-k] - dbar)) / T
    dm = dbar / np.sqrt(s / T)
    return float(dm), int(T)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--alpha", type=float, default=0.025)
    ap.add_argument("--baseline", default="garch_t")
    ap.add_argument("--out", default="next_fz_results.json")
    args = ap.parse_args()

    df = pd.read_csv(args.input, parse_dates=["date"])
    need = {"date", "name", "model", "ret", "var_alpha", "es_alpha"}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(f"Input missing columns: {missing} — fix export first.")

    df["fz0"] = fz0_loss(df["var_alpha"].values, df["es_alpha"].values,
                         df["ret"].values, args.alpha)

    wide = df.pivot_table(index=["date", "name"], columns="model",
                          values="fz0").reset_index()
    models = [c for c in wide.columns if c not in ("date", "name")]
    out = {"alpha": args.alpha, "baseline": args.baseline, "models": {}}
    for m in models:
        res = {"mean_fz0": float(np.nanmean(wide[m]))}
        if m != args.baseline and args.baseline in wide.columns:
            sub = wide.dropna(subset=[m, args.baseline])
            dm, T = per_date_dm(sub, args.baseline, m)  # >0: m better
            res["dm_vs_baseline"] = dm
            res["n_dates"] = T
        out["models"][m] = res

    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
