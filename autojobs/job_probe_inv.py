import os, glob, gzip, io, sys
import pandas as pd

OUT = r"C:\Users\OWNER\Claude\Projects\GBC Project\probe_inventory.txt"
DESK = r"C:\GBC_data"
PROJ = r"C:\Users\OWNER\Claude\Projects\GBC Project"
lines = []
def p(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)

def cols_of(path, nrows=3):
    try:
        if path.endswith(".gz"):
            df = pd.read_csv(path, nrows=nrows, compression="gzip")
        else:
            df = pd.read_csv(path, nrows=nrows)
        return list(df.columns), df
    except Exception as e:
        return [f"ERR {e}"], None

p("=== PROBE INVENTORY ===")
p("DESK exists:", os.path.isdir(DESK))

# 1. WRDS dir
for sub in ["data\\wrds", "data\\raw", "results\\pq_trade"]:
    d = os.path.join(DESK, sub)
    p(f"\n--- {sub} exists={os.path.isdir(d)} ---")
    if os.path.isdir(d):
        fs = sorted(os.listdir(d))
        p("  n_files:", len(fs))
        for pat in ["spreads_dte05_15", "spreads_dte45_70", "spreads_2", "surf10d", "delist", "etf", "xasset", "secprd", "earn"]:
            m = [f for f in fs if pat.replace("\\","") in f]
            if m:
                p(f"  [{pat}] ->", m[:6], ("..." if len(m)>6 else ""))

# 2. columns of key WRDS files
def find_one(sub, pat):
    d = os.path.join(DESK, sub)
    if not os.path.isdir(d): return None
    m = sorted(glob.glob(os.path.join(d, pat)))
    return m[0] if m else None

for label, sub, pat in [
    ("MONTHLY spreads", "data\\wrds", "spreads_20*.csv.gz"),
    ("WEEKLY spreads", "data\\wrds", "spreads_dte05_15_*.csv.gz"),
    ("2MO spreads", "data\\wrds", "spreads_dte45_70_*.csv.gz"),
    ("surf10d", "data\\wrds", "surf10d_*.csv.gz"),
    ("delist", "data\\wrds", "delist*.csv*"),
]:
    f = find_one(sub, pat)
    p(f"\n--- {label}: {f} ---")
    if f:
        c, df = cols_of(f)
        p("  cols:", c)
        if df is not None and len(df):
            p("  sample row:", df.iloc[0].to_dict())

# 3. mh_quantiles production
p("\n--- mh_quantiles_gpu_v2 search ---")
for base in [DESK, PROJ, os.path.join(DESK,"results","pq_trade")]:
    for f in glob.glob(os.path.join(base, "mh_quantiles*.csv")):
        try:
            sz = os.path.getsize(f)//1024//1024
        except: sz="?"
        p(f"  {f}  ({sz}MB)")
# columns of production v2 if found
for base in [DESK, PROJ, os.path.join(DESK,"results","pq_trade")]:
    ff = glob.glob(os.path.join(base, "mh_quantiles_gpu_v2.csv"))
    if ff:
        c, df = cols_of(ff[0])
        p("  v2 cols:", c)
        break

# 4. tpx single-name sample
p("\n--- tpx sample ---")
tpx = find_one("data\\raw", "tpx_*.csv")
p("  file:", tpx)
if tpx:
    c, df = cols_of(tpx)
    p("  cols:", c)
    if df is not None and len(df):
        p("  fields present:", None)
    try:
        full = pd.read_csv(tpx, nrows=5000)
        if "field" in full.columns:
            p("  distinct fields:", sorted(full["field"].unique())[:10])
    except Exception as e:
        p("  field-probe ERR", e)

# 5. earnings dates file
p("\n--- earnings dates ---")
for base in [os.path.join(DESK,"data","raw"), os.path.join(DESK,"data","wrds"), DESK, PROJ]:
    for f in glob.glob(os.path.join(base, "*earn*.csv*")):
        p("  ", f)
        c, _ = cols_of(f)
        p("     cols:", c)

# 6. exp_bt_series + monthly_book (mounted anyway, but confirm)
p("\n--- strategy series files (PROJ) ---")
for nm in ["exp_bt_series.csv","monthly_book.csv","tau10_monthly_series.csv","monthly_strategy_vs_spx.csv"]:
    f = os.path.join(PROJ, nm)
    if os.path.exists(f):
        c,_ = cols_of(f)
        p(f"  {nm}: {c}")

# 7. panel_mcaps / OI ranking helper
p("\n--- helper files ---")
for base in [os.path.join(DESK,"data","raw"), os.path.join(DESK,"results","pq_trade"), PROJ]:
    for pat in ["panel_mcaps*","*oi*rank*","*_reference*"]:
        for f in glob.glob(os.path.join(base, pat)):
            p("  ", f)

p("\n=== DONE ===")
with open(OUT, "w") as fh:
    fh.write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
