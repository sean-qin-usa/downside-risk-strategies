# SKEW-COMBINED (light): join small calls_{yr} files with improve_trades (already has put IV/net/vrp). No big spreads read.
import os, numpy as np, pandas as pd
W=r"C:\GBC_data\data\wrds"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
imp=pd.read_csv(os.path.join(P,"improve_trades.csv")); imp['ym']=pd.PeriodIndex(pd.to_datetime(imp['date']).dt.to_period('M'),freq='M'); imp=imp.dropna(subset=['vrp'])
rows=[]
for yr in range(2016,2026):
    fc=os.path.join(W,f"calls_{yr}.csv.gz")
    if not os.path.exists(fc): continue
    c=pd.read_csv(fc); c['date']=pd.to_datetime(c.date); c['exdate']=pd.to_datetime(c.exdate); c['dte']=(c.exdate-c.date).dt.days
    c=c[(c.dte>=20)&(c.dte<=40)&(c.impl_volatility>0)&(c.delta>0)]; c['cyc']=c['date'].dt.to_period('M')
    for (s,m),g in c.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        r=g.iloc[(g.delta-0.12).abs().values.argmin()]; rows.append((s,m,float(r.impl_volatility)))
cdf=pd.DataFrame(rows,columns=['secid','ym','civ'])
M=imp.merge(cdf,on=['secid','ym'],how='inner'); M['skew']=M['iv']-M['civ']
def SR(x): x=x.dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def selq(col,q): thr=M.groupby('ym')[col].transform(lambda s:s.quantile(q)); return SR(M[M[col]>=thr].groupby('ym')['net'].mean())
both=M[(M.vrp>=M.groupby('ym')['vrp'].transform(lambda s:s.quantile(0.75)))&(M.skew>=M.groupby('ym')['skew'].transform(lambda s:s.quantile(0.5)))]
out=dict(n=len(M), n_names=int(M.secid.nunique()), corr_vrp_skew=round(float(M.vrp.corr(M.skew)),2),
  all=SR(M.groupby('ym')['net'].mean()), top25_VRP=selq('vrp',0.75), top25_SKEW=selq('skew',0.75),
  top25VRP_and_top50SKEW=SR(both.groupby('ym')['net'].mean()))
import json; json.dump(out,open(os.path.join(P,"skew_light_results.json"),"w"),indent=2,default=str); print(json.dumps(out,indent=2,default=str)); print("SKEWLIGHTDONE")
