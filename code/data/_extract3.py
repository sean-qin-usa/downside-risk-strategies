
import os, json
import numpy as np, pandas as pd
RES=r"C:\GBC_data\results\pq_trade"
RAW=r"C:\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))

def readpq(path):
    for eng in ("fastparquet","pyarrow"):
        try:
            return pd.read_parquet(path, engine=eng), eng
        except Exception as e:
            L("  readfail", os.path.basename(path), eng, repr(e)[:90])
    return None, None

# ---- bt_series.parquet ----
df,eng = readpq(os.path.join(RES,"bt_series.parquet"))
if df is not None:
    L("bt_series OK via",eng,"shape",df.shape,"cols",list(df.columns))
    L("idx0",str(df.index[0]),"idxN",str(df.index[-1]),"idxtype",type(df.index).__name__)
    L("head:\n"+df.head(4).to_string())
    df.to_csv(os.path.join(OUT,"bt_series_dump.csv"))
    L("saved bt_series_dump.csv rows",len(df))

# ---- pfore_monthly.parquet ----
df2,eng2 = readpq(os.path.join(RES,"pfore_monthly.parquet"))
if df2 is not None:
    L("pfore OK via",eng2,"shape",df2.shape,"cols",list(df2.columns),"idx0",str(df2.index[0]))
    df2.to_csv(os.path.join(OUT,"pfore_monthly_dump.csv"))

# ---- deep dump bt_monthly.json ----
d=json.load(open(os.path.join(RES,"bt_monthly.json")))
def walk(o,pre=""):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v,pre+"."+str(k))
    elif isinstance(o,list):
        L(pre,"LIST len",len(o),"head",o[:3])
    else:
        L(pre,"=",str(o)[:40])
walk(d,"btm")

# ---- S&P (market) monthly total return from Fama-French ----
try:
    ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,
                   names=["date","mktrf","smb","hml","rf"])
    ff["date"]=pd.to_datetime(ff["date"].astype(float).astype(int).astype(str),format="%Y%m%d")
    ff["mkt_tot"]=(ff["mktrf"]+ff["rf"])/100.0
    ff["ym"]=ff["date"].dt.to_period("M")
    mkt_m=ff.groupby("ym")["mkt_tot"].apply(lambda x:(1+x).prod()-1)
    mkt_m.to_csv(os.path.join(OUT,"spx_monthly.csv"),header=["mkt_tot"])
    L("spx_monthly rows",len(mkt_m),"first",str(mkt_m.index[0]),"last",str(mkt_m.index[-1]))
except Exception as e:
    L("ff ERR",repr(e))

open(os.path.join(OUT,"_disc4.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("DONE4")
