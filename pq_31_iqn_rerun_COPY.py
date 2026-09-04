"""IQN P-side rerun harness - fires as soon as mh_quantiles_gpu.csv exists.
Wires the multi-horizon IQN quantiles into: (a) per-h calibration table,
(b) tail-hedge trigger (IQN 5% tail vs market), (c) Kelly strike selector with
IQN breach probs, (d) v2 switcher with IQN wedge, (e) per-h timed digitals.
Usage: python3 pq_31_iqn_rerun.py   (expects the csv in results/pq_trade/)
"""
import numpy as np, pandas as pd, json, os
OUT="/tmp/pq"
RES="/sessions/youthful-festive-planck/mnt/GBC_data/results/pq_trade"
MH=f"{RES}/mh_quantiles_gpu.csv"
assert os.path.exists(MH), "mh_quantiles_gpu.csv not fetched yet"
mh=pd.read_csv(MH,parse_dates=["date"])
TAUS=[.01,.05,.10,.25,.50,.75,.90,.95,.99]
PC=[f"p{int(t*100):02d}" for t in TAUS]
def nw_t(x,l=3):
    x=pd.Series(x).dropna().values; n=len(x)
    if n<8: return np.nan
    d=x-x.mean(); s=d.var(ddof=0)
    for k in range(1,l+1):
        if n>k+1: s+=2*(1-k/(l+1))*np.cov(d[k:],d[:-k],ddof=0)[0,1]
    return float(x.mean()/np.sqrt(s/n))
R={"calibration":{}}
for h in sorted(mh.h.unique()):
    sub=mh[(mh.h==h)&mh.y.notna()]
    R["calibration"][f"h{h}"]={f"{t:.2f}":round(float((sub.y<sub[c]).mean()),3) for t,c in zip(TAUS,PC)}
# join IQN P-quantiles onto the multi-horizon trade panel (Q_Q from smiles)
tp=pd.read_parquet(f"{OUT}/mh_trade_panel.parquet"); tp["date"]=pd.to_datetime(tp.date)
j=tp.merge(mh,on=["tk","date","h"],how="inner",suffixes=("","_iqn"))
print("joined rows:",len(j))
res_h={}
for h in sorted(j.h.unique()):
    s=j[j.h==h].copy()
    # (b) tail trigger: IQN 5% below market 5% strike = model sees fatter tail
    trig=s.p05<s.qq0
    dput=(s.y<s.qq0).astype(float)-0.05
    tt=pd.DataFrame({"d":dput[trig].values,"date":s.date[trig].values}).groupby("date").d.mean()
    # (e) timed via IQN wedge at .25
    w=s.p25-s.qq1
    s=s.sort_values(["tk","date"])
    z=s.assign(w=w).groupby("tk",group_keys=False).w.apply(
        lambda g:(g-g.shift(1).rolling(12,min_periods=8).mean())/g.shift(1).rolling(12,min_periods=8).std())
    d25=(0.25-(s.y<s.qq1).astype(float))/0.75
    timed=pd.DataFrame({"p":(np.sign(z.clip(-2,2))*d25).values,"date":s.date.values}).dropna().groupby("date").p.mean()
    res_h[f"h{h}"]={"tail_trigger_months":int(trig.sum()),
        "tail_hedge_mean":round(float(tt.mean()),4) if len(tt)>10 else None,
        "tail_hedge_t":round(nw_t(tt),2) if len(tt)>10 else None,
        "iqn_timed_mean":round(float(timed.mean()),4),"iqn_timed_t":round(nw_t(timed),2)}
R["by_horizon"]=res_h
json.dump(R,open(f"{OUT}/iqn_rerun.json","w"),indent=1)
json.dump(R,open(f"{RES}/iqn_rerun.json","w"),indent=1)
print(json.dumps(R,indent=1)[:1800])
