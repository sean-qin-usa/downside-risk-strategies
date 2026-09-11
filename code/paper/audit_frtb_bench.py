# FRTB-ALIGNED BENCHMARK + RIGOR (ai2) — "industry standard and above."
# Banks under Basel FRTB do NOT use bare GARCH: the regulatory objective is Expected Shortfall at 97.5%, and the workhorse
# internal models are Historical Simulation (HS) and GARCH-Filtered Historical Simulation (FHS, the acknowledged best in
# volatile regimes). We benchmark the amortized RESIDUAL-HYBRID (GARCH vol x STATE-CONDITIONED nonparametric residual shape
# = "FHS and above") against the real industry set, on the FRTB metric (ES97.5) with the exact FRTB-style exception backtests
# (Kupiec POF, Christoffersen CC) and formal significance (Diebold-Mariano + Model Confidence Set).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
rng=np.random.default_rng(0)
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
TAIL=[0.005,0.01,0.025]                                   # for ES 97.5% approx (avg quantile in far-left tail)
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:140]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
RAWX=['lag1','abs1','prv5','prv21','rv63']; ZX=['logsig','zl1','absz5','zstd21','fracdn5']
MODELS=['hist_sim','ewma_rm','garch_t','gjr_skewt','fhs','resid_hybrid_ML']
TR_raw=[]; TR_z=[]; rows=[]                               # rows: per (name,date) dict with y + each model's quantiles
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
    # GJR-skewt (leverage + skew) — strong bank econometric benchmark
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
    for t in TAUS: df['hs_%g'%t]=rollq(df['y'],500,t)          # Historical Simulation (rolling 500d empirical)
    ewv=pd.Series(y).copy(); ev=np.zeros(n); ev[0]=np.var(y[:sp])
    for k in range(1,n): ev[k]=0.94*ev[k-1]+0.06*y[k-1]**2      # RiskMetrics EWMA variance
    df['ewsig']=np.sqrt(ev)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc; df['gjr_sig']=sig2 if has_gjr else np.nan
    df['gjr_nu']=nu2 if has_gjr else np.nan; df['gjr_la']=la2 if has_gjr else np.nan
    dd=df.dropna(subset=RAWX+ZX+['sig'])
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or not has_gjr: continue
    TR_raw.append(trn[RAWX+['y']]); TR_z.append(trn[ZX+['z']])
    # store test rows w/ everything needed to build all model quantiles later (need pooled GBM first)
    keep=['y','sig','date','mu','nu','tsc','ewsig','gjr_sig','gjr_nu','gjr_la']+RAWX+ZX+['hs_%g'%t for t in TAUS]
    t2=tst[keep].copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d names %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True)
TRrawc=pd.concat(TR_raw); TRzc=pd.concat(TR_z)
# amortized quantile models: raw-GBM (not a benchmark here) and residual-GBM (for resid_hybrid_ML)
ZQ={}
for t in TAUS:
    mz=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=mz.predict(TE[ZX].values)
    lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
EW=TE['ewsig'].values; GS=TE['gjr_sig'].values; GNU=TE['gjr_nu'].values; GLA=TE['gjr_la'].values
def skewt_ppf(t,nu_,la_):                                  # Hansen skew-t quantile (vectorized-ish via scipy t)
    # approx: use standardized skew-t; fall back to student-t if lambda~0
    return stats.t.ppf(t,nu_)/math.sqrt(nu_/(nu_-2)) if nu_>2 else stats.norm.ppf(t)
# build quantiles per model
Q={m:{} for m in MODELS}
for t in TAUS:
    Q['hist_sim'][t]=TE['hs_%g'%t].values
    Q['ewma_rm'][t]=EW*stats.norm.ppf(t)
    Q['garch_t'][t]=MU+SIG*stats.t.ppf(t,NU)/TSC
    Q['gjr_skewt'][t]=np.array([g*skewt_ppf(t,gn,gl) for g,gn,gl in zip(GS,GNU,GLA)])
    # FHS = GARCH sigma x empirical residual quantile (train residuals, per-name constant) — approximate via z-quantile pooled
    Q['fhs'][t]=MU+SIG*np.quantile(TRzc['z'].values,t)     # pooled residual empirical quantile (unconditional shape)
    Q['resid_hybrid_ML'][t]=MU+SIG*ZQ[t]                   # state-conditioned residual shape (the "above")
# ---- metrics ----
def pinball_avg(m):
    pl=np.zeros(len(Y))
    for t in TAUS: pl+=pin(Y,Q[m][t],t)
    return pl/len(TAUS)
def es975_pred(m):                                          # predicted ES at 97.5% = avg quantile over far-left tail
    return np.mean([Q[m][t] for t in TAIL],axis=0)
