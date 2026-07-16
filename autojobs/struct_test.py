# Test option STRUCTURES from the same chain: short put, strangle, risk-reversal, put-spread, straddles.
# One consistent entry spot Se per (name,date) via ATM BS-inversion; all legs settle vs Sx=Se*(px1/px0). Priced at MID.
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
def invert_spot(K,sig,T,delta):
    # d1 from delta: call delta=N(d1); put delta=N(d1)-1
    d1 = ppf(delta) if delta>0 else ppf(1.0+delta)
    return K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
def nearest(df,tgt):
    if not len(df): return None
    return df.iloc[(df.delta-tgt).abs().values.argmin()]
rows=[]
for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    d=pd.concat(parts) if parts else pd.DataFrame()
    if not len(d): continue
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta.abs()>0.001)&(d.delta.abs()<0.999)]
    d['K']=d.strike_price/1000.0; d['mid']=(d.best_bid+d.best_offer)/2
    for (s,c),g in d.groupby(['secid',d['date'].dt.to_period('M')]):
        g=g[g.date==g.date.min()]
        if len(g)<6: continue
        puts=g[g.delta<0]; calls=g[g.delta>0]
        if not len(puts) or not len(calls): continue
        # entry spot from ATM (|delta|~0.5), pooled
        atm=g.iloc[(g.delta.abs()-0.5).abs().values.argmin()]
        T=atm.dte/365.0
        Se=invert_spot(atm.K,float(atm.impl_volatility),T,float(atm.delta))
        p0=pxat(s,atm.date); p1=pxat(s,atm.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0 and Se>0): continue
        Sx=Se*(p1/p0)
        def leg(row): return dict(K=row.K, mid=float(row.mid), put=row.delta<0)
        def payoff(L): return max(L['K']-Sx,0.0) if L['put'] else max(Sx-L['K'],0.0)
        P12=nearest(puts,-0.12); P05=nearest(puts,-0.05); C12=nearest(calls,0.12)
        Patm=nearest(puts,-0.5); Catm=nearest(calls,0.5)
        if any(x is None for x in [P12,P05,C12,Patm,Catm]): continue
        p12,p05,c12,patm,catm=[leg(x) for x in [P12,P05,C12,Patm,Catm]]
        def short(L): return L['mid']-payoff(L)     # collect premium, pay payoff
        def long(L): return payoff(L)-L['mid']       # pay premium, collect payoff
        st={}
        st['short_put_d12']      = short(p12)
        st['short_strangle_d12'] = short(p12)+short(c12)
        st['risk_reversal']      = short(p12)+long(c12)          # sell put, buy call (skew)
        st['bull_put_spread']    = short(p12)+long(p05)          # sell d12 put, buy d05 put
        st['short_straddle_atm'] = short(patm)+short(catm)
        st['long_straddle_atm']  = long(patm)+long(catm)
        rec={'date':atm.date,'Se':Se}; rec.update({k:v/Se for k,v in st.items()})
        rows.append(rec)
    lg("  %d %d rows %.0fs"%(yr,len(rows),time.time()-t0))
df=pd.DataFrame(rows); df['ym']=df['date'].dt.to_period('M')
df.to_csv(os.path.join(P,"struct_trades.csv"),index=False)
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
cols=['short_put_d12','short_strangle_d12','risk_reversal','bull_put_spread','short_straddle_atm','long_straddle_atm']
out={'n':len(df)}
for k in cols:
    m=df.groupby('ym')[k].mean()
    out[k]=dict(avg_bp=round(float(df[k].mean()*1e4),1), monthly_SR=sr(m), worst_mo_pct=round(float(m.min()*100),2),
                hit=round(float((df[k]>0).mean()),3), mar2020_bp=round(float(df[df.ym==pd.Period('2020-03')][k].mean()*1e4),1) if (df.ym==pd.Period('2020-03')).any() else None)
json.dump(out,open(os.path.join(P,"struct_test_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("STRUCTDONE")
