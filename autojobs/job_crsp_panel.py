# Build CRSP small-cap/IPO transfer PANEL: daily returns + static characteristics (cap, sector, beta) for held-out transfer test.
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
m=nm.merge(sz,on='permno',how='left'); m['sector']=(m['siccd']//1000).fillna(-1).astype(int)  # 1-digit SIC sector
def samp(df,n): return df.sample(min(n,len(df)),random_state=11) if len(df) else df
ipo=samp(m[m.st_date>='2020-01-01'],300); ipo['cohort']='recent_ipo'
small=samp(m[(m.mcap_mm>=100)&(m.mcap_mm<2000)&(m.st_date<'2018-01-01')],300); small['cohort']='smallcap'
large=samp(m[(m.mcap_mm>=50000)&(m.st_date<'2015-01-01')],120); large['cohort']='largecap'
uni=pd.concat([ipo,small,large]); ids=",".join(str(int(x)) for x in uni.permno)
lg("cohorts ipo=%d small=%d large=%d; pulling returns %.0fs"%(len(ipo),len(small),len(large),time.time()-t0))
rets=db.raw_sql(f"select permno,date,ret from crsp.dsf where permno in ({ids}) and date>='2014-01-01' and ret is not null")
mkt=db.raw_sql("select date,vwretd from crsp.dsi where date>='2014-01-01'")  # value-weighted market for beta
db.close()
rets['date']=pd.to_datetime(rets['date']); rets['ret']=pd.to_numeric(rets['ret'],errors='coerce')
mkt['date']=pd.to_datetime(mkt['date']); mkt['vwretd']=pd.to_numeric(mkt['vwretd'],errors='coerce'); mkt=mkt.set_index('date')['vwretd']
rets.to_csv(os.path.join(P,"crsp_panel_returns.csv"),index=False); lg("saved returns %d rows %.0fs"%(len(rets),time.time()-t0))
# characteristics + beta
coh={int(r.permno):r.cohort for r in uni.itertuples()}; sec={int(r.permno):int(r.sector) for r in uni.itertuples()}; cap={int(r.permno):(float(r.mcap_mm) if pd.notna(r.mcap_mm) else np.nan) for r in uni.itertuples()}
tkr={int(r.permno):r.ticker for r in uni.itertuples()}
chars=[]
for pn,g in rets.groupby('permno'):
    g=g.set_index('date').sort_index(); j=g.join(mkt,how='inner').dropna()
    beta=np.nan
    if len(j)>60 and j['vwretd'].std()>0: beta=float(np.cov(j['ret'],j['vwretd'])[0,1]/np.var(j['vwretd']))
    chars.append(dict(permno=int(pn),ticker=tkr.get(int(pn)),cohort=coh.get(int(pn)),sector=sec.get(int(pn)),
                      mcap_mm=cap.get(int(pn)),beta=round(beta,2) if np.isfinite(beta) else None,
                      hist_days=int(len(g)),annvol=round(float(g['ret'].std()*math.sqrt(252)),2)))
pd.DataFrame(chars).to_csv(os.path.join(P,"crsp_panel_chars.csv"),index=False)
out=dict(n_names=len(chars),n_return_rows=len(rets),
         by_cohort={c:int((pd.DataFrame(chars).cohort==c).sum()) for c in ['recent_ipo','smallcap','largecap']},
         note='crsp_panel_returns.csv + crsp_panel_chars.csv ready for amortized-IQN transfer test (hold out IPO/smallcap names, condition on cap/sector/beta).')
json.dump(out,open(os.path.join(P,"crsp_panel_results.json"),"w"),indent=2,default=str)
lg("CRSP_PANEL_DONE %s %.0fs"%(json.dumps(out['by_cohort']),time.time()-t0))
