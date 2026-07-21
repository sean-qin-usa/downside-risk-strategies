# Rebuild single-name monthly book (bid/mid/ask), save it, then test how much the VIX gate depends on specific crash months.
import os, glob, time, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
uni=[int(s) for s in pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def pxat(s,dt):
    ser=px.get(s)
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
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
    d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        row=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; dl=float(row.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
        p0=pxat(s,row.date); p1=pxat(s,row.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); payoff=max(K-Sx,0.0); bid=float(row.best_bid); off=float(row.best_offer)
        tr.append((row.date,(bid-payoff)/K,((bid+off)/2-payoff)/K,(off-payoff)/K))
    lg("  %d %.0fs"%(yr,time.time()-t0))
df=pd.DataFrame(tr,columns=['date','bid','mid','ask']); df['ym']=df['date'].dt.to_period('M')
M=df.groupby('ym')[['bid','mid','ask']].mean(); M.to_csv(os.path.join(P,"monthly_book.csv"))
v=pd.read_csv(os.path.join(RAW,'vol_indices.csv')); cl={c.lower():c for c in v.columns}
vv=v[v[cl['ticker']].astype(str).str.strip().isin(['VIX','VIX Index'])]
if cl.get('field'): vv=vv[vv[cl['field']].astype(str).str.contains('PX_LAST',case=False,na=False)]
vv=vv[[cl['date'],cl['value']]].dropna(); vv[cl['date']]=pd.to_datetime(vv[cl['date']]); vix=vv.set_index(cl['date'])[cl['value']].astype(float).sort_index()
vm=vix.resample('ME').last(); vm.index=vm.index.to_period('M'); vm=vm.reindex(M.index).ffill()
vpct=vm.rolling(24,min_periods=6).rank(pct=True); keep_gate=(vpct<0.80)
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
covid=[pd.Period('2020-02'),pd.Period('2020-03')]
crash=[pd.Period(p) for p in ['2018-02','2018-10','2018-11','2020-02','2020-03','2022-04','2025-03']]
out={}
for lbl,drop in [('full sample',[]),('ex-COVID (Feb/Mar2020)',covid),('ex-all-crash-months',crash)]:
    idx=[p for p in M.index if p not in drop]
    sub=M.loc[idx]; g=keep_gate.loc[idx]
    row={}
    for ex in ['bid','mid']:
        base=sub[ex]; gated=sub[ex].where(g,0.0)
        row[ex]=dict(baseline_SR=sr(base), gated_SR=sr(gated), uplift=round((sr(gated) or 0)-(sr(base) or 0),2))
    out[lbl]=row
json.dump(out,open(os.path.join(P,"bt_covid_gate_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("COVIDGATEDONE")
