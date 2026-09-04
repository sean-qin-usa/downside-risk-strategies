
import os
import numpy as np, pandas as pd
RAW=r"C:\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))

# ---- VIX daily ----
vix=pd.read_csv(os.path.join(RAW,"vix_daily_cboe_mirror.csv"))
datec=[c for c in vix.columns if "date" in c.lower()][0]
closecs=[c for c in vix.columns if "close" in c.lower()]
closec=closecs[-1] if closecs else vix.columns[-1]
vix["date"]=pd.to_datetime(vix[datec])
vix=vix[["date",closec]].rename(columns={closec:"vix"}).dropna().sort_values("date")
L("vix cols",list(pd.read_csv(os.path.join(RAW,'vix_daily_cboe_mirror.csv'),nrows=1).columns),
  "used close=",closec,"rows",len(vix),"range",str(vix['date'].min().date()),str(vix['date'].max().date()))

# ---- market daily total return (S&P proxy) from Fama-French ----
ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=["date","mktrf","smb","hml","rf"])
ff["date"]=pd.to_datetime(ff["date"].astype(float).astype(int).astype(str),format="%Y%m%d")
ff["mret"]=(ff["mktrf"]+ff["rf"])/100.0
mkt=ff[["date","mret"]].sort_values("date").reset_index(drop=True)

df=pd.merge(mkt,vix,on="date",how="left").sort_values("date").reset_index(drop=True)
df["vix"]=df["vix"].ffill()
df=df.dropna(subset=["vix"]).reset_index(drop=True)
df["ym"]=df["date"].dt.to_period("M")

# ---- Leg A: short 1M variance swap, non-overlapping monthly ----
rows=[]
for p,sub in df.groupby("ym"):
    if p.year<1995: continue
    entry=sub.iloc[0]; idx=entry.name
    K=(entry["vix"]/100.0)**2                 # strike variance
    Ksell=((entry["vix"]-0.25)/100.0)**2      # 0.25 vol-pt half-spread
    fwd=df.iloc[idx+1: idx+22]                 # next 21 trading days
    if len(fwd)<15: continue
    rv=252.0*np.mean(fwd["mret"].values**2)   # annualized realized variance
    ret=(Ksell-rv)/K                          # short-var return, % of strike
    rows.append((entry["date"].strftime("%Y-%m-%d"),int(p.year),int(p.month),float(ret)))
S=pd.DataFrame(rows,columns=["date","year","month","strat_ret"])
mm=S["strat_ret"].mean(); sd=S["strat_ret"].std()
L("RECON n",len(S),"mean_mo",round(mm,4),"ann(x12)",round(mm*12,3),
  "SR",round(mm/sd*np.sqrt(12),3),"hit",round((S['strat_ret']>0).mean(),3),
  "skew",round(S['strat_ret'].skew(),2))
L("TARGET (bt_monthly s0): mean_mo~0.252 ann~2.69 SR~1.07 hit~0.814 skew~-4.15")
S.to_csv(os.path.join(OUT,"monthly_strategy.csv"),index=False)

# ---- S&P monthly total return (same market proxy) ----
mkt["ym"]=mkt["date"].dt.to_period("M")
spx=mkt.groupby("ym")["mret"].apply(lambda x:(1+x).prod()-1).reset_index()
spx.columns=["ym","spx_ret"]; spx["ym"]=spx["ym"].astype(str)
spx.to_csv(os.path.join(OUT,"spx_monthly2.csv"),index=False)
L("spx rows",len(spx))

open(os.path.join(OUT,"recon6_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("DONE6")
