# job_perasset_backtest.py -- referee-gate fix for the FRTB battery's exception tests.
# The original frtb_bench.py pooled all ~155k asset-days into ONE Kupiec/Christoffersen
# sequence (invalid: cross-sectional dependence; Christoffersen transitions even cross
# name boundaries).  This job re-runs the battery pipeline VERBATIM (same models, same
# splits, same seeds) and replaces the exception inference with:
#   (a) PER-ASSET Kupiec + Christoffersen at 99% and Kupiec at 97.5%, reporting the
#       pass-rate distribution per model (share of names with p>0.05, median p);
#   (b) a DATE-CLUSTERED calibration test: per-date breach frequency f_t vs nominal,
#       tested on the ~1,100-date series with a Newey-West (lag-10) variance -- the
#       common-date dependence-respecting analogue of the pooled Kupiec;
#   (c) binomial expectation check: expected pass rates under H0 for calibration.
# VERBATIM pipeline from frtb_bench.py (paths switched to the host copy of the panel).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
D=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
OUTJ=os.path.join(D,"perasset_backtest_results.json")
rng=np.random.default_rng(0)
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:140]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
RAWX=['lag1','abs1','prv5','prv21','rv63']; ZX=['logsig','zl1','absz5','zstd21','fracdn5']
MODELS=['hist_sim','ewma_rm','garch_t','gjr_skewt','fhs','resid_hybrid_ML']
TR_z=[]; rows=[]
def rollq(s,win,tau): return s.rolling(win,min_periods=250).quantile(tau).shift(1)
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
    try:
        r2=arch_model(y[:sp],vol='Garch',p=1,o=1,q=1,dist='skewt',rescale=False).fit(disp='off',show_warning=False)
        q2=r2.params; om2,al2,ga2,be2,mu2=float(q2['omega']),float(q2['alpha[1]']),float(q2['gamma[1]']),float(q2['beta[1]']),float(q2.get('mu',0))
        nu2=float(q2.get('nu',8)); la2=float(q2.get('lambda',0)); e2=y-mu2; sg2=np.empty(n); sg2[0]=np.var(y[:sp])
        for k in range(1,n): sg2[k]=max(om2+al2*e2[k-1]**2+ga2*e2[k-1]**2*(e2[k-1]<0)+be2*sg2[k-1],1e-8)
        sig2=np.sqrt(sg2); has_gjr=True
    except Exception: has_gjr=False
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1); df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    for t in [0.005,0.01,0.025]: df['hs_%g'%t]=rollq(df['y'],500,t)
    ev=np.zeros(n); ev[0]=np.var(y[:sp])
    for k in range(1,n): ev[k]=0.94*ev[k-1]+0.06*y[k-1]**2
    df['ewsig']=np.sqrt(ev)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    df['gjr_sig']=sig2 if has_gjr else np.nan; df['gjr_nu']=nu2 if has_gjr else np.nan; df['gjr_la']=la2 if has_gjr else np.nan
    dd=df.dropna(subset=RAWX+ZX+['sig'])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or not has_gjr: continue
    TR_z.append(trn[ZX+['z']])
    keep=['y','sig','date','mu','nu','tsc','ewsig','gjr_sig','gjr_nu','gjr_la']+ZX+['hs_%g'%t for t in [0.005,0.01,0.025]]
    t2=tst[keep].copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d names %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TR_z)
ZQ={}
for t in [0.005,0.01,0.025]:
    mz=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=mz.predict(TE[ZX].values); lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
EW=TE['ewsig'].values; GS=TE['gjr_sig'].values; GNU=TE['gjr_nu'].values; GLA=TE['gjr_la'].values
def skewt_ppf(t,nu_,la_):
    return stats.t.ppf(t,nu_)/math.sqrt(nu_/(nu_-2)) if nu_>2 else stats.norm.ppf(t)
Q={m:{} for m in MODELS}
for t in [0.01,0.025]:
    Q['hist_sim'][t]=TE['hs_%g'%t].values
    Q['ewma_rm'][t]=EW*stats.norm.ppf(t)
    Q['garch_t'][t]=MU+SIG*stats.t.ppf(t,NU)/TSC
    Q['gjr_skewt'][t]=np.array([g*skewt_ppf(t,gn,gl) for g,gn,gl in zip(GS,GNU,GLA)])
    Q['fhs'][t]=MU+SIG*np.quantile(TRzc['z'].values,t)
    Q['resid_hybrid_ML'][t]=MU+SIG*ZQ[t]
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
    return float(x.mean()/math.sqrt(max(v/n,1e-16)))
OUT={"note":"Per-asset + date-clustered restatement of the FRTB exception tests (replaces the pooled Kupiec of frtb_bench.py).",
     "n_names":int(TE['permno'].nunique()),"n_rows":int(len(Y)),"per_model":{}}
perm=TE['permno'].values; dates=TE['date'].values
for m in MODELS:
    rec={}
    for lvl,p0 in [("99",0.01),("975",0.025)]:
        b=(Y<Q[m][p0]).astype(int)
        # (a) per-asset
        kp=[];cp=[]
        for pn in np.unique(perm):
            msk=perm==pn
            kpv=kupiec(int(b[msk].sum()),int(msk.sum()),p0)
            if kpv is not None: kp.append(kpv)
            if lvl=="99":
                cpv=christoffersen(b[msk],p0)
                if cpv is not None: cp.append(cpv)
        rec[f"breach{lvl}"]=round(float(b.mean()),4)
        rec[f"kupiec{lvl}_perasset_passrate"]=round(float(np.mean([x>0.05 for x in kp])),3)
        rec[f"kupiec{lvl}_perasset_median_p"]=round(float(np.median(kp)),3)
        rec[f"kupiec{lvl}_n_tested"]=len(kp)
        if lvl=="99" and cp:
            rec["christoffersen99_perasset_passrate"]=round(float(np.mean([x>0.05 for x in cp])),3)
            rec["christoffersen99_perasset_median_p"]=round(float(np.median(cp)),3)
        # (b) date-clustered: per-date breach freq minus nominal, NW t on date series
        fdf=pd.DataFrame({"b":b,"date":dates}).groupby("date")["b"].mean()
        tstat=nw_t(fdf.values-p0)
        rec[f"dateclustered{lvl}_NW_t"]=round(tstat,2) if tstat is not None else None
        rec[f"dateclustered{lvl}_mean_freq"]=round(float(fdf.mean()),4)
    OUT["per_model"][m]=rec
    lg(f"{m}: {json.dumps(rec)}")
OUT["expected_under_H0"]={"kupiec_passrate":"~0.95 if exactly calibrated (5% size)",
                          "dateclustered_NW_t":"|t|<1.96 if calibrated on average across dates"}
json.dump(OUT,open(OUTJ,"w"),indent=2)
lg("PERASSETDONE %.0fs"%(time.time()-t0))
