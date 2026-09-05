# Build per-name-day realized measures (RV, bipower BV, jump var JV, realized skew/kurt) from TAQ 5-min trades.
# Robust cleaning (regular sale conditions, daily price band, 20% return clip). One year per run (arg or YEAR var).
import json, time, datetime as dt, sys, os
YEAR=int(sys.argv[1]) if len(sys.argv)>1 else 2014
t0=time.time()
import wrds, numpy as np, pandas as pd
db=wrds.Connection(wrds_username='seanqin2028')
NAMES=['AAPL','MSFT','JPM','XOM','JNJ','PG','KO','WMT','CVX','HD','PFE','MRK','CSCO','INTC','VZ',
       'T','BAC','WFC','C','GS','IBM','MMM','CAT','BA','DIS','MCD','NKE','ORCL','QCOM','TXN']
inlist="','".join(NAMES)
d=dt.date(YEAR,1,1); end=dt.date(YEAR,12,31); days=[]
while d<=end:
    if d.weekday()<5: days.append(d)
    d+=dt.timedelta(days=1)
rows=[]; errs=[]; done=0
PROG=os.path.join('.', 'rm_progress_%d.txt'%YEAR)
for day in days:
    tbl="ctm_%s"%day.strftime("%Y%m%d")
    q=("select sym_root, floor(extract(epoch from time_m)/300)::int as bin, "
       "percentile_cont(0.5) within group (order by price) as px "
       "from taqm_%d.%s where sym_root in ('%s') and price>0 and tr_corr='00' "
       "and tr_scond not in ('O','Z','4','B','G','L','W','U','7','9','C','N','R') "
       "and time_m between '09:30:00' and '16:00:00' group by sym_root, bin"%(YEAR,tbl,inlist))
    try: df=db.raw_sql(q)
    except Exception as e: errs.append("%s %s"%(day,str(e)[:50])); continue
    if df is None or len(df)==0: continue
    for sym,g in df.groupby('sym_root'):
        g=g.sort_values('bin'); px=g['px'].astype(float).values
        if len(px)<20: continue
        med=np.median(px); px=px[(px>0.5*med)&(px<2.0*med)]
        if len(px)<20: continue
        r=np.diff(np.log(px)); r=r[np.abs(r)<0.20]
        N=len(r)
        if N<15: continue
        rv=float(np.sum(r*r))
        if rv<=0: continue
        bv=float((np.pi/2.0)*(N/(N-1.0))*np.sum(np.abs(r[1:])*np.abs(r[:-1])))
        jv=float(max(rv-bv,0.0))
        rskew=float((np.sqrt(N)*np.sum(r**3))/(rv**1.5))
        rkurt=float((N*np.sum(r**4))/(rv**2))
        rows.append({'date':str(day),'ticker':sym,'rv':rv,'bv':bv,'jv':jv,'rskew':rskew,'rkurt':rkurt,'n':N})
    done+=1
    if done%20==0:
        open(PROG,'w').write("day %s  %d/%d done  %d rows  %.0fs"%(day,done,len(days),len(rows),time.time()-t0))
db.close()
out=pd.DataFrame(rows); out.to_csv('panel_rm_%d.csv'%YEAR,index=False)
summ={'year':YEAR,'elapsed_s':round(time.time()-t0,1),'n_rows':len(out),'n_days':int(out.date.nunique()) if len(out) else 0,
      'n_names':int(out.ticker.nunique()) if len(out) else 0,'n_errs':len(errs),
      'median_ann_rvol':round(float(np.sqrt(out.rv.median()*252)*100),1) if len(out) else None,
      'median_jv_share':round(float((out.jv/out.rv).median()),3) if len(out) else None,
      'median_rkurt':round(float(out.rkurt.median()),2) if len(out) else None}
open('rm_build_%d.txt'%YEAR,'w').write(json.dumps(summ,indent=2,default=str))
