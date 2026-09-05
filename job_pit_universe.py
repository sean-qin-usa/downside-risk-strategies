# job_pit_universe.py -- POINT-IN-TIME holdout universe (kills the survivor-selection attack).
# The original holdout selected top-200 names by market cap averaged over the FULL 2000-2013
# window with a >=3000-obs filter -- selection uses information (survival, size) from after
# the evaluation start. This job selects the universe AS OF THE START: top 200 by average
# market cap over 2000-01-03..2000-03-31 among share codes 10/11, with NO minimum-history
# filter. Names that later delist STAY IN through their delisting date, with the CRSP
# delisting return appended as the final observation. The only later-dated requirements are
# model-fitting floors applied SYMMETRICALLY to both models (>=750 train obs to fit a GARCH,
# >=100 test obs to score), and attrition is reported. Frozen spec otherwise; frozen
# design-era mk63 edges for the real-time top bucket; qcut profile for comparability.
import builtins, os, json, time, math, warnings; warnings.filterwarnings("ignore")
def _fi(p=''):
    s=str(p).lower(); return os.environ.get('WRDS_USERNAME','YOUR_WRDS_USERNAME') if 'username' in s else 'n'
builtins.input=_fi
os.environ.setdefault('PGUSER', os.environ.get('WRDS_USERNAME','YOUR_WRDS_USERNAME'))  # WRDS reads the password from your standard pgpass file
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=os.environ.get('GBC_PROJECT_DIR', os.path.dirname(os.path.abspath(__file__))); t0=time.time(); lg=lambda s:print(s,flush=True)
CACHE=os.path.join(P,"pit_panel_2000_2013.csv")
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
RAWX=['lag1','abs1','prv5','prv21','rv63']

# ---------- pull (cached): universe fixed at Q1-2000, delistings kept ----------
if not os.path.exists(CACHE):
    import wrds
    db=wrds.Connection(wrds_username=os.environ.get('WRDS_USERNAME','YOUR_WRDS_USERNAME')); lg("WRDS CONNECTED %ds"%(time.time()-t0))
    cand=db.raw_sql("""
        select a.permno, avg(abs(a.prc)*a.shrout) as mc, count(*) as n
        from crsp.dsf a
        where a.date between '2000-01-03' and '2000-03-31' and a.ret is not null and a.prc is not null
        group by a.permno
    """)
    lg(f"Q1-2000 candidates {len(cand)} {time.time()-t0:.0f}s")
    shr=db.raw_sql("select distinct permno from crsp.stocknames where shrcd in (10,11)")
    cand=cand[cand.permno.isin(set(shr.permno))]
    top=cand.sort_values('mc',ascending=False).head(200)
    ids=",".join(str(int(x)) for x in top.permno)
    rr=db.raw_sql(f"select permno,date,ret from crsp.dsf where permno in ({ids}) and date between '2000-01-03' and '2013-12-31' and ret is not null")
    dl=db.raw_sql(f"select permno,dlstdt,dlret from crsp.dsedelist where permno in ({ids}) and dlstdt between '2000-01-03' and '2013-12-31'")
    db.close()
    dl=dl.dropna(subset=['dlret'])
    if len(dl):
        add=pd.DataFrame({'permno':dl['permno'].values,'date':dl['dlstdt'].values,'ret':dl['dlret'].values})
        rr=pd.concat([rr,add],ignore_index=True)
    rr.to_csv(CACHE,index=False)
    json.dump({'n_selected':200,'n_delist_events':int(len(dl))},open(os.path.join(P,"pit_pull_meta.json"),"w"))
    lg(f"pulled {len(rr):,} rows, {rr.permno.nunique()} names, {len(dl)} delisting returns appended {time.time()-t0:.0f}s")
rr=pd.read_csv(CACHE,dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
rr=rr.dropna(subset=['ret'])
lg(f"PIT panel: {len(rr):,} rows, {rr.permno.nunique()} names, {rr.date.min().date()}..{rr.date.max().date()}")

# ---------- design-era frozen mk63 edges ----------
def design_edges():
    r2=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
    r2['date']=pd.to_datetime(r2['date']); r2['ret']=pd.to_numeric(r2['ret'],errors='coerce')*100.0
    cnt=r2.groupby('permno')['ret'].count().sort_values(ascending=False); nm=cnt[cnt>=1500].index.tolist()[:200]
    vals=[]
    for pn in nm:
        g=r2[r2.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y)
        if n<1500: continue
        sp=int(n*0.6)
        try:
            res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
            p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0))
        except Exception: continue
        e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
        for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
        z=(y-mu)/np.maximum(np.sqrt(s2),1e-6)
        mk=pd.Series(z).rolling(63,min_periods=30).kurt().shift(1).values
        vals.append(mk[sp:])
    v=np.concatenate(vals); v=v[np.isfinite(v)]
    return [float(np.percentile(v,q)) for q in range(10,100,10)]
