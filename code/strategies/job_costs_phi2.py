# job_costs_phi2.py -- v2 of the phi-curve job. paper_trade.sim() writes paper_blotter.csv
# and THEN crashes in its summary block (pre-existing bug: sorted(set(str months)|set(Periods))).
# So: call sim() under try/except, then read the blotter from disk after each fill.
import os, sys, json, time
import numpy as np, pandas as pd
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
sys.path.insert(0,P)
lg=lambda s:print(s,flush=True); t0=time.time()
import paper_trade as pt

def run_fill(fill):
    try:
        pt.sim(fill)
    except Exception as e:
        lg(f"sim({fill}) raised after writing blotter (known summary bug): {e!r}")
    bl=pd.read_csv(os.path.join(P,"paper_blotter.csv"))
    lg(f"{fill}: blotter {len(bl)} tickets {time.time()-t0:.0f}s")
    return bl

OUT={"note":"phi-curve on full flagship book via paper_trade blotters (v2: read blotter from disk)"}
OUTJ=os.path.join(P,"costs_phi_results.json")
bl_mid=run_fill("mid").rename(columns={"credit":"credit_mid","pnl_pctK":"pnl_mid"})
bl_bid=run_fill("bid").rename(columns={"credit":"credit_bid","pnl_pctK":"pnl_bid"})
m=bl_mid.merge(bl_bid[["month","ticker","expiry","strike","credit_bid"]],
               on=["month","ticker","expiry","strike"],how="inner")
OUT["n_tickets"]=int(len(m)); lg(f"merged {len(m)}")
m["payoff"]=m["settle_intrinsic"] if "settle_intrinsic" in m else m["credit_mid"]-m["pnl_mid"]/1e4*m["strike"]
rows=[]
for phi in [0.0,0.25,0.5,0.75,1.0]:
    cr=(1-phi)*m["credit_mid"]+phi*m["credit_bid"]
    pnl=(cr-m["payoff"])/m["strike"]
    bym=pd.DataFrame({"p":pnl.values,"month":m["month"].astype(str).values}).groupby("month").p.mean()
    sr=float(bym.mean()/bym.std()*np.sqrt(12)) if bym.std()>0 else None
    rows.append(dict(phi=phi,SR=round(sr,3) if sr else None,
                     ann_pct=round(float(bym.mean()*12*100),2),
                     hit=round(float((pnl>0).mean()),3),
                     worst_mo_pct=round(float(bym.min()*100),2)))
    lg(f"phi={phi}: SR {rows[-1]['SR']} ann {rows[-1]['ann_pct']}% hit {rows[-1]['hit']}")
OUT["phi_curve"]=rows
half=(m["credit_mid"]-m["credit_bid"]).clip(lower=0)
sp=(2*half/m["credit_mid"].clip(lower=1e-9))
OUT["spread_pct_of_premium"]={"median":round(float(sp.median()),3),"p25":round(float(sp.quantile(.25)),3),"p75":round(float(sp.quantile(.75)),3)}
json.dump(OUT,open(OUTJ,"w"),indent=2,default=str)
lg("COSTSPHI2DONE %.0fs"%(time.time()-t0))