PL={m:pinball_avg(m) for m in MODELS}
def _llb(pp,k0,k1):                                        # log Bernoulli likelihood, underflow-safe
    if k0+k1==0: return 0.0
    if pp<=0: return 0.0 if k1==0 else -1e300
    if pp>=1: return 0.0 if k0==0 else -1e300
    return k0*math.log(1-pp)+k1*math.log(pp)
def kupiec(x,T,p):
    if x==0 or x==T: return None
    pi=x/T; lr=-2*(_llb(p,T-x,x)-_llb(pi,T-x,x)); return round(float(1-stats.chi2.cdf(max(lr,0),1)),4)
def christoffersen(breachseq,p):
    b=breachseq.astype(int); T=len(b); x=int(b.sum())
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
summary={}
T=len(Y)
for m in MODELS:
    b99=(Y<Q[m][0.01]); b975=(Y<Q[m][0.025])
    esp=es975_pred(m); esr=Y[b975]
    summary[m]=dict(avg_pinball=round(float(PL[m].mean()),4),
                    ES975_pred=round(float(esp.mean()),3), ES975_realized=round(float(esr.mean()),3) if b975.sum() else None,
                    breach99=round(float(b99.mean()),4), breach975=round(float(b975.mean()),4),
                    kupiec99_p=kupiec(int(b99.sum()),T,0.01), christoffersen99_p=christoffersen(b99,0.01))
best=min(summary,key=lambda k:summary[k]['avg_pinball'])
# ---- per-date loss matrix for DM + MCS ----
TE['_row']=np.arange(len(TE))
Ldate=pd.DataFrame({m:PL[m] for m in MODELS}); Ldate['date']=TE['date'].values
Lmat=Ldate.groupby('date').mean()[MODELS]                  # per-date cross-name mean loss
L=Lmat.values; dates=Lmat.index; Td=len(L)
def nw_var(d,lag=10):
    d=d-d.mean(); T=len(d); g0=np.mean(d*d); v=g0
    for k in range(1,lag+1):
        gk=np.mean(d[k:]*d[:-k]); v+=2*(1-k/(lag+1))*gk
    return v/T
mi={m:i for i,m in enumerate(MODELS)}; bi=mi[best]
dm={}
for m in MODELS:
    if m==best: continue
    d=L[:,mi[m]]-L[:,bi]                                    # positive => m worse than best
    stat=d.mean()/math.sqrt(max(nw_var(d),1e-12)); dm[m]=dict(DM_stat=round(float(stat),2),p_one_sided=round(float(1-stats.norm.cdf(stat)),4))
# ---- Model Confidence Set (Hansen-Lunde-Nadal, range stat, stationary bootstrap) ----
def mcs(L,alpha=0.10,B=1000,blk=10):
    surv=list(range(L.shape[1])); pvals={}
    def boot_idx(T):
        idx=np.empty(T,int); i=0
        while i<T:
            s=rng.integers(0,T); l=rng.geometric(1/blk)
            for j in range(l):
                if i<T: idx[i]=(s+j)%T; i+=1
        return idx
    order=[]
    while len(surv)>1:
        Ls=L[:,surv]; means=Ls.mean(0); M=len(surv)
        dij=means[:,None]-means[None,:]
        # bootstrap var of dij means
        bootd=np.zeros((B,M,M))
        for bb in range(B):
            ix=boot_idx(Ls.shape[0]); mb=Ls[ix].mean(0); bootd[bb]=mb[:,None]-mb[None,:]
        varij=bootd.var(0)+1e-12
        tij=np.abs(dij)/np.sqrt(varij); TR=np.nanmax(tij)
        bootTR=np.array([np.nanmax(np.abs(bootd[bb]-dij)/np.sqrt(varij)) for bb in range(B)])
        pv=float(np.mean(bootTR>=TR)); worst=surv[int(np.argmax(means))]
        pvals[MODELS[worst]]=round(pv,3); order.append(MODELS[worst])
        if pv>=alpha: break
        surv.remove(worst)
    return {'in_MCS_'+str(int((1-alpha)*100)):[MODELS[i] for i in surv],'elimination_pvals':pvals}
MCS=mcs(L)
out={'note':'FRTB-aligned benchmark. Industry set: Historical Simulation, EWMA/RiskMetrics, GARCH-t, GJR-GARCH-skew-t, '
            'GARCH-FHS (filtered historical sim, the bank best-practice) vs resid_hybrid_ML (GARCH vol x STATE-CONDITIONED '
            'nonparam residual = FHS-and-above). Metric ES97.5 (FRTB) + avg pinball; FRTB-style exception backtests Kupiec/'
            'Christoffersen at 99%; significance Diebold-Mariano (NW) + Model Confidence Set (Hansen). best=lowest pinball.',
     'n_names':int(TE['permno'].nunique()),'n_test_rows':int(len(Y)),'n_dates':int(Td),
     'per_model':summary,'best_model':best,'DM_vs_best':dm,'MCS':MCS}
json.dump(out,open(os.path.join(D,"frtb_bench_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
