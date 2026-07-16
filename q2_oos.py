
import os
import numpy as np, pandas as pd
RES=r"C:\Users\OWNER\Desktop\GBC_data\results\pq_trade"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a)); open(os.path.join(OUT,"q2_oos_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))

path=None
for f in ["mh_quantiles_gpu_v2.csv","mh_quantiles_gpu.csv"]:
    if os.path.exists(os.path.join(RES,f)): path=os.path.join(RES,f); break
if path is None: L("no mh_quantiles file"); print("noqfile"); raise SystemExit
d=pd.read_csv(path)
d.columns=[c.strip() for c in d.columns]
L("file",os.path.basename(path),"shape",d.shape,"cols",list(d.columns))
# detect
datec=[c for c in d.columns if c.lower() in ("date","dt")];
yc=[c for c in d.columns if c.lower() in ("y","realized","ret","target")]
hc=[c for c in d.columns if c.lower()=="h"]
qcols=[c for c in d.columns if c.lower().startswith(("q","qq")) and c.lower() not in ("qq","q")]
L("date",datec,"y",yc,"h",hc,"nq",len(qcols),"qcols",qcols[:12])
if not (datec and yc): L("cannot map columns; stopping after dump"); print("dumped"); raise SystemExit
d["year"]=pd.to_datetime(d[datec[0]],errors="coerce").dt.year
d=d.dropna(subset=["year"]); d["year"]=d["year"].astype(int)
if hc:
    hv=sorted(d[hc[0]].unique()); L("horizons",hv)
    d=d[d[hc[0]]==(21 if 21 in hv else hv[0])]; L("using horizon",21 if 21 in hv else hv[0])
y=pd.to_numeric(d[yc[0]],errors="coerce")
# infer nominal tau grid from #quantiles
nq=len(qcols)
grids={5:[.05,.25,.5,.75,.95],9:[.01,.05,.1,.25,.5,.75,.9,.95,.99],4:[.05,.25,.5,.75],3:[.1,.5,.9]}
taus=grids.get(nq,[ (i+1)/(nq+1) for i in range(nq)])
L("assumed tau grid",taus)
# coverage by era
for lab,yrs in {"TRAIN-ERA 2016-2024":range(2016,2025),"OOS 2025-2026":range(2025,2027)}.items():
    sub=d[d["year"].isin(list(yrs))]; ys=pd.to_numeric(sub[yc[0]],errors="coerce")
    L(f"--- {lab}  n={len(sub)} ---")
    for c,t in zip(qcols,taus):
        cov=(ys<=pd.to_numeric(sub[c],errors="coerce")).mean()
        L(f"   tau={t:.2f} nominal -> coverage {cov:.3f}")
# simple digital short: sell downside at the ~0.10 quantile; 'hit' if y above it
if nq>=2:
    qlow=qcols[1] if nq>=9 else qcols[0]
    for lab,yrs in {"2016-2024":range(2016,2025),"2025-2026":range(2025,2027)}.items():
        sub=d[d["year"].isin(list(yrs))]; ys=pd.to_numeric(sub[yc[0]],errors="coerce"); q=pd.to_numeric(sub[qlow],errors="coerce")
        breach=(ys<q).mean()
        L(f"digital sell @ {qlow}: {lab} breach-rate {breach:.3f} (n={len(sub)})")
print("Q2OOSDONE")
