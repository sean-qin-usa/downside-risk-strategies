# job_costs_phi.py -- measured-spread phi-curve on the FLAGSHIP book (all cohorts),
# extending the young-cohort-only measured-cost exhibit (bfig_measured_costs) to the
# full traded book.  phi = fraction of the quoted bid-ask spread actually paid
# (phi=0 mid fill, phi=1 full bid fill).
#
# Reuses paper_trade.py's validated sim VERBATIM: run once at fill='mid' and once at
# fill='bid'; merge blotters on (month,ticker,expiry,strike); interpolate
# credit(phi) = (1-phi)*credit_mid + phi*credit_bid; payoff identical across fills.
# Outputs Sharpe(phi), ann. return(phi), hit rate(phi) on the full book + per-year table.
import os, sys, json, time
import numpy as np, pandas as pd
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
sys.path.insert(0,P)
lg=lambda s:print(s,flush=True); t0=time.time()
import paper_trade as pt

OUT={"note":"phi-curve on full flagship book via paper_trade.sim mid+bid blotters"}
OUTJ=os.path.join(P,"costs_phi_results.json")

bl_mid=pt.sim("mid"); bl_mid=bl_mid.rename(columns={"credit":"credit_mid","pnl_pctK":"pnl_mid"})
bl_bid=pt.sim("bid"); bl_bid=bl_bid.rename(columns={"credit":"credit_bid","pnl_pctK":"pnl_bid"})
m=bl_mid.merge(bl_bid[["month","ticker","expiry","strike","credit_bid"]],
               on=["month","ticker","expiry","strike"],how="inner")
lg(f"merged tickets: {len(m)} (mid {len(bl_mid)}, bid {len(bl_bid)}) {time.time()-t0:.0f}s")
OUT["n_tickets"]=int(len(m))
m["payoff"]=m["credit_mid"]-m["pnl_mid"]/1e4*m["strike"]  # invert pnl definition to recover settle
# verify payoff recovery against settle_intrinsic column if present
if "settle_intrinsic" in m:
    err=float((m["payoff"]-m["settle_intrinsic"]).abs().median())
    OUT["payoff_recovery_median_err"]=err; lg(f"payoff recovery median err {err:.5f} (should be ~0)")
    m["payoff"]=m["settle_intrinsic"]
rows=[]
for phi in [0.0,0.25,0.5,0.75,1.0]:
    cr=(1-phi)*m["credit_mid"]+phi*m["credit_bid"]
    pnl=(cr-m["payoff"])/m["strike"]
    bym=pd.DataFrame({"p":pnl.values,"month":m["month"].values}).groupby("month").p.mean()
    sr=float(bym.mean()/bym.std()*np.sqrt(12)) if bym.std()>0 else None
    rows.append(dict(phi=phi,SR=round(sr,3) if sr else None,
                     ann_pct=round(float(bym.mean()*12*100),2),
                     hit=round(float((pnl>0).mean()),3),
                     worst_mo_pct=round(float(bym.min()*100),2)))
    lg(f"phi={phi}: SR {rows[-1]['SR']} ann {rows[-1]['ann_pct']}% hit {rows[-1]['hit']}")
OUT["phi_curve"]=rows
# quoted spread as % of premium, full book distribution (the measured quantity)
sp=(m["credit_mid"]-m["credit_bid"])*2/m["credit_mid"].clip(lower=1e-9)
OUT["spread_pct_of_premium"]={"median":round(float(sp.median()),3),
                              "p25":round(float(sp.quantile(.25)),3),
                              "p75":round(float(sp.quantile(.75)),3)}
json.dump(OUT,open(OUTJ,"w"),indent=2,default=str)
lg("COSTSPHIDONE %.0fs"%(time.time()-t0))
