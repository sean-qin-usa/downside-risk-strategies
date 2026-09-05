# Detached multi-year realized-measures build 2015-2024 (same logic as rm_build_year, internal loop).
import json, time, datetime as dt, os
import wrds, numpy as np, pandas as pd
db=wrds.Connection(wrds_username='seanqin2028')
NAMES=['AAPL','MSFT','JPM','XOM','JNJ','PG','KO','WMT','CVX','HD','PFE','MRK','CSCO','INTC','VZ',
       'T','BAC','WFC','C','GS','IBM','MMM','CAT','BA','DIS','MCD','NKE','ORCL','QCOM','TXN']
inlist="','".join(NAMES)
BAD="('O','Z','4','B','G','L','W','U','7','9','C','N','R')"
def build_year(YEAR):
    d=dt.date(YEAR,1,1); end=dt.date(YEAR,12,31); days=[]
    while d<=end:
        if d.weekday()<5: days.append(d)
        d+=dt.timedelta(days=1)
    rows=[]; errs=0; done=0; t0=time.time()
    for day in days:
        tbl="ctm_%s"%day.strftime("%Y%m%d")
        q=("select sym_root, floor(extract(epoch from time_m)/300)::int as bin, "
           "percentile_cont(0.5) within group (order by price) as px "
           "from taqm_%d.%s where sym_root in ('%s') and price>0 and tr_corr='00' "
           "and tr_scond not in %s and time_m between '09:30:00' and '16:00:00' "
           "group by sym_root, bin"%(YEAR,tbl,inlist,BAD))
        try: df=db.raw_sql(q)
        except Exception: errs+=1; continue
        if df is None or len(df)==0: continue
        for sym,g in df.groupby('sym_root'):
            g=g.sort_values('bin'); px=g['px'].astype(float).values
            if len(px)<20: continue
            med=np.median(px); px=px[(px>0.5*med)&(px<2.0*med)]
            if len(px)<20: continue
            r=np.diff(np.log(px)); r=r[np.abs(r)<0.20]; N=len(r)
            if N<15: continue
            rv=float(np.sum(r*r))
            if rv<=0: continue
            bv=float((np.pi/2.0)*(N/(N-1.0))*np.sum(np.abs(r[1:])*np.abs(r[:-1])))
            rows.append({'date':str(day),'ticker':sym,'rv':rv,'bv':bv,'jv':float(max(rv-bv,0.0)),
                         'rskew':float((np.sqrt(N)*np.sum(r**3))/(rv**1.5)),
                         'rkurt':float((N*np.sum(r**4))/(rv**2)),'n':N})
        done+=1
        if done%25==0: open('rm_progress_rest.txt','w').write("YEAR %d day %s %d/%d %d rows %.0fs"%(YEAR,day,done,len(days),len(rows),time.time()-t0))
    pd.DataFrame(rows).to_csv('panel_rm_%d.csv'%YEAR,index=False)
    return {'year':YEAR,'rows':len(rows),'errs':errs,'sec':round(time.time()-t0)}
res=[]
for Y in range(2015,2025):
    res.append(build_year(Y))
    open('rm_build_rest.txt','w').write(json.dumps(res,indent=2))
db.close()
open('rm_build_rest.txt','w').write(json.dumps(res,indent=2)+"\nALL DONE")
