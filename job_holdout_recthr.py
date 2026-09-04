# job_holdout_recthr.py -- RECURSIVE EX-ANTE THRESHOLD on the 2000-2013 holdout.
# The frozen design-era threshold preserved the holdout's threshold shape but thinned
# the top cell to 3.3% occupancy (DM 1.11). The referee-requested alternative is a
# recursive rule a desk could run from day one WITHOUT any design-era constant:
# on each date t, the top bucket is { mk63_it >= 90th percentile of ALL pooled mk63
# observed on dates < t }, expanding window, 250-date burn-in. Membership uses only
# past data; occupancy self-adapts to the era (~10% by construction after burn-in).
# Reports top/bottom recursive-bucket per-date DM with NW-lag sensitivity.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
RAWX=['lag1','abs1','prv5','prv21','rv63']
rr=pd.read_csv(os.path.join(P,"holdout_panel_2000_2013.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
TR=[]; TE=[]
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
    df['idx']=np.arange(n); df['insamp']=(df['idx']<sp).astype(int)
    df=df.dropna(subset=RAWX+['mk63'])
    trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
    if len(tst)<30: continue
    TR.append(trn[RAWX+['y']])
    te=tst[RAWX+['y','sig','mk63','date']].copy(); te['mu']=mu; te['nu']=nu; te['tsc']=tsc; te['permno']=pn
    TE.append(te)
lg("panels %d %.0fs"%(len(TE),time.time()-t0))
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
# expanding pooled 90th percentile of mk63 over ALL panel observations at dates < t
# (a desk sees the whole panel's history to date, train and test alike)
frames=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
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
    frames.append(pd.DataFrame({'date':dts,'mk':mk}))
AM=pd.concat(frames).dropna()
AM['date']=pd.to_datetime(AM['date'])
lg("pooled mk63 history rows %d %.0fs"%(len(AM),time.time()-t0))
# expanding q90/q10 per date over strictly earlier dates
udates=np.sort(AM['date'].unique())
AMs=AM.sort_values('date'); vals=AMs['mk'].values; dts_sorted=AMs['date'].values
cutidx=np.searchsorted(dts_sorted,udates)   # first index at each date -> values before are strictly earlier
q90=np.full(len(udates),np.nan); q10=np.full(len(udates),np.nan)
BURN=250
for i in range(len(udates)):
    m5=cutidx[i]
    if i>=BURN and m5>=5000:
        q90[i]=np.quantile(vals[:m5],0.90); q10[i]=np.quantile(vals[:m5],0.10)
thrmap9=pd.Series(q90,index=udates); thrmap1=pd.Series(q10,index=udates)
GQ={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values)
    GQ[t]=m.predict(TEc[RAWX].values)
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
pl_g=np.mean([pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t) for t in TAUS],axis=0)
pl_b=np.mean([pin(Y,GQ[t],t) for t in TAUS],axis=0)
edge=pl_g-pl_b
tdt=pd.to_datetime(TEc['date'].values)
thr9=thrmap9.reindex(tdt).values; thr1=thrmap1.reindex(tdt).values
mk=TEc['mk63'].values
ok=np.isfinite(mk)&np.isfinite(thr9)
top=ok&(mk>=thr9); bot=ok&np.isfinite(thr1)&(mk<=thr1)
def dm_on(mask,lag=10):
    d=pd.DataFrame({'d':edge[mask],'date':TEc['date'].values[mask]}).groupby('date')['d'].mean().values
    d=d[np.isfinite(d)]
    if len(d)<20: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(dd[k:]*dd[:-k])
    v/=len(d); s=d.mean()/math.sqrt(max(v,1e-12))
    return dict(edge_pct=round(100*float(edge[mask].mean())/float(pl_g[mask].mean()),2),
                DM_stat=round(float(s),2),p_one_sided=round(float(1-stats.norm.cdf(s)),4),n_dates=int(len(d)))
OUT={'note':'Recursive ex-ante threshold on the 2000-2013 holdout: top bucket = mk63 >= expanding pooled 90th percentile over strictly earlier dates (250-date burn-in); no design-era constant, no test-era ranks. Membership computable in real time on day one of the test window.',
     'n_test':int(len(Y)),'n_scored':int(ok.sum()),
     'top_share_pct':round(100*float(top.sum())/float(ok.sum()),1),
     'top_recursive':dm_on(top),'bottom_recursive':dm_on(bot),
     'top_NWlag_sensitivity':{('lag%d'%L):dm_on(top,L) for L in (5,10,20,44)},
     'overall':dm_on(np.ones(len(Y),bool))}
json.dump(OUT,open(os.path.join(P,"holdout_recthr_results.json"),"w"),indent=2)
lg("RECTHRDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1))
