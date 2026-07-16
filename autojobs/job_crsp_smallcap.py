# CRSP small-cap / IPO characterization + panel for the transfer test.
# Tests: are small-caps/IPOs (a) fatter-tailed and (b) more data-starved (GARCH can't fit) => IQN territory?
import builtins, os, json, time, math
def _fi(p=''):
    s=str(p).lower(); return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import numpy as np, pandas as pd, wrds
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
db=wrds.Connection(wrds_username='seanqin2028'); lg("CONNECTED %ds"%(time.time()-t0))
nm=db.raw_sql("select permno,ticker,comnam,siccd,st_date,shrcd from crsp.stocknames where shrcd in (10,11) and ticker is not null")
nm['st_date']=pd.to_datetime(nm['st_date']); nm=nm.sort_values('st_date').groupby('permno',as_index=False).last()
sz=db.raw_sql("select permno, abs(prc)*shrout/1000.0 as mcap_mm from crsp.dsf where date='2024-12-31' and prc is not null and shrout>0")
m=nm.merge(sz,on='permno',how='left'); lg("names=%d %.0fs"%(len(m),time.time()-t0))
rng=np.random.default_rng(7)
def samp(df,n): return df.sample(min(n,len(df)),random_state=7) if len(df) else df
ipo=samp(m[(m.st_date>='2020-01-01')],180)
small=samp(m[(m.mcap_mm>=100)&(m.mcap_mm<2000)&(m.st_date<'2018-01-01')],180)
large=samp(m[(m.mcap_mm>=50000)&(m.st_date<'2015-01-01')],80)
ipo['cohort']='recent_ipo'; small['cohort']='smallcap'; large['cohort']='largecap_ctrl'
uni=pd.concat([ipo,small,large]); ids=",".join(str(int(x)) for x in uni.permno)
lg("cohorts ipo=%d small=%d large=%d, pulling returns... %.0fs"%(len(ipo),len(small),len(large),time.time()-t0))
rets=db.raw_sql(f"select permno,date,ret from crsp.dsf where permno in ({ids}) and date>='2015-01-01' and ret is not null")
db.close(); rets['date']=pd.to_datetime(rets['date']); rets['ret']=pd.to_numeric(rets['ret'],errors='coerce')
lg("return rows=%d %.0fs"%(len(rets),time.time()-t0))
coh={int(r.permno):r.cohort for r in uni.itertuples()}
def name_stats(g):
    r=g['ret'].dropna().values
    if len(r)<30: return None
    z=(r-r.mean())/(r.std()+1e-12)
    return dict(n=len(r), kurt=float((z**4).mean()-3), skew=float((z**3).mean()),
                jump5=float((np.abs(z)>5).mean()*100), annvol=float(r.std()*math.sqrt(252)), worst=float(r.min()*100))
per=[]
for pn,g in rets.groupby('permno'):
    st=name_stats(g)
    if st: per.append(dict(permno=int(pn),cohort=coh.get(int(pn)),**st))
per=pd.DataFrame(per); per.to_csv(os.path.join(P,"crsp_smallcap_panel.csv"),index=False)
out={'n_names':len(per),'by_cohort':{}}
for c in ['recent_ipo','smallcap','largecap_ctrl']:
    cc=per[per.cohort==c]
    if not len(cc): continue
    out['by_cohort'][c]=dict(n_names=int(len(cc)),
        median_hist_days=int(cc.n.median()), pct_under250d=round(float((cc.n<250).mean()*100),1),
        median_kurtosis=round(float(cc.kurt.median()),1), median_skew=round(float(cc.skew.median()),2),
        median_jump5sig_pct=round(float(cc.jump5.median()),3), median_annvol=round(float(cc.annvol.median()),2),
        median_worst_day_pct=round(float(cc.worst.median()),1))
json.dump(out,open(os.path.join(P,"crsp_smallcap_results.json"),"w"),indent=2,default=str)
lg("SMALLCAP\n"+json.dumps(out,indent=2,default=str)); lg("SMALLCAP_DONE %.0fs"%(time.time()-t0))
