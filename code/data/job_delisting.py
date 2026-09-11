# job_delisting.py -- CRSP delisting-return merge for the GRAFT-Q panel (pre-registered App. robust(a)).
# Registered prediction: calibration statistics change negligibly (delisting months are a tiny
# fraction of observations on this liquid optionable panel); single-name short-put economics
# deteriorate modestly.  This job MEASURES both claims.
#
# VERIFY-BEFORE-RUN: WRDS boilerplate copied verbatim from the proven job_crsp_panel.py
# (pgpass + seanqin2028).  Column layouts printed before use; every stage guarded.
#
# Stages:
#  1. Pull crsp.dsedelist (permno, dlstdt, dlret, dlstcd) + crsp.stocknames ticker map.
#  2. Map the mh_quantiles_gpu.csv panel tickers -> permno (latest stocknames row per ticker,
#     shrcd 10/11).  Report match rate -- unmatched tickers listed for manual review.
#  3. Exposure count: panel name-dates whose h-day forward window contains a delisting date.
#  4. For affected name-dates, rebuild the realized forward return from crsp.dsf INCLUDING
#     the delisting return (compound daily rets to the delist date, then dlret), and
#     recompute 5%/1% breach rates and the h=21 crash-section quantities before/after.
import builtins, os, json, time, math
def _fi(p=''):
    s=str(p).lower(); return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import numpy as np, pandas as pd
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; RES=r"C:\GBC_data\results\pq_trade"
lg=lambda s:print(s,flush=True); t0=time.time()
OUT={"stages_done":[],"errors":{}}
OUTJ=os.path.join(P,"delisting_merge_results.json")
def dump(): json.dump(OUT,open(OUTJ,"w"),indent=2,default=str)

try:
    import wrds
    db=wrds.Connection(wrds_username='seanqin2028'); lg("WRDS CONNECTED %ds"%(time.time()-t0))
    dl=db.raw_sql("select permno, dlstdt, dlret, dlstcd from crsp.dsedelist where dlstdt>='2005-01-01'")
    nm=db.raw_sql("select permno,ticker,comnam,shrcd,st_date from crsp.stocknames where shrcd in (10,11) and ticker is not null")
    lg(f"delist rows={len(dl)}  stocknames={len(nm)}")
    OUT["stage1"]={"n_delist":int(len(dl)),"n_names":int(nm.permno.nunique())}
    OUT["stages_done"].append(1); dump()
except Exception as e:
    OUT["errors"]["stage1"]=repr(e); dump(); lg("STAGE1 FAIL "+repr(e)); raise SystemExit

try:
    IQ=pd.read_csv(os.path.join(RES,"mh_quantiles_gpu.csv"),usecols=["tk","date","h","p01","p05","y"])
    IQ["date"]=pd.to_datetime(IQ["date"])
    tks=sorted(IQ.tk.unique())
    nm["st_date"]=pd.to_datetime(nm["st_date"])
    latest=nm.sort_values("st_date").groupby("ticker",as_index=False).last()
    tkmap={r.ticker:int(r.permno) for r in latest.itertuples() if r.ticker in set(tks)}
    unmatched=[t for t in tks if t not in tkmap]
    lg(f"panel names={len(tks)} matched={len(tkmap)} unmatched={unmatched}")
    OUT["stage2"]={"n_panel_names":len(tks),"n_matched":len(tkmap),"unmatched":unmatched}
    OUT["stages_done"].append(2); dump()
except Exception as e:
    OUT["errors"]["stage2"]=repr(e); dump(); lg("STAGE2 FAIL "+repr(e)); raise SystemExit

