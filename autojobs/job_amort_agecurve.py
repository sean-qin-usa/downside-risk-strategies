# AMORTIZATION EDGE vs LISTING AGE + HIERARCHICAL BLEND (Gibbs/partial-pooling).
# Q: how does amortized-vs-own-history edge decay as a name accumulates its own data?
#    Does a shrinkage blend (amortized prior + own empirical, age-weighted) dominate both at every age?
import builtins, os, json, time, math
def _fi(p=''):
    s=str(p).lower(); return 'seanqin2028' if 'username' in s else 'n'
builtins.input=_fi
os.environ['PGPASSFILE']=r'C:\Users\OWNER\AppData\Roaming\postgresql\pgpass.conf'; os.environ.setdefault('PGUSER','seanqin2028')
import numpy as np, pandas as pd, wrds
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
db=wrds.Connection(wrds_username='seanqin2028'); lg("CONNECTED %ds"%(time.time()-t0))
nm=db.raw_sql("select permno,ticker,siccd,st_date,shrcd from crsp.stocknames where shrcd in (10,11) and ticker is not null")
nm['st_date']=pd.to_datetime(nm['st_date']); nm=nm.sort_values('st_date').groupby('permno',as_index=False).last()
sz=db.raw_sql("select permno, abs(prc)*shrout/1000.0 as mcap_mm from crsp.dsf where date='2024-12-31' and prc is not null and shrout>0")
m=nm.merge(sz,on='permno',how='left')
m['sector']=pd.to_numeric(m['siccd'],errors='coerce').fillna(-1000)//1000; m['sector']=m['sector'].astype(int)
m['mcap_mm']=pd.to_numeric(m['mcap_mm'],errors='coerce').fillna(300.0)
ipo=m[m.st_date>='2019-01-01'].sample(min(1400,len(m[m.st_date>='2019-01-01'])),random_state=5)
smid=m[(m.mcap_mm>=100)&(m.mcap_mm<10000)&(m.st_date<'2016-01-01')].sample(1000,random_state=5)  # long-history names -> populate mature buckets
uni=pd.concat([ipo.assign(cohort='ipo'),smid.assign(cohort='smid')]); ids=",".join(str(int(x)) for x in uni.permno)
SEC={int(r.permno):int(r.sector) for r in uni.itertuples()}; MC={int(r.permno):float(r.mcap_mm) for r in uni.itertuples()}
lg("universe ipo=%d smid=%d; pulling returns %.0fs"%(len(ipo),len(smid),time.time()-t0))
rets=db.raw_sql(f"select permno,date,ret from crsp.dsf where permno in ({ids}) and date>='2010-01-01' and ret is not null")
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
for c in ['rv21','rv5','mean21','abs1']: D[c]=pd.to_numeric(D[c],errors='coerce')
D['rv5']=D['rv5'].fillna(D['rv21']).fillna(2.0); D['rv21']=D['rv21'].fillna(2.0)
D['mean21']=D['mean21'].fillna(0.0); D=D.dropna(subset=['lag1']); D['abs1']=D['abs1'].fillna(D['abs1'].median())
Xc=['lag1','abs1','rv5','rv21','mean21','dn','logmcap','sector','age']
# hold out 40% of BOTH cohorts so mature buckets are populated by held-out long-history names
rng=np.random.default_rng(7); allp=np.array([int(x) for x in uni.permno]); rng.shuffle(allp); hold=set(allp[:int(len(allp)*0.4)])
tr=D[~D.permno.isin(hold)]; TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
amq={}
for tau in TAUS:
    mdl=HistGradientBoostingRegressor(loss='quantile',quantile=tau,max_iter=250,max_depth=4,learning_rate=0.06); mdl.fit(tr[Xc].values,tr['y'].values); amq[tau]=mdl
