import os, glob, time, json
import numpy as np, pandas as pd
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
uni=[int(s) for s in pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
V=[]
for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta','volume','open_interest'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    d=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
    if not len(d): continue
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta<0)]
    d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        r=g.iloc[(g.delta+0.12).abs().values.argmin()]
        mid=(float(r.best_bid)+float(r.best_offer))/2
        V.append(dict(vol=float(r.volume), oi=float(r.open_interest), spr_pct=(float(r.best_offer)-float(r.best_bid))/mid if mid>0 else np.nan))
    lg("  %d %d %.0fs"%(yr,len(V),time.time()-t0))
df=pd.DataFrame(V)
q=lambda s,ps: {f"p{int(p*100)}":round(float(s.quantile(p)),1) for p in ps}
out={'n_trades':len(df),
 'daily_volume_at_strike': q(df.vol,[.1,.25,.5,.75,.9]),
 'open_interest_at_strike': q(df.oi,[.1,.25,.5,.75,.9]),
 'bidask_spread_pct_of_mid': q(df.spr_pct.dropna(),[.25,.5,.75]),
 'pct_days_volume_ge': {'10':round(float((df.vol>=10).mean()*100),0),'50':round(float((df.vol>=50).mean()*100),0),'100':round(float((df.vol>=100).mean()*100),0),'500':round(float((df.vol>=500).mean()*100),0)},
 'note':'volume=contracts traded that DAY at the exact strike; 1 contract=100 sh. Capacity ~ small fraction of daily volume to avoid impact.'}
json.dump(out,open(os.path.join(P,"fillability_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("FILLDONE")
