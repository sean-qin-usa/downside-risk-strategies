# full_crash_section.py -- regenerate the ENTIRE crash section of graftq_main_v2.tex
# at full panel scale, using the EXACT trigger definition from pq_31_iqn_rerun.py
# (trigger: IQN physical 5% quantile BELOW the market's 5% risk-neutral strike),
# plus the first full-scale run of the Stage-3 cross-sectional conformal layer.
#
# VERIFY-BEFORE-RUN: file paths and column layouts are asserted and printed before
# each stage; every stage is guarded so partial results still emit.
# Outputs: full_crash_section_results.json + full_crash_console.txt in GBC Project.
#
# Stages:
#   0. load IQN full quantile panel (mh_quantiles_gpu.csv, fallback _v2) + market
#      Q-quantiles (mh_trade_panel.parquet); infer the qq tau-grid from column count.
#   1. GJR-GARCH-t same-rows quantiles for ALL names (job4_samerows.py logic,
#      cached to garch_quantiles_full.csv so reruns skip the ~1h simulation).
#   2. EXACT trigger counts per horizon: IQN p05<K_Q(5%) vs GARCH g05<K_Q(5%)
#      (the "525 vs 6" numbers, now at full scale) + trigger-conditional digital-put
#      returns (payoff 1{y<K}, premium approximated by the risk-neutral prob).
#   3. Skill battery (AUC + top-decile lift) for exact trigger margin, shape ratios,
#      depth signals, IQN-minus-GARCH, at crash thresholds -15/-20/-30%.
#   4. Conditional puts by decile of forecast crash risk (depth signal), at the
#      5% (and 10% if available) market strike; NW t on date-aggregated returns.
#   5. Cross-sectional conformal layer at full scale: same-date split (diagnostic),
#      lagged split-conformal K in {8,60,250}, and ACI with h-lagged feedback.
#   6. Informational-ceiling shares: fraction of crashes occurring in unflagged months.
import os, sys, time, math, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

RES = r"C:\GBC_data\results\pq_trade"
RAW = r"C:\GBC_data\data\raw"
P   = r"C:\Users\OWNER\Claude\Projects\GBC Project"
OUTJ = os.path.join(P, "full_crash_section_results.json")
CACHE_G = os.path.join(RES, "garch_quantiles_full.csv")
t0 = time.time(); lg = lambda s: print(s, flush=True)
OUT = {"stages_done": [], "errors": {}}
def dump():
    json.dump(OUT, open(OUTJ, "w"), indent=2, default=str)

def nw_t(x, l=3):
    x = pd.Series(x).dropna().values; n = len(x)
    if n < 8: return np.nan
    d = x - x.mean(); s = d.var(ddof=0)
    for k in range(1, l + 1):
        if n > k + 1: s += 2 * (1 - k / (l + 1)) * np.cov(d[k:], d[:-k], ddof=0)[0, 1]
    return float(x.mean() / np.sqrt(s / n)) if s > 0 else np.nan

