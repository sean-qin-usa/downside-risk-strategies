# job_absorb.py -- CAN A PARAMETRIC-ADJACENT MODEL ABSORB THE FRONTIER SIGNAL?
# The thesis says the pooled nonparametric shape model wins where residual-shape
# misspecification (mk63) is high. The natural rebuttal: maybe mk63 is just an omitted
# variable, and a simple state-conditioned FHS -- reweighting the historical z window
# toward days with similar mk63 -- captures the same edge without any pooled learner.
# This job tests that rebuttal on the design panel. Entrants at the 11-tau pinball battery:
#   garch_t     : parametric baseline
#   fhs         : per-name filtered historical simulation (train z, unweighted)
#   fhs_mk63    : per-name FHS with Gaussian-kernel weights on |mk63_train - mk63_today|
#   pooled_z    : the engine's pooled shape stage (GBM on ZX incl. state, no EVT/conformal)
# Read-out: top-mk63-decile pinball + date-level DM of (fhs_mk63 - fhs) and (pooled_z - fhs_mk63).
# If fhs_mk63 closes most of the gap, the signal is absorbable (report honestly);
# if pooled_z stays ahead, the flexible shape model matters beyond the univariate signal.
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
ZX=['logsig','zl1','absz5','zstd21','fracdn5','mk63','skew63','jump5']
TRz=[]; rows=[]
def wq(zs,w,taus):
    o=np.argsort(zs); z=zs[o]; ww=np.maximum(w[o],0)
    cw=np.cumsum(ww); tot=cw[-1]
    if tot<=0: return {t:np.quantile(zs,t) for t in taus}
    return {t: float(z[np.searchsorted(cw, t*tot, side='left').clip(0,len(z)-1)]) for t in taus}
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
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().shift(1).abs()
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(trn)<300: continue
    TRz.append(trn[ZX+['z']])
    ztr=trn['z'].values; mtr=trn['mk63'].values
    bw=max(float(np.nanstd(mtr))/2.0,1e-3)
    qs_fhs={t:float(np.quantile(ztr,t)) for t in TAUS}
    t2=tst[['y','sig','date','mu','nu','tsc','mk63']+ZX].copy(); t2['permno']=pn
    # fhs (static) quantiles
    for t in TAUS: t2[f'fhs_{t}']=mu+t2['sig']*qs_fhs[t]
    # mk63-kernel-reweighted FHS, row by row (vectorized kernel per row-block)
    mk=t2['mk63'].values
    W=np.exp(-0.5*((mk[:,None]-mtr[None,:])/bw)**2)     # ntest x ntrain
    qmat={t:np.empty(len(t2)) for t in TAUS}
    for i in range(len(t2)):
        qi=wq(ztr,W[i],TAUS)
        for t in TAUS: qmat[t][i]=qi[t]
    for t in TAUS: t2[f'fhsw_{t}']=mu+t2['sig']*qmat[t]
    rows.append(t2)
lg("panels %d %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz)
ZQ={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=m.predict(TE[ZX].values)
    if t in (0.01,0.5,0.99): lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
L={}
L['garch_t']=np.mean([pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t) for t in TAUS],axis=0)
L['fhs']=np.mean([pin(Y,TE[f'fhs_{t}'].values,t) for t in TAUS],axis=0)
L['fhs_mk63']=np.mean([pin(Y,TE[f'fhsw_{t}'].values,t) for t in TAUS],axis=0)
L['pooled_z']=np.mean([pin(Y,MU+SIG*ZQ[t],t) for t in TAUS],axis=0)
dates=TE['date'].values; mk=TE['mk63'].values
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
def dm(a,b,mask=None):
    d=L[a]-L[b]
    if mask is not None: d=np.where(mask,d,np.nan)
    s=pd.DataFrame({'d':d,'date':dates}).dropna().groupby('date')['d'].mean()
    return {'mean_diff':round(float(np.nanmean(d)),5),'DM_t':nw_t(s.values),'n_dates':int(len(s))}
thr=np.nanquantile(mk,0.9); top=np.isfinite(mk)&(mk>=thr)
out={'note':'Absorption test: does mk63-kernel-reweighted FHS absorb the frontier signal? DM_t>0 in a_vs_b means model a has HIGHER loss (b better). Pinball = 11-tau average.',
     'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),
     'mean_pinball':{k:round(float(np.nanmean(v)),5) for k,v in L.items()},
     'top_decile_mean_pinball':{k:round(float(np.nanmean(v[top])),5) for k,v in L.items()},
     'overall':{'fhs_vs_fhs_mk63':dm('fhs','fhs_mk63'),'fhs_mk63_vs_pooled':dm('fhs_mk63','pooled_z'),'fhs_vs_pooled':dm('fhs','pooled_z'),'garch_vs_pooled':dm('garch_t','pooled_z')},
     'top_mk63_decile':{'fhs_vs_fhs_mk63':dm('fhs','fhs_mk63',top),'fhs_mk63_vs_pooled':dm('fhs_mk63','pooled_z',top),'fhs_vs_pooled':dm('fhs','pooled_z',top),'garch_vs_pooled':dm('garch_t','pooled_z',top)}}
json.dump(out,open(os.path.join(P,"absorb_results.json"),"w"),indent=2)
lg("ABSORBDONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
