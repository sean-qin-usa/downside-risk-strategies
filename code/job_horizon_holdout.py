# job_horizon_holdout.py -- the LAST registered analysis: horizon + ES comparison on 2000-2013.
# Directly-learned 10-day quantiles vs GARCH sqrt(h)-scaling on the holdout era (includes 2008).
# Mirrors the design-era horizon methodology: pooled amortized GBM on h-day-ahead cumulative
# returns with causal features; overlapping targets, so date-level DM uses NW lag 20.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
CACHE=os.path.join(P,"holdout_panel_2000_2013.csv")
H=10
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
EST=[0.005,0.01,0.015,0.02,0.025]   # tail grid for ES97.5 as tail average
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(CACHE,dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
RAWX=['lag1','abs1','prv5','prv21','rv63']
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
    sig=np.sqrt(s2); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    # h-day-ahead cumulative return, causal target: sum of y_{t}..y_{t+H-1} seen from t-1 features
    df['yH']=df['y'].rolling(H).sum().shift(-(H-1))
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=RAWX+['yH'])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TR.append(trn[RAWX+['yH']])
    TE.append(tst[RAWX+['yH','sig','date','mu','nu','tsc']])
lg("panels %d %.0fs"%(len(TE),time.time()-t0))
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
GQ={}
for t in sorted(set(TAUS+EST)):
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['yH'].values)
    GQ[t]=m.predict(TEc[RAWX].values)
    if t in (0.01,0.5,0.99): lg("  tau %.3f %.0fs"%(t,time.time()-t0))
Y=TEc['yH'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
pl_g=np.zeros(len(Y)); pl_b=np.zeros(len(Y))
for t in TAUS:
    gq=MU*H+math.sqrt(H)*SIG*stats.t.ppf(t,NU)/TSC     # sqrt(h) scaling under test
    pl_g+=pin(Y,gq,t); pl_b+=pin(Y,GQ[t],t)
pl_g/=len(TAUS); pl_b/=len(TAUS)
dates=TEc['date'].values
def nw_t(x,l=20):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
dd=pd.DataFrame({'d':pl_g-pl_b,'date':dates}).groupby('date')['d'].mean()
t_dm=nw_t(dd.values)
# ES97.5 at 10 days: predicted tail average vs realized conditional mean
q975_b=GQ[0.025]; es_b=np.mean([GQ[t] for t in EST],axis=0)
q975_g=MU*H+math.sqrt(H)*SIG*stats.t.ppf(0.025,NU)/TSC
qq=stats.t.ppf(0.025,NU); es_g=MU*H+math.sqrt(H)*SIG*(-stats.t.pdf(qq,NU)*(NU+qq*qq)/((NU-1)*0.025))/TSC
def es_block(q,es):
    b=Y<=q
    return {'breach975':round(float(b.mean()),4),
            'pred_ES':round(float(es.mean()),2),
            'realized_ES':round(float(Y[b].mean()),2) if b.any() else None}
out={'note':f'Horizon h={H} on the 2000-2013 holdout era: direct-learned {H}-day quantiles (pooled GBM, causal features) vs GARCH-t sqrt(h) scaling. Overlapping targets; date-level DM NW lag 20. edge_pct>0 = direct better.',
     'n_names':int(len(TE)),'n_test':int(len(Y)),'n_dates':int(len(dd)),
     'pinball_garch_sqrt_h':round(float(pl_g.mean()),4),'pinball_direct':round(float(pl_b.mean()),4),
     'edge_pct':round(100*float((pl_g-pl_b).mean())/float(pl_g.mean()),2),
     'DM_date_NW20':t_dm,
     'garch_sqrt_h_ES':es_block(q975_g,es_g),'direct_ES':es_block(q975_b,es_b)}
json.dump(out,open(os.path.join(P,"horizon_holdout_results.json"),"w"),indent=2)
lg("HORIZONHOLDOUTDONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
