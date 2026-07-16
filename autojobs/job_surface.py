# Fit the delta-smile per name/date/expiry; is the d-0.12 put RICH vs its own surface a tradable signal?
import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time(); lg=lambda s:print(s,flush=True)
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
d23=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','open_interest'])
uni=[int(s) for s in d23.groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:40]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
        t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def pxat(s,dt):
    ser=px.get(s)
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
tr=[]
for f in sorted(glob.glob(os.path.join(W,"spreads_[12]*.csv.gz"))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','impl_volatility','delta'],chunksize=1000000)
    d=pd.concat([c[c.secid.isin(uni)] for c in parts])
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.impl_volatility>0)&(d.delta<0)&(d.delta>-0.99)]; d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        gs=g[g.best_bid>0]
        if not len(gs): continue
        sell=gs.iloc[(gs.delta+0.12).abs().values.argmin()]
        smile=g[g.exdate==sell.exdate]
        if len(smile)<5: continue
        try: coef=np.polyfit(smile.delta.values, smile.impl_volatility.values, 2)
        except Exception: continue
        resid=float(sell.impl_volatility - np.polyval(coef, sell.delta))   # >0 = rich vs surface
        K=sell.strike_price/1000.0; sig=float(sell.impl_volatility); T=sell.dte/365.0; dl=float(sell.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        Se=K*math.exp(-ppf(-dl)*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,sell.date); p1=pxat(s,sell.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); net=(sell.best_bid-max(K-Sx,0.0))/K
        tr.append((sell.date,net,resid))
T=pd.DataFrame(tr,columns=['date','net','resid'])
def sr(df):
    if len(df)<12: return None
    m=df.groupby(df['date'].dt.to_period('M'))['net'].mean(); return round(float(m.mean()/m.std()*np.sqrt(12)),2) if m.std()>0 else None
ql,qh=T.resid.quantile([1/3,2/3])
res=dict(n=len(T), resid_mean=round(float(T.resid.mean()),4), resid_std=round(float(T.resid.std()),4),
    corr_resid_net=round(float(T.resid.corr(T.net)),3),
    sell_ALL=dict(SR=sr(T), net_bp=round(T.net.mean()*1e4,1), n=len(T)),
    sell_RICH_vs_surface=dict(SR=sr(T[T.resid>qh]), net_bp=round(T[T.resid>qh].net.mean()*1e4,1), n=int((T.resid>qh).sum())),
    sell_cheap_vs_surface=dict(SR=sr(T[T.resid<=ql]), net_bp=round(T[T.resid<=ql].net.mean()*1e4,1), n=int((T.resid<=ql).sum())))
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"surface_rv_results.json"),"w"), indent=2, default=str)
lg("DONE "+json.dumps(res))
