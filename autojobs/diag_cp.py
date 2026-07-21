import os, pandas as pd, numpy as np
W=r"C:\GBC_data\data\wrds"
d=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['delta'],nrows=500000)
print("delta min=%.3f max=%.3f  |  n_calls(delta>0)=%d  n_puts(delta<0)=%d"%(d.delta.min(),d.delta.max(),(d.delta>0).sum(),(d.delta<0).sum()))
cols=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),nrows=3).columns.tolist(); print("columns:",cols)
print("DIAGDONE")
