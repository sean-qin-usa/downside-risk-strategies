import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time(); lg=lambda s:print(s,flush=True)
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
# rank ALL names by 2023 OI, split into 5 liquidity quintiles, ~28 names each
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
names=[int(s) for s in oi.index]; n=len(names); q=n//5
cohorts={f"Q{i+1}_{'liq' if i==0 else ('illiq' if i==4 else 'mid')}": names[i*q:(i*q+28)] for i in range(5)}
allsec=[s for v in cohorts.values() for s in v]
lg("cohorts sizes: %s ; loading px..."%({k:len(v) for k,v in cohorts.items()}))
px={}
for s in allsec:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
        t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def pxat(s,dt):
    ser=px.get(s)
    if ser is None: return np.nan
    x=ser[:dt]; return float(x.iloc[-1]) if len(x) else np.nan
setc={s:k for k,v in cohorts.items() for s in v}
tr=[]
for f in sorted(glob.glob(os.path.join(W,"spreads_[12]*.csv.gz"))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    d=pd.concat([c[c.secid.isin(allsec)] for c in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000)])
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.impl_volatility>0)&(d.delta<0)]; d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        row=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; dl=float(row.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        Se=K*math.exp(-ppf(-dl)*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,row.date); p1=pxat(s,row.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); payoff=max(K-Sx,0.0); bid=row.best_bid; mid=(bid+row.best_offer)/2 if row.best_offer>0 else bid
        tr.append((setc[s],s,row.date,(bid-payoff)/K,(mid-payoff)/K,bid/K,sig))
    lg("  %d %.0fs"%(yr,time.time()-t0))
T=pd.DataFrame(tr,columns=['coh','secid','date','net','gross','premK','iv']); T['ym']=T['date'].dt.to_period('M')
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>3 and x.std()>0 else None
res={'by_cohort':{}}
for k in cohorts:
    c=T[T.coh==k]; m=c.groupby('ym')['net'].mean()
    res['by_cohort'][k]=dict(gross_premium_pctK=round(c.premK.mean()*100,2), mean_IV=round(c.iv.mean(),3),
        net_SR=sr(m), net_bp_trade=round(c.net.mean()*1e4,1), gross_bp_trade=round(c.gross.mean()*1e4,1),
        spread_cost_bp=round((c.gross-c.net).mean()*1e4,1), worst_mo=round(m.min()*100,1), n=len(c))
# ---- MACRO vs IDIOSYNCRATIC loss decomposition (pooled) ----
mm=T.groupby('ym')['net'].mean()                 # systematic/market component each month
macro_months=set(mm[mm<mm.quantile(0.2)].index)  # bottom-quintile months = systematic stress
neg=T[T.net<0]; tot=neg.net.sum()
macro=neg[neg.ym.isin(macro_months)].net.sum(); idio=tot-macro
# variance decomposition: each trade net = month-mean(macro) + residual(idio)
T['mnet']=T.groupby('ym')['net'].transform('mean'); T['resid']=T['net']-T['mnet']
res['loss_decomp']=dict(macro_crash_month_share_of_loss=round(float(macro/tot),2),
                        idio_singlename_share_of_loss=round(float(idio/tot),2),
                        systematic_var_share=round(float(T['mnet'].var()/T['net'].var()),2),
                        idio_var_share=round(float(T['resid'].var()/T['net'].var()),2))
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res,open(os.path.join(P,"liq_cohort_results.json"),"w"),indent=2,default=str)
lg("DONE"); 
for k,v in res['by_cohort'].items(): lg(f"  {k:12s} gross_prem {v['gross_premium_pctK']}%  IV {v['mean_IV']}  netSR {v['net_SR']}  net {v['net_bp_trade']}bp  spread {v['spread_cost_bp']}bp  worst {v['worst_mo']}")
lg("  LOSS: macro-crash-months %s / idio-singlename %s ; var: systematic %s / idio %s"%(res['loss_decomp']['macro_crash_month_share_of_loss'],res['loss_decomp']['idio_singlename_share_of_loss'],res['loss_decomp']['systematic_var_share'],res['loss_decomp']['idio_var_share']))
