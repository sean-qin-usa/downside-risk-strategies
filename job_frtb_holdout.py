# job_frtb_holdout.py -- FRTB exception-test battery STRESS RE-RUN on the 2000-2013 holdout era.
# Closes the registered limitation "the FRTB battery's stress re-run on that era remains registered".
# Uses the cached, gitignored holdout_panel_2000_2013.csv (CRSP top-200, includes the 2008 crisis).
# Same evaluation machinery as job_perasset_v2.py: per-asset Kupiec/Christoffersen + date-clustered
# NW t on per-date breach frequency. Engine variant follows the PAPER's design exactly:
# EVT splice at 99, conformal shift applied at 97.5 ONLY (lesson from v2: stacking conf on EVT at 99
# double-corrects and over-covers).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
CACHE=os.path.join(P,"holdout_panel_2000_2013.csv")
rr=pd.read_csv(CACHE,dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
lg(f"holdout panel: {len(rr):,} rows, {rr.permno.nunique()} names")
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
TRz=[]; CALz=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
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
    # baseline forecasts, all causal
    df['hs250_99']=df['y'].rolling(250,min_periods=100).quantile(0.01).shift(1)
    df['hs250_975']=df['y'].rolling(250,min_periods=100).quantile(0.025).shift(1)
    s2e=pd.Series(y**2).ewm(alpha=0.06,adjust=False).mean().shift(1).values
    df['ewma_sig']=np.sqrt(np.maximum(s2e,1e-8))
    ztr=z[:cp]
    df['fhs_99']=mu+df['sig']*np.quantile(ztr,0.01); df['fhs_975']=mu+df['sig']*np.quantile(ztr,0.025)
    df['garch_99']=mu+df['sig']*stats.t.ppf(0.01,nu)/tsc; df['garch_975']=mu+df['sig']*stats.t.ppf(0.025,nu)/tsc
    df['idx']=np.arange(n); df['mu']=mu
    dd=df.dropna(subset=ZX+['hs250_99'])
    trn=dd[dd['idx']<cp]; cal=dd[(dd['idx']>=cp)&(dd['idx']<sp)]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(cal)<60: continue
    TRz.append(trn[ZX+['z']]); CALz.append(cal[ZX+['z']])
    keep=['y','sig','date','mu','hs250_99','hs250_975','ewma_sig','fhs_99','fhs_975','garch_99','garch_975']+ZX
    t2=tst[keep].copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz); CALzc=pd.concat(CALz)
ZQ={}; ZQcal={}
for t in [0.01,0.025]:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=m.predict(TE[ZX].values); ZQcal[t]=m.predict(CALzc[ZX].values)
    lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
ztr=TRzc['z'].values; u=np.quantile(ztr,0.025); exc=u-ztr[ztr<u]
xi,loc,beta=stats.genpareto.fit(exc,floc=0.0)
def evt_q(tau,p0=0.025):
    return u-(beta/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u-beta*math.log(p0/tau)
lg(f"GPD: u={u:.3f} xi={xi:.3f} beta={beta:.3f}")
s975=CALzc['z'].values-ZQcal[0.025]; CONF975=float(np.quantile(s975,0.025*(1+1/len(s975))))
lg(f"conf shift @975: {CONF975:+.4f}")
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values
variants={
  'hist_sim':   {0.01: TE['hs250_99'].values, 0.025: TE['hs250_975'].values},
  'ewma':       {0.01: stats.norm.ppf(0.01)*TE['ewma_sig'].values, 0.025: stats.norm.ppf(0.025)*TE['ewma_sig'].values},
  'garch_t':    {0.01: TE['garch_99'].values, 0.025: TE['garch_975'].values},
  'fhs':        {0.01: TE['fhs_99'].values, 0.025: TE['fhs_975'].values},
  'raw_hybrid': {t: MU+SIG*ZQ[t] for t in [0.01,0.025]},
  'hybrid_EVT': {0.01: MU+SIG*np.minimum(ZQ[0.01],evt_q(0.01)),
                 0.025: MU+SIG*np.minimum(ZQ[0.025],evt_q(0.025))},
  'engine_evt_conf975': {0.01: MU+SIG*np.minimum(ZQ[0.01],evt_q(0.01)),
                         0.025: MU+SIG*(np.minimum(ZQ[0.025],evt_q(0.025))+CONF975)},
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
OUT={'note':'FRTB battery stress re-run on the 2000-2013 holdout era (includes 2008). Test window = last 40% per name (~2008.6-2013). engine_asdeployed = EVT splice at 99, conformal shift at 97.5 only (paper design).',
     'gpd':{'u':round(float(u),4),'xi':round(float(xi),4),'beta':round(float(beta),4)},'conf_shift_975':round(CONF975,4),
     'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),'per_variant':{}}
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
json.dump(OUT,open(os.path.join(P,"frtb_holdout_results.json"),"w"),indent=2)
lg("FRTBHOLDOUTDONE %.0fs"%(time.time()-t0))
