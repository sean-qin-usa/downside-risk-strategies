# job_wrds_holdout.py -- THE UNTOUCHED-ERA HOLDOUT (frozen specification; referee point 1.7 / forking paths).
# Terminology note: the paper deliberately avoids the word 'registered' -- no third-party
# timestamp exists for this freeze; the claim is line-for-line diffability against the
# design-era pipeline, plus the predictions written in advance below.
# Pulls CRSP daily returns 2000-2013 -- an era NO prior run in this program has touched
# (existing panels are 2014+ / 2016+) -- and runs the FROZEN frontier specification on it:
# same signals (.shift(1) causal), same features, same GBM hyperparameters, same 60/40
# per-name temporal split, same date-level NW DM. Nothing tuned on this data, ever.
# Predictions written in advance: (i) top-mk63-decile edge positive and significant, bottom ~0;
# (ii) overall edge small positive; (iii) decile profile qualitatively matches Table 2.
# Data stays LOCAL (holdout_panel_2000_2013.csv is gitignored; CRSP no-redistribution).
import builtins, os, json, time, math, warnings; warnings.filterwarnings("ignore")
# Reproducibility: set WRDS_USERNAME to your own WRDS login and (optionally) GBC_PROJECT_DIR to
# your local data directory. The wrds package reads the password from your platform's standard
# pgpass file (~/.pgpass on POSIX, %APPDATA%\postgresql\pgpass.conf on Windows); none is stored here.
WRDS_USER=os.environ.get('WRDS_USERNAME','YOUR_WRDS_USERNAME')
def _fi(p=''):
    s=str(p).lower(); return WRDS_USER if 'username' in s else 'n'
builtins.input=_fi
os.environ.setdefault('PGUSER', WRDS_USER)
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=os.environ.get('GBC_PROJECT_DIR', os.path.dirname(os.path.abspath(__file__))); t0=time.time(); lg=lambda s:print(s,flush=True)
OUTJ=os.path.join(P,"holdout_frontier_results.json")
CACHE=os.path.join(P,"holdout_panel_2000_2013.csv")

# ---------- pull (cached) ----------
if not os.path.exists(CACHE):
    import wrds
    db=wrds.Connection(wrds_username=WRDS_USER); lg("WRDS CONNECTED %ds"%(time.time()-t0))
    cand=db.raw_sql("""
        select a.permno, count(*) as n, avg(abs(a.prc)*a.shrout) as mc
        from crsp.dsf a
        where a.date between '2000-01-03' and '2013-12-31' and a.ret is not null
        group by a.permno having count(*) >= 3000
    """)
    lg(f"candidates {len(cand)} {time.time()-t0:.0f}s")
    shr=db.raw_sql("select distinct permno from crsp.stocknames where shrcd in (10,11)")
    cand=cand[cand.permno.isin(set(shr.permno))]
    top=cand.sort_values('mc',ascending=False).head(200)
    ids=",".join(str(int(x)) for x in top.permno)
    rr=db.raw_sql(f"select permno,date,ret from crsp.dsf where permno in ({ids}) and date between '2000-01-03' and '2013-12-31' and ret is not null")
    db.close()
    rr.to_csv(CACHE,index=False); lg(f"pulled {len(rr):,} rows, {rr.permno.nunique()} names {time.time()-t0:.0f}s")
rr=pd.read_csv(CACHE,dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
lg(f"holdout panel: {len(rr):,} rows, {rr.permno.nunique()} names, {rr.date.min().date()}..{rr.date.max().date()}")

# ---------- FROZEN SPEC (verbatim from audited misspec_frontier.py + date-level DM) ----------
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
RAWX=['lag1','abs1','prv5','prv21','rv63']
TR=[]; TE=[]; META=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().shift(1).abs()
    df['idx']=np.arange(n); df=df.dropna()
    trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
    if len(tst)<30: continue
    TR.append(trn[RAWX+['y']])
    te=tst[RAWX+['y','sig','mk63','jump5','skew63','date']].copy(); te['mu']=mu; te['nu']=nu; te['tsc']=tsc
    TE.append(te); META.append(pn)
lg("panels %d names %.0fs"%(len(META),time.time()-t0))
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
GQ={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values)
    GQ[t]=m.predict(TEc[RAWX].values)
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
pl_g=np.zeros(len(Y)); pl_b=np.zeros(len(Y))
for t in TAUS:
    gq=MU+SIG*stats.t.ppf(t,NU)/TSC
    pl_g+=pin(Y,gq,t); pl_b+=pin(Y,GQ[t],t)
pl_g/=len(TAUS); pl_b/=len(TAUS)
edge=pl_g-pl_b
def dm_on(mask):
    d=pd.DataFrame({'d':edge[mask],'date':TEc['date'].values[mask]}).groupby('date')['d'].mean().values
    d=d[np.isfinite(d)]
    if len(d)<20: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,11): v+=2*(1-k/11)*np.mean(dd[k:]*dd[:-k])
    v/=len(d); s=d.mean()/math.sqrt(max(v,1e-12))
    return dict(mean_edge=round(float(d.mean()),5),edge_pct=round(100*float(d.mean())/float(pl_g[mask].mean()),2),
                DM_stat=round(float(s),2),p_one_sided=round(float(1-stats.norm.cdf(s)),4),n_dates=int(len(d)))
def frontier(sig_name):
    s=TEc[sig_name].values; ok=np.isfinite(s)
    dec=pd.qcut(s[ok],10,labels=False,duplicates='drop')
    rows=[]
    for d in sorted(np.unique(dec)):
        m2=np.zeros(len(Y),bool); m2[np.where(ok)[0][dec==d]]=True
        rows.append(dict(decile=int(d)+1,edge_pct=round(100*float(edge[m2].mean())/float(pl_g[m2].mean()),2),n=int(m2.sum())))
    return rows
mk=TEc['mk63'].values; okm=np.isfinite(mk); decm=pd.qcut(mk[okm],10,labels=False,duplicates='drop')
top=np.zeros(len(Y),bool); top[np.where(okm)[0][decm==decm.max()]]=True
bot=np.zeros(len(Y),bool); bot[np.where(okm)[0][decm==0]]=True
OUT={'note':'CONFIRMATORY HOLDOUT 2000-2013 (untouched era), FROZEN spec from misspec_frontier.py; registered predictions in header.',
     'n_names':len(META),'n_test':int(len(Y)),
     'overall':dm_on(np.ones(len(Y),bool)),'top_decile_mk63':dm_on(top),'bottom_decile_mk63':dm_on(bot),
     'deciles_mk63':frontier('mk63'),'deciles_skew63':frontier('skew63'),'deciles_jump5':frontier('jump5')}
json.dump(OUT,open(OUTJ,"w"),indent=2)
lg("HOLDOUTDONE %.0fs "%(time.time()-t0)+json.dumps({k:OUT[k] for k in ['overall','top_decile_mk63','bottom_decile_mk63']}))
