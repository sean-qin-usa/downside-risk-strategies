
import os
import numpy as np, pandas as pd
RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a));
def flush(): open(os.path.join(OUT,"timed7_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))

vix=pd.read_csv(os.path.join(RAW,"vix_daily_cboe_mirror.csv"))
dc=[c for c in vix.columns if "date" in c.lower()][0]
cc=[c for c in vix.columns if "close" in c.lower()][-1]
vix["date"]=pd.to_datetime(vix[dc]); vix=vix[["date",cc]].rename(columns={cc:"vix"}).dropna()

ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=["date","mktrf","smb","hml","rf"])
ff["date"]=pd.to_datetime(ff["date"].astype(float).astype(int).astype(str),format="%Y%m%d")
ff["mret"]=(ff["mktrf"]+ff["rf"])/100.0
df=pd.merge(ff[["date","mret"]],vix,on="date",how="left").sort_values("date")
df["vix"]=df["vix"].ffill(); df=df.dropna(subset=["vix"]).reset_index(drop=True)
df["ym"]=df["date"].dt.to_period("M")

have_arch=False
try:
    from arch import arch_model; have_arch=True; L("arch: available (GJR-GARCH-t)")
except Exception as e:
    L("arch: NOT available ->",repr(e)[:50],"| using HAR-RV fallback")
flush()

def har_forecast(hist_r2_daily):
    # HAR on daily realized var proxy r^2: components 1d,5d,22d ; forecast next-day var, annualize
    s=pd.Series(hist_r2_daily)
    rvd=s.iloc[-1]; rvw=s.iloc[-5:].mean(); rvm=s.iloc[-22:].mean()
    # simple HAR-ish blend
    return (0.3*rvd+0.4*rvw+0.3*rvm)*252.0

recs=[]
periods=[p for p in sorted(df["ym"].unique()) if p.year>=1995]
for n,p in enumerate(periods):
    sub=df[df["ym"]==p]; entry=sub.iloc[0]; idx=entry.name
    K=(entry["vix"]/100.0)**2
    Ksell=((entry["vix"]-0.25)/100.0)**2
    fwd=df.iloc[idx+1:idx+22]
    if len(fwd)<15: continue
    rv=252.0*np.mean(fwd["mret"].values**2)
    s0=(Ksell-rv)/K
    hist=df.iloc[:idx+1]
    Fp=np.nan
    if len(hist)>=300:
        if have_arch:
            r=hist["mret"].values[-1200:]*100.0
            try:
                am=arch_model(r,vol="GARCH",p=1,o=1,q=1,dist="t",rescale=False)
                res=am.fit(disp="off",show_warning=False)
                f=res.forecast(horizon=21,reindex=False)
                Fp=float(f.variance.values[-1].mean())*252.0/(100.0**2)
            except Exception:
                Fp=har_forecast(hist["mret"].values**2)
        else:
            Fp=har_forecast(hist["mret"].values**2)
    recs.append([entry["date"].strftime("%Y-%m-%d"),int(p.year),int(p.month),float(s0),float(K),float(Fp)])
    if n%60==0: L("...",p); flush()

T=pd.DataFrame(recs,columns=["date","year","month","s0","K","Fp"])
T["lr"]=np.log(T["K"]/T["Fp"])
# trailing standardized wedge (past-only)
z=np.full(len(T),np.nan)
for i in range(len(T)):
    past=T["lr"].iloc[max(0,i-60):i].dropna()
    if len(past)>=24 and past.std()>0:
        z[i]=(T["lr"].iloc[i]-past.mean())/past.std()
T["z"]=z
T["w1"]=(T["lr"]>0).astype(float)              # sign timing (stand aside if wedge<0)
T["w2"]=(1.0+0.5*T["z"]).clip(0,2).fillna(1.0) # sized timing
T["s1"]=T["w1"]*T["s0"]
T["s2"]=T["w2"]*T["s0"]

def stat(x):
    x=pd.Series(x).dropna(); m=x.mean(); s=x.std()
    return f"n={len(x)} ann={m*12:.3f} SR={m/s*np.sqrt(12):.3f} skew={x.skew():.2f} hit={(x>0).mean():.3f} min={x.min():.2f}"
L("s0(always short):",stat(T["s0"]))
L("s1(sign timing) :",stat(T["s1"]))
L("s2(sized timing):",stat(T["s2"]),"avg_w2",round(T["w2"].mean(),3))
L("TARGETS gjr_t: s1 SR~1.04 skew~-1.14 | s2 SR~1.35 skew~-1.51 ann~3.65")
T.to_csv(os.path.join(OUT,"monthly_timed.csv"),index=False)
L("saved monthly_timed.csv"); flush()
print("DONE7")
