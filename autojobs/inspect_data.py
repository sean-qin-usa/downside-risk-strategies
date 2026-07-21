import os, glob, time
import pandas as pd
RES=r"C:\GBC_data\results\pq_trade"; PROJ=r"C:\Users\OWNER\Claude\Projects\GBC Project"
W=r"C:\GBC_data\data\wrds"
out=os.path.join(PROJ,"iqn_data_inspect.txt"); L=[]; p=lambda s:L.append(str(s))
p("INSPECT "+time.ctime())
# IQN quantile files (in results, and exported in project)
cands=glob.glob(os.path.join(RES,"*quantil*"))+glob.glob(os.path.join(PROJ,"*quantil*"))+glob.glob(os.path.join(RES,"mh_*.csv"))
p("=== candidate IQN quantile files ===")
for f in sorted(set(cands)):
    p("  %8dKB %s"%(os.path.getsize(f)//1024, f))
# peek the main one
for nm in ["mh_quantiles_gpu_v2.csv","mh_quantiles_frozen_c2024.csv"]:
    for base in [RES,PROJ]:
        fp=os.path.join(base,nm)
        if os.path.exists(fp):
            d=pd.read_csv(fp,nrows=5); p("\n=== %s ==="%nm); p("cols: %s"%list(d.columns))
            dd=pd.read_csv(fp,usecols=[c for c in d.columns if c in ('tk','date','h')] or None)
            p("  names(sample): %s"%sorted(dd['tk'].unique())[:12] if 'tk' in dd else "no tk")
            if 'h' in dd: p("  horizons: %s"%sorted(dd['h'].unique()))
            if 'date' in dd: p("  date range: %s..%s"%(dd['date'].min(),dd['date'].max()))
            p(d.to_string()); break
# option IV data for surface fitting: strikes per name/date
d=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','date','exdate','strike_price','impl_volatility','delta'], nrows=400000)
g=d.groupby(['secid','date','exdate']).size()
p("\n=== strikes per (name,date,expiry) in 2023 (for surface fit) ===")
p("  median strikes/smile: %.0f  p25 %.0f p75 %.0f"%(g.median(),g.quantile(.25),g.quantile(.75)))
open(out,"w").write("\n".join(L)); print("wrote",out)
