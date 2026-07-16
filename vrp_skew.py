# VRP + SKEW combined selection (top-60 names w/ calls, 2016-25). skew = put_IV(d-0.12) - call_IV(d+0.12).
import os, glob, math, json, time
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
uni=[int(s) for s in pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:60]]
px={}; rv={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); ser=t.set_index('date')['value'].sort_index()
        px[s]=ser; rv[s]=(np.log(ser/ser.shift(1)).rolling(21).std()*math.sqrt(252))
def at(d,dt): 
    z=d[:dt]; return float(z.iloc[-1]) if len(z) else np.nan
def rd(f,cols):
    parts=[]
    for ch in pd.read_csv(f,usecols=cols,chunksize=1000000): parts.append(ch[ch.secid.isin(uni)])
    return pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
rows=[]
for yr in range(2016,2026):
    fp=os.path.join(W,f'spreads_{yr}.csv.gz'); fc=os.path.join(W,f'calls_{yr}.csv.gz')
    if not(os.path.exists(fp) and os.path.exists(fc)): continue
    dp=rd(fp,['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'])
    dc=rd(fc,['secid','date','exdate','impl_volatility','delta'])
    for D in (dp,dc): D['date']=pd.to_datetime(D['date']); D['exdate']=pd.to_datetime(D['exdate']); D['dte']=(D['exdate']-D['date']).dt.days
    dp=dp[(dp.dte>=20)&(dp.dte<=40)&(dp.best_bid>0)&(dp.best_offer>0)&(dp.impl_volatility>0)&(dp.delta<0)]
    dc=dc[(dc.dte>=20)&(dc.dte<=40)&(dc.impl_volatility>0)&(dc.delta>0)]
    dp['cyc']=dp['date'].dt.to_period('M'); dc['cyc']=dc['date'].dt.to_period('M')
    ck={(s,c):g for (s,c),g in dc.groupby(['secid','cyc'])}
    for (s,c),g in dp.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g) or s not in px: continue
        r=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=r.strike_price/1000.0; sig=float(r.impl_volatility); T=r.dte/365.0; dl=float(r.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        gc=ck.get((s,c));
        if gc is None: continue
        gc=gc[gc.date==gc.date.min()]
        if not len(gc): continue
        cr=gc.iloc[(gc.delta-0.12).abs().values.argmin()]; civ=float(cr.impl_volatility)
        d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
        p0=at(px[s],r.date); p1=at(px[s],r.exdate); rvt=at(rv[s],r.date)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0 and np.isfinite(rvt)): continue
        Sx=Se*(p1/p0); mid=(float(r.best_bid)+float(r.best_offer))/2; net=(mid-max(K-Sx,0.0))/K
        rows.append((r.date,net,sig-rvt,sig-civ))  # date, net, VRP, skew
    lg("  %d %d %.0fs"%(yr,len(rows),time.time()-t0))
df=pd.DataFrame(rows,columns=['date','net','vrp','skew']); df['ym']=df['date'].dt.to_period('M')
def SR(s): s=s.dropna(); return round(float(s.mean()/s.std()*np.sqrt(12)),2) if len(s)>6 and s.std()>0 else None
def selq(col,q): thr=df.groupby('ym')[col].transform(lambda s:s.quantile(q)); return df[df[col]>=thr].groupby('ym')['net'].mean()
out=dict(n=len(df), corr_vrp_skew=round(float(df.vrp.corr(df.skew)),2),
  all=SR(df.groupby('ym')['net'].mean()),
  top25_VRP=SR(selq('vrp',0.75)), top25_SKEW=SR(selq('skew',0.75)))
both=df[(df.vrp>=df.groupby('ym')['vrp'].transform(lambda s:s.median()))&(df.skew>=df.groupby('ym')['skew'].transform(lambda s:s.median()))]
out['top50_VRP_AND_SKEW']=SR(both.groupby('ym')['net'].mean())
json.dump(out,open(os.path.join(P,"vrp_skew_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("VRPSKEWDONE")
