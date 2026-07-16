# Does VRP selection survive within LIQUID names (executable)? Restrict to top-100 by OI, then VRP-select.
import os, numpy as np, pandas as pd
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
df=pd.read_csv(os.path.join(P,"improve_trades.csv")); df['ym']=pd.PeriodIndex(pd.to_datetime(df['date']).dt.to_period('M'),freq='M')
df=df.dropna(subset=['vrp'])
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
rank={int(s):i for i,s in enumerate(oi.index)}
df['liq']=df.secid.map(rank)
def sr(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def sel(d,q): 
    keep=d.groupby('ym',group_keys=False).apply(lambda g: g[g.vrp>=g.vrp.quantile(q)] if len(g) else g, include_groups=False)
    return sr(keep.groupby(keep.index if 'ym' not in keep else 'ym')['net'].mean()) if False else sr(d[d.vrp>=d.groupby('ym')['vrp'].transform(lambda s:s.quantile(q))].groupby('ym')['net'].mean())
out={}
for Nlab,N in [("top50 liquid",50),("top100 liquid",100),("top200 liquid",200),("all 542",100000)]:
    d=df[df.liq<N]
    row={"n_names":int(d.secid.nunique()),"all":sr(d.groupby('ym')['net'].mean())}
    for q,lab in [(0.5,"top50%VRP"),(0.75,"top25%VRP"),(0.9,"top10%VRP")]:
        thr=d.groupby('ym')['vrp'].transform(lambda s:s.quantile(q)); row[lab]=sr(d[d.vrp>=thr].groupby('ym')['net'].mean())
    out[Nlab]=row
import json; print(json.dumps(out,indent=2,default=str)); json.dump(out,open(os.path.join(P,"liq_vrp_results.json"),"w"),indent=2,default=str)
print("LIQVRPDONE")
