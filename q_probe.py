
import os, glob
import pandas as pd
RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))

for t in ["AAPL","TSLA","NVDA"]:
    for pre in ["tiv2_","tiv_","biv_"]:
        p=os.path.join(RAW,pre+t+".csv")
        if os.path.exists(p):
            try:
                d=pd.read_csv(p,nrows=4)
                L(pre+t,"cols",list(d.columns),"| sample row:", d.iloc[0].to_dict())
            except Exception as e: L(pre+t,"err",repr(e)[:60])
            break
for t in ["AAPL","TSLA"]:
    p=os.path.join(RAW,"tpx_"+t+".csv")
    if os.path.exists(p):
        try:
            d=pd.read_csv(p,nrows=4); L("tpx_"+t,"cols",list(d.columns))
        except Exception as e: L("tpx err",repr(e)[:60])
L("tiv2 name count", len(glob.glob(os.path.join(RAW,"tiv2_*.csv"))))
L("tpx name count", len(glob.glob(os.path.join(RAW,"tpx_*.csv"))))
open(os.path.join(OUT,"q_probe_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("PROBEDONE")
