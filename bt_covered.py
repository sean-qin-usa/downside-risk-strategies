# NAKED short put vs COVERED (put spread: sell d-0.12, buy d-0.05 underneath). Real bid/ask, real settle.
import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time(); lg=lambda s:print(s,flush=True); COMM=0.70
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
nak=[]; cov=[]
for f in sorted(glob.glob(os.path.join(W,"spreads_[12]*.csv.gz"))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    d=pd.concat(parts); d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.impl_volatility>0)&(d.delta<0)]
    d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        gs=g[g.best_bid>0]
        if not len(gs): continue
        rs=gs.iloc[(gs.delta+0.12).abs().values.argmin()]     # SELL leg d-0.12
        Ks=rs.strike_price/1000.0; sig=float(rs.impl_volatility); T=rs.dte/365.0; dl=float(rs.delta)
        if Ks<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        Se=Ks*math.exp(-ppf(-dl)*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,rs.date); p1=pxat(s,rs.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0)
        commK=(COMM/100.0)/Ks
        nak.append((rs.date,(rs.best_bid-max(Ks-Sx,0.0))/Ks - commK))
        # BUY leg: same exdate, lower strike, delta near -0.05, tradeable ask
        cb=g[(g.exdate==rs.exdate)&(g.strike_price<rs.strike_price)&(g.best_offer>0)]
        if not len(cb): continue
        rb=cb.iloc[(cb.delta+0.05).abs().values.argmin()]
        Kb=rb.strike_price/1000.0
        net_prem=rs.best_bid-rb.best_offer
        payoff=max(Ks-Sx,0.0)-max(Kb-Sx,0.0)
        pnl=net_prem-payoff
        cov.append((rs.date, pnl/Ks - 2*commK, (Ks-Kb), net_prem, Kb/Ks))
    lg("  %d %.0fs"%(yr,time.time()-t0))
def stats(df,col):
    m=df.groupby(df['date'].dt.to_period('M'))[col].mean()
    return dict(net_bp=round(df[col].mean()*1e4,1), SR=round(float(m.mean()/m.std()*np.sqrt(12)),2) if m.std()>0 else None,
                ann_ret_pctK=round(m.mean()*12*100,2), hit=round(float((df[col]>0).mean()),3),
                worst_pctK=round(df[col].min()*100,1), avg_loss_bp=round(df[df[col]<0][col].mean()*1e4,1) if (df[col]<0).any() else None,
                skew=round(float(df[col].skew()),2), n=len(df))
N=pd.DataFrame(nak,columns=['date','net']); C=pd.DataFrame(cov,columns=['date','net','width','prem','KbKs'])
res=dict(naked=stats(N,'net'), covered=stats(C,'net'))
res['covered_extra']=dict(avg_spread_width_pctK=round(float((C.width/ (C.width)).mean()),3) if len(C) else None,
                          mean_buyleg_strike_ratio=round(float(C.KbKs.mean()),3),
                          premium_kept_vs_naked_pct=round(float(C.prem.mean()/N.net.mean()*100),1) if N.net.mean() else None)
# return on DEFINED-RISK capital for covered (normalize by max loss = width - prem)
C['maxloss']=(C.width-C.prem).clip(lower=0.001); C['ret_on_risk']=(C.net*0+ (C.prem - (C.width - C.prem)*0))  # placeholder
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"bt_covered_results.json"),"w"), indent=2, default=str)
lg("ALL DONE"); lg(json.dumps(res['naked'])); lg(json.dumps(res['covered']))
