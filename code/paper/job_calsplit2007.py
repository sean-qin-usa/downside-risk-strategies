# job_calsplit2007.py -- strict calendar cut INSIDE the holdout era, crisis fully out-of-sample.
# Train: strictly before 2007-01-01 for every name (GARCH fits, pooled learner). Test:
# 2007-01-01..2013 for every name -- so the 2008-09 crisis is entirely outside training,
# for every name simultaneously; no calendar overlap between any train and any test window.
# Buckets by BOTH (a) design-era frozen mk63 edges (real-time rule) and (b) within-sample
# qcut (for comparability with the published profile). NW-lag sensitivity on top bucket.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
CUT=pd.Timestamp("2007-01-01")
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
RAWX=['lag1','abs1','prv5','prv21','rv63']

# ---- design-era frozen mk63 edges (same construction as job_holdout_frozen) ----
def design_edges():
    rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
    rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
    cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
    vals=[]
    for pn in names:
        g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y)
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

# ---- holdout panel with 2007 calendar cut ----
rr=pd.read_csv(os.path.join(P,"holdout_panel_2000_2013.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
TR=[]; TE=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=pd.to_datetime(g['date'].values); n=len(y)
    sp=int(np.searchsorted(dts,CUT))
    if sp<750 or n-sp<250: continue
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
    df['idx']=np.arange(n); df=df.dropna(subset=RAWX+['mk63'])
    trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
    if len(tst)<100: continue
    TR.append(trn[RAWX+['y']])
    te=tst[RAWX+['y','sig','mk63','date']].copy(); te['mu']=mu; te['nu']=nu; te['tsc']=tsc; te['permno']=pn
    TE.append(te)
lg("panels %d (cut %s) %.0fs"%(len(TE),CUT.date(),time.time()-t0))
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
prof_q=[]
for d in range(10):
    m2=qdec==d
    prof_q.append(round(100*float(edge[m2].mean())/float(pl_g[m2].mean()),2) if m2.sum()>500 else None)
OUT={'note':'Calendar cut 2007-01-01 inside the holdout era: everything trained strictly pre-2007; test 2007-2013 (entire GFC out-of-sample for every name; no calendar overlap). Top/bottom buckets by design-era FROZEN mk63 edges (real-time rule) and within-sample qcut profile for comparability.',
     'cut':'2007-01-01','n_names':int(TEc.permno.nunique()),'n_test':int(len(Y)),
     'design_edges_mk63':[round(e,4) for e in EDGES],
     'overall':dm_on(np.ones(len(Y),bool)),
     'top_bucket_frozen':dm_on(topF),'bottom_bucket_frozen':dm_on(botF),
     'top_frozen_share_pct':round(100*float(topF.sum())/float(okm.sum()),1),
     'top_bucket_NWlag_sensitivity':{('lag%d'%L):dm_on(topF,L) for L in (5,10,20,44)},
     'decile_profile_qcut_edge_pct':prof_q}
json.dump(OUT,open(os.path.join(P,"calsplit2007_results.json"),"w"),indent=2)
lg("CAL2007DONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1)[:1500])
