# Stress test: strike sweep + wider universe + real commissions + seasonality gate + era splits + bootstrap.
import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time(); lg=lambda s:print(s,flush=True)
COMM=0.70   # $/contract (commission+fees) ; per share = COMM/100 ; frac of K = (COMM/100)/K
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
d23=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','open_interest'])
uni=[int(s) for s in d23.groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:40]]
lg("universe n=%d"%len(uni))
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
        t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
lg("px %d/%d %.0fs"%(len(px),len(uni),time.time()-t0))
def pxat(s,dt):
    ser=px.get(s);
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
DELTAS=[-0.05,-0.10,-0.15,-0.20,-0.30]
rows={dl:[] for dl in DELTAS}
for f in sorted(glob.glob(os.path.join(W,"spreads_[12]*.csv.gz"))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    d=pd.concat(parts); d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.impl_volatility>0)&(d.delta<0)]
    d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        p0=pxat(s,g.iloc[0].date)
        for dl in DELTAS:
            row=g.iloc[(g.delta-dl).abs().values.argmin()]
            K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; d0=float(row.delta)
            if K<=0 or sig<=0 or T<=0 or -d0<=0 or -d0>=1: continue
            Se=K*math.exp(-ppf(-d0)*sig*math.sqrt(T)-0.5*sig*sig*T); p1=pxat(s,row.exdate)
            if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
            Sx=Se*(p1/p0); payoff=max(K-Sx,0.0); comm=(COMM/100.0)/K
            rows[dl].append((s,row.date,(row.best_bid-payoff)/K - comm))
    lg("  %d %.0fs"%(yr,time.time()-t0))
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>2 and x.std()>0 else None
res={'universe_n':len(uni),'commission_per_contract':COMM}
sweep={}
best=None; bestsr=-9
for dl in DELTAS:
    T=pd.DataFrame(rows[dl],columns=['secid','date','net']); T['ym']=T['date'].dt.to_period('M')
    mon=T.groupby('ym')['net'].mean()
    s=sr(mon); sweep[str(dl)]=dict(net_SR_with_comm=s, ann_ret_pctK=round(mon.mean()*12*100,2), net_bp_trade=round(T.net.mean()*1e4,1), n=len(T))
    if s and s>bestsr: bestsr=s; best=dl
res['strike_sweep']=sweep; res['best_delta']=best
# deep-dive on best delta
T=pd.DataFrame(rows[best],columns=['secid','date','net']); T['ym']=T['date'].dt.to_period('M'); T['mo']=T['date'].dt.month; T['yr']=T['date'].dt.year
mon=T.groupby('ym')['net'].mean()
res['best']=dict(delta=best, net_SR=sr(mon), ann_ret_pctK=round(mon.mean()*12*100,2))
# era splits
eras={'2016-2019':range(2016,2020),'2020-2022':range(2020,2023),'2023-2025':range(2023,2026)}
res['era_splits']={k:sr(T[T.yr.isin(v)].groupby('ym')['net'].mean()) for k,v in eras.items()}
# seasonality gate (drop Feb+Mar)
res['seasonality_gate']=dict(all=sr(mon), ex_feb_mar=sr(T[~T.mo.isin([2,3])].groupby('ym')['net'].mean()),
                             feb_mar_only_mean_bp=round(T[T.mo.isin([2,3])].net.mean()*1e4,1))
# block bootstrap CI on SR (3-month blocks of monthly returns)
mv=mon.values; n=len(mv); bl=3; srs=[]
rng=np.random.default_rng(0)
for _ in range(2000):
    idx=[]; 
    while len(idx)<n:
        st=rng.integers(0,n-bl); idx+=list(range(st,st+bl))
    b=np.array([mv[i] for i in idx[:n]]); 
    if b.std()>0: srs.append(b.mean()/b.std()*np.sqrt(12))
res['bootstrap_SR_ci']=dict(p5=round(float(np.percentile(srs,5)),2), p50=round(float(np.percentile(srs,50)),2), p95=round(float(np.percentile(srs,95)),2))
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"bt_sweep_results.json"),"w"), indent=2)
lg("ALL DONE"); lg(json.dumps(res['strike_sweep'])); lg(json.dumps(res['era_splits'])); lg(json.dumps(res['seasonality_gate']))
