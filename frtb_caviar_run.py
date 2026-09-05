# FRTB + CAViaR (ai2) — close the "why not CAViaR?" gap. Engle-Manganelli CAViaR is the direct conditional-VaR quantile
# competitor. Add SAV-CAViaR to the FRTB battery vs GARCH-t, GARCH-FHS, hybrid_GBM (ML residual), hybrid_EVT (ML body + GPD tail).
# Report avg pinball + ES97.5, Kupiec+Christoffersen at BOTH 99% and 97.5% (FRTB tests both), Diebold-Mariano + Model Confidence Set.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats, optimize
from arch import arch_model
D="C:/Users/OWNER/Claude/Projects/GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True); rng=np.random.default_rng(0)
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]; TAILT=[0.005,0.01,0.025]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:90]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
def gpd_left_q(ztr,tau,pu=0.05):
    u=np.quantile(ztr,pu); ex=u-ztr[ztr<u]; ex=ex[ex>0]
    if len(ex)<30: return np.quantile(ztr,tau)
    try: xi,loc,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return np.quantile(ztr,tau)
    if beta<=0: return np.quantile(ztr,tau)
    q_ex=-beta*math.log(tau/pu) if abs(xi)<1e-6 else (beta/xi)*(((tau/pu)**(-xi))-1)
    return u-q_ex
def caviar_sav(rtrain,rfull,tau):
    # Symmetric Absolute Value CAViaR: f_t = b1 + b2 f_{t-1} + b3 |r_{t-1}|; fit b on train by pinball; return full-path quantiles
    r=rfull; n=len(r); q0=np.quantile(rtrain[:300],tau); absr=np.abs(r)
    def path(b):
        f=np.empty(n); f[0]=q0
        for i in range(1,n): f[i]=b[0]+b[1]*f[i-1]+b[2]*absr[i-1]
        return f
    ntr=len(rtrain)
    def obj(b):
        f=path(b)[:ntr]; d=rtrain-f; return np.mean(np.where(d>=0,tau*d,(tau-1)*d))
    b0=np.array([q0*0.1,0.8,-0.1 if tau<0.5 else 0.1])
    try:
        res=optimize.minimize(obj,b0,method='Nelder-Mead',options={'maxiter':400,'xatol':1e-3,'fatol':1e-5}); b=res.x
    except Exception:
        b=b0
    return path(b)
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
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0; ztr=z[:sp]
    evtq={t:gpd_left_q(ztr,t) for t in TAILT}; fhsq={t:np.quantile(ztr,t) for t in TAUS}
    cav={t:caviar_sav(y[:sp],y,t) for t in TAUS}          # CAViaR full-path quantiles per tau
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts,'idx':np.arange(n)})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1); df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    for t in TAUS: df['fhs_%g'%t]=fhsq[t]; df['cav_%g'%t]=cav[t]
    for t in TAILT: df['evt_%g'%t]=evtq[t]
    dd=df.dropna(subset=ZX+['sig']); trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TR_z.append(trn[ZX+['z']]); t2=tst.copy(); t2['permno']=pn; rows.append(t2)
    if len(rows)%25==0: lg("  %d names %.0fs"%(len(rows),time.time()-t0))
lg("panels %d names %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TR_z)
ZQ={}
for t in TAUS:
    mz=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values); ZQ[t]=mz.predict(TE[ZX].values)
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
Q={'garch_t':{},'fhs':{},'caviar_sav':{},'hybrid_GBM':{},'hybrid_EVT':{}}
for t in TAUS:
    Q['garch_t'][t]=MU+SIG*stats.t.ppf(t,NU)/TSC; Q['fhs'][t]=MU+SIG*TE['fhs_%g'%t].values
    Q['caviar_sav'][t]=TE['cav_%g'%t].values; Q['hybrid_GBM'][t]=MU+SIG*ZQ[t]
    Q['hybrid_EVT'][t]=(MU+SIG*TE['evt_%g'%t].values) if t in TAILT else (MU+SIG*ZQ[t])
