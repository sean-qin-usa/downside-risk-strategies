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
def nr(df,tgt): return df.iloc[(df.delta-tgt).abs().values.argmin()] if len(df) else None
rows=[]
for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    d=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
    if not len(d): continue
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta<0)]
    d['K']=d.strike_price/1000.0; d['mid']=(d.best_bid+d.best_offer)/2; d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if len(g)<3: continue
        P12=nr(g,-0.12); 
        if P12 is None: continue
        K=P12.K; sig=float(P12.impl_volatility); T=P12.dte/365.0; dl=float(P12.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,P12.date); p1=pxat(s,P12.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0)
        def sp(row): return (float(row.mid)-max(row.K-Sx,0.0))/Se       # short put per unit spot
        def lp(row): return (max(row.K-Sx,0.0)-float(row.mid))/Se        # long put
        rec={'date':P12.date}; rec['naked_d12']=sp(P12)
        for lt,nm in [(-0.05,'spread_buy_d05'),(-0.03,'spread_buy_d03'),(-0.08,'spread_buy_d08')]:
            L=nr(g,lt)
            rec[nm]= sp(P12)+lp(L) if (L is not None and L.K<P12.K) else np.nan
        rows.append(rec)
    lg("  %d %d %.0fs"%(yr,len(rows),time.time()-t0))
df=pd.DataFrame(rows); df['ym']=df['date'].dt.to_period('M')
def sr(x): x=x.dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
out={'n':len(df)}
for k in ['naked_d12','spread_buy_d08','spread_buy_d05','spread_buy_d03']:
    m=df.groupby('ym')[k].mean()
    out[k]=dict(avg_bp=round(float(df[k].mean()*1e4),1), SR=sr(m), worst_mo_pct=round(float(m.min()*100),2),
                mar2020_bp=round(float(df[df.ym==pd.Period('2020-03')][k].mean()*1e4),1) if (df.ym==pd.Period('2020-03')).any() else None)
json.dump(out,open(os.path.join(P,"put_struct_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("PUTSTRUCTDONE")
