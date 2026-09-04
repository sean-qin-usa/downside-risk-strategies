# job_stress_dm.py -- provenance addendum (adversarial review, wave 7): the manuscript
# quoted the out-of-era ten-day direct-model advantage as +0.65% (DM 0.22), carried over
# from the UNPURGED run; the purged stress_es_results.json implies ~0.5% and stores no DM.
# This job recomputes the holdout-era h=10 panel under the identical purged pipeline
# (same code path as frtb_stress_exact.py v2 / job_stress_purged.py), computes the exact
# pinball edge and the date-clustered NW(10) DM t-stat for direct-vs-GARCH and
# direct-vs-FHS, and writes them INTO stress_es_results.json (replacing the holdout block
# with the recomputed one so every quoted number traces to this one artifact).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
A=0.025; h=10
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
SUB=[A*(i+0.5)/20.0 for i in range(20)]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def t_es(a,nu):
    q=stats.t.ppf(a,nu)
    return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return float(x.mean()/math.sqrt(max(v/n,1e-16)))
FEAT=['prv5','prv21','rv63','logsig','absz5']
rr=pd.read_csv(os.path.join(P,"holdout_panel_2000_2013.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
rr=rr.dropna(subset=['ret'])
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
TRr=[]; TEr=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    ycum=pd.Series(y).rolling(h).sum().shift(-(h-1)).values
    df=pd.DataFrame({'yc':ycum,'sig':sig,'date':dts,'idx':np.arange(n)})
    df['prv5']=pd.Series(y).rolling(5,min_periods=3).std().shift(1); df['prv21']=pd.Series(y).rolling(21,min_periods=8).std().shift(1)
    df['rv63']=pd.Series(y).rolling(63,min_periods=20).std().shift(1); df['logsig']=np.log(np.maximum(sig,1e-6))
    df['absz5']=pd.Series(np.abs(z)).rolling(5,min_periods=3).mean().shift(1)
    df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    ztr=z[:sp]
    for t in TAUS: df['fhs_%g'%t]=float(np.quantile(ztr,t))
    qa=np.quantile(ztr,A); df['fhsES']=float(np.mean(ztr[ztr<=qa]))
    dd=df.dropna(subset=FEAT+['yc'])
    trn=dd[dd['idx']<sp-(h-1)]        # PURGE: label window t..t+h-1 must end before sp
    tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TRr.append(trn[FEAT+['yc']]); t2=tst.copy(); t2['permno']=pn; TEr.append(t2)
TR=pd.concat(TRr); TE=pd.concat(TEr).reset_index(drop=True)
lg("panel h=%d: %d names, %d test rows %.0fs"%(h,TE['permno'].nunique(),len(TE),time.time()-t0))
GQ={}
for t in TAUS:
    GQ[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR[FEAT].values,TR['yc'].values).predict(TE[FEAT].values)
GES=[]
for u in SUB:
    GES.append(HistGradientBoostingRegressor(loss='quantile',quantile=u,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR[FEAT].values,TR['yc'].values).predict(TE[FEAT].values))
ES_gbm=np.mean(GES,axis=0)
Y=TE['yc'].values; SIGh=TE['sig'].values*math.sqrt(h); MUh=TE['mu'].values*h; NU=TE['nu'].values; TSC=TE['tsc'].values
Q={'garch_scale':{t:MUh+SIGh*stats.t.ppf(t,NU)/TSC for t in TAUS},
   'fhs':{t:MUh+SIGh*TE['fhs_%g'%t].values for t in TAUS},
   'hybrid_GBM':{t:GQ[t] for t in TAUS}}
ES={'garch_scale':MUh+SIGh*np.array([t_es(A,nu_)/ts_ for nu_,ts_ in zip(NU,TSC)]),
    'fhs':MUh+SIGh*TE['fhsES'].values,
    'hybrid_GBM':ES_gbm}
PL={}
for m in Q:
    pl=np.zeros(len(Y))
    for t in TAUS: pl+=pin(Y,Q[m][t],t)
    PL[m]=pl/len(TAUS)
dates=TE['date'].values
def dm(a,b):
    d=pd.DataFrame({'d':PL[a]-PL[b],'date':dates}).groupby('date')['d'].mean()
    t=nw_t(d.values); return None if t is None else round(t,2)
blk={}
for m in Q:
    b975=(Y<Q[m][A])
    blk[m]=dict(pinball=round(float(PL[m].mean()),4),
                ES975_pred_true=round(float(ES[m].mean()),3),
                ES975_real_ownVaR=round(float(Y[b975].mean()),3) if b975.sum() else None,
                breach975=round(float(b975.mean()),4),n=int(len(Y)))
edge_g=100.0*(PL['garch_scale'].mean()-PL['hybrid_GBM'].mean())/PL['garch_scale'].mean()
edge_f=100.0*(PL['fhs'].mean()-PL['hybrid_GBM'].mean())/PL['fhs'].mean()
add={'edge_pct_direct_vs_garch':round(float(edge_g),3),'DM_t_direct_vs_garch':dm('garch_scale','hybrid_GBM'),
     'edge_pct_direct_vs_fhs':round(float(edge_f),3),'DM_t_direct_vs_fhs':dm('fhs','hybrid_GBM')}
fp=os.path.join(P,"stress_es_results.json")
J=json.load(open(fp))
J['holdout_2000_2013_h10']={'all':blk,**add}
J['note']=J['note']+" Wave-7 addendum: holdout block recomputed by job_stress_dm.py with exact edge percentages and date-clustered NW(10) DM t-stats stored in-artifact."
json.dump(J,open(fp,"w"),indent=2)
lg(json.dumps({'holdout':blk,'add':add},indent=1))
lg("STRESSDMDONE %.0fs"%(time.time()-t0))
