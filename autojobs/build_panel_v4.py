import os, numpy as np, pandas as pd
PROJ=r"C:\Users\OWNER\Claude\Projects\GBC Project"
d=pd.read_csv(os.path.join(PROJ,"mh_panel_v3.csv.gz"))
NEW=['vrp','ivz','skwz','skew_chg','rv5','rv63','amihud','netcorr','earn_prox']  # non-seasonality, winsorize
for c in NEW:
    x=pd.to_numeric(d[c],errors='coerce').replace([np.inf,-np.inf],np.nan)
    lo,hi=x.quantile(0.01),x.quantile(0.99)
    d[c]=x.clip(lo,hi).fillna(x.median()).fillna(0.0)
    d[c]=(d[c]-d[c].mean())/(d[c].std()+1e-9)   # standardize -> stable
print("winsorized+standardized:", {c: [round(float(d[c].min()),2),round(float(d[c].max()),2)] for c in NEW})
d.to_csv(os.path.join(PROJ,"mh_panel_v4.csv.gz"),index=False,compression='gzip')
print("saved v4", d.shape)
