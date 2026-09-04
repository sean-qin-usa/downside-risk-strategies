# job_perasset_v2.py -- per-asset + date-clustered exception tests for the FINISHED engine
# (residual-hybrid + GPD tail below tau<=0.025 + per-level conformal shift), completing the
# 2026-08-15 restatement that covered raw models only.  Closes referee point 1.2 fully.
# Faithful-variant note: GPD fit on pooled TRAIN residual exceedances; conformal shifts
# learned on the last 25% of TRAIN rows (disjoint from test); both frozen before test.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:140]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
TRz=[]; CALz=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)     # 0..cp train-fit, cp..sp calibration, sp.. test
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6)
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['idx']=np.arange(n); df['mu']=mu
    dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<cp]; cal=dd[(dd['idx']>=cp)&(dd['idx']<sp)]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(cal)<60: continue
    TRz.append(trn[ZX+['z']]); CALz.append(cal[ZX+['z']])
    t2=tst[['y','sig','date','mu']+ZX].copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz); CALzc=pd.concat(CALz)
# body models at the two regulatory tail levels
ZQ={}; ZQcal={}
for t in [0.01,0.025]:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=m.predict(TE[ZX].values); ZQcal[t]=m.predict(CALzc[ZX].values)
    lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
# GPD tail on pooled TRAIN residual exceedances below the empirical 2.5% threshold
ztr=TRzc['z'].values; u=np.quantile(ztr,0.025); exc=u-ztr[ztr<u]     # positive exceedances
xi,loc,beta=stats.genpareto.fit(exc,floc=0.0)
def evt_q(tau,p0=0.025):
    return u-(beta/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u-beta*math.log(p0/tau)
lg(f"GPD: u={u:.3f} xi={xi:.3f} beta={beta:.3f}; evt q01={evt_q(0.01):.3f}")
# conformal per-level shifts from the CALIBRATION split (order statistic of z - q)
CONF={}
for t in [0.01,0.025]:
    s=CALzc['z'].values-ZQcal[t]; ncal=len(s)
    CONF[t]=float(np.quantile(s,t*(1+1/ncal)))            # lower-tail: tau-quantile of signed error
    lg(f"conf shift tau={t}: {CONF[t]:+.4f} (ncal={ncal})")
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values
variants={
  'raw_hybrid':      {t: MU+SIG*ZQ[t] for t in [0.01,0.025]},
  'hybrid_EVT':      {0.01: MU+SIG*np.minimum(ZQ[0.01],evt_q(0.01)), 0.025: MU+SIG*np.minimum(ZQ[0.025],evt_q(0.025))},
  'hybrid_EVT_conf': {t: MU+SIG*(np.minimum(ZQ[t],evt_q(t))+CONF[t]) for t in [0.01,0.025]},
}
def _llb(pp,k0,k1):
    if k0+k1==0: return 0.0
    if pp<=0: return 0.0 if k1==0 else -1e300
    if pp>=1: return 0.0 if k0==0 else -1e300
    return k0*math.log(1-pp)+k1*math.log(pp)
def kupiec(x,T,p):
    if T==0 or x==T: return None
    if x==0: return round(float(1-stats.chi2.cdf(-2*_llb(p,T,0),1)),4)
    pi=x/T; lr=-2*(_llb(p,T-x,x)-_llb(pi,T-x,x)); return round(float(1-stats.chi2.cdf(max(lr,0),1)),4)
def christoffersen(b,p):
    b=b.astype(int); T=len(b); x=int(b.sum())
    if x==0: return None
    n00=n01=n10=n11=0
    for i in range(1,T):
        a,c=b[i-1],b[i]
        if a==0 and c==0:n00+=1
        elif a==0 and c==1:n01+=1
        elif a==1 and c==0:n10+=1
        else:n11+=1
    pi=x/T; pi0=n01/max(n00+n01,1); pi1=n11/max(n10+n11,1)
    lr_uc=-2*(_llb(p,T-x,x)-_llb(pi,T-x,x))
    lr_ind=-2*(_llb(pi,n00+n10,n01+n11)-(_llb(pi0,n00,n01)+_llb(pi1,n10,n11)))
    return round(float(1-stats.chi2.cdf(max(lr_uc+lr_ind,0),2)),4)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
perm=TE['permno'].values; dates=TE['date'].values
OUT={'note':'Finished-engine per-asset + date-clustered exception restatement (v2). GPD u/xi/beta and conformal shifts frozen pre-test.',
     'gpd':{'u':round(float(u),4),'xi':round(float(xi),4),'beta':round(float(beta),4)},'conf_shifts':{str(k):round(v,4) for k,v in CONF.items()},
     'n_names':int(TE.permno.nunique()),'per_variant':{}}
for vname,Q in variants.items():
    rec={}
    for lvl,p0 in [("99",0.01),("975",0.025)]:
        b=(Y<Q[p0]).astype(int)
        kp=[];cp2=[]
        for pn in np.unique(perm):
            msk=perm==pn
            v=kupiec(int(b[msk].sum()),int(msk.sum()),p0)
            if v is not None: kp.append(v)
            if lvl=="99":
                c=christoffersen(b[msk],p0)
                if c is not None: cp2.append(c)
        fdf=pd.DataFrame({"b":b,"date":dates}).groupby("date")["b"].mean()
        rec[f"breach{lvl}"]=round(float(b.mean()),4)
        rec[f"kupiec{lvl}_passrate"]=round(float(np.mean([x>0.05 for x in kp])),3)
        if lvl=="99" and cp2: rec["christoffersen99_passrate"]=round(float(np.mean([x>0.05 for x in cp2])),3)
        rec[f"dateclustered{lvl}_NW_t"]=nw_t(fdf.values-p0)
    OUT['per_variant'][vname]=rec
    lg(f"{vname}: {json.dumps(rec)}")
json.dump(OUT,open(os.path.join(P,"perasset_v2_results.json"),"w"),indent=2)
lg("PERASSETV2DONE %.0fs"%(time.time()-t0))