try:
    dl["dlstdt"]=pd.to_datetime(dl["dlstdt"]); dl["dlret"]=pd.to_numeric(dl["dlret"],errors="coerce")
    pmset=set(tkmap.values())
    dlp=dl[dl.permno.isin(pmset)].copy()
    inv={v:k for k,v in tkmap.items()}
    dlp["tk"]=dlp.permno.map(inv)
    # in-sample delistings only (within panel date range + horizon)
    dmin,dmax=IQ.date.min(),IQ.date.max()+pd.Timedelta(days=100)
    dlp=dlp[(dlp.dlstdt>=dmin)&(dlp.dlstdt<=dmax)]
    lg(f"delistings among panel names in-sample: {len(dlp)}")
    lg(dlp[["tk","dlstdt","dlret","dlstcd"]].to_string())
    OUT["stage3"]={"n_panel_delistings":int(len(dlp)),
                   "detail":dlp[["tk","dlstdt","dlret","dlstcd"]].to_dict("records")}
    # exposure: name-dates whose forward window [date, date+1.45*h cal days] contains dlstdt
    exposed={}
    for h in sorted(IQ.h.unique()):
        sub=IQ[IQ.h==h]; n_exp=0
        for r in dlp.itertuples():
            w=sub[(sub.tk==r.tk)&(sub.date<=r.dlstdt)&(sub.date>=r.dlstdt-pd.Timedelta(days=int(h*1.45)))]
            n_exp+=len(w)
        exposed[int(h)]={"n_exposed":int(n_exp),"n_total":int(len(sub)),
                         "share":round(float(n_exp/max(len(sub),1)),6)}
    OUT["stage3"]["exposure_by_h"]=exposed
    OUT["stages_done"].append(3); dump()
    lg(json.dumps(exposed,indent=1))
except Exception as e:
    OUT["errors"]["stage3"]=repr(e); dump(); lg("STAGE3 FAIL "+repr(e))

try:
    # stage 4: recompute breach rates with delisting-adjusted y for exposed rows
    if len(dlp):
        ids=",".join(str(int(x)) for x in dlp.permno.unique())
        dsf=db.raw_sql(f"select permno,date,ret from crsp.dsf where permno in ({ids}) and date>='2015-01-01'")
        dsf["date"]=pd.to_datetime(dsf["date"]); dsf["ret"]=pd.to_numeric(dsf["ret"],errors="coerce")
        adj_rows=[]
        for h in sorted(IQ.h.unique()):
            sub=IQ[IQ.h==h].copy(); sub["y_adj"]=sub["y"]
            for r in dlp.itertuples():
                g=dsf[dsf.permno==r.permno].set_index("date")["ret"].sort_index()
                w=sub[(sub.tk==r.tk)&(sub.date<=r.dlstdt)&(sub.date>=r.dlstdt-pd.Timedelta(days=int(h*1.45)))]
                for i,row in w.iterrows():
                    path=g[(g.index>row.date)&(g.index<=r.dlstdt)]
                    cum=float(np.prod(1.0+path.dropna().values))-1.0
                    dr=r.dlret if np.isfinite(r.dlret) else -0.30  # CRSP convention: missing dlret for perf-delist ~ -30%
                    sub.loc[i,"y_adj"]=(1.0+cum)*(1.0+dr)-1.0
            b5_raw=float((sub.y<sub.p05).mean()); b5_adj=float((sub.y_adj<sub.p05).mean())
            b1_raw=float((sub.y<sub.p01).mean()); b1_adj=float((sub.y_adj<sub.p01).mean())
            cr_raw=float((sub.y<-0.20).mean()); cr_adj=float((sub.y_adj<-0.20).mean())
            adj_rows.append(dict(h=int(h),breach5_raw=round(b5_raw,5),breach5_adj=round(b5_adj,5),
                                 breach1_raw=round(b1_raw,5),breach1_adj=round(b1_adj,5),
                                 crash20_raw=round(cr_raw,5),crash20_adj=round(cr_adj,5)))
            lg(f"h={h}: breach5 {b5_raw:.5f}->{b5_adj:.5f}  breach1 {b1_raw:.5f}->{b1_adj:.5f}  crash20 {cr_raw:.5f}->{cr_adj:.5f}")
        OUT["stage4_restated"]=adj_rows
    else:
        OUT["stage4_restated"]="no in-sample delistings among panel names -> calibration statistics unchanged exactly"
        lg("no in-sample delistings among panel names")
    OUT["stages_done"].append(4); dump()
    db.close()
except Exception as e:
    OUT["errors"]["stage4"]=repr(e); dump(); lg("STAGE4 FAIL "+repr(e))
lg("DELISTDONE %.0fs"%(time.time()-t0))
