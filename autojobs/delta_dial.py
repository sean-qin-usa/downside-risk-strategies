# Dial-down-delta: in stress (VIX>18) sell FARTHER OTM (delta-0.05) instead of standing down. Compare to baseline & full-standdown.
import os, glob, time, math, json
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
v=pd.read_csv(os.path.join(RAW,'vol_indices.csv')); cl={c.lower():c for c in v.columns}
vv=v[v[cl['ticker']].astype(str).str.strip().isin(['VIX','VIX Index'])]
if cl.get('field'): vv=vv[vv[cl['field']].astype(str).str.contains('PX_LAST',case=False,na=False)]
vv=vv[[cl['date'],cl['value']]].dropna(); vv[cl['date']]=pd.to_datetime(vv[cl['date']]); vix=vv.set_index(cl['date'])[cl['value']].astype(float).sort_index()
def vixat(dt): z=vix[:dt]; return float(z.iloc[-1]) if len(z) else 20.0
def sel(g,tgt):
    r=g.iloc[(g.delta-tgt).abs().values.argmin()]; return r
tr=[]
for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    d=pd.concat(parts) if parts else pd.DataFrame()
    if not len(d): continue
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta<0)]
    for (s,c),g in d.groupby(['secid',d['date'].dt.to_period('M')]):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        asof=g.date.min(); vx=vixat(asof); stress=vx>18
        def pnl(tgt):
            r=sel(g,tgt); K=r.strike_price/1000.0; sig=float(r.impl_volatility); T=r.dte/365.0; dl=float(r.delta)
            if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: return None
            d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,r.date); p1=pxat(s,r.exdate)
            if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): return None
            Sx=Se*(p1/p0); payoff=max(K-Sx,0.0); mid=(float(r.best_bid)+float(r.best_offer))/2; return (mid-payoff)/K
        base=pnl(-0.12)
        if base is None: continue
        dialed = 0.0 if not stress else (pnl(-0.05) if pnl(-0.05) is not None else base)   # stress: sell delta.05
        standdown = 0.0 if stress else base                                                  # stress: skip
        alwaysdial = pnl(-0.05) if stress else base
        tr.append((asof,base,dialed,standdown,alwaysdial))
    lg("  %d %.0fs"%(yr,time.time()-t0))
df=pd.DataFrame(tr,columns=['date','baseline','dial_or_skip','standdown','dial_in_stress']); df['ym']=df['date'].dt.to_period('M')
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
out={'n':len(df)}
for k in ['baseline','standdown','dial_in_stress']:
    m=df.groupby('ym')[k].mean(); out[k]=dict(avg_bp=round(float(df[k].mean()*1e4),1), SR=sr(m), worst_mo_pct=round(float(m.min()*100),2))
json.dump(out,open(os.path.join(P,"delta_dial_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("DIALDONE")