def _llb(pp,k0,k1):
    if k0+k1==0: return 0.0
    if pp<=0: return 0.0 if k1==0 else -1e300
    if pp>=1: return 0.0 if k0==0 else -1e300
    return k0*math.log(1-pp)+k1*math.log(pp)
def kupiec(x,T,p):
    if x==0 or x==T: return None
    pi=x/T; return round(float(1-stats.chi2.cdf(max(-2*(_llb(p,T-x,x)-_llb(pi,T-x,x)),0),1)),4)
def christ(b,p):
    b=b.astype(int); T=len(b); x=int(b.sum()); n00=n01=n10=n11=0
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
T=len(Y); summ={}; PLm={}
for m in Q:
    pl=np.zeros(T)
    for t in TAUS: pl+=pin(Y,Q[m][t],t)
    pl/=len(TAUS); PLm[m]=pl
    b99=(Y<Q[m][0.01]); b975=(Y<Q[m][0.025]); esp=np.mean([Q[m][t] for t in TAILT],axis=0)
    summ[m]=dict(avg_pinball=round(float(pl.mean()),4),ES975_pred=round(float(esp.mean()),3),
                 ES975_realized=round(float(Y[b975].mean()),3) if b975.sum() else None,
                 breach99=round(float(b99.mean()),4),breach975=round(float(b975.mean()),4),
                 kupiec99_p=kupiec(int(b99.sum()),T,0.01),christ99_p=christ(b99,0.01),
                 kupiec975_p=kupiec(int(b975.sum()),T,0.025),christ975_p=christ(b975,0.025))
best=min(summ,key=lambda k:summ[k]['avg_pinball'])
Ld=pd.DataFrame({m:PLm[m] for m in Q}); Ld['date']=TE['date'].values; Lm=Ld.groupby('date').mean(); L=Lm.values; cols=list(Lm.columns)
def nwv(d,lag=10):
    d=d-d.mean(); v=np.mean(d*d)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(d[k:]*d[:-k])
    return v/len(d)
bi=cols.index(best); dm={}
for m in cols:
    if m==best: continue
    d=L[:,cols.index(m)]-L[:,bi]; s=d.mean()/math.sqrt(max(nwv(d),1e-12)); dm[m]=dict(DM_stat=round(float(s),2),p_one_sided=round(float(1-stats.norm.cdf(s)),4))
def mcs(L,alpha=0.10,B=800,blk=10):
    surv=list(range(L.shape[1])); pv={}
    def bidx(T):
        idx=np.empty(T,int); i=0
        while i<T:
            s=rng.integers(0,T); l=rng.geometric(1/blk)
            for j in range(l):
                if i<T: idx[i]=(s+j)%T; i+=1
        return idx
    while len(surv)>1:
        Ls=L[:,surv]; means=Ls.mean(0); M=len(surv); dij=means[:,None]-means[None,:]
        bd=np.zeros((B,M,M))
        for bb in range(B): ix=bidx(Ls.shape[0]); mb=Ls[ix].mean(0); bd[bb]=mb[:,None]-mb[None,:]
        varij=bd.var(0)+1e-12; TR=np.nanmax(np.abs(dij)/np.sqrt(varij))
        bootTR=np.array([np.nanmax(np.abs(bd[bb]-dij)/np.sqrt(varij)) for bb in range(B)])
        pval=float(np.mean(bootTR>=TR)); worst=surv[int(np.argmax(np.nanmax(dij/np.sqrt(varij),axis=1)))]; pv[cols[worst]]=round(pval,3)
        if pval>=alpha: break
        surv.remove(worst)
    return {'in_MCS_90':[cols[i] for i in surv],'elim_pvals':pv}
out={'note':'FRTB battery WITH CAViaR (Engle-Manganelli SAV). garch_t, GARCH-FHS, caviar_sav, hybrid_GBM (ML residual), '
            'hybrid_EVT (ML body+GPD tail). Metrics ES97.5+pinball; Kupiec/Christoffersen at BOTH 99% and 97.5%; DM+MCS.',
     'n_names':int(TE['permno'].nunique()),'n_test_rows':int(T),'per_model':summ,'best_model':best,'DM_vs_best':dm,'MCS':mcs(L)}
json.dump(out,open(os.path.join(D,"frtb_caviar_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
