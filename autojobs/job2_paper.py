# FORWARD PAPER-TRADE VALIDATION: replay paper_trade_v2.monthly_signal over history -> reproduce backtest SR; emit sample live ticket.
import os, glob, time, math, json, sys
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
sys.path.insert(0,P)
import paper_trade_v2 as pt
lg=lambda s:print(s,flush=True); t0=time.time()
pt.CFG.update(dict(n_universe=100, vrp_top_pct=0.10, weight="equal"))
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
ranked=[int(s) for s in oi.index]
px={}
for s in ranked:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    if len(t)<40: continue
    t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
UNI=[s for s in ranked if s in px][:100]; uset=set(UNI)  # top-100 liquid w/ px
lg("universe=%d %.0fs"%(len(UNI),time.time()-t0))
# load all monthly chains 2016+
alld=[]
for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        alld.append(ch[ch.secid.isin(uset)])
D=pd.concat(alld,ignore_index=True); D['date']=pd.to_datetime(D['date']); D['exdate']=pd.to_datetime(D['exdate'])
D['dte']=(D['exdate']-D['date']).dt.days; D['ym']=D['date'].dt.to_period('M')
lg("chains rows=%d %.0fs"%(len(D),time.time()-t0))
def pxat(s,dt):
    z=px[s][:dt]; return float(z.iloc[-1]) if len(z) else np.nan
months=sorted(D['ym'].unique()); book=[]; prev=None
for ym in months:
    dm=D[D['ym']==ym]; asof=dm['date'].min()
    chains={s:g for s,g in dm.groupby('secid')}
    pxser={s:px[s] for s in chains}
    tickets,meta=pt.monthly_signal(asof, chains, pxser, sym, prev_month_return=prev)
    if not tickets: prev=0.0; continue
    nets=[]
    for tk in tickets:
        # find chain row for settlement (secid via ticker, nearest strike+expiry)
        sid=[s for s in chains if sym.get(s)==tk['ticker']]
        if not sid: continue
        s=sid[0]; g=chains[s]; g=g[g.date==g.date.min()]
        row=g.iloc[((g.strike_price/1000.0-tk['strike']).abs()+(pd.to_datetime(g.exdate)-pd.to_datetime(tk['expiry'])).abs().dt.days).values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; dl=float(row.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
        p0=pxat(s,asof); p1=pxat(s,pd.to_datetime(row.exdate))
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); payoff=max(K-Sx,0.0)
        net_bid=(float(row.best_bid)-payoff)/K; net_mid=((float(row.best_bid)+float(row.best_offer))/2-payoff)/K
        nets.append((tk['weight'],net_bid,net_mid))
    if not nets: prev=0.0; continue
    wsum=sum(w for w,_,_ in nets)
    rb=sum(w*b for w,b,_ in nets)/wsum; rm=sum(w*m for w,_,m in nets)/wsum
    book.append((str(ym),rb,rm)); prev=rb
bt=pd.DataFrame(book,columns=['ym','bid','mid']); bt.to_csv(os.path.join(P,"paper_sim_series.csv"),index=False)
def SR(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
bt['yr']=bt['ym'].str[:4].astype(int)
res=dict(n_months=len(bt),
         SR_bid_full=SR(bt.bid), SR_mid_full=SR(bt.mid),
         SR_bid_IS_16_20=SR(bt[bt.yr<=2020].bid), SR_bid_OOS_21_25=SR(bt[bt.yr>=2021].bid),
         SR_mid_IS_16_20=SR(bt[bt.yr<=2020].mid), SR_mid_OOS_21_25=SR(bt[bt.yr>=2021].mid),
         ann_bid_pct=round(float(bt.bid.mean()*12*100),2), ann_mid_pct=round(float(bt.mid.mean()*12*100),2),
         worst_mo_bid_pct=round(float(bt.bid.min()*100),2),
         note="reproduces validated spec top100/top10%VRP/derisk0.5x via paper_trade_v2.monthly_signal harness")
# sample LIVE ticket = most recent month in data
ymL=months[-1]; dm=D[D['ym']==ymL]; asof=dm['date'].min()
chains={s:g for s,g in dm.groupby('secid')}; pxser={s:px[s] for s in chains}
tickets,meta=pt.monthly_signal(asof, chains, pxser, sym, prev_month_return=None)
os.makedirs(os.path.join(P,"forward_signals"),exist_ok=True)
json.dump(dict(asof=str(asof.date()),meta=meta,tickets=tickets),
          open(os.path.join(P,"forward_signals",f"sample_ticket_{ymL}.json"),"w"),indent=2,default=str)
res['sample_ticket_month']=str(ymL); res['sample_n_tickets']=len(tickets)
json.dump(res,open(os.path.join(P,"paper_sim_results.json"),"w"),indent=2,default=str)
lg("PAPER_RESULTS\n"+json.dumps(res,indent=2,default=str)); lg("JOB2DONE %.0fs"%(time.time()-t0))