EDGES=design_edges()
lg("design edges: "+", ".join("%.3f"%e for e in EDGES)+" (%.0fs)"%(time.time()-t0))

# ---------- frozen spec on the PIT panel (60/40 per-name split as in the holdout) ----------
names=rr.groupby('permno')['ret'].count().sort_values(ascending=False).index.tolist()
TR=[]; TE=[]; n_short=0
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    sp=int(n*0.6)
    if sp<750 or n-sp<100:
        n_short+=1; continue
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception:
        n_short+=1; continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['idx']=np.arange(n); df=df.dropna(subset=RAWX+['mk63'])
    trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
    if len(tst)<30:
        n_short+=1; continue
    TR.append(trn[RAWX+['y']])
    te=tst[RAWX+['y','sig','mk63','date']].copy(); te['mu']=mu; te['nu']=nu; te['tsc']=tsc; te['permno']=pn
    TE.append(te)
lg("panels %d kept, %d dropped by fitting floors %.0fs"%(len(TE),n_short,time.time()-t0))
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
GQ={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values)
    GQ[t]=m.predict(TEc[RAWX].values)
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
pl_g=np.mean([pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t) for t in TAUS],axis=0)
pl_b=np.mean([pin(Y,GQ[t],t) for t in TAUS],axis=0)
edge=pl_g-pl_b
def dm_on(mask,lag=10):
    d=pd.DataFrame({'d':edge[mask],'date':TEc['date'].values[mask]}).groupby('date')['d'].mean().values
    d=d[np.isfinite(d)]
    if len(d)<20: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(dd[k:]*dd[:-k])
    v/=len(d); s=d.mean()/math.sqrt(max(v,1e-12))
    return dict(edge_pct=round(100*float(edge[mask].mean())/float(pl_g[mask].mean()),2),
                DM_stat=round(float(s),2),p_one_sided=round(float(1-stats.norm.cdf(s)),4),n_dates=int(len(d)))
mk=TEc['mk63'].values; okm=np.isfinite(mk)
binid=np.digitize(np.where(okm,mk,np.nan),EDGES)
topF=okm&(binid==9); botF=okm&(binid==0)
qdec=np.full(len(mk),-1); qdec[okm]=pd.qcut(mk[okm],10,labels=False,duplicates='drop')
prof_q=[(round(100*float(edge[qdec==d].mean())/float(pl_g[qdec==d].mean()),2) if (qdec==d).sum()>500 else None) for d in range(10)]
# delisted names present in test?
try:
    meta=json.load(open(os.path.join(P,"pit_pull_meta.json")))
except Exception:
    meta={}
OUT={'note':'POINT-IN-TIME universe: top 200 by Q1-2000 market cap (shrcd 10/11), NO minimum-history filter, delisting returns appended; names ride to their delisting date. Fitting floors (>=750 train obs, >=100 test obs) applied symmetrically to both models; attrition reported. Frozen spec; frozen design-era mk63 edges for the real-time top bucket.',
     'universe_rule':'top 200 avg mcap 2000-01-03..2000-03-31',
     'pull_meta':meta,'n_names_kept':int(TEc.permno.nunique()),'n_dropped_fitting_floor':int(n_short),
     'n_test':int(len(Y)),
     'overall':dm_on(np.ones(len(Y),bool)),
     'top_bucket_frozen':dm_on(topF),'bottom_bucket_frozen':dm_on(botF),
     'top_frozen_share_pct':round(100*float(topF.sum())/float(okm.sum()),1),
     'decile_profile_qcut_edge_pct':prof_q,
     'design_edges_mk63':[round(e,4) for e in EDGES]}
json.dump(OUT,open(os.path.join(P,"pit_universe_results.json"),"w"),indent=2)
lg("PITDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1)[:1500])
