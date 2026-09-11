
import os, glob, traceback
import pandas as pd
RES=r"C:\GBC_data\results\pq_trade"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))
import pyarrow
L("pyarrow version:", pyarrow.__version__)

# metadata for every parquet
for p in sorted(glob.glob(os.path.join(RES,"*.parquet"))):
    try:
        import pyarrow.parquet as pq
        md=pq.read_metadata(p)
        L("META", os.path.basename(p), "rows", md.num_rows, "cols", md.num_columns)
    except Exception as e:
        L("meta-err", os.path.basename(p), repr(e)[:80])

# export the series-bearing parquets
targets=["bt_series.parquet","mh_trade_panel.parquet","panel_wedge.parquet",
         "pfore_monthly.parquet","pq_iqn_quantiles.parquet","ts_wedge_h21.parquet"]
for f in targets:
    p=os.path.join(RES,f)
    if not os.path.exists(p): L("MISSING",f); continue
    try:
        df=pd.read_parquet(p)
        L(f,"OK shape",df.shape,"cols",list(df.columns)[:25])
        outname="exp_"+f.replace(".parquet",".csv")
        if len(df)<=30000:
            df.to_csv(os.path.join(OUT,outname)); L("  wrote",outname,"(full)")
        else:
            df.head(3000).to_csv(os.path.join(OUT,"head_"+outname)); L("  wrote head_"+outname)
    except Exception as e:
        L(f,"READ-ERR",repr(e)[:120])
open(os.path.join(OUT,"q_export_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("EXPORTDONE")
