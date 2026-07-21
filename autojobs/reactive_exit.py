import os, glob, time, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
Ncdf=NormalDist().cdf; ppf=NormalDist().inv_cdf
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
uni=[int(s) for s in pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def path(s,d0,d1):
    ser=px.get(s)
    if ser is None: return None
    p=ser[(ser.index>=d0)&(ser.index<=d1)]; return p if len(p)>=2 else None
def bs_put(S,K,T,sig):
    if T<=1e-6 or sig<=0: return max(K-S,0.0)
    d1=(math.log(S/K)+0.5*sig*sig*T)/(sig*math.sqrt(T)); d2=d1-sig*math.sqrt(T); return K*Ncdf(-d2)-S*Ncdf(-d1)
STOPS={'hold':None,'stop_-10%':0.10,'stop_-15%':0.15,'stop_-20%':0.20,'stop_strike':'K'}
tr=[]
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
    d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        row=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); dl=float(row.delta); T0=row.dte/365.0
        if K<=0 or sig<=0 or -dl<=0 or -dl>=1: continue
        d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T0)-0.5*sig*sig*T0)
        pp=path(s,row.date,row.exdate)
        if pp is None: continue
        p_e=float(pp.iloc[0]); Spath=Se*(pp.values/p_e); dates=pp.index; mid=(float(row.best_bid)+float(row.best_offer))/2
        rec={'date':row.date}
        for name,lvl in STOPS.items():
            exited=False
            if lvl is not None:
                stopS = K if lvl=='K' else Se*(1-lvl)
                for i in range(1,len(Spath)):
                    if Spath[i]<=stopS:
                        Trem=max((row.exdate-dates[i]).days,0)/365.0
                        buyback=bs_put(Spath[i],K,Trem,sig)   # entry IV (optimistic; real crash IV higher)
                        rec[name]=(mid-buyback)/K; exited=True; break
            if not exited:
                rec[name]=(mid-max(K-Spath[-1],0.0))/K
        tr.append(rec)
    lg("  %d %d %.0fs"%(yr,len(tr),time.time()-t0))
df=pd.DataFrame(tr); df['ym']=df['date'].dt.to_period('M')
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
out={'n':len(df)}
for k in STOPS:
    m=df.groupby('ym')[k].mean()
    out[k]=dict(avg_bp=round(float(df[k].mean()*1e4),1), monthly_SR=sr(m), worst_mo_pct=round(float(m.min()*100),2),
                mar2020_bp=round(float(df[df.ym==pd.Period('2020-03')][k].mean()*1e4),1) if (df.ym==pd.Period('2020-03')).any() else None)
json.dump(out,open(os.path.join(P,"reactive_exit_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("REACTDONE")
