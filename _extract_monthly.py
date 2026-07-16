
# Host-side extractor: pull month-by-month master-book returns + S&P total return
# from Desktop GBC_data and write tidy CSVs into the project folder.
import os, json, glob, sys
import numpy as np, pandas as pd

RES = r"C:\Users\OWNER\Desktop\GBC_data\results\pq_trade"
RAW = r"C:\Users\OWNER\Desktop\GBC_data\data\raw"
OUT = r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a):
    s=" ".join(str(x) for x in a); print(s); log.append(s)

# ---------- 1. discovery ----------
L("=== results/pq_trade listing ===")
try:
    for f in sorted(os.listdir(RES)):
        L(f, os.path.getsize(os.path.join(RES,f)))
except Exception as e:
    L("RES listing err", e)

for cand in ["book_sim.json","netbook.json","master_book.json","sizing.json",
             "yearly_stats.json","pctcap_corrected.json","strategy_suite.json",
             "three_stream.json","battery.json"]:
    p=os.path.join(RES,cand)
    if os.path.exists(p):
        try:
            d=json.load(open(p))
            def shp(v):
                if isinstance(v,list): return f"list[{len(v)}]"
                if isinstance(v,dict): return f"dict{list(v.keys())[:8]}"
                return type(v).__name__
            if isinstance(d,dict):
                L(f"--- {cand}:", {k:shp(v) for k,v in d.items()})
            else:
                L(f"--- {cand}: {type(d)} len", len(d) if hasattr(d,'__len__') else '?')
        except Exception as e: L(cand,"ERR",e)

for pq in glob.glob(os.path.join(RES,"*.parquet")):
    try:
        df=pd.read_parquet(pq)
        L("PARQUET",os.path.basename(pq),df.shape,list(df.columns)[:20])
    except Exception as e: L("pq err",os.path.basename(pq),e)

L("=== data/raw candidates for S&P ===")
for f in ["ff_factors.csv","spy_totret.csv","names_totret.csv","etf_totret.csv"]:
    p=os.path.join(RAW,f)
    if os.path.exists(p):
        try:
            h=pd.read_csv(p,nrows=3); L(f, "cols=", list(h.columns)[:12])
        except Exception as e: L(f,"ERR",e)

open(os.path.join(OUT,"_monthly_discovery.txt"),"w").write("\n".join(log))
print("DISCOVERY WRITTEN")
