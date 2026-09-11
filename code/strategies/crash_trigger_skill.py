#!/usr/bin/env python3
"""
crash_trigger_skill.py  --  Does the IQN fat-tail trigger actually predict crashes?

Runs the out-of-sample skill test for the GRAFT-Q crash trigger on the FULL panel.
Reproduces (at 543-name scale) the 47/111-name local result: the fat-tail SHAPE
signal (the "525 vs 6" signal) has ~no crash-prediction skill, while crash
predictability is carried by conditional volatility and is matched by GARCH.

Run on ai2 (ssh steveqin@ai2) or wherever the full quantile panel lives:
    python3 crash_trigger_skill.py --panel /path/to/full_quantile_panel.csv

Expected panel columns (one row per name-month-horizon):
    tk, date, h, y,                          # ticker, date, horizon(days), realized fwd return
    p01,p05,p10,p25,p50,p75,p90,p95,p99,     # IQN physical quantiles
    g05,g25,g50,g75,g95                       # GARCH-t physical quantiles (optional but recommended)
Missing GARCH columns -> GARCH comparison is skipped.
"""
import argparse, json
import numpy as np, pandas as pd
from scipy.stats import rankdata

def auc(score, label):
    label = np.asarray(label); score = np.asarray(score)
    ok = np.isfinite(score) & np.isfinite(label)
    score, label = score[ok], label[ok]
    r = rankdata(score); n1 = label.sum(); n0 = len(label) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return (r[label == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

def decile_lift(score, crash, q=0.90):
    score = np.asarray(score); crash = np.asarray(crash)
    ok = np.isfinite(score)
    score, crash = score[ok], crash[ok]
    thr = np.quantile(score, q); flag = score >= thr
    base = crash.mean()
    return dict(flagged=float(crash[flag].mean()), unflagged=float(crash[~flag].mean()),
                base=float(base), lift=float(crash[flag].mean() / base) if base > 0 else np.nan,
                recall=float((flag & (crash == 1)).sum() / max(crash.sum(), 1)))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", required=True)
    ap.add_argument("--h", type=int, default=21, help="horizon in days (crash-insurance = 21)")
    ap.add_argument("--crash", type=float, nargs="+", default=[-0.15, -0.20, -0.30])
    ap.add_argument("--out", default="crash_trigger_skill_results.json")
    a = ap.parse_args()

    d = pd.read_csv(a.panel)
    d = d[d["h"] == a.h].copy()
    need = ["p01", "p05", "p25", "p50", "p75", "y"]
    d = d.dropna(subset=[c for c in need if c in d])
    has_garch = all(c in d.columns for c in ["g05", "g25", "g50"])
    print(f"panel: {len(d):,} name-months, {d['tk'].nunique()} names, "
          f"{d['date'].min()}..{d['date'].max()}, GARCH={'yes' if has_garch else 'no'}")

    # signals
    sigs = {
        "IQN_depth_p05":  -d["p05"].values,
        "IQN_depth_p01":  -d["p01"].values,
        "IQN_shape1_(p50-p05)/(p50-p25)": ((d["p50"]-d["p05"])/(d["p50"]-d["p25"])).values,
        "IQN_shape2_(p25-p05)/(p75-p25)": ((d["p25"]-d["p05"])/(d["p75"]-d["p25"])).values,
        "IQN_shape3_(p50-p01)/(p50-p10)": ((d["p50"]-d["p01"])/(d["p50"]-d["p10"])).values if "p10" in d else None,
    }
    if has_garch:
        sigs["GARCH_depth_g05"] = -d["g05"].values
        sigs["GARCH_shape_(g50-g05)/(g50-g25)"] = ((d["g50"]-d["g05"])/(d["g50"]-d["g25"])).values
        sigs["IQN_minus_GARCH_depth"] = (-d["p05"].values) - (-d["g05"].values)
    sigs = {k: v for k, v in sigs.items() if v is not None}

    out = {"panel": a.panel, "h": a.h, "n": int(len(d)), "n_names": int(d["tk"].nunique()),
           "has_garch": has_garch, "by_crash_threshold": {}}
    for cthr in a.crash:
        crash = (d["y"] < cthr).astype(int).values
        rec = {"base_rate": float(crash.mean()), "n_crash": int(crash.sum()), "signals": {}}
        print(f"\n=== crash < {cthr:.0%}  (base {crash.mean():.1%}, n={crash.sum()}) ===")
        for name, s in sigs.items():
            A = auc(s, crash); L = decile_lift(s, crash)
            rec["signals"][name] = {"AUC": float(A), **L}
            print(f"  {name:34s} AUC {A:.3f} | flagged {L['flagged']:.1%} vs unflagged {L['unflagged']:.1%}  lift {L['lift']:.1f}x")
        out["by_crash_threshold"][f"{cthr}"] = rec

    json.dump(out, open(a.out, "w"), indent=2)
    print(f"\nwrote {a.out}")
    print("INTERPRETATION: if the IQN_shape* AUCs are ~0.5 and IQN_minus_GARCH_depth is ~0.5,")
    print("the fat-tail shape trigger has no crash-prediction skill and the IQN adds nothing")
    print("over GARCH -> the '525 vs 6' gap is architectural, not predictive.")

if __name__ == "__main__":
    main()
