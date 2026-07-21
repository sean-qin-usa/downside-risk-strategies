# Rigorous net P&L for the tau.10 short-put book: sell at real BID, settle at REAL PX_LAST.
# Runs monthly (20-40 DTE) and weekly (5-15 DTE) to answer: does weekly's richer raw
# premium survive its wider spread?  Universe = top-liquid names (fixed-strategy universe).
import os, glob, json, time
import numpy as np, pandas as pd
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time()
def lg(s): print(s,flush=True)
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
# liquid universe = top 18 by 2023 open interest
d23=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','open_interest'])
uni=[int(s) for s in d23.groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
lg("universe: "+",".join(sym.get(s,str(s)) for s in uni))
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if not os.path.exists(f): lg("no px "+str(sym.get(s))); continue
    t=pd.read_csv(f, usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
lg("px loaded %d/%d"%(len(px),len(uni)))
def spot(s,dt):
    ser=px.get(s)
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
def read_filt(f, cols):
    parts=[]
    for ch in pd.read_csv(f, usecols=cols, chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    return pd.concat(parts) if parts else pd.DataFrame(columns=cols)
def run_band(pat, lo, hi, cyc):
    tr=[]
    for f in sorted(glob.glob(os.path.join(W,pat))):
        yr=int(os.path.basename(f).split('_')[-1][:4])
        if yr<2016: continue
        d=read_filt(f, ['secid','date','exdate','strike_price','best_bid','best_offer','delta'])
        if len(d)==0: continue
        d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate'])
        d['dte']=(d['exdate']-d['date']).dt.days
        d=d[(d.dte>=lo)&(d.dte<=hi)&(d.best_bid>0)]
        d['cyc']=d['date'].dt.to_period(cyc)
        for (s,c),g in d.groupby(['secid','cyc']):
            g=g[g.date==g.date.min()]
            if not len(g): continue
            row=g.iloc[(g.delta+0.12).abs().values.argmin()]
            K=row.strike_price/1000.0
            if K<=0: continue
            Sx=spot(s,row.exdate)
            if not np.isfinite(Sx): continue
            payoff=max(K-Sx,0.0); mid=(row.best_bid+row.best_offer)/2 if row.best_offer>0 else row.best_bid
            tr.append((s,row.date,(row.best_bid-payoff)/K,(mid-payoff)/K,float(row.delta)))
        lg("  %s %d rows->%d trades  %.0fs"%(pat[:12],yr,len(tr),time.time()-t0))
    return pd.DataFrame(tr,columns=['secid','date','net','gross','delta'])
res={}
for name,(pat,lo,hi,cyc) in {'monthly':('spreads_[12]*.csv.gz',20,40,'M'),
                             'weekly':('spreads_dte05_15_*.csv.gz',5,15,'W')}.items():
    tr=run_band(pat,lo,hi,cyc)
    mb=tr.groupby(tr['date'].dt.to_period('M'))
    mn=mb['net'].mean(); mg=mb['gross'].mean()
    sr=lambda x: round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
    res[name]=dict(n_trades=int(len(tr)),
        net_per_trade_pctK=round(float(tr.net.mean()*100),3),
        gross_per_trade_pctK=round(float(tr.gross.mean()*100),3),
        spread_cost_per_trade_pctK=round(float((tr.gross-tr.net).mean()*100),3),
        net_SR=sr(mn), gross_SR=sr(mg), net_hit=round(float((tr.net>0).mean()),2),
        net_by_year={int(y):round(float(tr[tr.date.dt.year==y].net.mean()*100),3) for y in range(2016,2026) if (tr.date.dt.year==y).any()})
    lg(name+" => "+json.dumps(res[name]))
res['runtime_sec']=round(time.time()-t0,1); res['universe']=[sym.get(s) for s in uni]
json.dump(res, open(os.path.join(P,"bt_real_results.json"),"w"), indent=2)
lg("ALL DONE "+str(res.get('runtime_sec')))
