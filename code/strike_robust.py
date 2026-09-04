# STRIKE ROBUSTNESS: does VRP cross-sectional edge hold at delta -0.05 and -0.20 (not just -0.12)?
import os, glob, math, json, time
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
uni=[int(s) for s in oi.index[:100]]; uset=set(uni)
px={}; rv={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); ser=t.set_index('date')['value'].sort_index(); px[s]=ser; rv[s]=(np.log(ser/ser.shift(1)).rolling(21).std()*math.sqrt(252))
def at(d,dt): z=d[:dt]; return float(z.iloc[-1]) if len(z) else np.nan
def SR(s): s=s.dropna(); return round(float(s.mean()/s.std()*np.sqrt(12)),2) if len(s)>6 and s.std()>0 else None
def build(tgt):
    rows=[]
    for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
        yr=int(os.path.basename(f).split('_')[-1][:4])
        if yr<2016: continue
        parts=[]
        for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
            parts.append(ch[ch.secid.isin(uset)])
        d=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
        if not len(d): continue
        d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
        d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta<0)]
        d['cyc']=d['date'].dt.to_period('M')
        for (s,c),g in d.groupby(['secid','cyc']):
            g=g[g.date==g.date.min()]
            if not len(g) or s not in px: continue
            r=g.iloc[(g.delta-tgt).abs().values.argmin()]
            K=r.strike_price/1000.0; sig=float(r.impl_volatility); T=r.dte/365.0; dl=float(r.delta)
            if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
            d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
            p0=at(px[s],r.date); p1=at(px[s],r.exdate); rvt=at(rv[s],r.date)
            if not(np.isfinite(p0) and np.isfinite(p1) and p0>0 and np.isfinite(rvt)): continue
            Sx=Se*(p1/p0); mid=(float(r.best_bid)+float(r.best_offer))/2
            rows.append((r.date,(mid-max(K-Sx,0.0))/K, sig-rvt))
        lg("  d%.2f %d %.0fs"%(tgt,yr,time.time()-t0))
    return pd.DataFrame(rows,columns=['date','net','vrp'])
out={}
for tgt,lab in [(-0.05,'delta_-0.05'),(-0.12,'delta_-0.12'),(-0.20,'delta_-0.20')]:
    b=build(tgt); b['ym']=b['date'].dt.to_period('M')
    thr=b.groupby('ym')['vrp'].transform(lambda s:s.quantile(0.90)); sel=b[b.vrp>=thr]
    out[lab]=dict(all=SR(b.groupby('ym')['net'].mean()), top10VRP=SR(sel.groupby('ym')['net'].mean()), n=len(b))
    lg(lab+": "+json.dumps(out[lab]))
json.dump(out,open(os.path.join(P,"strike_robust_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("STRIKEDONE")
