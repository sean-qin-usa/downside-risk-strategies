# FIX: recover entry spot via BS inversion from (delta,IV,K,T) [split-consistent w/ raw strike],
# then settle S_exdate = S_entry * (adj_px_ratio over holding window) [split-robust return].
import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time(); lg=lambda s: print(s,flush=True)
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
d23=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','open_interest'])
uni=[int(s) for s in d23.groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
lg("universe: "+",".join(sym.get(s,str(s)) for s in uni))
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f, usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
lg("px %d/%d"%(len(px),len(uni)))
def pxat(s,dt):
    ser=px.get(s)
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
def read_filt(f):
    parts=[]
    for ch in pd.read_csv(f, usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'], chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    return pd.concat(parts) if parts else pd.DataFrame()
def run_band(pat,lo,hi,cyc):
    tr=[]
    for f in sorted(glob.glob(os.path.join(W,pat))):
        yr=int(os.path.basename(f).split('_')[-1][:4])
        if yr<2016: continue
        d=read_filt(f)
        if not len(d): continue
        d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate'])
        d['dte']=(d['exdate']-d['date']).dt.days
        d=d[(d.dte>=lo)&(d.dte<=hi)&(d.best_bid>0)&(d.impl_volatility>0)&(d.delta<0)]
        d['cyc']=d['date'].dt.to_period(cyc)
        for (s,c),g in d.groupby(['secid','cyc']):
            g=g[g.date==g.date.min()]
            if not len(g): continue
            row=g.iloc[(g.delta+0.12).abs().values.argmin()]
            K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; dl=float(row.delta)
            if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
            d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)   # entry spot (raw)
            p0=pxat(s,row.date); p1=pxat(s,row.exdate)
            if not (np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
            Sx=Se*(p1/p0)                     # split-robust settle
            payoff=max(K-Sx,0.0); mid=(row.best_bid+row.best_offer)/2 if row.best_offer>0 else row.best_bid
            tr.append((s,row.date,(row.best_bid-payoff)/K,(mid-payoff)/K,dl,K/Se))
        lg("  %s %d -> %d tr %.0fs"%(pat[:11],yr,len(tr),time.time()-t0))
    return pd.DataFrame(tr,columns=['secid','date','net','gross','delta','moneyness'])
res={}
for name,(pat,lo,hi,cyc) in {'monthly':('spreads_[12]*.csv.gz',20,40,'M'),
                             'weekly':('spreads_dte05_15_*.csv.gz',5,15,'W')}.items():
    tr=run_band(pat,lo,hi,cyc)
    mb=tr.groupby(tr['date'].dt.to_period('M')); mn=mb['net'].mean(); mg=mb['gross'].mean()
    sr=lambda x: round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
    res[name]=dict(n=int(len(tr)), avg_moneyness_KoverS=round(float(tr.moneyness.mean()),3),
        net_bp_per_trade=round(float(tr.net.mean()*1e4),1), gross_bp_per_trade=round(float(tr.gross.mean()*1e4),1),
        spread_cost_bp=round(float((tr.gross-tr.net).mean()*1e4),1),
        net_SR=sr(mn), gross_SR=sr(mg), net_hit=round(float((tr.net>0).mean()),3),
        worst_trade_pctK=round(float(tr.net.min()*100),1),
        net_by_year={int(y):round(float(tr[tr.date.dt.year==y].net.mean()*1e4),1) for y in range(2016,2026) if (tr.date.dt.year==y).any()})
    lg(name+" => "+json.dumps(res[name]))
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"bt_real2_results.json"),"w"), indent=2)
lg("ALL DONE")
