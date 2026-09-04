# job_timing_diag.py -- frontier TIMING DIAGNOSTICS table (referee-proofing for point 1.1).
# The audited code lags every signal one day (.shift(1)); this job makes the timing claim an
# EXHIBIT: re-runs the frontier with the mk63 signal at alignments
#   lag1   = deployed spec, S_{t-1} -> loss_t   (should show the edge)
#   lag5   = S_{t-5} -> loss_t                  (edge should persist, attenuated)
#   lag0   = contaminated same-day window incl. z_t (diagnostic of contamination size)
#   lead1  = S_{t+1} -> loss_t, deliberately invalid placebo (edge should NOT exceed lag1;
#            a placebo beating the deployed signal would indicate mechanical sorting)
# Uses the local crsp_panel_returns.csv; frozen features/hyperparams from misspec_frontier.py.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
RAWX=['lag1','abs1','prv5','prv21','rv63']
ALIGN={'lag1':1,'lag5':5,'lag0':0,'lead1':-1}
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
    mkraw=df['z'].rolling(63,min_periods=30).kurt()
    for nm,sh in ALIGN.items(): df['mk_'+nm]=mkraw.shift(sh)
    df['mu']=mu; df['nu']=nu; df['tsc']=tsc; df['idx']=np.arange(n)
    dd=df.dropna(subset=RAWX+['mk_lag1'])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<30: continue
    TR.append(trn[RAWX+['y']]); TE.append(tst[RAWX+['y','sig','mu','nu','tsc','date']+['mk_'+k for k in ALIGN]])
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
lg("panels %d rows %.0fs"%(len(TEc),time.time()-t0))
GQ={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values).predict(TEc[RAWX].values) for t in TAUS}
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values
pg=np.zeros(len(Y)); pb=np.zeros(len(Y))
for t in TAUS: pg+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t); pb+=pin(Y,GQ[t],t)
pg/=len(TAUS); pb/=len(TAUS); edge=pg-pb
def dm_on(mask):
    d=pd.DataFrame({'d':edge[mask],'date':TEc['date'].values[mask]}).groupby('date')['d'].mean().values
    d=d[np.isfinite(d)]
    if len(d)<20: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,11): v+=2*(1-k/11)*np.mean(dd[k:]*dd[:-k])
    v/=len(d); s=d.mean()/math.sqrt(max(v,1e-12))
    return dict(edge_pct=round(100*float(d.mean())/float(pg[mask].mean()),2),DM=round(float(s),2),n_dates=int(len(d)))
OUT={'note':'Timing diagnostics: top-mk63-decile edge under signal alignments. lag1=deployed; lag5=persistence; lag0=contaminated diagnostic; lead1=invalid placebo.'}
for nm in ALIGN:
    s=TEc['mk_'+nm].values; ok=np.isfinite(s)
    dec=np.full(len(Y),-1); dec[ok]=pd.qcut(s[ok],10,labels=False,duplicates='drop')
    OUT[nm]={'top_decile':dm_on(dec==dec.max()),'bottom_decile':dm_on(dec==0)}
    lg(f"{nm}: {json.dumps(OUT[nm])}")
json.dump(OUT,open(os.path.join(P,"timing_diag_results.json"),"w"),indent=2)
lg("TIMINGDIAGDONE %.0fs"%(time.time()-t0))
