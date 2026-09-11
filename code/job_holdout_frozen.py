# job_holdout_frozen.py -- kills the "future-informed qcut" attack on the holdout.
# The holdout frontier previously bucketed mk63 by pd.qcut over the WHOLE holdout test
# sample (boundaries a function of the full test era). This job re-runs the holdout
# top/bottom-bucket tests with NUMERIC THRESHOLDS FROZEN FROM THE DESIGN ERA:
# the design panel's pooled test-sample mk63 decile edges (the published Table-2
# partition) applied to the holdout as fixed constants. Membership at (name, day)
# then depends only on that name's own past 63 days and a constant known before any
# holdout day is scored -- a rule implementable in real time.
# Also reports NW-lag sensitivity (5/10/20/44) for the top-bucket DM.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
RAWX=['lag1','abs1','prv5','prv21','rv63']

def build_panel(csvpath):
    rr=pd.read_csv(csvpath,dtype={'permno':'int32'})
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
        df['idx']=np.arange(n); df=df.dropna(subset=RAWX+['mk63'])
        trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
        if len(tst)<30: continue
        TR.append(trn[RAWX+['y']])
        te=tst[RAWX+['y','sig','mk63','date']].copy(); te['mu']=mu; te['nu']=nu; te['tsc']=tsc
        TE.append(te)
    return pd.concat(TR), pd.concat(TE).reset_index(drop=True)

# ---- 1. design-era frozen edges: pooled test-sample mk63 decile boundaries ----
lg("building DESIGN panel for frozen edges...")
_,TEd=build_panel(os.path.join(P,"crsp_panel_returns.csv"))
mkd=TEd['mk63'].values; mkd=mkd[np.isfinite(mkd)]
EDGES=[float(np.percentile(mkd,q)) for q in range(10,100,10)]   # 9 interior boundaries
lg("design-era mk63 decile edges: "+", ".join("%.4f"%e for e in EDGES)+"  (%.0fs)"%(time.time()-t0))

# ---- 2. holdout panel (cached), frozen spec ----
lg("building HOLDOUT panel...")
TRc,TEc=build_panel(os.path.join(P,"holdout_panel_2000_2013.csv"))
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
# frozen-edge bins: bin b = (EDGES[b-1], EDGES[b]] with bin 0 = (-inf, EDGES[0]], bin 9 = (EDGES[8], inf)
binid=np.digitize(np.where(okm,mk,np.nan),EDGES)   # 0..9, nan->9 but masked by okm
top=okm & (binid==9); bot=okm & (binid==0)
profile=[]
for b in range(10):
    m2=okm & (binid==b)
    profile.append(dict(bin=b+1,share_pct=round(100*float(m2.sum())/float(okm.sum()),1),
                        edge_pct=(round(100*float(edge[m2].mean())/float(pl_g[m2].mean()),2) if m2.sum()>500 else None),
                        n=int(m2.sum())))
lag_sens={('lag%d'%L):dm_on(top,L) for L in (5,10,20,44)}
OUT={'note':'Holdout 2000-2013 frontier with mk63 thresholds FROZEN from the design era (pooled design test-sample decile edges applied as numeric constants). No holdout-era quantities enter the bucketing rule. Top bucket = mk63 >= design-era 90th pct; bottom = < 10th pct. Bin shares in the holdout will differ from 10% by construction and are reported.',
     'design_edges_mk63':[round(e,4) for e in EDGES],
     'n_test':int(len(Y)),'overall':dm_on(np.ones(len(Y),bool)),
     'top_bucket_frozen':dm_on(top),'bottom_bucket_frozen':dm_on(bot),
     'top_bucket_NWlag_sensitivity':lag_sens,
     'profile_frozen_bins':profile}
json.dump(OUT,open(os.path.join(P,"holdout_frozen_results.json"),"w"),indent=2)
lg("HOLDFROZENDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1)[:1500])
