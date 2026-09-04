# conformal_width_v2.py -- conformal Stage-3 width test at the FULL host export width
# (111 names, IQN-only, mh_quantiles_gpu.csv): does the per-date split guarantee tighten
# from 47 -> 111 names as 1/(n_cal+1) predicts?  Plus lagged split + ACI at this width.
import os, json, time
import numpy as np, pandas as pd
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; RES=r"C:\GBC_data\results\pq_trade"
lg=lambda s:print(s,flush=True); t0=time.time()
rng=np.random.default_rng(0)
d=pd.read_csv(os.path.join(RES,"mh_quantiles_gpu.csv"),usecols=["tk","date","h","p01","p05","y"])
d["date"]=pd.to_datetime(d["date"]); d=d[d.h==21]
lg(f"rows={len(d):,} names={d.tk.nunique()}")
def prep(qcol):
    dd=d.dropna(subset=[qcol,"y"]).sort_values("date")
    dates=np.array(sorted(dd.date.unique()))
    groups={t:(dd.loc[dd.date==t,qcol].values,dd.loc[dd.date==t,"y"].values) for t in dates}
    return dates,groups
def same_date_split(dates,groups,alpha,n_rep=3,min_n=20):
    b=[];ns=[]
    for t in dates:
        q,y=groups[t];n=len(q)
        if n<min_n:continue
        ns.append(n);s=q-y
        for _ in range(n_rep):
            idx=rng.permutation(n);half=n//2
            c=np.quantile(s[idx[:half]],min((1-alpha)*(1+1/half),1.0))
            b.append((y[idx[half:]]<q[idx[half:]]-c).mean())
    return (float(np.mean(b)) if b else None),(float(np.median(ns)) if ns else None)
def lagged(dates,groups,alpha,K,lag):
    br,ba=[],[]
    for i in range(len(dates)):
        j=i-lag
        if j-K<0:continue
        s=np.concatenate([groups[dates[k]][0]-groups[dates[k]][1] for k in range(j-K,j)])
        c=np.quantile(s,min((1-alpha)*(1+1/len(s)),1.0))
        q,y=groups[dates[i]]
        br.append((y<q).mean());ba.append((y<q-c).mean())
    return float(np.mean(br)),float(np.mean(ba))
def aci(dates,groups,alpha,K,lag,gamma=0.005):
    a=alpha;b=[];hist={}
    for i in range(len(dates)):
        j=i-lag
        if j-K<0:continue
        s=np.concatenate([groups[dates[k]][0]-groups[dates[k]][1] for k in range(j-K,j)])
        ae=float(np.clip(a,0.001,0.2))
        c=np.quantile(s,min((1-ae)*(1+1/len(s)),1.0))
        q,y=groups[dates[i]]
        r=(y<q-c).mean();b.append(r);hist[i]=r
        if hist.get(j) is not None:a=a+gamma*(alpha-hist[j])
    return float(np.mean(b))
OUT={}
for qcol,alpha in [("p05",0.05),("p01",0.01)]:
    dates,groups=prep(qcol)
    sd,medn=same_date_split(dates,groups,alpha)
    raw,k250=lagged(dates,groups,alpha,250,26)
    _,k60=lagged(dates,groups,alpha,60,26)
    a60=aci(dates,groups,alpha,60,26)
    OUT[f"{qcol}_a{alpha}"]=dict(median_xsec_n=medn,same_date_split=sd,raw=raw,
                                 lagged_K60=k60,lagged_K250=k250,ACI_K60=a60,
                                 slack_bound=round(alpha+1/((medn//2)+1),4) if medn else None)
    lg(f"{qcol}@{alpha}: n/date~{medn} raw {raw:.4f} same-date {sd:.4f} K60 {k60:.4f} K250 {k250:.4f} ACI {a60:.4f}")
json.dump(OUT,open(os.path.join(P,"conformal_width111_results.json"),"w"),indent=2)
lg("CONFWIDTHDONE %.0fs"%(time.time()-t0))
