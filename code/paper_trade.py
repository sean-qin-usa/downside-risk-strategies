"""
PAPER-TRADE HARNESS  (P-vs-Q downside-put writing, tau.10 book, VIX-gated)
--------------------------------------------------------------------------
Runs the FULL live decision pipeline. Two modes:
  * mode="sim"  : replay over historical OptionMetrics chains (testable now).
  * mode="live" : plug a broker paper-account API where marked [BROKER HOOK].
                  This harness NEVER sends orders; it only PRODUCES tickets.
Signal:  first trading day of month -> if VIX not in top-20% of trailing 24m,
         sell 1 put nearest delta=-0.12 (20-40 DTE) on each universe name,
         LIMIT price = mid (bid/ask midpoint). Cash-secured. Hold to expiry.
"""
import os, glob, math, json, datetime as dt
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"

CFG=dict(delta_target=-0.12, dte_lo=20, dte_hi=40, gate_pct=0.80, gate_win=24, n_names=18, limit="mid")

def universe():
    d=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest'])
    sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
    sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
    ids=[int(s) for s in d.groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:CFG['n_names']]]
    return ids, sym

def vix_series():
    v=pd.read_csv(os.path.join(RAW,'vol_indices.csv')); cl={c.lower():c for c in v.columns}
    vv=v[v[cl['ticker']].astype(str).str.strip().isin(['VIX','VIX Index'])]
    if cl.get('field'): vv=vv[vv[cl['field']].astype(str).str.contains('PX_LAST',case=False,na=False)]
    vv=vv[[cl['date'],cl['value']]].dropna(); vv[cl['date']]=pd.to_datetime(vv[cl['date']])
    return vv.set_index(cl['date'])[cl['value']].astype(float).sort_index()

def gate_open(vix, asof):
    """True = TRADE this month; False = STAND DOWN (VIX elevated). Ex-ante only.
    Uses trailing gate_win-month rolling percentile (matches validated backtest)."""
    m=vix[:asof].resample('ME').last()
    if len(m)<6: return True, np.nan
    win=m.tail(CFG['gate_win'])                       # rolling 24m window
    pct=float(win.rank(pct=True).iloc[-1]); return (pct < CFG['gate_pct']), round(pct,3)

def pick_put(chain_rows):
    """chain_rows: DataFrame for one name on one date (strike_price/1000, best_bid, best_offer, impl_volatility, delta, dte)."""
    g=chain_rows[(chain_rows.dte>=CFG['dte_lo'])&(chain_rows.dte<=CFG['dte_hi'])&(chain_rows.best_bid>0)&(chain_rows.best_offer>0)&(chain_rows.delta<0)]
    if not len(g): return None
    r=g.iloc[(g.delta-CFG['delta_target']).abs().values.argmin()]
    bid,off=float(r.best_bid),float(r.best_offer); limit={'mid':(bid+off)/2,'bid':bid,'ask':off}[CFG['limit']]
    return dict(strike=float(r.strike_price)/1000.0, expiry=str(pd.to_datetime(r.exdate).date()), iv=float(r.impl_volatility),
                delta=float(r.delta), bid=bid, ask=off, limit_price=round(limit,2))

def make_tickets(asof, chains, sym, ids):
    """Return list of SELL-TO-OPEN put tickets for this month (the thing a human submits)."""
    tk=[]
    for s in ids:
        cr=chains.get(s)
        if cr is None or not len(cr): continue
        p=pick_put(cr)
        if p: tk.append(dict(action="SELL_TO_OPEN", ticker=sym.get(s,str(s)), right="PUT",
                             expiry=p['expiry'], strike=p['strike'], qty=1, order_type="LIMIT",
                             limit_price=p['limit_price'], ref_bid=p['bid'], ref_ask=p['ask'], iv=round(p['iv'],3), delta=round(p['delta'],3)))
    return tk
# ---- [BROKER HOOK] live mode would: fetch chains from broker, then for each ticket call broker.place_limit_order(...) ----
# ---- This module deliberately stops at ticket generation; a human reviews & submits.                                   ----

def sim(fill="mid"):
    ids,sym=universe(); vix=vix_series()
    px={}
    for s in ids:
        f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
        if os.path.exists(f):
            t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
    def pxat(s,d):
        ser=px.get(s);
        if ser is None: return np.nan
        z=ser[:d]; return float(z.iloc[-1]) if len(z) else np.nan
    blotter=[]; skipped=[]
    for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
        yr=int(os.path.basename(f).split('_')[-1][:4])
        if yr<2016: continue
        parts=[]
        for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
            parts.append(ch[ch.secid.isin(ids)])
        d=pd.concat(parts) if parts else pd.DataFrame()
        if not len(d): continue
        d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
        for cyc,dm in d.groupby(d['date'].dt.to_period('M')):
            asof=dm['date'].min(); openq,pct=gate_open(vix,asof)
            if not openq: skipped.append(str(cyc)); continue
            chains={s:g[g.date==g.date.min()] for s,g in dm.groupby('secid')}
            for s in ids:
                cr=chains.get(s)
                if cr is None or not len(cr): continue
                p=pick_put(cr)
                if not p: continue
                K=p['strike']; sig=p['iv']; T=(pd.to_datetime(p['expiry'])-asof).days/365.0; dl=p['delta']
                if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
                d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
                p0=pxat(s,asof); p1=pxat(s,pd.to_datetime(p['expiry']))
                if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
                Sx=Se*(p1/p0); payoff=max(K-Sx,0.0)
                credit={'mid':(p['bid']+p['ask'])/2,'bid':p['bid'],'ask':p['ask']}[fill]
                blotter.append(dict(month=str(cyc),ticker=sym.get(s),expiry=p['expiry'],strike=K,credit=round(credit,3),
                                    settle_intrinsic=round(payoff,3), pnl_pctK=round((credit-payoff)/K*1e4,1)))
    bl=pd.DataFrame(blotter)
    bl.to_csv(os.path.join(P,"paper_blotter.csv"),index=False)
    traded=bl.groupby('month')['pnl_pctK'].mean()/1e4
    skip_periods=[pd.Period(x,freq='M') for x in set(skipped)]
    allmix=sorted(set(traded.index)|set(skip_periods))
    port=pd.Series(0.0,index=pd.PeriodIndex(allmix,freq='M'))
    port.loc[traded.index]=traded.values
    def sr(x):
        return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
    summ={"fill":fill,"months_traded":int(bl.month.nunique()),"months_skipped":len(set(skipped)),
          "n_tickets":int(len(bl)),"avg_pnl_bp":round(float(bl.pnl_pctK.mean()),1),
          "portfolio_SR":sr(port),"conditional_SR_tradedonly":sr(traded),
          "win_rate":round(float((bl.pnl_pctK>0).mean()),3),
          "worst_month_pct":round(float(port.min()*100),2)}
    json.dump(summ,open(os.path.join(P,"paper_trade_summary.json"),"w"),indent=2)
    print(json.dumps(summ,indent=2))
    return bl

if __name__=="__main__":
    for fl in ["mid","bid"]:
        print("=== SIM fill@%s ==="%fl); sim(fl)
    print("HARNESSDONE")