lg("amort trained on %d rows %.0fs"%(len(tr),time.time()-t0))
te=D[D.permno.isin(hold)].sort_values(['permno','age']).reset_index(drop=True)
AM={tau:amq[tau].predict(te[Xc].values) for tau in TAUS}
tppf={tau:float(stats.t.ppf(tau,5)) for tau in TAUS}; tscale=math.sqrt(5/3.0)  # unit-var Student-t(5)
def pin(y,q,tau): d=y-q; return tau*d if d>=0 else (tau-1)*d
BUCK=[('d15_30',15,30),('d30_60',30,60),('d60_120',60,120),('d120_250',120,250),('d250_500',250,500),('d500_1000',500,1000),('d1000_2500',1000,2500)]
K=60.0  # shrinkage constant: w_own = age/(age+K)
agg={b[0]:{'am':0.0,'emp':0.0,'par':0.0,'bl':0.0,'n':0} for b in BUCK}
ages=te['age'].values; ys=te['y'].values; perm=te['permno'].values
ownlist={pn:g['y'].values for pn,g in te.groupby('permno')}
idxpos={}
for i in range(len(te)):
    pn=perm[i]; pos=idxpos.get(pn,0); idxpos[pn]=pos+1; a=ages[i]
    b=next((bb for bb in BUCK if bb[1]<=a<bb[2]),None)
    if b is None: continue
    own=ownlist[pn][:pos]
    if len(own)<12: continue
    own_w=own[-500:]  # cap window for cost
    y=ys[i]; mu=float(own_w.mean()); sd=float(own_w.std()) or 1.0
    w_own=pos/(pos+K)
    la=le=lp=lb=0.0
    for tau in TAUS:
        aq=float(AM[tau][i]); eq=float(np.quantile(own_w,tau)); pq=mu+sd*tppf[tau]/tscale
        bq=(1-w_own)*aq+w_own*eq
        la+=pin(y,aq,tau); le+=pin(y,eq,tau); lp+=pin(y,pq,tau); lb+=pin(y,bq,tau)
    n=len(TAUS); g=agg[b[0]]; g['am']+=la/n; g['emp']+=le/n; g['par']+=lp/n; g['bl']+=lb/n; g['n']+=1
out={'note':'Amortized(from characteristics) vs own expanding-empirical vs own EWMA/param-t vs HIERARCHICAL BLEND (w_own=age/(age+60)). Pinball avg over 7 taus, by listing-age bucket. Lower=better.',
     'n_heldout_names':len(hold),'n_train_rows':int(len(tr)),'shrinkage_K':K,'curve':{}}
for name,lo,hi in BUCK:
    g=agg[name]
    if g['n']<30: continue
    am=g['am']/g['n']; emp=g['emp']/g['n']; par=g['par']/g['n']; bl=g['bl']/g['n']
    best=min(am,emp,par,bl)
    out['curve'][name]=dict(n=g['n'],amortized=round(am,4),empirical=round(emp,4),param_t=round(par,4),blend=round(bl,4),
                            amort_vs_emp=round(am/emp,3),blend_vs_best_single=round(bl/min(am,emp,par),3),winner=['amort','emp','param','blend'][[am,emp,par,bl].index(best)])
json.dump(out,open(os.path.join(P,"amort_agecurve.json"),"w"),indent=2,default=str)
# chart
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    names=list(out['curve'].keys()); x=np.arange(len(names))
    fig,ax=plt.subplots(1,2,figsize=(15,5.5))
    for key,lab,col in [('amortized','amortized (transfer prior)','#d62728'),('empirical','own empirical','#1f77b4'),('param_t','own EWMA-t param','#7f7f7f'),('blend','hierarchical blend','#2ca02c')]:
        ax[0].plot(x,[out['curve'][n][key] for n in names],marker='o',label=lab,color=col,lw=2)
    ax[0].set_xticks(x); ax[0].set_xticklabels([n.replace('d','') for n in names],rotation=45); ax[0].set_xlabel('listing age (trading days)'); ax[0].set_ylabel('avg pinball loss (lower=better)')
    ax[0].set_title('Amortization edge vs age: transfer wins young, own-data catches up, blend dominates'); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].axhline(1.0,color='k',lw=.7,ls='--')
    ax[1].plot(x,[out['curve'][n]['amort_vs_emp'] for n in names],marker='s',color='#d62728',label='amortized / own-empirical')
    ax[1].plot(x,[out['curve'][n]['blend_vs_best_single'] for n in names],marker='^',color='#2ca02c',label='blend / best single method')
    ax[1].set_xticks(x); ax[1].set_xticklabels([n.replace('d','') for n in names],rotation=45); ax[1].set_xlabel('listing age (trading days)'); ax[1].set_ylabel('ratio (<1 = numerator better)')
    ax[1].set_title('Edge ratios: <1 means the method beats the benchmark'); ax[1].legend(); ax[1].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(os.path.join(P,"amort_agecurve.png"),dpi=120); plt.close()
except Exception as e: lg("chart err %s"%str(e)[:80])
lg("AMORT_AGECURVE\n"+json.dumps(out['curve'],indent=2,default=str)); lg("DONE %.0fs"%(time.time()-t0))
