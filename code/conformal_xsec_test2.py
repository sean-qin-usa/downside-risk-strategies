#!/usr/bin/env python3
"""
conformal_xsec_test2.py -- variants that decompose WHY the lagged layer fails.
(a) same-date half-split conformal  -> tests pure cross-sectional exchangeability
    (diagnostic only; not deployable because same-date outcomes are unobserved).
(b) lagged pooled calibration, K in {8, 60, 250} dates -> deployable variants.
(c) ACI (Gibbs-Berber adaptive conformal) on the lagged shift -> drift-robust fix,
    breach feedback delayed by the h-day observation lag (deployable).
"""
import json
import numpy as np, pandas as pd

PANEL = "/mnt/user-data/uploads/GBC Project/samerows_merged.csv"
rng = np.random.default_rng(0)

def prep(d, qcol):
    d = d.dropna(subset=[qcol, "y"]).copy().sort_values("date")
    dates = np.array(sorted(d["date"].unique()))
    groups = {t: (d.loc[d["date"] == t, qcol].values, d.loc[d["date"] == t, "y"].values) for t in dates}
    return dates, groups

def same_date_split(dates, groups, alpha, n_rep=5):
    """calibrate on random half of names at date t, evaluate other half, same date"""
    b = []
    for t in dates:
        q, y = groups[t]
        n = len(q)
        if n < 20: continue
        s = q - y
        for _ in range(n_rep):
            idx = rng.permutation(n); half = n // 2
            cal, test = idx[:half], idx[half:]
            qq = min((1 - alpha) * (1 + 1 / half), 1.0)
            c = np.quantile(s[cal], qq)
            b.append((y[test] < q[test] - c).mean())
    return float(np.mean(b))

def lagged_pooled(dates, groups, alpha, K, lag_idx):
    b_raw, b_adj = [], []
    for i in range(len(dates)):
        j = i - lag_idx
        if j - K < 0: continue
        s = np.concatenate([groups[dates[k]][0] - groups[dates[k]][1] for k in range(j - K, j)])
        qq = min((1 - alpha) * (1 + 1 / len(s)), 1.0)
        c = np.quantile(s, qq)
        q, y = groups[dates[i]]
        b_raw.append((y < q).mean()); b_adj.append((y < q - c).mean())
    return float(np.mean(b_raw)), float(np.mean(b_adj))

def aci(dates, groups, alpha, K, lag_idx, gamma=0.005):
    """ACI: adapt working level a_t with h-lagged breach feedback; shift from pooled scores at working level"""
    a_t = alpha; b_adj = []; c_hist = {}
    for i in range(len(dates)):
        j = i - lag_idx
        if j - K < 0: continue
        s = np.concatenate([groups[dates[k]][0] - groups[dates[k]][1] for k in range(j - K, j)])
        a_eff = float(np.clip(a_t, 0.001, 0.2))
        c = np.quantile(s, min((1 - a_eff) * (1 + 1 / len(s)), 1.0))
        q, y = groups[dates[i]]
        br = (y < q - c).mean()
        b_adj.append(br); c_hist[i] = br
        # feedback available only for date i - lag_idx
        fb = c_hist.get(j)
        if fb is not None:
            a_t = a_t + gamma * (alpha - fb)
    return float(np.mean(b_adj))

def main():
    d = pd.read_csv(PANEL, parse_dates=["date"])
    out = {}
    for h in [21]:
        dh = d[d["h"] == h]
        lag_idx = h + 5  # trading-day lag: h days for outcome + embargo
        for qcol, alpha in [("p05", 0.05), ("p01", 0.01), ("g05", 0.05)]:
            if qcol not in dh: continue
            dates, groups = prep(dh, qcol)
            rec = {"same_date_split": same_date_split(dates, groups, alpha)}
            for K in [8, 60, 250]:
                raw, adj = lagged_pooled(dates, groups, alpha, K, lag_idx)
                rec[f"lagged_K{K}"] = adj
                rec["raw"] = raw
            rec["ACI_K60"] = aci(dates, groups, alpha, 60, lag_idx)
            out[f"h{h}_{qcol}"] = rec
            print(f"h={h} {qcol} target {alpha}: raw {rec['raw']:.4f} | same-date split {rec['same_date_split']:.4f} | "
                  f"lag K8 {rec['lagged_K8']:.4f} K60 {rec['lagged_K60']:.4f} K250 {rec['lagged_K250']:.4f} | ACI {rec['ACI_K60']:.4f}")
    json.dump(out, open("/home/claude/gbc/out/conformal_xsec_results2.json", "w"), indent=2)

if __name__ == "__main__":
    main()
