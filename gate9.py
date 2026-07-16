
import os
import numpy as np, pandas as pd
RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))

# --- VIX daily + market daily ---
vix=pd.read_csv(os.path.join(RAW,"vix_daily_cboe_mirror.csv"))
dc=[c for c in vix.columns if "date" in c.lower()][0]
cc=[c for c in vix.columns if "close" in c.lower()][-1]
vix["date"]=pd.to_datetime(vix[dc]); vix=vix[["date",cc]].rename(columns={cc:"vix"}).dropna()
ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=["date","mktrf","smb","hml","rf"])
ff["date"]=pd.to_datetime(ff["date"].astype(float).astype(int).astype(str),format="%Y%m%d")
ff["mret"]=(ff["mktrf"]+ff["rf"])/100.0

# --- VIX3M for term structure (try bbg_impvol.csv then vol_indices.csv) ---
def find_vix3m():
    for fn in ["bbg_impvol.csv","vol_indices.csv"]:
        p=os.path.join(RAW,fn)
        if not os.path.exists(p): continue
        d=pd.read_csv(p)
        L(fn,"cols:",list(d.columns)[:40])
        datecol=[c for c in d.columns if "date" in c.lower()]
        if not datecol: continue
        dcol=datecol[0]
        v3=[c for c in d.columns if ("3M" in c.upper() or "VXV" in c.upper()) and "VIX" in c.upper()]
        if not v3: v3=[c for c in d.columns if "VIX3M" in c.upper() or c.upper() in("VXV","VXV INDEX")]
        if v3:
            d["date"]=pd.to_datetime(d[dcol],errors="coerce")
            out=d[["date",v3[0]]].rename(columns={v3[0]:"vix3m"}).dropna()
            L("VIX3M source",fn,"col",v3[0],"rows",len(out),"range",str(out['date'].min().date()),str(out['date'].max().date()))
            return out
    return None
v3=find_vix3m()

df=pd.merge(ff[["date","mret"]],vix,on="date",how="left").sort_values("date")
if v3 is not None:
    df=pd.merge(df,v3,on="date",how="left")
df["vix"]=df["vix"].ffill()
if "vix3m" in df: df["vix3m"]=df["vix3m"].ffill()
df=df.dropna(subset=["vix"]).reset_index(drop=True)
df["ym"]=df["date"].dt.to_period("M")

CAP=-0.75  # defined-risk floor
rows=[]
for p,sub in df.groupby("ym"):
    if p.year<1995: continue
    e=sub.iloc[0]; idx=e.name
    K=(e["vix"]/100.0)**2; Ksell=((e["vix"]-0.25)/100.0)**2
    fwd=df.iloc[idx+1:idx+22]
    if len(fwd)<15: continue
    rv=252.0*np.mean(fwd["mret"].values**2)
    s0=max((Ksell-rv)/K, CAP)
    ts=(e["vix"]/e["vix3m"]) if ("vix3m" in df and pd.notna(e.get("vix3m"))) else np.nan
    rows.append((str(p),int(p.year),float(s0),float(ts) if ts==ts else np.nan,float(e["vix"])))
T=pd.DataFrame(rows,columns=["ym","year","s0","ts","vix_entry"])

# GATE (a-priori, NO tuning): stand aside when term structure inverted (VIX >= VIX3M)
T["gated"]= np.where(T["ts"]<1.0, T["s0"], 0.0)
T.loc[T["ts"].isna(),"gated"]=T["s0"]   # if no TS data (pre-2007), stay short

def stats(x):
    x=pd.Series(x).dropna();
    if len(x)<6: return "n<6"
    m=x.mean(); s=x.std()
    return f"n={len(x):3d} SR={m/s*np.sqrt(12):5.2f} mean/mo={m*100:5.1f}% totPnL={x.sum()*100:6.0f}% worst={x.min()*100:5.0f}% hit={(x>0).mean()*100:.0f}%"
for lab,(a,b) in {"POST-2008 (2009-2026)":(2009,2026),"LAST 10Y (2016-2026)":(2016,2026),
                  "2026 HOLDOUT (design<=2025)":(2026,2026),"FULL 1995-2026":(1995,2026)}.items():
    sub=T[(T.year>=a)&(T.year<=b)]
    L(f"[{lab}]  s0   : {stats(sub['s0'])}")
    L(f"[{lab}]  gated: {stats(sub['gated'])}")
    L(f"[{lab}]  share gated-to-cash: {(sub['gated']==0).mean()*100:.0f}%")
    L("")

T.to_csv(os.path.join(OUT,"gate9_series.csv"),index=False)
open(os.path.join(OUT,"gate9_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("DONEGATE")
