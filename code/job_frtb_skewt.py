# job_frtb_skewt.py -- CORRECTED FRTB battery: real Hansen skew-t quantiles for gjr_skewt.
# The original frtb_bench.py had two defects in the GJR-skew-t benchmark:
#   (1) skewt_ppf(t,nu_,la_) ignored la_ entirely (returned a symmetric standardized t);
#   (2) params.get('nu',8) always returned the default 8 because arch names the skew-t
#       dof 'eta' -- so the fitted dof never entered the quantile either.
# Net effect: the benchmark labeled GJR-skew-t was actually GJR-vol x symmetric t(8) with
# no mean term. This job re-runs the full battery with the correct Hansen (1994) skew-t
# inverse CDF (validated against arch's SkewStudent.ppf and against the symmetric-t limit
# before any data are touched), fitted eta/lambda per name, and the mean term included.
# Output: frtb_bench_v2_results.json (schema of the original + 97.5% backtests).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rng=np.random.default_rng(0)
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
TAIL=[0.005,0.01,0.025]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)

# ---- correct Hansen (1994) skew-t inverse CDF (standardized: zero mean, unit variance) ----
def hansen_ppf(u,eta,lam):
    c=math.gamma((eta+1)/2)/(math.sqrt(math.pi*(eta-2))*math.gamma(eta/2))
    a=4*lam*c*(eta-2)/(eta-1); b=math.sqrt(max(1+3*lam*lam-a*a,1e-12))
    s=math.sqrt((eta-2)/eta)
    if u<(1-lam)/2.0:
        return ((1-lam)*s*float(stats.t.ppf(u/(1-lam),eta))-a)/b
    return ((1+lam)*s*float(stats.t.ppf((u+lam)/(1+lam),eta))-a)/b
# self-tests BEFORE any data: symmetric limit + arch agreement + skew direction
_sym=hansen_ppf(0.025,8.0,0.0); _ref=float(stats.t.ppf(0.025,8))*math.sqrt(6.0/8.0)
assert abs(_sym-_ref)<1e-9, (_sym,_ref)
assert hansen_ppf(0.01,8.0,-0.3)<hansen_ppf(0.01,8.0,0.0)<hansen_ppf(0.01,8.0,0.3)
try:
    from arch.univariate.distribution import SkewStudent
    _sst=SkewStudent()
    for _u,_e,_l in ((0.01,7.3,-0.21),(0.025,5.5,0.15),(0.10,12.0,-0.05)):
        _av=float(np.asarray(_sst.ppf(_u,np.array([_e,_l]))).ravel()[0])
        assert abs(_av-hansen_ppf(_u,_e,_l))<1e-4,(_u,_e,_l,_av,hansen_ppf(_u,_e,_l))
    lg("hansen_ppf validated against arch SkewStudent.ppf")
except ImportError:
    lg("arch SkewStudent not importable for cross-check; manual formula self-tested only")

rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
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
        nu2=float(q2['eta']) if 'eta' in q2 else float(q2.get('nu',8))
        la2=float(q2['lambda']) if 'lambda' in q2 else 0.0
        e2=y-mu2; sg2=np.empty(n); sg2[0]=np.var(y[:sp])
        for k in range(1,n): sg2[k]=max(om2+al2*e2[k-1]**2+ga2*e2[k-1]**2*(e2[k-1]<0)+be2*sg2[k-1],1e-8)
        sig2=np.sqrt(sg2); has_gjr=True
    except Exception: has_gjr=False
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1); df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    for t in TAUS: df['hs_%g'%t]=rollq(df['y'],500,t)
    ev=np.zeros(n); ev[0]=np.var(y[:sp])
    for k in range(1,n): ev[k]=0.94*ev[k-1]+0.06*y[k-1]**2
    df['ewsig']=np.sqrt(ev)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    df['gjr_sig']=sig2 if has_gjr else np.nan; df['gjr_nu']=nu2 if has_gjr else np.nan
    df['gjr_la']=la2 if has_gjr else np.nan; df['gjr_mu']=mu2 if has_gjr else np.nan
    dd=df.dropna(subset=RAWX+ZX+['sig'])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or not has_gjr: continue
    TR_z.append(trn[ZX+['z']])
    keep=['y','sig','date','mu','nu','tsc','ewsig','gjr_sig','gjr_nu','gjr_la','gjr_mu']+RAWX+ZX+['hs_%g'%t for t in TAUS]
    t2=tst[keep].copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d names %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TR_z)
ZQ={}
for t in TAUS:
    mz=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=mz.predict(TE[ZX].values)
    if t in (0.005,0.5,0.99): lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
EW=TE['ewsig'].values; GS=TE['gjr_sig'].values; GNU=TE['gjr_nu'].values; GLA=TE['gjr_la'].values; GMU=TE['gjr_mu'].values
# per-name constant (eta,lambda): compute skew-t quantile once per (name,tau)
Q={m:{} for m in MODELS}
pairs=TE[['gjr_nu','gjr_la']].drop_duplicates().values
lg("unique (eta,lambda) pairs: %d"%len(pairs))
for t in TAUS:
    Q['hist_sim'][t]=TE['hs_%g'%t].values
    Q['ewma_rm'][t]=EW*stats.norm.ppf(t)
    Q['garch_t'][t]=MU+SIG*stats.t.ppf(t,NU)/TSC
    qmap={(round(e_,10),round(l_,10)):hansen_ppf(t,e_,l_) for e_,l_ in pairs}
    key=np.array([qmap[(round(e_,10),round(l_,10))] for e_,l_ in zip(GNU,GLA)])
    Q['gjr_skewt'][t]=GMU+GS*key
    Q['fhs'][t]=MU+SIG*np.quantile(TRzc['z'].values,t)
    Q['resid_hybrid_ML'][t]=MU+SIG*ZQ[t]
