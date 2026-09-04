# job_delisting2.py -- v2 of the CRSP delisting merge.  Fixes from v1's output:
#  (a) dlstcd==100 means ACTIVE (end-of-file placeholder rows, dlstdt=2024-12-31) -> filter
#      to real delistings dlstcd in [200,599];
#  (b) bankrupt panel names appear under Q-suffixed tickers (BBBYQ, HTZGQ, SHLDQ) and were
#      unmatched -> add Q-stripped ticker fallback in the map;
#  (c) pd.NA dlret crashed np.isfinite -> use pd.notna + CRSP missing-dlret convention -0.30
#      for performance delistings (dlstcd 500s), 0.0 otherwise.
import builtins, os, json, time
def _fi(p=''):
    s=str(p).lower(); return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import numpy as np, pandas as pd
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; RES=r"C:\GBC_data\results\pq_trade"
lg=lambda s:print(s,flush=True); t0=time.time()
OUT={"stages_done":[],"errors":{}}; OUTJ=os.path.join(P,"delisting_merge_results_v2.json")
def dump(): json.dump(OUT,open(OUTJ,"w"),indent=2,default=str)

import wrds
db=wrds.Connection(wrds_username='seanqin2028'); lg("WRDS CONNECTED %ds"%(time.time()-t0))
dl=db.raw_sql("select permno, dlstdt, dlret, dlstcd from crsp.dsedelist where dlstdt>='2005-01-01' and dlstcd between 200 and 599")
nm=db.raw_sql("select permno,ticker,comnam,shrcd,st_date from crsp.stocknames where ticker is not null")
lg(f"REAL delist rows={len(dl)}  stocknames={len(nm)}")

IQ=pd.read_csv(os.path.join(RES,"mh_quantiles_gpu.csv"),usecols=["tk","date","h","p01","p05","y"])
IQ["date"]=pd.to_datetime(IQ["date"])
tks=sorted(IQ.tk.unique())
nm["st_date"]=pd.to_datetime(nm["st_date"])
latest=nm.sort_values("st_date").groupby("ticker",as_index=False).last()
byt={r.ticker:int(r.permno) for r in latest.itertuples()}
tkmap={}
for t in tks:
    if t in byt: tkmap[t]=byt[t]
    elif t.endswith("Q") and t[:-1] in byt: tkmap[t]=byt[t[:-1]]   # BBBYQ -> BBBY
unmatched=[t for t in tks if t not in tkmap]
lg(f"panel names={len(tks)} matched={len(tkmap)} unmatched(mostly ETFs)={unmatched}")
OUT["stage2"]={"n_matched":len(tkmap),"unmatched":unmatched}; OUT["stages_done"].append(2); dump()

dl["dlstdt"]=pd.to_datetime(dl["dlstdt"]); dl["dlret"]=pd.to_numeric(dl["dlret"],errors="coerce")
inv={}
for t,p in tkmap.items(): inv.setdefault(p,t)
dlp=dl[dl.permno.isin(set(tkmap.values()))].copy(); dlp["tk"]=dlp.permno.map(inv)
dmin,dmax=IQ.date.min(),IQ.date.max()+pd.Timedelta(days=100)
dlp=dlp[(dlp.dlstdt>=dmin)&(dlp.dlstdt<=dmax)]
lg(f"REAL delistings among panel names in-sample: {len(dlp)}")
lg(dlp[["tk","dlstdt","dlret","dlstcd"]].to_string())
OUT["stage3"]={"n_real_delistings":int(len(dlp)),"detail":dlp[["tk","dlstdt","dlret","dlstcd"]].to_dict("records")}
OUT["stages_done"].append(3); dump()

if len(dlp):
    ids=",".join(str(int(x)) for x in dlp.permno.unique())
    dsf=db.raw_sql(f"select permno,date,ret from crsp.dsf where permno in ({ids}) and date>='2015-01-01'")
    dsf["date"]=pd.to_datetime(dsf["date"]); dsf["ret"]=pd.to_numeric(dsf["ret"],errors="coerce")
    adj=[]
    for h in sorted(IQ.h.unique()):
        sub=IQ[IQ.h==h].copy(); sub["y_adj"]=sub["y"]; n_restated=0
        for r in dlp.itertuples():
            g=dsf[dsf.permno==r.permno].set_index("date")["ret"].sort_index()
            w=sub[(sub.tk==r.tk)&(sub.date<=r.dlstdt)&(sub.date>=r.dlstdt-pd.Timedelta(days=int(h*1.45)))]
            if not len(w): continue
            if pd.notna(r.dlret): dr=float(r.dlret)
            else: dr=-0.30 if 500<=int(r.dlstcd)<600 else 0.0
            for i,row in w.iterrows():
                path=g[(g.index>row.date)&(g.index<=r.dlstdt)]
                cum=float(np.prod(1.0+path.dropna().values))-1.0
                sub.loc[i,"y_adj"]=(1.0+cum)*(1.0+dr)-1.0; n_restated+=1
        rec=dict(h=int(h),n_restated=n_restated,
                 breach5_raw=round(float((sub.y<sub.p05).mean()),5),breach5_adj=round(float((sub.y_adj<sub.p05).mean()),5),
                 breach1_raw=round(float((sub.y<sub.p01).mean()),5),breach1_adj=round(float((sub.y_adj<sub.p01).mean()),5),
                 crash20_raw=round(float((sub.y<-0.20).mean()),5),crash20_adj=round(float((sub.y_adj<-0.20).mean()),5))
        adj.append(rec); lg(str(rec))
    OUT["stage4_restated"]=adj
else:
    OUT["stage4_restated"]="zero real delistings among matched panel names -> statistics unchanged exactly"
OUT["stages_done"].append(4); dump()
db.close(); lg("DELIST2DONE %.0fs"%(time.time()-t0))
