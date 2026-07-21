
import os, json
RES=r"C:\GBC_data\results\pq_trade"
OUT=r"C:\Users\OWNER\Claude\Projects\GBC Project"
log=[]
def L(*a): log.append(" ".join(str(x) for x in a))

def desc(v):
    if isinstance(v,list):
        return f"list[{len(v)}] head={v[:3]}"
    if isinstance(v,dict):
        return f"dict keys={list(v.keys())[:14]}"
    return f"{type(v).__name__}={str(v)[:60]}"

for fn in ["book_sim.json","netbook.json","sizing.json","master_book.json",
           "three_stream.json","yearly_stats.json","strategy_suite.json",
           "battery.json","pctcap_corrected.json"]:
    p=os.path.join(RES,fn)
    if not os.path.exists(p):
        L("MISSING",fn); continue
    try:
        d=json.load(open(p))
    except Exception as e:
        L("ERR",fn,e); continue
    if isinstance(d,dict):
        for k,v in d.items(): L(f"[{fn}] {k}: {desc(v)}")
    else:
        L(f"[{fn}] top {type(d).__name__} len={len(d) if hasattr(d,'__len__') else '?'}")
    L("")

L("=== ALL FILES in results/pq_trade ===")
try:
    for f in sorted(os.listdir(RES)):
        L(f, os.path.getsize(os.path.join(RES,f)))
except Exception as e:
    L("listdir err",e)

open(os.path.join(OUT,"_disc2.txt"),"w",encoding="utf-8").write("\n".join(map(str,log)))
print("DONE2")
