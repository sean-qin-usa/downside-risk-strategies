
import os
import numpy as np, pandas as pd
RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))

vix=pd.read_csv(os.path.join(RAW,"vix_daily_cboe_mirror.csv"))
dc=[c for c in vix.columns if "date" in c.lower()][0]
cc=[c for c in vix.columns if "close" in c.lower()][-1]
vix["date"]=pd.to_datetime(vix[dc]); vix=vix[["date",cc]].rename(columns={cc:"vix"}).dropna()
ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=["date","mktrf","smb","hml","rf"])
ff["date"]=pd.to_datetime(ff["date"].astype(float).astype(int).astype(str),format="%Y%m%d")
ff["mret"]=(ff["mktrf"]+ff["rf"])/100.0

def load_vix3m():
    for fn in ["vol_indices.csv","bbg_impvol.csv"]:
        p=os.path.join(RAW,fn)
        if not os.path.exists(p): continue
        d=pd.read_csv(p); d.columns=[c.strip() for c in d.columns]
        tk=d["ticker"].astype(str).str.upper()
        L(fn,"VIX-ish tickers:",sorted(set(tk[tk.str.contains('VIX')]))[:25])
        cand=d[tk.str.contains("VIX3M")|tk.str.contains("VXV")]
        if len(cand)==0: continue
        if "field" in d.columns:
            flds=set(cand["field"].astype(str).str.upper())
            pref=[f for f in ["PX_LAST","LAST_PRICE","PX_CLOSE","LAST","CLOSE"] if f in flds]
            if pref: cand=cand[cand["field"].astype(str).str.upper()==pref[0]]
        cand=cand.copy()
        cand["date"]=pd.to_datetime(cand["date"],errors="coerce")
        cand["vix3m"]=pd.to_numeric(cand["value"],errors="coerce")
        out=cand[["date","vix3m"]].dropna().drop_duplicates("date").sort_values("date")
        if len(out)>100:
            L("VIX3M from",fn,"rows",len(out),"range",str(out.date.min().date()),str(out.date.max().date()))
            return out
    return None
v3=load_vix3m()

df=pd.merge(ff[["date","mret"]],vix,on="date",how="left").sort_values("date")
if v3 is not None: df=pd.merge(df,v3,on="date",how="left")
df["vix"]=df["vix"].ffill()
if "vix3m" in df: df["vix3m"]=df["vix3m"].ffill()
df=df.dropna(subset=["vix"]).reset_index(drop=True); df["ym"]=df["date"].dt.to_period("M")

rows=[]
for p,sub in df.groupby("ym"):
    if p.year<1995: continue
    e=sub.iloc[0]; idx=e.name
    K=(e["vix"]/100.0)**2; Ksell=((e["vix"]-0.25)/100.0)**2
    fwd=df.iloc[idx+1:idx+22]
    if len(fwd)<15: continue
    rv=252.0*np.mean(fwd["mret"].values**2)
    s0=(Ksell-rv)/K
    ts=(e["vix"]/e["vix3m"]) if ("vix3m" in df and pd.notna(e.get("vix3m")) and e.get("vix3m")>0) else np.nan
    rows.append((str(p),int(p.year),float(s0),float(ts) if ts==ts else np.nan))
T=pd.DataFrame(rows,columns=["ym","year","s0","ts"])
T["inverted"]=T["ts"]>=1.0
T["gated"]=np.where(T["inverted"], 0.0, T["s0"])
T.loc[T["ts"].isna(),"gated"]=T.loc[T["ts"].isna(),"s0"]

def stats(x):
    x=pd.Series(x).dropna()
    if len(x)<3: return "n<3"
    m=x.mean(); s=x.std()
    return f"n={len(x):3d} SR={m/s*np.sqrt(12):5.2f} mean/mo={m*100:5.1f}% totPnL={x.sum()*100:6.0f}% worst={x.min()*100:6.0f}% hit={(x>0).mean()*100:.0f}%"
for lab,(a,b) in {"POST-2008 2009-2026":(2009,2026),"LAST 10Y 2016-2026":(2016,2026),
                  "2026 HOLDOUT (partial)":(2026,2026),"FULL 1995-2026":(1995,2026)}.items():
    sub=T[(T.year>=a)&(T.year<=b)]
    L(f"[{lab}]  always-short: {stats(sub['s0'])}")
    L(f"[{lab}]  TS-gated    : {stats(sub['gated'])}")
    L(f"[{lab}]  months stood aside: {int((sub['gated']==0).sum())}/{len(sub)}")
    L("")
T.to_csv(os.path.join(OUT,"gate10_series.csv"),index=False)
open(os.path.join(OUT,"gate10_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("DONE10")
