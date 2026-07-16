# Execution study: sell put by CROSSING (bid) vs MAKING (mid / ask) + adverse-selection scenarios.
import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time(); lg=lambda s: print(s,flush=True)
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
    ser=px.get(s)
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
        Sx=Se*(p1/p0); payoff=max(K-Sx,0.0)
        bid=float(row.best_bid); off=float(row.best_offer); mid=(bid+off)/2
        tr.append((s,row.date,bid,off,mid,payoff,K, 1 if Sx<Se else 0))
    lg("  %d -> %d tr %.0fs"%(yr,len(tr),time.time()-t0))
df=pd.DataFrame(tr,columns=['secid','date','bid','off','mid','payoff','K','dropped'])
df['ym']=df['date'].dt.to_period('M')
def scen(price): return (price-df['payoff'])/df['K']
def sr(net):
    m=net.groupby(df['ym']).mean(); return round(float(m.mean()/m.std()*np.sqrt(12)),2) if m.std()>0 else None
def rep(net): return dict(net_bp=round(float(net.mean()*1e4),1), SR=sr(net), hit=round(float((net>0).mean()),3), worst_pctK=round(float(net.min()*100),1))
out={'n_trades':len(df), 'avg_halfspread_bp':round(float(((df.off-df.bid)/2/df.K).mean()*1e4),1)}
out['CROSS_sell_at_bid']=rep(scen(df.bid))
out['MID_fair_value']=rep(scen(df.mid))
out['MAKE_sell_at_ask_alwaysfill']=rep(scen(df.off))
# adverse selection: you post at ask but preferentially fill when the put gains (stock dropped).
# model: fill at ASK on all 'dropped' trades (buyers lifting), but only fraction q of non-dropped (you miss calm winners)
for q in [1.0,0.5,0.0]:
    rng=np.random.default_rng(7); keep=(df.dropped==1)|((df.dropped==0)&(rng.random(len(df))<q))
    sub=df[keep]; net=(sub.off-sub.payoff)/sub.K
    m=net.groupby(sub['ym']).mean()
    out[f'MAKE_adverse_fill_calmkeep{int(q*100)}']=dict(n=int(keep.sum()),net_bp=round(float(net.mean()*1e4),1),
        SR=round(float(m.mean()/m.std()*np.sqrt(12)),2) if m.std()>0 else None, worst_pctK=round(float(net.min()*100),1))
json.dump(out,open(os.path.join(P,"bt_maker_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("MAKERDONE")
