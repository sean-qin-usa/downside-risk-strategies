
import os
import numpy as np, pandas as pd
RES=r"C:\GBC_data\results\pq_trade"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))
path=os.path.join(RES,"mh_quantiles_gpu_v2.csv")
d=pd.read_csv(path); d.columns=[c.strip() for c in d.columns]
d["year"]=pd.to_datetime(d["date"],errors="coerce").dt.year
d=d.dropna(subset=["year"]); d["year"]=d["year"].astype(int)
if "h" in d.columns: d=d[d["h"]==21]
qcols=[c for c in d.columns if c.startswith("p") and c[1:].isdigit()]
taus={c:int(c[1:])/100.0 for c in qcols}
L("h=21 rows",len(d),"quantile cols",qcols)
rows=[]
for lab,yrs in {"TRAIN 2016-2024":range(2016,2025),"OOS 2025-2026":range(2025,2027)}.items():
    sub=d[d["year"].isin(list(yrs))]; y=pd.to_numeric(sub["y"],errors="coerce")
    L(f"=== {lab}  n={len(sub)} ===")
    for c in qcols:
        cov=float((y<=pd.to_numeric(sub[c],errors="coerce")).mean())
        L(f"   tau {taus[c]:.2f} nominal -> coverage {cov:.3f}  (miss {cov-taus[c]:+.3f})")
        rows.append((lab,taus[c],round(cov,3)))
# tail digital: sell downside at p10; breach = y below the strike
for lab,yrs in {"2016-2024":range(2016,2025),"2025-2026":range(2025,2027)}.items():
    sub=d[d["year"].isin(list(yrs))]; y=pd.to_numeric(sub["y"],errors="coerce")
    if "p10" in sub: L(f"digital sell@p10: {lab} realized breach {float((y<pd.to_numeric(sub['p10'],errors='coerce')).mean()):.3f} (nominal 0.10)")
pd.DataFrame(rows,columns=["era","tau","coverage"]).to_csv(os.path.join(OUT,"oos_calibration.csv"),index=False)
open(os.path.join(OUT,"q3_oos_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("Q3OOSDONE")
