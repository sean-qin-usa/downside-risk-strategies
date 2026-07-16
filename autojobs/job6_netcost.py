# NET-OF-SPREAD weekly vs monthly: settle at BID (full half-spread) vs MID. Does weekly tail advantage survive real cost?
import os, glob, time, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
ranked=[int(s) for s in oi.index]; oi_rank={s:i for i,s in enumerate(ranked)}
px={}; rv={}
for s in ranked:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    if len(t)<40: continue
    t['date']=pd.to_datetime(t['date']); ser=t.set_index('date')['value'].sort_index()
    px[s]=ser; lr=np.log(ser/ser.shift(1)); rv[s]=(lr.rolling(21).std()*math.sqrt(252))
uset=set(px); lg("names=%d %.0fs"%(len(uset),time.time()-t0))
def pxat(s,dt):
    z=px[s][:dt]; return float(z.iloc[-1]) if len(z) else np.nan
def rvat(s,dt):
    z=rv[s][:dt].dropna(); return float(z.iloc[-1]) if len(z) else np.nan
def sr(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def build(pat,dlo,dhi,period):
    rows=[]
    for f in sorted(glob.glob(os.path.join(W,pat))):
        yr=int(os.path.basename(f).split('_')[-1][:4])
        if yr<2016: continue
        parts=[]
        for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
            parts.append(ch[ch.secid.isin(uset)])
        d=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
        if not len(d): continue
        d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
        d=d[(d.dte>=dlo)&(d.dte<=dhi)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta<0)]
        d['cyc']=d['date'].dt.to_period(period)
        for (s,c),g in d.groupby(['secid','cyc']):
            g=g[g.date==g.date.min()]
            if not len(g): continue
            r=g.iloc[(g.delta+0.12).abs().values.argmin()]
            K=r.strike_price/1000.0; sig=float(r.impl_volatility); T=r.dte/365.0; dl=float(r.delta)
            if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
            d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
            p0=pxat(s,r.date); p1=pxat(s,r.exdate); rvt=rvat(s,r.date)
            if not(np.isfinite(p0) and np.isfinite(p1) and p0>0 and np.isfinite(rvt)): continue
            Sx=Se*(p1/p0); payoff=max(K-Sx,0.0); bid=float(r.best_bid); off=float(r.best_offer); mid=(bid+off)/2
            rows.append((s,r.date,(mid-payoff)/K,(bid-payoff)/K,sig,rvt))
        lg("  %s %d %d %.0fs"%(pat,yr,len(rows),time.time()-t0))
    df=pd.DataFrame(rows,columns=['secid','date','net_mid','net_bid','iv','rv_trail'])
    df['ym']=df['date'].dt.to_period('M'); df['vrp']=df['iv']-df['rv_trail']; df['rank']=df.secid.map(oi_rank)
    return df
def sel_stats(df,col,topn=100):
    d=df[df['rank']<topn].dropna(subset=['vrp']); out={}
    for lbl,q in [('all',None),('top25pct',0.75),('top10pct',0.90)]:
        keep=d if q is None else d.groupby('ym',group_keys=False).apply(lambda g:g[g.vrp>=g.vrp.quantile(q)])
        m=keep.groupby('ym')[col].mean()
        out[lbl]=dict(SR=sr(m), avg_bp=round(float(keep[col].mean()*1e4),1), worst_mo=round(float(m.min()*100),2))
    return out
RES={}
wk=build('spreads_dte05_15_*.csv.gz',5,15,'W')
mo=build('spreads_[12]*.csv.gz',20,40,'M')
for lbl,df in [('WEEKLY',wk),('MONTHLY',mo)]:
    RES[lbl]=dict(n=len(df),
        MID={k:sel_stats(df,'net_mid')[k] for k in ['all','top25pct','top10pct']},
        BID={k:sel_stats(df,'net_bid')[k] for k in ['all','top25pct','top10pct']})
json.dump(RES,open(os.path.join(P,"netcost_weekly_vs_monthly.json"),"w"),indent=2,default=str)
lg("NETCOST\n"+json.dumps(RES,indent=2,default=str)); lg("JOB6DONE %.0fs"%(time.time()-t0))
