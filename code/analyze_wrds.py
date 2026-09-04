import os, glob, json, time
import numpy as np, pandas as pd
W=r"C:\GBC_data\data\wrds"
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
res={}; t0=time.time()
DB=[-0.5,-0.3,-0.2,-0.15,-0.10,-0.05,0.0]
crisis={2008,2020,2022}
# ---- A) execution-cost surface across all years ----
rows=[]; band_ts=[]
for f in sorted(glob.glob(os.path.join(W,"spreads_*.csv.gz"))):
    yr=int(f[-11:-7])
    d=pd.read_csv(f, usecols=['date','best_bid','best_offer','delta','open_interest','volume'])
    d=d[(d.best_offer>0)&(d.best_bid>=0)]
    d['mid']=(d.best_bid+d.best_offer)/2
    d=d[d['mid']>=0.05]                       # tradeable price floor
    d['relhalf']=(d.best_offer-d.best_bid)/(2*d['mid'])
    d['relhalf']=d['relhalf'].clip(0,1.0)
    d['db']=pd.cut(d['delta'], DB)
    g=d.groupby('db',observed=True)['relhalf'].median()
    rows.append(pd.Series(g, name=yr))
    band=d[(d.delta<=-0.08)&(d.delta>=-0.18)]  # tau.10-.25 trading zone
    band_ts.append((yr, float(band['relhalf'].median()), int(2008<=yr), len(band)))
surf=pd.concat(rows,axis=1)                    # buckets x years
surf.columns=[str(c) for c in surf.columns]
res['halfspread_by_delta_pooled']={str(k):round(float(v),3) for k,v in surf.median(axis=1).items()}
res['halfspread_target_band_by_year']={int(y):round(m,3) for y,m,_,_ in band_ts}
calm=[m for y,m,_,_ in band_ts if y not in crisis]; cri=[m for y,m,_,_ in band_ts if y in crisis]
res['target_band_calm_median']=round(float(np.median(calm)),3)
res['target_band_crisis_median']=round(float(np.median(cri)),3)
# ---- B) net premium by strike (measured cost + documented gross) ----
# documented GROSS annualized return-on-capital & Sharpe (from prior placeholder-cost study)
gross={'tau05':dict(delta=-0.07,yr_ret=0.54,SR=1.59),
       'tau10':dict(delta=-0.12,yr_ret=0.49,SR=1.59),
       'tau25':dict(delta=-0.20,yr_ret=0.82,SR=1.02),
       'tau50':dict(delta=-0.42,yr_ret=1.28,SR=0.85)}
# map each strike to its measured one-way half-spread (nearest bucket)
def hs(delta):
    b=pd.cut([delta],DB)[0]; return float(surf.loc[str(b)].median())
netb={}
for k,v in gross.items():
    h=hs(v['delta'])
    # crude: annual cost drag ~ trades/yr * one-way half-spread * (premium turnover).
    # Paper: 10%-of-premium cost took sell10 SR 1.59->1.20 (0.39 SR drag). Scale drag by (real_hs/0.10).
    drag_10pct=0.39
    scaled=drag_10pct*(h/0.10)
    netb[k]=dict(delta=v['delta'], one_way_halfspread=round(h,3), gross_SR=v['SR'],
                 est_net_SR=round(v['SR']-scaled,2))
res['net_by_strike']=netb
# ---- C) horizon: 10d vs 30d IV term structure (surf10d) ----
tsr=[]
for f in sorted(glob.glob(os.path.join(W,"surf10d_*.csv.gz"))):
    yr=int(f[-11:-7])
    d=pd.read_csv(f)
    d=d[(d.delta<=-0.20)&(d.delta>=-0.30)]    # ~25-delta put
    piv=d.pivot_table(index=['secid','date'],columns='days',values='impl_volatility')
    piv=piv.dropna()
    if 10.0 in piv and 30.0 in piv:
        ratio=(piv[10.0]/piv[30.0])
        tsr.append((yr, round(float(ratio.median()),3), int((ratio>1).mean()*100)))
res['iv_10d_over_30d_by_year']={int(y):r for y,r,_ in tsr}
res['iv_10d_over_30d_pooled_median']=round(float(np.median([r for _,r,_ in tsr])),3)
res['pct_days_10d_above_30d_recent']= [p for y,_,p in tsr if y>=2020]
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"wrds_trading_results.json"),"w"), indent=2)
surf.to_csv(os.path.join(P,"wrds_spread_surface.csv"))
pd.DataFrame(band_ts,columns=['year','band_halfspread','post2008','n']).to_csv(os.path.join(P,"wrds_band_ts.csv"),index=False)
print("DONE", res['runtime_sec'],"s")
print(json.dumps(res,indent=2))
