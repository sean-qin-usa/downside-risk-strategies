# Delta-hedged short put vs unhedged. Daily rebalance on split-consistent price path. Isolates vol premium; cuts directional crash risk.
import os, glob, time, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
Ncdf=NormalDist().cdf; ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
HEDGE_COST_BP=1.0  # per-share rebalance cost as bp of |dDelta|*S (round-trip-ish)
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
uni=[int(s) for s in pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def path(s,d0,d1):
    ser=px.get(s)
    if ser is None: return None
    p=ser[(ser.index>=d0)&(ser.index<=d1)]
    return p if len(p)>=2 else None
def put_delta(S,K,T,sig):
    if T<=1e-6 or sig<=0: return -1.0 if S<K else 0.0
    d1=(math.log(S/K)+0.5*sig*sig*T)/(sig*math.sqrt(T)); return Ncdf(d1)-1.0
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
        row=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); dl=float(row.delta)
        if K<=0 or sig<=0 or -dl<=0 or -dl>=1: continue
        T0=row.dte/365.0; d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T0)-0.5*sig*sig*T0)
        pp=path(s,row.date,row.exdate)
        if pp is None: continue
        p_entry=float(pp.iloc[0]); Spath=Se*(pp.values/p_entry); dates=pp.index
        mid=(float(row.best_bid)+float(row.best_offer))/2
        payoff=max(K-Spath[-1],0.0)
        # delta-hedge daily: hold Δp_t shares (negative). hedge pnl=Σ Δp_t*(S_{t+1}-S_t). cost on |dΔ|.
        hp=0.0; cost=0.0; prevdelta=0.0
        for i in range(len(Spath)-1):
            Ti=max((row.exdate-dates[i]).days,0)/365.0
            dp=put_delta(Spath[i],K,Ti,sig)
            hp+=dp*(Spath[i+1]-Spath[i])
            cost+=abs(dp-prevdelta)*Spath[i]*HEDGE_COST_BP/1e4; prevdelta=dp
        cost+=abs(prevdelta)*Spath[-1]*HEDGE_COST_BP/1e4  # unwind
        unhedged=(mid-payoff)/K
        hedged=(mid-payoff+hp-cost)/K
        tr.append((row.date,unhedged,hedged))
    lg("  %d %.0fs"%(yr,time.time()-t0))
df=pd.DataFrame(tr,columns=['date','unhedged','hedged']); df['ym']=df['date'].dt.to_period('M')
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
out={'n':len(df)}
for k in ['unhedged','hedged']:
    m=df.groupby('ym')[k].mean()
    out[k]=dict(avg_bp=round(float(df[k].mean()*1e4),1), monthly_SR=sr(m), worst_mo_pct=round(float(m.min()*100),2),
                worst_trade_pctK=round(float(df[k].min()*100),1),
                mar2020_bp=round(float(df[df.ym==pd.Period('2020-03')][k].mean()*1e4),1) if (df.ym==pd.Period('2020-03')).any() else None)
json.dump(out,open(os.path.join(P,"delta_hedge_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("DHEDGEDONE")
