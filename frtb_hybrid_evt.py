# FRTB HYBRID + EVT TAIL (ai2) — finish "industry standard and above": keep the residual-hybrid's ES/pinball win AND pass the
# 99% VaR exception test. Fix the slightly-thin far tail with Peaks-Over-Threshold (GPD) on the standardized-residual left tail
# (a recognized regulatory EVT method) for tau<=0.025; keep the ML-conditioned residual for the body (tau>=0.05).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
TAILT=[0.005,0.01,0.025]; TAIL_ES=[0.005,0.01,0.025]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:140]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
def gpd_left_q(ztrain,tau,pu=0.05):
    # POT on the LEFT tail: threshold u at pu quantile; fit GPD to exceedances (u - z) for z<u; return residual quantile at tau<pu
    u=np.quantile(ztrain,pu); ex=u-ztrain[ztrain<u]; ex=ex[ex>0]
    if len(ex)<30: return np.quantile(ztrain,tau)
    try:
        xi,loc,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return np.quantile(ztrain,tau)
    if beta<=0: return np.quantile(ztrain,tau)
    if abs(xi)<1e-6: q_ex=-beta*math.log(tau/pu)
    else: q_ex=(beta/xi)*(((tau/pu)**(-xi))-1)
    return u-q_ex                                          # more negative = fatter left tail
TR_z=[]; rows=[]
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
    ztr=z[:sp]
    evtq={t:gpd_left_q(ztr,t) for t in TAILT}; fhsq={t:np.quantile(ztr,t) for t in TAUS}
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1); df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=ZX+['sig']); trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TR_z.append(trn[ZX+['z']])
    t2=tst[['y','sig','date','mu','nu','tsc']+ZX].copy(); t2['permno']=pn
    for t in TAUS: t2['fhs_%g'%t]=fhsq[t]
    for t in TAILT: t2['evt_%g'%t]=evtq[t]
    rows.append(t2)
lg("panels %d names %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TR_z)
ZQ={}
for t in TAUS:
    mz=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=mz.predict(TE[ZX].values)
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
Q={'garch_t':{},'fhs':{},'hybrid_ML':{},'hybrid_EVT':{}}
for t in TAUS:
    Q['garch_t'][t]=MU+SIG*stats.t.ppf(t,NU)/TSC
    Q['fhs'][t]=MU+SIG*TE['fhs_%g'%t].values
    Q['hybrid_ML'][t]=MU+SIG*ZQ[t]
    # EVT hybrid: EVT residual quantile in the far tail, ML residual quantile in the body
    if t in TAILT: Q['hybrid_EVT'][t]=MU+SIG*TE['evt_%g'%t].values
    else: Q['hybrid_EVT'][t]=MU+SIG*ZQ[t]
def _llb(pp,k0,k1):
    if k0+k1==0: return 0.0
    if pp<=0: return 0.0 if k1==0 else -1e300
    if pp>=1: return 0.0 if k0==0 else -1e300
    return k0*math.log(1-pp)+k1*math.log(pp)
def kupiec(x,T,p):
    if x==0 or x==T: return None
    pi=x/T; return round(float(1-stats.chi2.cdf(max(-2*(_llb(p,T-x,x)-_llb(pi,T-x,x)),0),1)),4)
def christ(b,p):
    b=b.astype(int); T=len(b); x=int(b.sum())
    n00=n01=n10=n11=0
    for i in range(1,T):
        a,c=b[i-1],b[i]
        if a==0 and c==0:n00+=1
        elif a==0 and c==1:n01+=1
        elif a==1 and c==0:n10+=1
        else:n11+=1
    if x==0: return None
    pi=x/T; pi0=n01/max(n00+n01,1); pi1=n11/max(n10+n11,1)
    lr=-2*(_llb(p,T-x,x)-_llb(pi,T-x,x))-2*(_llb(pi,n00+n10,n01+n11)-(_llb(pi0,n00,n01)+_llb(pi1,n10,n11)))
    return round(float(1-stats.chi2.cdf(max(lr,0),2)),4)
T=len(Y); summ={}
for m in Q:
    pl=np.zeros(T)
    for t in TAUS: pl+=pin(Y,Q[m][t],t)
    pl/=len(TAUS); b99=(Y<Q[m][0.01]); b975=(Y<Q[m][0.025])
    esp=np.mean([Q[m][t] for t in TAIL_ES],axis=0)
    summ[m]=dict(avg_pinball=round(float(pl.mean()),4),ES975_pred=round(float(esp.mean()),3),
                 ES975_realized=round(float(Y[b975].mean()),3) if b975.sum() else None,
                 breach99=round(float(b99.mean()),4),breach975=round(float(b975.mean()),4),
                 kupiec99_p=kupiec(int(b99.sum()),T,0.01),christoffersen99_p=christ(b99,0.01))
# DM hybrid_EVT vs each on per-date mean pinball
PLm={m:np.zeros(T) for m in Q}
for m in Q:
    for t in TAUS: PLm[m]+=pin(Y,Q[m][t],t)
    PLm[m]/=len(TAUS)
Ld=pd.DataFrame({m:PLm[m] for m in Q}); Ld['date']=TE['date'].values; Lm=Ld.groupby('date').mean(); L=Lm.values; cols=list(Lm.columns)
def nwv(d,lag=10):
    d=d-d.mean(); v=np.mean(d*d)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(d[k:]*d[:-k])
    return v/len(d)
ei=cols.index('hybrid_EVT'); dm={}
for m in cols:
    if m=='hybrid_EVT': continue
    d=L[:,cols.index(m)]-L[:,ei]; s=d.mean()/math.sqrt(max(nwv(d),1e-12)); dm[m]=dict(DM_stat=round(float(s),2),p_one_sided=round(float(1-stats.norm.cdf(s)),4))
out={'note':'FRTB hybrid + EVT tail. hybrid_EVT = ML-conditioned residual body (tau>=0.05) + Peaks-Over-Threshold GPD left tail '
            '(tau<=0.025). vs garch_t, GARCH-FHS, hybrid_ML. Goal: keep ES97.5/pinball win AND pass Kupiec/Christoffersen@99%. '
            'DM = hybrid_EVT vs others (positive stat => other worse).',
     'n_names':int(TE['permno'].nunique()),'n_test_rows':int(T),'per_model':summ,'DM_vs_hybrid_EVT':dm}
json.dump(out,open(os.path.join(D,"frtb_hybrid_evt_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
