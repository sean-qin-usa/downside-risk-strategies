import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; RES=r"C:\GBC_data\results\pq_trade"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
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
# IQN physical quantiles, h=21
q=pd.read_csv(os.path.join(RES,"mh_quantiles_gpu_v2.csv")); q=q[q.h==21].copy(); q['date']=pd.to_datetime(q['date'])
qcols=['p01','p05','p10','p25','p50','p75','p90','p95','p99']; taus=np.array([.01,.05,.10,.25,.50,.75,.90,.95,.99])
byname={}
for tk,g in q.groupby('tk'):
    g=g.sort_values('date'); byname[tk]=(g['date'].values.astype('datetime64[D]'), g[qcols].values)
lg("IQN names %d  %.0fs"%(len(byname),time.time()-t0))
def iqn_breach(tk,dt,x):
    if tk not in byname: return np.nan
    dates,Q=byname[tk]; d0=np.datetime64(pd.Timestamp(dt),'D'); i=np.searchsorted(dates,d0)
    cand=[j for j in (i-1,i) if 0<=j<len(dates)]
    if not cand: return np.nan
    j=min(cand,key=lambda k:abs((dates[k]-d0).astype(int)))
    if abs((dates[j]-d0).astype(int))>7: return np.nan
    return float(np.interp(x, Q[j], taus))
tr=[]
for f in sorted(glob.glob(os.path.join(W,"spreads_[12]*.csv.gz"))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','impl_volatility','delta'],chunksize=1000000)]
    d=pd.concat([c[c.secid.isin(uni)] for c in parts[0]])
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.impl_volatility>0)&(d.delta<0)]; d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        row=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; dl=float(row.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        Se=K*math.exp(-ppf(-dl)*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,row.date); p1=pxat(s,row.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); net=(row.best_bid-max(K-Sx,0.0))/K
        Pb=iqn_breach(sym.get(s),row.date, math.log(K/Se))
        if Pb!=Pb: continue
        tr.append((row.date,net,(-dl)-Pb,-dl,Pb))
T=pd.DataFrame(tr,columns=['date','net','gap','Qb','Pb'])
def sr(df):
    if len(df)<12: return None
    m=df.groupby(df['date'].dt.to_period('M'))['net'].mean(); return round(float(m.mean()/m.std()*np.sqrt(12)),2) if m.std()>0 else None
ql,qh=T.gap.quantile([1/3,2/3])
res=dict(n=len(T), mean_Qb_market=round(float(T.Qb.mean()),3), mean_Pb_model=round(float(T.Pb.mean()),3),
    corr_gap_net=round(float(T.gap.corr(T.net)),3),
    sell_ALL=dict(SR=sr(T), net_bp=round(T.net.mean()*1e4,1), n=len(T)),
    sell_OVERPRICED_topgap=dict(SR=sr(T[T.gap>qh]), net_bp=round(T[T.gap>qh].net.mean()*1e4,1), n=int((T.gap>qh).sum())),
    sell_cheap_bottomgap=dict(SR=sr(T[T.gap<=ql]), net_bp=round(T[T.gap<=ql].net.mean()*1e4,1), n=int((T.gap<=ql).sum())))
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"iqn_fairvalue_results.json"),"w"), indent=2, default=str)
lg("DONE "+json.dumps(res))
