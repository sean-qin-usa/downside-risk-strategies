import os, glob, math, json, time
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
uni=[int(s) for s in pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def pxat(s,dt):
    ser=px.get(s)
    if ser is None: return np.nan
    z=ser[:dt]; return float(z.iloc[-1]) if len(z) else np.nan
def book(pat,lo,hi,cyc):
    rows=[]
    for f in sorted(glob.glob(os.path.join(W,pat))):
        yr=int(''.join([c for c in os.path.basename(f).split('_')[-1] if c.isdigit()])[:4])
        if yr<2016: continue
        parts=[]
        for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
            parts.append(ch[ch.secid.isin(uni)])
        d=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
        if not len(d): continue
        d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
        d=d[(d.dte>=lo)&(d.dte<=hi)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta<0)]
        d['cyc']=d['date'].dt.to_period(cyc)
        for (s,c),g in d.groupby(['secid','cyc']):
            g=g[g.date==g.date.min()]
            if not len(g): continue
            r=g.iloc[(g.delta+0.12).abs().values.argmin()]
            K=r.strike_price/1000.0; sig=float(r.impl_volatility); T=r.dte/365.0; dl=float(r.delta)
            if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
            d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
            p0=pxat(s,r.date); p1=pxat(s,r.exdate)
            if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
            Sx=Se*(p1/p0); mid=(float(r.best_bid)+float(r.best_offer))/2
            rows.append((r.date,(mid-max(K-Sx,0.0))/K))
        lg("  %s %d %.0fs"%(pat[:16],yr,time.time()-t0))
    b=pd.DataFrame(rows,columns=['date','net']); b['ym']=b['date'].dt.to_period('M'); return b.groupby('ym')['net'].mean()
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
mo=book('spreads_[12]*.csv.gz',20,40,'M')
wkpat='spreads_dte05_15_*.csv.gz'
out={'monthly_SR':sr(mo),'monthly_avg_bp':round(float(mo.mean()*1e4),1)}
if glob.glob(os.path.join(W,wkpat)):
    wk=book(wkpat,5,15,'W')
    idx=mo.index.union(wk.index)
    mo2=mo.reindex(idx).fillna(0); wk2=wk.reindex(idx).fillna(0)
    blend=0.5*mo2+0.5*wk2
    out.update(weekly_SR=sr(wk), weekly_avg_bp=round(float(wk.mean()*1e4),1),
               blend_50_50_SR=sr(blend), blend_worst=round(float(blend.min()*100),2), monthly_worst=round(float(mo.min()*100),2))
else:
    out['weekly']='no weekly data (spreads_dte05_15_*) found'
json.dump(out,open(os.path.join(P,"tenor_ladder_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("TENORDONE")