def pinball_avg(m):
    pl=np.zeros(len(Y))
    for t in TAUS: pl+=pin(Y,Q[m][t],t)
    return pl/len(TAUS)
def es975_pred(m): return np.mean([Q[m][t] for t in TAIL],axis=0)
PL={m:pinball_avg(m) for m in MODELS}
def _llb(pp,k0,k1):
    if k0+k1==0: return 0.0
    if pp<=0: return 0.0 if k1==0 else -1e300
    if pp>=1: return 0.0 if k0==0 else -1e300
    return k0*math.log(1-pp)+k1*math.log(pp)
def kupiec(x,T,p):
    if x==0 or x==T: return None
    pi=x/T; lr=-2*(_llb(p,T-x,x)-_llb(pi,T-x,x)); return round(float(1-stats.chi2.cdf(max(lr,0),1)),4)
def christoffersen(b,p):
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
    lr_uc=-2*(_llb(p,T-x,x)-_llb(pi,T-x,x))
    lr_ind=-2*(_llb(pi,n00+n10,n01+n11)-(_llb(pi0,n00,n01)+_llb(pi1,n10,n11)))
    return round(float(1-stats.chi2.cdf(max(lr_uc+lr_ind,0),2)),4)
summary={}; T=len(Y)
for m in MODELS:
    b99=(Y<Q[m][0.01]); b975=(Y<Q[m][0.025])
    esp=es975_pred(m); esr=Y[b975]
    summary[m]=dict(avg_pinball=round(float(PL[m].mean()),4),
                    ES975_pred=round(float(esp.mean()),3), ES975_realized=round(float(esr.mean()),3) if b975.sum() else None,
                    breach99=round(float(b99.mean()),4), breach975=round(float(b975.mean()),4),
                    kupiec99_p=kupiec(int(b99.sum()),T,0.01), christoffersen99_p=christoffersen(b99,0.01),
                    kupiec975_p=kupiec(int(b975.sum()),T,0.025), christoffersen975_p=christoffersen(b975,0.025))
best=min(summary,key=lambda k:summary[k]['avg_pinball'])
Ldate=pd.DataFrame({m:PL[m] for m in MODELS}); Ldate['date']=TE['date'].values
Lmat=Ldate.groupby('date').mean()[MODELS]; L=Lmat.values; Td=len(L)
def nw_var(d,lag=10):
    d=d-d.mean(); Tn=len(d); v=np.mean(d*d)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(d[k:]*d[:-k])
    return v/Tn
mi={m:i for i,m in enumerate(MODELS)}; bi=mi[best]
dm={}
for m in MODELS:
    if m==best: continue
    d=L[:,mi[m]]-L[:,bi]
    stat=d.mean()/math.sqrt(max(nw_var(d),1e-12)); dm[m]=dict(DM_stat=round(float(stat),2),p_one_sided=round(float(1-stats.norm.cdf(stat)),4))
def mcs(L,alpha=0.10,B=1000,blk=10):
    surv=list(range(L.shape[1])); pvals={}
    def boot_idx(T2):
        idx=np.empty(T2,int); i=0
        while i<T2:
            s=rng.integers(0,T2); l=rng.geometric(1/blk)
            for j in range(l):
                if i<T2: idx[i]=(s+j)%T2; i+=1
        return idx
    while len(surv)>1:
        Ls=L[:,surv]; means=Ls.mean(0); M=len(surv)
        dij=means[:,None]-means[None,:]
        bootd=np.zeros((B,M,M))
        for bb in range(B):
            ix=boot_idx(Ls.shape[0]); mb=Ls[ix].mean(0); bootd[bb]=mb[:,None]-mb[None,:]
        varij=bootd.var(0)+1e-12
        tij=np.abs(dij)/np.sqrt(varij); TR2=np.nanmax(tij)
        bootTR=np.array([np.nanmax(np.abs(bootd[bb]-dij)/np.sqrt(varij)) for bb in range(B)])
        pv=float(np.mean(bootTR>=TR2)); worst=surv[int(np.argmax(means))]
        pvals[MODELS[worst]]=round(pv,3)
        if pv>=alpha: break
        surv.remove(worst)
    return {'in_MCS_90':[MODELS[i] for i in surv],'elimination_pvals':pvals}
MCS=mcs(L)
la_stats=TE.groupby('permno')[['gjr_nu','gjr_la']].first()
out={'note':'CORRECTED FRTB battery: gjr_skewt now uses the true Hansen skew-t inverse CDF with the FITTED eta/lambda per name (validated vs arch SkewStudent.ppf and the symmetric-t limit) and includes the mean term. Original frtb_bench.py used symmetric t(8) mislabeled as skew-t; that defect and this correction are disclosed in the paper. Everything else identical (140 names, same split, same metrics, MCS B=1000).',
     'n_names':int(TE['permno'].nunique()),'n_test_rows':int(len(Y)),'n_dates':int(Td),
     'fitted_eta_median':round(float(la_stats['gjr_nu'].median()),2),
     'fitted_lambda_median':round(float(la_stats['gjr_la'].median()),3),
     'fitted_lambda_share_negative':round(float((la_stats['gjr_la']<0).mean()),3),
     'per_model':summary,'best_model':best,'DM_vs_best':dm,'MCS':MCS}
json.dump(out,open(os.path.join(P,"frtb_bench_v2_results.json"),"w"),indent=2)
lg("SKEWTFIXDONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2)[:2000])
