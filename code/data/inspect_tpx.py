import os, glob, time
import pandas as pd
D=r"C:\GBC_data\data\raw"
out=r"C:\Users\OWNER\Claude\Projects\GBC Project\tpx_inspect_out.txt"
L=[]; p=lambda s:L.append(str(s))
p("TPX INSPECT "+time.ctime())
# find price / total-return single-name files
for pat in ['tpx*','tpx2*','*totret*','names_totret*','*px*']:
    fs=sorted(glob.glob(os.path.join(D,pat)))[:6]
    if fs:
        p("\npattern %s -> %d files (showing<=6):"%(pat,len(glob.glob(os.path.join(D,pat)))))
        for f in fs: p("  %8dKB %s"%(os.path.getsize(f)//1024, os.path.basename(f)))
# peek the most likely price file
cand=None
for pat in ['tpx_*.csv','tpx*.csv','names_totret.csv','*totret*.csv']:
    fs=sorted(glob.glob(os.path.join(D,pat)))
    if fs: cand=fs[0]; break
if cand:
    d=pd.read_csv(cand, nrows=8)
    p("\n=== sample %s ==="%os.path.basename(cand)); p("cols: %s"%list(d.columns)); p(d.head(6).to_string())
# also check secids/ticker mapping we already have
p("\n(option secids->ticker map is in data/wrds/secids.csv)")
open(out,"w").write("\n".join(L)); print("wrote",out)
