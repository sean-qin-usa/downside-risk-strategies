# AMORTIZATION where it MATTERS: brand-new IPOs' first weeks. On days<250 GARCH can't fit; only benchmark = own expanding-empirical quantiles.
import builtins, os, json, time, math
def _fi(p=''):
    s=str(p).lower(); return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import numpy as np, pandas as pd, wrds
from sklearn.ensemble import HistGradientBoostingRegressor
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
db=wrds.Connection(wrds_username='seanqin2028'); lg("CONNECTED %ds"%(time.time()-t0))
nm=db.raw_sql("select permno,ticker,siccd,st_date,shrcd from crsp.stocknames where shrcd in (10,11) and ticker is not null")
nm['st_date']=pd.to_datetime(nm['st_date']); nm=nm.sort_values('st_date').groupby('permno',as_index=False).last()
sz=db.raw_sql("select permno, abs(prc)*shrout/1000.0 as mcap_mm from crsp.dsf where date='2024-12-31' and prc is not null and shrout>0")
m=nm.merge(sz,on='permno',how='left')
m['sector']=pd.to_numeric(m['siccd'],errors='coerce').fillna(-1000)//1000; m['sector']=m['sector'].astype(int)
m['mcap_mm']=pd.to_numeric(m['mcap_mm'],errors='coerce').fillna(300.0)
ipo=m[m.st_date>='2019-01-01'].sample(min(1600,len(m[m.st_date>='2019-01-01'])),random_state=5)
smid=m[(m.mcap_mm>=100)&(m.mcap_mm<10000)&(m.st_date<'2018-01-01')].sample(900,random_state=5)
uni=pd.concat([ipo.assign(cohort='ipo'),smid.assign(cohort='smid')]); ids=",".join(str(int(x)) for x in uni.permno)
SEC={int(r.permno):int(r.sector) for r in uni.itertuples()}; MC={int(r.permno):float(r.mcap_mm) for r in uni.itertuples()}; COH={int(r.permno):r.cohort for r in uni.itertuples()}
lg("universe ipo=%d smid=%d; pulling returns %.0fs"%(len(ipo),len(smid),time.time()-t0))
rets=db.raw_sql(f"select permno,date,ret from crsp.dsf where permno in ({ids}) and date>='2018-01-01' and ret is not null")
db.close(); rets['date']=pd.to_datetime(rets['date']); rets['ret']=pd.to_numeric(rets['ret'],errors='coerce')*100; rets=rets.dropna(subset=['ret'])
lg("returns %d rows %.0fs"%(len(rets),time.time()-t0))
def build(g):
    g=g.sort_values('date'); r=g['ret'].astype(float); n=len(g)
    d=pd.DataFrame({'permno':np.full(n,int(g['permno'].iloc[0])),'y':r.values,'age':np.arange(n)})
    d['lag1']=r.shift(1).values; d['abs1']=r.abs().shift(1).values
    d['rv5']=r.rolling(5,min_periods=3).std().shift(1).values; d['rv21']=r.rolling(21,min_periods=8).std().shift(1).values
    d['mean21']=r.rolling(21,min_periods=8).mean().shift(1).values; d['dn']=(r.shift(1)<0).astype(float).values
    return d
D=pd.concat([build(g) for _,g in rets.groupby('permno')],ignore_index=True)
D['logmcap']=np.log(np.maximum(D.permno.map(MC).fillna(300.0).values,1.0))
D['sector']=D.permno.map(SEC).fillna(-1).astype(int)
D['rv21']=pd.to_numeric(D['rv21'],errors='coerce'); D['rv5']=pd.to_numeric(D['rv5'],errors='coerce')
D['rv5']=D['rv5'].fillna(D['rv21']).fillna(2.0); D['rv21']=D['rv21'].fillna(2.0)
D['mean21']=pd.to_numeric(D['mean21'],errors='coerce').fillna(0.0); D['abs1']=pd.to_numeric(D['abs1'],errors='coerce')
D=D.dropna(subset=['lag1']); D['abs1']=D['abs1'].fillna(D['abs1'].median())
Xc=['lag1','abs1','rv5','rv21','mean21','dn','logmcap','sector','age']
rng=np.random.default_rng(5); ipop=np.array([int(x) for x in ipo.permno]); rng.shuffle(ipop); hold=set(ipop[:int(len(ipop)*0.4)])
tr=D[~D.permno.isin(hold)]; TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
amq={}
for tau in TAUS:
    mdl=HistGradientBoostingRegressor(loss='quantile',quantile=tau,max_iter=250,max_depth=4,learning_rate=0.06); mdl.fit(tr[Xc].values,tr['y'].values); amq[tau]=mdl
lg("amort trained on %d rows %.0fs"%(len(tr),time.time()-t0))
te=D[D.permno.isin(hold)].sort_values(['permno','age']).reset_index(drop=True)
AM={tau:amq[tau].predict(te[Xc].values) for tau in TAUS}  # vectorized
def pin(y,q,tau): d=y-q; return tau*d if d>=0 else (tau-1)*d
buckets={'d15_60':(15,60),'d60_120':(60,120),'d120_250':(120,250)}
agg={b:{'am':0.0,'emp':0.0,'n':0} for b in buckets}
ages=te['age'].values; ys=te['y'].values; perm=te['permno'].values
ownlist={};
for pn,g in te.groupby('permno'): ownlist[pn]=g['y'].values
# per-name expanding index
idxpos={}
for i in range(len(te)):
    pn=perm[i]; idxpos.setdefault(pn,0)
    pos=idxpos[pn]; idxpos[pn]+=1  # position within this name
    a=ages[i]
    for b,(lo,hi) in buckets.items():
        if lo<=a<hi:
            own=ownlist[pn][:pos]
            if len(own)<12: break
            y=ys[i]; eq={tau:float(np.quantile(own,tau)) for tau in TAUS}
            la=np.mean([pin(y,float(AM[tau][i]),tau) for tau in TAUS]); le=np.mean([pin(y,eq[tau],tau) for tau in TAUS])
            agg[b]['am']+=la; agg[b]['emp']+=le; agg[b]['n']+=1
            break
out={'note':'Held-out IPOs first weeks (GARCH cannot fit <250d). Amortized (from characteristics, never saw these names) vs expanding-empirical (own returns to date). ratio<1 => amortized better on brand-new names.','n_heldout_ipos':len(hold),'n_train_rows':int(len(tr))}
out['young_windows']={}
for b in buckets:
    if agg[b]['n']<20: continue
    a=agg[b]['am']/agg[b]['n']; e=agg[b]['emp']/agg[b]['n']
    out['young_windows'][b]=dict(n=agg[b]['n'],amortized=round(a,4),expanding_empirical=round(e,4),ratio_amort_over_emp=round(a/e,3),garch='N/A cannot fit')
json.dump(out,open(os.path.join(P,"amort_young.json"),"w"),indent=2,default=str)
lg("AMORT_YOUNG\n"+json.dumps(out['young_windows'],indent=2,default=str)); lg("DONE %.0fs"%(time.time()-t0))
