# High-impact CLEAN levers: (1) BREADTH (more names -> diversify idio), (2) CROSS-SECTIONAL VRP SELECTION.
# Leakage-free: VRP = entry IV - TRAILING 21d realized vol (both known at entry). Mid execution.
import os, glob, time, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
ranked=[int(s) for s in oi.index]
# load px + trailing RV for every name that has a tpx file (this bounds our breadth)
px={}; rv={}
for s in ranked:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    if len(t)<40: continue
    t['date']=pd.to_datetime(t['date']); ser=t.set_index('date')['value'].sort_index()
    px[s]=ser; lr=np.log(ser/ser.shift(1)); rv[s]=(lr.rolling(21).std()*math.sqrt(252))  # trailing 21d annualized
uni=[s for s in ranked if s in px]
lg("names with px (max breadth)=%d"%len(uni))
def pxat(s,dt):
    z=px[s][:dt]; return float(z.iloc[-1]) if len(z) else np.nan
def rvat(s,dt):
    z=rv[s][:dt].dropna(); return float(z.iloc[-1]) if len(z) else np.nan
uset=set(uni); rows=[]
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
        if not len(g): continue
        r=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=r.strike_price/1000.0; sig=float(r.impl_volatility); T=r.dte/365.0; dl=float(r.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
        p0=pxat(s,r.date); p1=pxat(s,r.exdate); rvt=rvat(s,r.date)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); mid=(float(r.best_bid)+float(r.best_offer))/2; net=(mid-max(K-Sx,0.0))/K
        rows.append((s,r.date,net,sig,rvt))
    lg("  %d %d %.0fs"%(yr,len(rows),time.time()-t0))
df=pd.DataFrame(rows,columns=['secid','date','net','iv','rv_trail']); df['ym']=df['date'].dt.to_period('M')
df['vrp']=df['iv']-df['rv_trail']
df.to_csv(os.path.join(P,"improve_trades.csv"),index=False)
def sr(x): x=x.dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
out={'n_trades':len(df),'n_names':df.secid.nunique(),'baseline_18':None}
# BREADTH: top-N names by OI, equal-weight monthly
oi_rank={s:i for i,s in enumerate(ranked)}
df['rank']=df.secid.map(oi_rank)
br={}
for N in [18,50,100,200,100000]:
    sub=df[df['rank']<N]; m=sub.groupby('ym')['net'].mean()
    br[f"top{min(N,df.secid.nunique())}"]=dict(SR=sr(m), avg_bp=round(float(sub.net.mean()*1e4),1), names=int(sub.secid.nunique()), worst_mo=round(float(m.min()*100),2))
out['BREADTH']=br
# CROSS-SECTIONAL VRP SELECTION: each month keep top/bottom quantile by entry VRP (clean)
sel={}
d2=df.dropna(subset=['vrp'])
for lbl,fn in [('all',lambda g:g),
               ('top50pct_VRP',lambda g:g[g.vrp>=g.vrp.median()]),
               ('top25pct_VRP',lambda g:g[g.vrp>=g.vrp.quantile(0.75)]),
               ('bottom25pct_VRP',lambda g:g[g.vrp<=g.vrp.quantile(0.25)])]:
    keep=d2.groupby('ym',group_keys=False).apply(fn); m=keep.groupby('ym')['net'].mean()
    sel[lbl]=dict(SR=sr(m), avg_bp=round(float(keep.net.mean()*1e4),1), worst_mo=round(float(m.min()*100),2))
out['CROSS_SECTIONAL_VRP']=sel
json.dump(out,open(os.path.join(P,"improve_sharpe_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("IMPROVEDONE")