def auc(score, label):
    from scipy.stats import rankdata
    label = np.asarray(label); score = np.asarray(score)
    ok = np.isfinite(score) & np.isfinite(label)
    score, label = score[ok], label[ok]
    r = rankdata(score); n1 = label.sum(); n0 = len(label) - n1
    if n1 == 0 or n0 == 0: return np.nan
    return float((r[label == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))

def decile_stats(score, crash, q=0.90):
    score = np.asarray(score); crash = np.asarray(crash)
    ok = np.isfinite(score); score, crash = score[ok], crash[ok]
    thr = np.quantile(score, q); flag = score >= thr; base = crash.mean()
    return dict(flagged=float(crash[flag].mean()), unflagged=float(crash[~flag].mean()),
                base=float(base), lift=float(crash[flag].mean() / base) if base > 0 else None,
                recall=float((flag & (crash == 1)).sum() / max(crash.sum(), 1)))

# ---------------- stage 0: load panels ----------------
try:
    src = os.path.join(RES, "mh_quantiles_gpu.csv")
    if not os.path.exists(src):
        src = os.path.join(RES, "mh_quantiles_gpu_v2.csv")
    lg(f"IQN panel: {src}")
    IQ = pd.read_csv(src); IQ["date"] = pd.to_datetime(IQ["date"]); IQ["h"] = IQ["h"].astype(int)
    lg(f"IQN rows={len(IQ):,} names={IQ.tk.nunique()} horizons={sorted(IQ.h.unique())} cols={list(IQ.columns)} {time.time()-t0:.0f}s")
    TP = pd.read_parquet(os.path.join(RES, "mh_trade_panel.parquet"))
    TP["date"] = pd.to_datetime(TP["date"])
    qqcols = [c for c in TP.columns if c.startswith("qq")]
    lg(f"trade panel rows={len(TP):,} qqcols={qqcols} cols={list(TP.columns)[:25]}")
    # infer qq tau-grid by column count (verified conventions from pq_31 / exp_panel_wedge)
    if len(qqcols) >= 9:
        qgrid = dict(zip([f"qq{i}" for i in range(9)], [.01, .05, .10, .25, .50, .75, .90, .95, .99]))
    else:
        qgrid = dict(zip([f"qq{i}" for i in range(len(qqcols))], [.05, .25, .50, .75, .95][:len(qqcols)]))
    K5  = [c for c, t in qgrid.items() if abs(t - .05) < 1e-9]
    K10 = [c for c, t in qgrid.items() if abs(t - .10) < 1e-9]
    K5 = K5[0] if K5 else None; K10 = K10[0] if K10 else None
    OUT["stage0"] = {"iqn_src": src, "n_iqn": int(len(IQ)), "n_names": int(IQ.tk.nunique()),
                     "qq_grid": qgrid, "K5_col": K5, "K10_col": K10}
    # empirical check of the grid: physical breach freq at each qq col (fat Q wing -> below tau)
    j0 = TP.merge(IQ[["tk", "date", "h", "y"]].drop_duplicates(), on=["tk", "date", "h"], how="inner") \
         if "y" not in TP.columns else TP
    OUT["stage0"]["qq_breach_freq_check"] = {c: round(float((j0["y"] < j0[c]).mean()), 4)
                                             for c in qqcols if c in j0}
    lg(f"qq grid check: {OUT['stage0']['qq_breach_freq_check']}")
    OUT["stages_done"].append(0); dump()
except Exception as e:
    OUT["errors"]["stage0"] = repr(e); dump(); lg("STAGE0 FAIL " + repr(e)); sys.exit(1)

# ---------------- stage 1: GARCH same-rows quantiles (cached) ----------------
try:
    if os.path.exists(CACHE_G):
        G = pd.read_csv(CACHE_G); G["date"] = pd.to_datetime(G["date"])
        lg(f"GARCH cache hit: {len(G):,} rows")
    else:
        from arch import arch_model
        rng = np.random.default_rng(7)
        TAUS = [("g05", 0.05), ("g25", 0.25), ("g50", 0.50), ("g75", 0.75), ("g95", 0.95)]
        HS = sorted(IQ.h.unique()); HMAX = max(HS); S = 600
        gar_rows = []; names = sorted(IQ.tk.unique())
        for ni, tk in enumerate(names):
            f = os.path.join(RAW, f"tpx_{tk}.csv")
            if not os.path.exists(f): continue
            t = pd.read_csv(f, usecols=["date", "field", "value"])
            t = t[t.field == "PX_LAST"][["date", "value"]].dropna()
            t["date"] = pd.to_datetime(t["date"])
            s = t.set_index("date")["value"].sort_index().astype(float)
            s = s[~s.index.duplicated()]
            if len(s) < 400: continue
            r = s.pct_change().dropna(); rpct = r * 100.0; idx = r.index
            yrs = sorted(set(idx.year)); params_by_year = {}
            for y in yrs:
                train = rpct[idx.year < y]
                if len(train) < 250: continue
                try:
                    fit = arch_model(train, mean="Zero", vol="GARCH", p=1, o=1, q=1, dist="t").fit(disp="off")
                    pr = fit.params
                    params_by_year[y] = (float(pr.get("omega")), float(pr.get("alpha[1]", 0)),
                                         float(pr.get("gamma[1]", 0)), float(pr.get("beta[1]", 0)),
                                         float(pr.get("nu", 8)))
                except Exception:
                    continue
            if not params_by_year: continue
            rp = rpct.values; n = len(rp); sig2 = np.empty(n); uncond = np.var(rp)
            cur = params_by_year[min(params_by_year)]; sig2[0] = uncond
            yarr = idx.year.values
            for i in range(1, n):
                if yarr[i] in params_by_year: cur = params_by_year[yarr[i]]
                om, al, ga, be, nu = cur
                e = rp[i - 1]; sig2[i] = om + (al + ga * (e < 0)) * e * e + be * sig2[i - 1]
                if not np.isfinite(sig2[i]) or sig2[i] <= 0: sig2[i] = uncond
            sigser = pd.Series(np.sqrt(sig2), index=idx)
            nu_ser = pd.Series([(params_by_year.get(y, cur))[4] for y in yarr], index=idx)
            sub = IQ[IQ.tk == tk]
            for dt in sorted(sub.date.unique()):
                pos = sigser.index.searchsorted(pd.Timestamp(dt), side="right") - 1
                if pos < 0: continue
                sig0 = sigser.iloc[pos]; nu = float(nu_ser.iloc[pos])
                y = pd.Timestamp(dt).year; cur = None
                for yy in sorted(params_by_year):
                    if yy <= y: cur = params_by_year[yy]
                if cur is None: continue
                om, al, ga, be, _ = cur
                nu = max(nu, 2.05); std = math.sqrt(nu / (nu - 2.0))
                h2 = np.full(S, sig0 * sig0); cum = np.ones(S); qstore = {}
                for step in range(1, HMAX + 1):
                    z = rng.standard_t(nu, size=S) / std
                    e = z * np.sqrt(h2); cum *= (1.0 + e / 100.0)
                    h2 = om + (al + ga * (e < 0)) * e * e + be * h2
                    h2 = np.where(np.isfinite(h2) & (h2 > 0), h2, sig0 * sig0)
                    if step in HS:
                        cr = cum - 1.0
                        qstore[step] = {lab: np.quantile(cr, tau) for lab, tau in TAUS}
                for h in HS:
                    if h in qstore:
                        q = qstore[h]
                        gar_rows.append((tk, pd.Timestamp(dt), h, q["g05"], q["g25"], q["g50"], q["g75"], q["g95"]))
            if ni % 20 == 0:
                lg(f"  GARCH {ni}/{len(names)} {tk} rows={len(gar_rows):,} {time.time()-t0:.0f}s")
        G = pd.DataFrame(gar_rows, columns=["tk", "date", "h", "g05", "g25", "g50", "g75", "g95"])
        G.to_csv(CACHE_G, index=False)
    M = IQ.merge(G, on=["tk", "date", "h"], how="inner")
    lg(f"same-rows merged: {len(M):,} rows, {M.tk.nunique()} names {time.time()-t0:.0f}s")
    OUT["stage1"] = {"n_garch": int(len(G)), "n_samerows": int(len(M)), "n_names_samerows": int(M.tk.nunique())}
    OUT["stages_done"].append(1); dump()
except Exception as e:
    OUT["errors"]["stage1"] = repr(e); dump(); lg("STAGE1 FAIL " + repr(e)); M = IQ.copy()

# ---------------- stage 2: EXACT trigger, full scale ----------------
try:
    keep_tp = ["tk", "date", "h"] + [c for c in [K5, K10] if c]
    J = M.merge(TP[keep_tp].drop_duplicates(["tk", "date", "h"]), on=["tk", "date", "h"], how="inner")
    lg(f"joined with market strikes: {len(J):,} rows")
    st2 = {"n_joined": int(len(J))}
    for h in sorted(J.h.unique()):
        s = J[(J.h == h) & J.y.notna() & J[K5].notna()]
        trig_i = s.p05 < s[K5]
        rec = {"n": int(len(s)), "iqn_trigger_fires": int(trig_i.sum())}
        if "g05" in s:
            sg = s[s.g05.notna()]; rec["garch_trigger_fires"] = int((sg.g05 < sg[K5]).sum())
            rec["n_garch_rows"] = int(len(sg))
        # trigger-conditional digital put at the 5% strike (premium approx = RN prob 0.05)
        dput = (s.y < s[K5]).astype(float) - 0.05
        tt = pd.DataFrame({"d": dput[trig_i].values, "date": s.date[trig_i].values})
        if len(tt) > 10:
            m = tt.groupby("date").d.mean()
            rec["trig_put_mean_permonth"] = round(float(m.mean()), 4)
            rec["trig_put_nw_t"] = round(nw_t(m), 2)
            rec["trig_put_pct_of_premium"] = round(float(m.mean() / 0.05), 3)
        st2[f"h{h}"] = rec
        lg(f"h={h}: IQN fires {rec['iqn_trigger_fires']} vs GARCH {rec.get('garch_trigger_fires')} of n={rec['n']}")
    OUT["stage2_exact_trigger"] = st2; OUT["stages_done"].append(2); dump()
except Exception as e:
    OUT["errors"]["stage2"] = repr(e); dump(); lg("STAGE2 FAIL " + repr(e))

# ---------------- stage 3: skill battery at h=21 ----------------
try:
    H = 21
    d = J[(J.h == H)].dropna(subset=["p01", "p05", "p25", "p50", "y"]).copy()
    sigs = {
        "EXACT_trigger_margin_(qq5pct-p05)": (d[K5] - d["p05"]).values,   # >0 = fires; continuous margin
        "IQN_depth_p05": -d["p05"].values,
        "IQN_depth_p01": -d["p01"].values,
        "IQN_shape1_(p50-p05)/(p50-p25)": ((d.p50 - d.p05) / (d.p50 - d.p25)).values,
        "IQN_shape2_(p25-p05)/(p75-p25)": ((d.p25 - d.p05) / (d.p75 - d.p25)).values if "p75" in d else None,
    }
    if "g05" in d.columns:
        dd = d.dropna(subset=["g05"])
        sigs["GARCH_depth_g05"] = None  # computed on dd below
    st3 = {"n": int(len(d)), "n_names": int(d.tk.nunique()), "by_crash_threshold": {}}
    for cthr in [-0.15, -0.20, -0.30]:
        crash = (d.y < cthr).astype(int).values
        rec = {"base_rate": float(crash.mean()), "n_crash": int(crash.sum()), "signals": {}}
        for name, s in sigs.items():
            if s is None: continue
            rec["signals"][name] = {"AUC": auc(s, crash), **decile_stats(s, crash)}
        if "g05" in d.columns:
            dg = d.dropna(subset=["g05"]); crg = (dg.y < cthr).astype(int).values
            for name, s in {"GARCH_depth_g05": -dg.g05.values,
                            "GARCH_shape_(g50-g05)/(g50-g25)": ((dg.g50 - dg.g05) / (dg.g50 - dg.g25)).values,
                            "IQN_minus_GARCH_depth": (-dg.p05.values) - (-dg.g05.values),
                            "EXACT_trigger_margin_GARCH_(qq5pct-g05)": (dg[K5] - dg.g05).values}.items():
                rec["signals"][name] = {"AUC": auc(s, crg), **decile_stats(s, crg)}
        st3["by_crash_threshold"][str(cthr)] = rec
        lg(f"crash<{cthr}: " + " | ".join(f"{k} AUC {v['AUC']:.3f}" for k, v in rec["signals"].items()))
    OUT["stage3_skill"] = st3; OUT["stages_done"].append(3); dump()
except Exception as e:
    OUT["errors"]["stage3"] = repr(e); dump(); lg("STAGE3 FAIL " + repr(e))

# ---------------- stage 4: conditional puts by forecast-risk decile ----------------
try:
    H = 21
    st4 = {}
    for Kcol, tau_k, label in [(K5, 0.05, "strike5pct")] + ([(K10, 0.10, "strike10pct")] if K10 else []):
        s = J[(J.h == H)].dropna(subset=["p05", "y", Kcol]).copy()
        s["risk"] = -s.p05
        s["dec"] = pd.qcut(s["risk"], 10, labels=False, duplicates="drop")
        rows = {}
        for dec, g in s.groupby("dec"):
            net = (g.y < g[Kcol]).astype(float) - tau_k          # digital payoff - premium approx
            bym = pd.DataFrame({"d": net.values, "date": g.date.values}).groupby("date").d.mean()
            rows[int(dec)] = {"n": int(len(g)),
                              "pct_of_premium": round(float(net.mean() / tau_k), 3),
                              "nw_t": round(nw_t(bym), 2),
                              "crash_rate_20": round(float((g.y < -0.20).mean()), 4),
                              "breach_rate": round(float((g.y < g[Kcol]).mean()), 4)}
        overall = (s.y < s[Kcol]).astype(float) - tau_k
        st4[label] = {"overall_pct_of_premium": round(float(overall.mean() / tau_k), 3),
                      "by_decile": rows}
        lg(f"{label}: overall {st4[label]['overall_pct_of_premium']:+.0%} of premium; "
           f"decile9 {rows.get(9, {}).get('pct_of_premium')}")
    OUT["stage4_conditional_puts"] = st4; OUT["stages_done"].append(4); dump()
except Exception as e:
    OUT["errors"]["stage4"] = repr(e); dump(); lg("STAGE4 FAIL " + repr(e))

# ---------------- stage 5: cross-sectional conformal at full scale ----------------
try:
    rngc = np.random.default_rng(0)
    def prep(dh, qcol):
        dd = dh.dropna(subset=[qcol, "y"]).sort_values("date")
        dates = np.array(sorted(dd.date.unique()))
        groups = {t: (dd.loc[dd.date == t, qcol].values, dd.loc[dd.date == t, "y"].values) for t in dates}
        return dates, groups
    def same_date_split(dates, groups, alpha, n_rep=3):
        b = []
        for t in dates:
            q, y = groups[t]; n = len(q)
            if n < 40: continue
            sarr = q - y
            for _ in range(n_rep):
                idx = rngc.permutation(n); half = n // 2
                c = np.quantile(sarr[idx[:half]], min((1 - alpha) * (1 + 1 / half), 1.0))
                b.append((y[idx[half:]] < q[idx[half:]] - c).mean())
        return float(np.mean(b)) if b else None
    def lagged_pooled(dates, groups, alpha, K, lag_idx):
        b_raw, b_adj = [], []
        for i in range(len(dates)):
            j = i - lag_idx
            if j - K < 0: continue
            sarr = np.concatenate([groups[dates[k]][0] - groups[dates[k]][1] for k in range(j - K, j)])
            c = np.quantile(sarr, min((1 - alpha) * (1 + 1 / len(sarr)), 1.0))
            q, y = groups[dates[i]]
            b_raw.append((y < q).mean()); b_adj.append((y < q - c).mean())
        return (float(np.mean(b_raw)), float(np.mean(b_adj))) if b_adj else (None, None)
    def aci(dates, groups, alpha, K, lag_idx, gamma=0.005):
        a_t = alpha; b_adj = []; hist = {}
        for i in range(len(dates)):
            j = i - lag_idx
            if j - K < 0: continue
            sarr = np.concatenate([groups[dates[k]][0] - groups[dates[k]][1] for k in range(j - K, j)])
            a_eff = float(np.clip(a_t, 0.001, 0.2))
            c = np.quantile(sarr, min((1 - a_eff) * (1 + 1 / len(sarr)), 1.0))
            q, y = groups[dates[i]]
            br = (y < q - c).mean(); b_adj.append(br); hist[i] = br
            fb = hist.get(j)
            if fb is not None: a_t = a_t + gamma * (alpha - fb)
        return float(np.mean(b_adj)) if b_adj else None
    H = 21; lag_idx = H + 5
    dh = M[M.h == H]
    st5 = {}
    for qcol, alpha in [("p05", 0.05), ("p01", 0.01)] + ([("g05", 0.05)] if "g05" in dh else []):
        if qcol not in dh: continue
        dates, groups = prep(dh, qcol)
        rec = {"same_date_split": same_date_split(dates, groups, alpha)}
        for K in [8, 60, 250]:
            raw, adj = lagged_pooled(dates, groups, alpha, K, lag_idx)
            rec["raw"] = raw; rec[f"lagged_K{K}"] = adj
        rec["ACI_K60"] = aci(dates, groups, alpha, 60, lag_idx)
        st5[f"{qcol}_a{alpha}"] = rec
        lg(f"conformal {qcol}@{alpha}: raw {rec.get('raw')} same-date {rec['same_date_split']} "
           f"K250 {rec.get('lagged_K250')} ACI {rec['ACI_K60']}")
    OUT["stage5_conformal"] = st5; OUT["stages_done"].append(5); dump()
except Exception as e:
    OUT["errors"]["stage5"] = repr(e); dump(); lg("STAGE5 FAIL " + repr(e))

# ---------------- stage 6: informational-ceiling shares ----------------
try:
    H = 21
    d = J[(J.h == H)].dropna(subset=["p05", "p25", "p50", "y", K5]).copy()
    st6 = {}
    crash = (d.y < -0.20)
    for name, flag in {
        "exact_trigger": (d.p05 < d[K5]),
        "shape_top_decile": (((d.p50 - d.p05) / (d.p50 - d.p25)) >= ((d.p50 - d.p05) / (d.p50 - d.p25)).quantile(0.9)),
        "depth_top_decile": ((-d.p05) >= (-d.p05).quantile(0.9)),
    }.items():
        st6[name] = {"crash_rate_flagged": round(float(crash[flag].mean()), 4),
                     "crash_rate_unflagged": round(float(crash[~flag].mean()), 4),
                     "share_of_crashes_unflagged": round(float(crash[~flag].sum() / max(crash.sum(), 1)), 4)}
    st6["base_rate"] = round(float(crash.mean()), 4)
    OUT["stage6_ceiling"] = st6; OUT["stages_done"].append(6); dump()
    lg("ALLDONE " + json.dumps({k: OUT[k] for k in ["stages_done"]}) + f" {time.time()-t0:.0f}s")
except Exception as e:
    OUT["errors"]["stage6"] = repr(e); dump(); lg("STAGE6 FAIL " + repr(e))
print("FULLCRASHDONE %.0fs" % (time.time() - t0))
