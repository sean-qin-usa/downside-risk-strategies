
import os
import numpy as np, pandas as pd
RAW=r"C:\GBC_data\data\raw"
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
df=pd.merge(ff[["date","mret"]],vix,on="date",how="left").sort_values("date")
df["vix"]=df["vix"].ffill(); df=df.dropna(subset=["vix"]).reset_index(drop=True)

def leg(hold):  # hold = trading days per swap (5=weekly, 21=monthly)
    rows=[]
    i=0
    while i < len(df)-hold-1:
        entry=df.iloc[i]
        if entry["date"].year<1995: i+=hold; continue
        K=(entry["vix"]/100.0)**2
        Ksell=((entry["vix"]-0.25)/100.0)**2
        fwd=df.iloc[i+1:i+1+hold]
        if len(fwd)<max(3,hold-2): i+=hold; continue
        rv=252.0*np.mean(fwd["mret"].values**2)
        rows.append((entry["date"].strftime("%Y-%m-%d"),(Ksell-rv)/K))
        i+=hold
    return pd.DataFrame(rows,columns=["date","ret"])

wk=leg(5); mo=leg(21)
for nm,s in [("WEEKLY(5d)",wk["ret"]),("MONTHLY(21d)",mo["ret"])]:
    m=s.mean(); sd=s.std(); ann=np.sqrt(252/ (5 if "WEEK" in nm else 21))
    L(nm,"n",len(s),"mean%strike",round(m,4),"SR_ann",round(m/sd*ann,3),
      "skew",round(s.skew(),2),"worst",round(s.min(),2),"hit",round((s>0).mean(),3))

# April 2025 focus
wk["dt"]=pd.to_datetime(wk["date"]); mo["dt"]=pd.to_datetime(mo["date"])
apr_wk=wk[(wk["dt"]>="2025-03-25")&(wk["dt"]<="2025-05-05")]
apr_mo=mo[(mo["dt"]>="2025-03-25")&(mo["dt"]<="2025-05-05")]
L("APR2025 weekly legs:",[ (d[5:10],round(r,2)) for d,r in zip(apr_wk["date"],apr_wk["ret"]) ])
L("APR2025 weekly compounded over the window:",round((1+apr_wk["ret"]).prod()-1,2))
L("APR2025 monthly leg(s):",[ (d[5:10],round(r,2)) for d,r in zip(apr_mo["date"],apr_mo["ret"]) ])

wk[["date","ret"]].to_csv(os.path.join(OUT,"weekly_strategy.csv"),index=False)
mo[["date","ret"]].to_csv(os.path.join(OUT,"monthly_strategy_recheck.csv"),index=False)
open(os.path.join(OUT,"recon_wk_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("DONEWK")
