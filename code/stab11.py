
import os
import numpy as np, pandas as pd
from arch import arch_model
RAW=r"C:\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))

ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=["date","mktrf","smb","hml","rf"])
ff["date"]=pd.to_datetime(ff["date"].astype(float).astype(int).astype(str),format="%Y%m%d")
ff["mret"]=(ff["mktrf"]+ff["rf"])/100.0
vix=pd.read_csv(os.path.join(RAW,"vix_daily_cboe_mirror.csv"))
dc=[c for c in vix.columns if "date" in c.lower()][0]; cc=[c for c in vix.columns if "close" in c.lower()][-1]
vix["date"]=pd.to_datetime(vix[dc]); vix=vix[["date",cc]].rename(columns={cc:"vix"}).dropna()
df=pd.merge(ff[["date","mret"]],vix,on="date",how="left").sort_values("date")
df["vix"]=df["vix"].ffill(); df=df.dropna(subset=["vix"]).reset_index(drop=True)
r=(df["mret"].values)*100.0

def fitp(cutoff):
    m=df["date"]<=cutoff
    am=arch_model(r[m.values],vol="GARCH",p=1,o=1,q=1,dist="t",rescale=False)
    res=am.fit(disp="off",show_warning=False); p=res.params
    return dict(omega=float(p["omega"]),alpha=float(p["alpha[1]"]),gamma=float(p["gamma[1]"]),
                beta=float(p["beta[1]"]),nu=float(p["nu"]))
pA=fitp("2019-12-31")   # pre-COVID
pB=fitp("2024-12-31")   # through 2024
pF=fitp("2026-07-01")   # full
for nm,p in [("<=2019 (pre-COVID)",pA),("<=2024",pB),("FULL",pF)]:
    persist=p["alpha"]+p["gamma"]/2+p["beta"]
    L(f"params {nm}: omega={p['omega']:.4f} alpha={p['alpha']:.3f} gamma(leverage)={p['gamma']:.3f} beta={p['beta']:.3f} nu(tail df)={p['nu']:.2f} persist={persist:.4f}")

def condvar(p):  # frozen-param GJR recursion over FULL daily series
    om,al,ga,be=p["omega"],p["alpha"],p["gamma"],p["beta"]
    s2=np.empty(len(r)); s2[0]=np.var(r[:250])
    for t in range(1,len(r)):
        e=r[t-1]; s2[t]=om+(al+ga*(e<0))*e*e+be*s2[t-1]
    return s2*252.0/(100.0**2)   # annualized variance, VIX^2 units
df["fA"]=condvar(pA); df["fB"]=condvar(pB)
df["ym"]=df["date"].dt.to_period("M")

# monthly entry forecasts + strategy comparison
rows=[]
for p,sub in df.groupby("ym"):
    if p.year<2009: continue
    e=sub.iloc[0]; idx=e.name
    K=(e["vix"]/100.0)**2; Ksell=((e["vix"]-0.25)/100.0)**2
    fwd=df.iloc[idx+1:idx+22]
    if len(fwd)<15: continue
    rv=252.0*np.mean(fwd["mret"].values**2)
    s0=(Ksell-rv)/K
    wA=np.log(K/e["fA"]); wB=np.log(K/e["fB"])
    rows.append((str(p),int(p.year),s0,e["fA"],e["fB"],wA,wB))
T=pd.DataFrame(rows,columns=["ym","year","s0","fA","fB","wedgeA","wedgeB"])
L("")
L(f"FORECAST agreement 2009-2026: corr(fA,fB)={np.corrcoef(T['fA'],T['fB'])[0,1]:.4f}  mean ratio fA/fB={ (T['fA']/T['fB']).mean():.3f}")
# sign-timing strategy under each frozen model
for tag,w in [("model<=2019","wedgeA"),("model<=2024","wedgeB")]:
    s=np.where(T[w]>0,T["s0"],0.0); s=pd.Series(s)
    L(f"sign-timed by {tag}: SR={s.mean()/s.std()*np.sqrt(12):.2f} totPnL={s.sum()*100:.0f}% aside={(s==0).mean()*100:.0f}%")
# COVID + Apr2025 forecast state
for d in ["2020-02","2020-03","2025-04"]:
    row=T[T["ym"]==d]
    if len(row): L(f"{d}: VIX2 strike vs fA(pre-COVID)={row['fA'].iloc[0]:.4f} vs fB(<=2024)={row['fB'].iloc[0]:.4f}")
T.to_csv(os.path.join(OUT,"stab11_series.csv"),index=False)
open(os.path.join(OUT,"stab11_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("DONESTAB")
