
import os
import numpy as np, pandas as pd
RAW=r"C:\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))

# --- daily VIX + market + VIX3M ---
vix=pd.read_csv(os.path.join(RAW,"vix_daily_cboe_mirror.csv"))
dc=[c for c in vix.columns if "date" in c.lower()][0]; cc=[c for c in vix.columns if "close" in c.lower()][-1]
vix["date"]=pd.to_datetime(vix[dc]); vix=vix[["date",cc]].rename(columns={cc:"vix"}).dropna()
ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=["date","mktrf","smb","hml","rf"])
ff["date"]=pd.to_datetime(ff["date"].astype(float).astype(int).astype(str),format="%Y%m%d")
ff["mret"]=(ff["mktrf"]+ff["rf"])/100.0
def load_long(fn,match):
    p=os.path.join(RAW,fn)
    if not os.path.exists(p): return None
    d=pd.read_csv(p); d.columns=[c.strip() for c in d.columns]
    if "ticker" not in d.columns:
        L(fn,"cols",list(d.columns)[:15]); return None
    tk=d["ticker"].astype(str).str.upper()
    L(fn,"tickers:",sorted(set(tk))[:30])
    cand=d[tk.str.contains(match)]
    if "field" in d.columns:
        fl=set(cand["field"].astype(str).str.upper()); pref=[f for f in ["PX_LAST","LAST_PRICE","PX_CLOSE","LAST","CLOSE"] if f in fl]
        if pref: cand=cand[cand["field"].astype(str).str.upper()==pref[0]]
    cand=cand.copy(); cand["date"]=pd.to_datetime(cand["date"],errors="coerce")
    cand["val"]=pd.to_numeric(cand["value"],errors="coerce")
    return cand[["date","val"]].dropna().drop_duplicates("date").sort_values("date")
v3=load_long("vol_indices.csv","VIX3M");
if v3 is None: v3=load_long("bbg_impvol.csv","VIX3M")
# front VIX future (UX1)
f1=load_long("vix_futs_all.csv","UX1")
if f1 is None: f1=load_long("bbg_impvol.csv","UX1")

df=pd.merge(ff[["date","mret"]],vix,on="date",how="left").sort_values("date")
if v3 is not None: df=pd.merge(df,v3.rename(columns={"val":"vix3m"}),on="date",how="left")
if f1 is not None: df=pd.merge(df,f1.rename(columns={"val":"ux1"}),on="date",how="left")
for c in ["vix","vix3m","ux1"]:
    if c in df: df[c]=df[c].ffill()
df=df.dropna(subset=["vix"]).reset_index(drop=True); df["ym"]=df["date"].dt.to_period("M")
L("has ux1:", "ux1" in df, "nonnull ux1:", int(df["ux1"].notna().sum()) if "ux1" in df else 0)

rows=[]
for p,sub in df.groupby("ym"):
    if p.year<2009: continue
    e=sub.iloc[0]; idx=e.name
    K=(e["vix"]/100.0)**2; Ksell=((e["vix"]-0.25)/100.0)**2
    fwd=df.iloc[idx+1:idx+22]
    if len(fwd)<15: continue
    rv=252.0*np.mean(fwd["mret"].values**2)
    s0=(Ksell-rv)/K
    ts=(e["vix"]/e["vix3m"]) if ("vix3m" in df and pd.notna(e.get("vix3m")) and e.get("vix3m")>0) else np.nan
    gated = 0.0 if (ts==ts and ts>=1.0) else s0
    # VIX futures short-carry leg: short front future, cover ~21d later near spot
    fut=np.nan
    if "ux1" in df and pd.notna(e.get("ux1")) and e.get("ux1")>0 and len(fwd)>=15:
        vix_exit=fwd["vix"].iloc[-1]
        fut=(e["ux1"]-vix_exit)/e["ux1"]      # short front future return
    rows.append((str(p),int(p.year),s0,gated,fut))
T=pd.DataFrame(rows,columns=["ym","year","varleg","varleg_gated","futleg"])

def z(x): x=np.asarray(x,float); return x/ (np.nanstd(x)+1e-12)
# scale each leg to comparable risk, build inverse-vol combined book (var-gated + futures)
have_fut = T["futleg"].notna().sum()>50
if have_fut:
    a=T["varleg_gated"].values; b=T["futleg"].values
    m=~np.isnan(b)
    corr=np.corrcoef(a[m],b[m])[0,1]
    L(f"corr(var-gated, futures) = {corr:.3f}  (futures n={m.sum()})")
    # inverse-vol weights, rescale legs to 15% vol each then average
    sa=0.15/(np.nanstd(a)*np.sqrt(12)); sb=0.15/(np.nanstd(b)*np.sqrt(12))
    T["book2"]=np.where(m, 0.5*sa*a+0.5*sb*b, sa*a)
else:
    L("futures leg unavailable -> book2 = var-gated only")
    T["book2"]=T["varleg_gated"]*(0.15/(np.nanstd(T['varleg_gated'])*np.sqrt(12)))

def stats(x):
    x=pd.Series(x).dropna(); m=x.mean(); s=x.std()
    return f"SR={m/s*np.sqrt(12):.2f} mean/mo={m*100:.1f}% worst={x.min()*100:.0f}%"
for lab,(a,b) in {"2009-2026":(2009,2026),"2016-2026":(2016,2026)}.items():
    sub=T[(T.year>=a)&(T.year<=b)]
    L(f"[{lab}] var-gated leg : {stats(sub['varleg_gated']*(0.15/(np.nanstd(T['varleg_gated'])*np.sqrt(12))))}")
    if have_fut: L(f"[{lab}] futures leg   : {stats(sub['futleg']*(0.15/(np.nanstd(T['futleg'])*np.sqrt(12))))}")
    L(f"[{lab}] COMBINED book : {stats(sub['book2'])}")
    L("")
T.to_csv(os.path.join(OUT,"divbook_series.csv"),index=False)
open(os.path.join(OUT,"divbook_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("DONEDIV")
