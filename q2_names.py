
import os, glob
import numpy as np, pandas as pd
RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a)); open(os.path.join(OUT,"q2_names_log.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))

def series(path, prefs):
    try: d=pd.read_csv(path)
    except: return None
    d.columns=[c.strip() for c in d.columns]
    if "date" not in d.columns or "value" not in d.columns: return None
    if "field" in d.columns:
        f=d["field"].astype(str)
        for pr in prefs:
            m=f.str.contains(pr,case=False,regex=False)
            if m.any(): d=d[m]; break
    d["date"]=pd.to_datetime(d["date"],errors="coerce")
    d["value"]=pd.to_numeric(d["value"],errors="coerce")
    return d[["date","value"]].dropna().drop_duplicates("date").sort_values("date")

names=sorted(os.path.basename(p)[4:-4] for p in glob.glob(os.path.join(RAW,"tpx_*.csv")))
L("candidate names:",len(names))
recs=[]; used=0
for nm in names:
    tp=os.path.join(RAW,f"tpx_{nm}.csv"); iv=os.path.join(RAW,f"tiv2_{nm}.csv")
    if not (os.path.exists(tp) and os.path.exists(iv)): continue
    px=series(tp,["TOT_RETURN","PX_LAST","LAST_PRICE","PX","LAST"])
    atm=series(iv,["100.0%MNY","100.0","ATM","90.0%MNY"])  # prefer ATM 100% moneyness 30d IV
    if px is None or atm is None or len(px)<300 or len(atm)<80: continue
    m=pd.merge(px.rename(columns={"value":"px"}),atm.rename(columns={"value":"iv"}),on="date",how="left").sort_values("date")
    m["iv"]=m["iv"].ffill(); m["ret"]=m["px"].pct_change()
    m=m.dropna(subset=["ret","iv"]).reset_index(drop=True); m["ym"]=m["date"].dt.to_period("M")
    if len(m)<300: continue
    for p,sub in m.groupby("ym"):
        e=sub.iloc[0]; idx=e.name
        if not (e["iv"]>0): continue
        K=(e["iv"]/100.0)**2; Ksell=((e["iv"]-0.5)/100.0)**2
        fwd=m.iloc[idx+1:idx+22]
        if len(fwd)<15: continue
        rv=252.0*np.mean(fwd["ret"].values**2)
        recs.append((str(p),nm,max((Ksell-rv)/K,-3.0)))
    used+=1
    if used%100==0: L("...processed",used,"names, obs so far",len(recs))
R=pd.DataFrame(recs,columns=["ym","name","r"])
R["year"]=pd.PeriodIndex(R["ym"],freq="M").year
book=R.groupby("ym")["r"].mean().to_frame("r"); book["n"]=R.groupby("ym")["r"].count()
book=book.reset_index(); book["year"]=pd.PeriodIndex(book["ym"],freq="M").year
def sr(x): x=pd.Series(x).dropna(); return x.mean()/x.std()*np.sqrt(12)
L("names used",used,"total asset-months",len(R),"book months",len(book))
for a,b in [(1996,2026),(2009,2026),(2016,2026)]:
    bk=book[(book.year>=a)&(book.year<=b)]
    L(f"[{a}-{b}] equal-weight single-name book: SR={sr(bk['r']):.2f} mean/mo={bk['r'].mean()*100:.1f}% worst={bk['r'].min()*100:.0f}% avg_n={bk['n'].mean():.0f}")
book.to_csv(os.path.join(OUT,"names_book_series.csv"),index=False)
R.groupby("name")["r"].agg(["mean","std","count"]).to_csv(os.path.join(OUT,"names_perleg.csv"))
L("SAVED names_book_series.csv + names_perleg.csv")
print("Q2NAMESDONE")
