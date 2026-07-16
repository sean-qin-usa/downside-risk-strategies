# tau.10 monthly book: per-year & per-month Sharpe/return/tradecount + adverse-selection tests.
import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time(); lg=lambda s:print(s,flush=True)
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
d23=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','open_interest'])
uni=[int(s) for s in d23.groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
        t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def pxat(s,dt):
    ser=px.get(s);
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
tr=[]
for f in sorted(glob.glob(os.path.join(W,"spreads_[12]*.csv.gz"))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    d=pd.concat(parts)
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.impl_volatility>0)&(d.delta<0)]
    d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        row=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; dl=float(row.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        Se=K*math.exp(-ppf(-dl)*sig*math.sqrt(T)-0.5*sig*sig*T)
        p0=pxat(s,row.date); p1=pxat(s,row.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); payoff=max(K-Sx,0.0)
        tr.append((s,row.date,(row.best_bid-payoff)/K, row.best_bid/K, sig, dl))
    lg("  %d -> %d tr %.0fs"%(yr,len(tr),time.time()-t0))
T=pd.DataFrame(tr,columns=['secid','date','net','richness','iv','delta'])
T['ym']=T['date'].dt.to_period('M'); T['yr']=T['date'].dt.year; T['mo']=T['date'].dt.month
# monthly portfolio return series (equal-weight across names)
mon=T.groupby('ym').agg(net=('net','mean'), n=('net','size'))
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
res={}
res['overall']=dict(net_bp_per_trade=round(T.net.mean()*1e4,1), ann_SR=sr(mon.net),
                    ann_ret_pctK=round(mon.net.mean()*12*100,2), n_trades=int(len(T)), n_months=int(len(mon)))
# per year
py={}
for y,g in mon.groupby(mon.index.year):
    tg=T[T.yr==y]
    py[int(y)]=dict(ann_SR=sr(g.net), net_ret_pctK=round(g.net.sum()*100,2), mean_bp_trade=round(tg.net.mean()*1e4,1),
                    n_trades=int(len(tg)), n_months=int(len(g)))
res['by_year']=py
# monthly series (last 30 months for readability) + full saved to csv
mon2=mon.copy(); mon2['net_pctK']=(mon2.net*100).round(3)
mon2[['net_pctK','n']].to_csv(os.path.join(P,"tau10_monthly_series.csv"))
res['monthly_series_tail']= {str(k): dict(net_pctK=round(float(v.net*100),3), n=int(v.n)) for k,v in mon.tail(18).iterrows()}
# calendar-month seasonality
res['calendar_month_mean_bp']={int(m):round(float(T[T.mo==m].net.mean()*1e4),1) for m in range(1,13)}
# ADVERSE SELECTION: terciles by premium richness (bid/K) and by IV
def terciles(col):
    q=T[col].quantile([1/3,2/3]).values; out={}
    for lab,mask in [('low',T[col]<=q[0]),('mid',(T[col]>q[0])&(T[col]<=q[1])),('high',T[col]>q[1])]:
        sub=T[mask]; out[lab]=dict(mean_net_bp=round(sub.net.mean()*1e4,1), hit=round(float((sub.net>0).mean()),3), n=int(len(sub)))
    return out
res['advsel_by_richness']=terciles('richness')   # premium as %strike
res['advsel_by_iv']=terciles('iv')
# winner's curse: each month sell ONLY the single richest-premium name vs the median-premium name
wc_rich=[]; wc_med=[]
for ym,g in T.groupby('ym'):
    g=g.sort_values('richness')
    wc_rich.append(g.iloc[-1].net); wc_med.append(g.iloc[len(g)//2].net)
res['winners_curse']=dict(sell_richest_name_mean_bp=round(np.mean(wc_rich)*1e4,1),
                          sell_median_name_mean_bp=round(np.mean(wc_med)*1e4,1),
                          richest_hit=round(float((np.array(wc_rich)>0).mean()),3),
                          median_hit=round(float((np.array(wc_med)>0).mean()),3), n_months=len(wc_rich))
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"tau10_advsel_results.json"),"w"), indent=2)
lg("ALL DONE"); lg(json.dumps(res['advsel_by_richness'])); lg(json.dumps(res['winners_curse']))
