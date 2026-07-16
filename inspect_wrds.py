import os, glob, gzip, time
import pandas as pd
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"
out=r"C:\Users\OWNER\Claude\Projects\GBC Project\wrds_inspect_out.txt"
L=[]; p=lambda s:L.append(str(s))
p("INSPECT "+time.ctime())
files=sorted(glob.glob(os.path.join(W,"*")))
p("=== files (%d) ==="%len(files))
for f in files:
    p("  %8dKB  %s"%(os.path.getsize(f)//1024, os.path.basename(f)))
def peek(name, nrows=4):
    fp=os.path.join(W,name)
    if not os.path.exists(fp): p("\n%s MISSING"%name); return None
    try:
        d=pd.read_csv(fp, nrows=200000)
        p("\n=== %s ===  cols: %s"%(name, list(d.columns)))
        p("  rows(sample<=200k): %d"%len(d))
        if 'date' in d.columns: p("  date range: %s .. %s"%(d['date'].min(), d['date'].max()))
        p(d.head(nrows).to_string())
        return d
    except Exception as e:
        p("\n%s ERR %s"%(name, str(e)[:150])); return None
peek("secids.csv")
peek("spreads_2020.csv.gz")
peek("surf10d_2020.csv.gz")
peek("delist_returns.csv.gz")
# quick spread stats on one year
try:
    d=pd.read_csv(os.path.join(W,"spreads_2020.csv.gz"))
    d['mid']=(d['best_bid']+d['best_offer'])/2
    d=d[d['mid']>0.05]
    d['relhalf']=(d['best_offer']-d['best_bid'])/(2*d['mid'])
    p("\n=== spreads_2020 effective half-spread (rel to mid) ===")
    p("  n=%d  median relhalf=%.3f  mean=%.3f  p25=%.3f p75=%.3f"%(len(d), d['relhalf'].median(), d['relhalf'].mean(), d['relhalf'].quantile(.25), d['relhalf'].quantile(.75)))
    p("  DTE range: %s .. %s (exdate-date)"% (None,None))
    p("  by delta bucket median relhalf:")
    d['db']=pd.cut(d['delta'], [-0.5,-0.3,-0.2,-0.1,-0.05,0])
    p(d.groupby('db')['relhalf'].median().to_string())
except Exception as e:
    p("spread stats ERR "+str(e)[:150])
open(out,"w").write("\n".join(L)); print("wrote",out)
