# Inventory intraday EQUITY data + locate the crypto-hourly harness to mirror. Decide TAQ vs Bloomberg intraday5.
import os, glob, json
import pandas as pd
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project\intraday_probe.txt"
DESK=r"C:\GBC_data"; RAW=os.path.join(DESK,"data","raw"); W=os.path.join(DESK,"data","wrds")
L=[]
def p(*a): L.append(" ".join(str(x) for x in a))
def cols(f,n=3):
    try:
        d=pd.read_csv(f,nrows=n) if not f.endswith(".gz") else pd.read_csv(f,nrows=n,compression="gzip")
        return list(d.columns), d
    except Exception as e: return [f"ERR {e}"],None

p("=== BLOOMBERG intraday5_* ===")
i5=sorted(glob.glob(os.path.join(RAW,"intraday5_*")))
p("n_files:",len(i5))
for f in i5[:20]: p("  ",os.path.basename(f), os.path.getsize(f))
if i5:
    c,d=cols(i5[0]); p("cols:",c)
    if d is not None and len(d): p("sample:",d.iloc[0].to_dict())
    # coverage of one file
    try:
        full=pd.read_csv(i5[0])
        dc=[x for x in full.columns if 'date' in x.lower() or 'time' in x.lower()]
        if dc: p("time col",dc[0],"range",str(full[dc[0]].min()),"->",str(full[dc[0]].max()),"rows",len(full))
    except Exception as e: p("coverage ERR",str(e)[:100])

p("\n=== other intraday-ish equity files ===")
for pat in ["*intraday*","*_5min*","*_1min*","*hourly*","*taq*","*TAQ*"]:
    for f in glob.glob(os.path.join(RAW,pat))+glob.glob(os.path.join(W,pat)):
        p("  ",f, os.path.getsize(f))

p("\n=== crypto hourly (mirror target) ===")
for pat in ["crypto_hourly*.csv","*hourly*.py","rolling_hourly*.py","clean_hourly*.py","iqn_np*.py"]:
    for base in [RAW, os.path.join(DESK,"code"), os.path.join(DESK,"code","pq_trade"), os.path.join(DESK,"results","pq_trade"), DESK]:
        for f in glob.glob(os.path.join(base,pat))+glob.glob(os.path.join(base,"**",pat),recursive=True):
            p("  ",f, os.path.getsize(f))
# crypto_hourly.csv structure
for base in [RAW, DESK, os.path.join(DESK,"data")]:
    for f in glob.glob(os.path.join(base,"crypto_hourly*.csv"))+glob.glob(os.path.join(base,"**","crypto_hourly*.csv"),recursive=True):
        c,d=cols(f); p("crypto_hourly cols:",c)
        if d is not None and len(d): p("  sample:",d.iloc[0].to_dict())
        break

p("\n=== names_reference / liquid equity names available ===")
for f in ["names_reference.csv","eq100_reference.csv","panel_mcaps.csv"]:
    ff=os.path.join(RAW,f)
    if os.path.exists(ff):
        c,_=cols(ff); p("  ",f,c)
p("\n=== DONE ===")
open(OUT,"w").write("\n".join(L)); print("wrote",OUT,len(L),"lines")
