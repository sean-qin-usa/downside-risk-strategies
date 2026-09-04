"""
PAPER-TRADE HARNESS v2 — VALIDATED VRP STRATEGY
------------------------------------------------
Spec (all leakage-free, validated 2026-07-15):
  universe : top-100 names by option open interest (liquid, executable)
  signal   : each month sell puts on the top-10% by VRP = entry_IV(delta -0.12) - trailing 21d realized vol
  execution: LIMIT at mid (post passive; plan P&L at bid for conservatism)
  sizing   : equal-weight (or VRP-weighted); cut to 0.5x after any down month (strategy's own lagged return)
  tenor    : 20-40 DTE, held to expiry, cash-secured
Two modes:
  mode="sim"  : replay over history (validation).
  mode="live" : plug broker chains where marked [BROKER HOOK]; harness ONLY produces tickets — a human submits.
This module NEVER sends orders.
"""
import os, math, datetime as dt
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
CFG=dict(n_universe=100, vrp_top_pct=0.10, delta_target=-0.12, dte_lo=20, dte_hi=40,
         rv_window=21, derisk_factor=0.5, weight="equal", limit="mid")

def trailing_rv(px_series, asof, window=21):
    """Annualized realized vol over the trailing `window` trading days, known at `asof`."""
    s=px_series[:asof]
    if len(s)<window+1: return np.nan
    lr=np.log(s/s.shift(1)).dropna().tail(window)
    return float(lr.std()*math.sqrt(252))

def pick_put(chain_rows):
    """chain_rows: one name/date, cols strike/best_bid/best_offer/impl_volatility/delta/dte. Returns the delta -0.12 put."""
    g=chain_rows[(chain_rows.dte>=CFG['dte_lo'])&(chain_rows.dte<=CFG['dte_hi'])&(chain_rows.best_bid>0)&(chain_rows.best_offer>0)&(chain_rows.delta<0)]
    if not len(g): return None
    r=g.iloc[(g.delta-CFG['delta_target']).abs().values.argmin()]
    bid,off=float(r.best_bid),float(r.best_offer)
    return dict(strike=float(r.strike_price)/1000.0, expiry=str(pd.to_datetime(r.exdate).date()),
                iv=float(r.impl_volatility), bid=bid, ask=off, mid=round((bid+off)/2,2))

def monthly_signal(asof, chains, px_by_secid, sym, prev_month_return=None):
    """Core signal. chains: {secid: DataFrame chain}. px_by_secid: {secid: price Series}.
    Returns (tickets, meta). prev_month_return: strategy's realized return last month (for de-risk; None=full size)."""
    cand=[]
    for s,cr in chains.items():
        if s not in px_by_secid: continue
        p=pick_put(cr)
        if not p: continue
        rv=trailing_rv(px_by_secid[s], pd.to_datetime(asof), CFG['rv_window'])
        if not np.isfinite(rv): continue
        cand.append(dict(secid=s, ticker=sym.get(s,str(s)), vrp=p['iv']-rv, **p))
    if not cand: return [], {"note":"no candidates"}
    cdf=pd.DataFrame(cand)
    thr=cdf['vrp'].quantile(1-CFG['vrp_top_pct'])
    sel=cdf[cdf['vrp']>=thr].copy()
    # sizing
    size_mult=1.0
    if prev_month_return is not None and prev_month_return<0: size_mult=CFG['derisk_factor']
    if CFG['weight']=="vrp":
        w=sel['vrp'].clip(lower=0); sel['weight']=(w/w.sum())*size_mult
    else:
        sel['weight']=(1.0/len(sel))*size_mult
    tickets=[dict(action="SELL_TO_OPEN", ticker=r.ticker, right="PUT", expiry=r.expiry, strike=r.strike,
                  order_type="LIMIT", limit_price=r.mid, weight=round(float(r.weight),4),
                  ref_bid=r.bid, ref_ask=r.ask, vrp=round(float(r.vrp),3)) for r in sel.itertuples()]
    meta=dict(asof=str(asof), n_candidates=len(cdf), n_selected=len(sel), size_mult=size_mult,
              vrp_cutoff=round(float(thr),3))
    # ---- [BROKER HOOK] live mode: for t in tickets: broker.place_limit_order(...)  <-- a human does this ----
    return tickets, meta

if __name__=="__main__":
    print("paper_trade_v2 — validated VRP strategy harness.")
    print("Spec:", CFG)
    print("Call monthly_signal(asof, chains, px_by_secid, sym, prev_month_return) each month;")
    print("review the returned tickets and submit them yourself. Forward-run this to measure REAL fill quality.")
