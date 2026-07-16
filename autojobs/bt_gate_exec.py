# Combine execution style (bid/mid/ask) with the VIX-standdown gate, on the single-name tau.10 book.
import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s: print(s,flush=True); t0=time.time()
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
d23=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','open_interest'])
uni=[int(s) for s in d23.groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f, usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def pxat(s,dt):
    ser=px.get(s);
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
def read_filt(f):
    parts=[]
    for ch in pd.read_csv(f, usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'], chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    return pd.concat(parts) if parts else pd.DataFrame()
tr=[]
for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    d=read_filt(f)
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
        if not (np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); payoff=max(K-Sx,0.0); bid=float(row.best_bid); off=float(row.best_offer)
        tr.append((row.date,(bid-payoff)/K,((bid+off)/2-payoff)/K,(off-payoff)/K))
    lg("  %d %.0fs"%(yr,time.time()-t0))
df=pd.DataFrame(tr,columns=['date','bid','mid','ask']); df['ym']=df['date'].dt.to_period('M')
M=df.groupby('ym')[['bid','mid','ask']].mean()   # monthly book return by execution
# VIX gate
def volser(t):
    v=pd.read_csv(os.path.join(RAW,'vol_indices.csv')); cl={c.lower():c for c in v.columns}
    tc,dc,fc,vc=cl['ticker'],cl['date'],cl.get('field'),cl['value']
    m=v[v[tc].astype(str).str.strip().isin([t,t+' Index'])]
    if fc: m=m[m[fc].astype(str).str.contains('PX_LAST',case=False,na=False)]
    m=m[[dc,vc]].dropna(); m[dc]=pd.to_datetime(m[dc]); return m.set_index(dc)[vc].astype(float).sort_index()
vix=volser('VIX'); vm=vix.resample('ME').last(); vm.index=vm.index.to_period('M'); vm=vm.reindex(M.index).ffill()
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
def rep(x): return dict(SR=sr(x), ann_bp=round(float(x.mean()*12*1e4),0), worst_pct=round(float(x.min()*100),2), inmkt=round(float((x!=0).mean()*100),0))
out={'n_months':len(M)}
for thr,lbl in [(1.0,'ALL_no_gate'),(0.80,'gate_top20pct'),(0.75,'gate_top25pct')]:
    vpct=vm.rolling(24,min_periods=6).rank(pct=True); keep=(vpct<thr) if thr<1 else pd.Series(True,index=M.index)
    row={}
    for ex in ['bid','mid','ask']:
        g=M[ex].where(keep,0.0); row[ex+'_'+ ({'bid':'CROSS','mid':'MID','ask':'ASK'}[ex])]=rep(g)
    out[lbl]=row
json.dump(out,open(os.path.join(P,"bt_gate_exec_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("GATEEXECDONE")
