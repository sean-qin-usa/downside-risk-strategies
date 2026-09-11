# job_bench_all.py -- EVERY STANDARD BENCHMARK ON THE CANONICAL ROWS, THROUGH EVERY STATISTIC.
# Extends job_garch_evt.py: the same 200-name panel, filter and splits as job_composite.py / job_fz_fullpanel.py,
# with the full comparison set of the paper on the same test rows:
#   garch_t, gjr_skewt, ewma (RiskMetrics 0.94, Gaussian), hs500 (rolling 500-day empirical return quantile),
#   fhs_pool, fhs_name, fhs_roll500 (GARCH-t scale times pooled / per-name / rolling-500 empirical residual quantiles),
#   sav_caviar (Engle-Manganelli SAV, one regression quantile per level per name, pinball-estimated on the estimation window [:sp]),
#   evt_name, evt_pool (McNeil-Frey GARCH-EVT), body (pooled boosted residual quantile), engine (body/EVT minimum),
#   and, at the two regulatory levels only, gas_pzc (Patton-Ziegel-Chen one-factor GAS) and taylor (Taylor ES-CAViaR),
#   both FZ0-estimated per name with three starts as in code/job_pzc_taylor.py.
# Statistics, all on the same rows: eleven-level pinball edge vs GARCH-t by score region (top mk63 decile, deciles 1-9,
# top composite decile, overall) with per-date NW(10) DM; engine head-to-head vs every model; Giacomini-White CPA of the
# loss differential on the lagged composite percentile; Murphy diagrams at 1% and 2.5%; Engle-Manganelli DQ pass rates;
# FZ0 at 1% and 2.5% with breach and DM vs the accuracy layer; dispersion of the per-date loss differential; and a
# 90% Model Confidence Set (Hansen-Lunde-Nason 2011, T_max, stationary bootstrap over dates, mean block 10, B=1000) on
# pinball and on FZ0 at each level. Output bench_all_results.json. Self-test: --synthetic.
import os, sys, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats, optimize
try:
    from arch import arch_model; GARCH_BACKEND="arch"
except ImportError:                       # sandbox self-test only; the Windows run uses arch
    GARCH_BACKEND="builtin_qml"
    class _Res:
        def __init__(s,p): s.params=p
    def _garch_t_fit(y):
        y=np.asarray(y,float); n=len(y); v0=np.var(y)
        def nll(th):
            mu,lom,la,lb,lnu=th; om=math.exp(lom); a=1/(1+math.exp(-la)); b=(1-a)/(1+math.exp(-lb)); nu=2.05+math.exp(lnu)
            e=y-mu; s2=np.empty(n); s2[0]=v0
            for k in range(1,n): s2[k]=om+a*e[k-1]**2+b*s2[k-1]
            sc=math.sqrt(nu/(nu-2))                     # standardized-t: unit variance
            zt=e/np.sqrt(s2)*sc
            ll=stats.t.logpdf(zt,nu)+math.log(sc)-0.5*np.log(s2)
            return -float(np.sum(ll)) if np.isfinite(ll).all() else 1e12
        x0=[float(np.mean(y)),math.log(0.05*v0),math.log(0.1/0.9),math.log(0.9/0.1),math.log(6-2.05)]
        r=optimize.minimize(nll,x0,method='Nelder-Mead',options={'maxiter':4000,'xatol':1e-6,'fatol':1e-6})
        mu,lom,la,lb,lnu=r.x; a=1/(1+math.exp(-la)); b=(1-a)/(1+math.exp(-lb))
        return _Res({'mu':mu,'omega':math.exp(lom),'alpha[1]':a,'beta[1]':b,'nu':2.05+math.exp(lnu)})
    class _AM:
        def __init__(s,y,**k): s.y=y
        def fit(s,**k): return _garch_t_fit(s.y)
    def arch_model(y,**k): return _AM(y)
P=os.environ.get("GBC_PROJ",r"C:\Users\OWNER\Claude\Projects\GBC Project"); t0=time.time(); lg=lambda s:print(s,flush=True)
SYN="--synthetic" in sys.argv
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
ALPHAS=[0.01,0.025]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
P0_ENGINE=0.025          # engine EVT threshold (job_fz_fullpanel.py)
P0_MF=0.10               # McNeil-Frey threshold: 10% of the training residuals per tail
P0_GRID=[0.025,0.05,0.10,0.15]
SUBN=20                  # sub-alpha midpoint nodes for the integrated ES (job_fz_fullpanel.py)
HGB=dict(max_iter=250,max_depth=3,learning_rate=0.06)

# ---------------------------------------------------------------- data
if SYN:
    rng=np.random.default_rng(7); recs=[]
    dates=pd.bdate_range("2004-01-01",periods=2600)
    for pn in range(24):
        om,al,be,nu=0.04,0.08,0.90,5.0+rng.uniform(-1,3)
        s2=np.empty(2600); e=np.empty(2600); s2[0]=om/(1-al-be)
        for k in range(2600):
            if k: s2[k]=om+al*e[k-1]**2+be*s2[k-1]
            z=stats.t.rvs(nu,random_state=rng)/math.sqrt(nu/(nu-2))
            if rng.uniform()<0.02: z-=rng.exponential(2.5)   # left jumps: real skew/kurtosis stress
            e[k]=math.sqrt(s2[k])*z
        recs.append(pd.DataFrame({'permno':pn,'date':dates,'ret':(0.02+e)/100.0}))
    rr=pd.concat(recs); NMAX=24
else:
    rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'}); NMAX=200
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:NMAX]

# ---------------------------------------------------------------- helpers
def pin(y,q,t): dd=y-q; return np.where(dd>=0,t*dd,(t-1)*dd)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    dm=x-x.mean(); v=np.mean(dm*dm)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(dm[k:]*dm[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
def conf_ostat(sc,tau):
    n=len(sc); k=int(math.ceil((n+1)*tau)); k=min(max(k,1),n)
    return float(np.sort(np.asarray(sc,float))[k-1])
def fz0(r,v,e,a):
    v=np.minimum(v,-1e-8); e=np.minimum(e,v)
    hit=(r<=v).astype(float)
    return -(1.0/(a*e))*hit*(v-r)+v/e+np.log(-e)-1.0
def t_es(a,nu):
    q=stats.t.ppf(a,nu); return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)
class GPDTail:
    """Lower-tail GPD on standardized residuals z: threshold u = empirical p0 quantile of z (training),
    excesses u - z for z < u, ML fit with location 0 (McNeil-Frey 2000)."""
    def __init__(self,z,p0,sign=-1):
        z=np.asarray(z,float); z=z[np.isfinite(z)]
        self.sign=sign; zz=sign*z                       # sign=-1: lower tail as losses; +1: upper tail
        self.u=float(np.quantile(zz,1-p0)); exc=zz[zz>self.u]-self.u
        self.p0=p0; self.n_exc=int(len(exc)); self.ok=self.n_exc>=20
        if self.ok:
            self.xi,_,self.beta=stats.genpareto.fit(exc,floc=0.0)
        else: self.xi,self.beta=np.nan,np.nan
    def q(self,tau):
        """tau is the residual-space level of the quantile in z-space (tau<=p0 for lower tail, tau>=1-p0 upper)."""
        p=tau if self.sign<0 else 1-tau                 # tail probability beyond u
        xi,b,u,p0=self.xi,self.beta,self.u,self.p0
        loss=u+(b/xi)*((p/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u+b*math.log(p0/p)
        return self.sign*loss
    def es(self,tau):
        """McNeil-Frey closed-form ES beyond the tau-quantile (lower tail), z-space; needs xi<1."""
        ql=-self.q(tau); xi,b,u=self.xi,self.beta,self.u
        if not (xi<1): return -np.inf
        return -(ql+(b+xi*(ql-u))/(1.0-xi))

def caviar_sav(rtrain,rfull,tau):
    """Symmetric absolute value CAViaR f_t = b1 + b2 f_{t-1} + b3 |r_{t-1}|, fitted by pinball on the training window."""
    r=rfull; n=len(r); q0=float(np.quantile(rtrain[:300],tau)); absr=np.abs(r); ntr=len(rtrain)
    def path(b,m):
        f=np.empty(m); f[0]=q0
        for i in range(1,m): f[i]=b[0]+b[1]*f[i-1]+b[2]*absr[i-1]
        return f
    def obj(b):
        if not (0<=b[1]<=0.999): return 1e6
        d=rtrain-path(b,ntr); return float(np.mean(np.where(d>=0,tau*d,(tau-1)*d)))
    b0=np.array([q0*0.1,0.8,-0.1 if tau<0.5 else 0.1])
    try: b=optimize.minimize(obj,b0,method='Nelder-Mead',options={'maxiter':300,'xatol':1e-3,'fatol':1e-6}).x
    except Exception: b=b0
    return path(b,n)
# ---------------------------------------------------------------- panel (identical construction to the canonical jobs)
TRz=[]; CALz=[]; rows=[]; NAME_TAILS={}; NAME_DIAG={}; GASROWS=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        pp=r1.params; om,al,be,mu=float(pp['omega']),float(pp['alpha[1]']),float(pp['beta[1]']),float(pp.get('mu',0)); nu=float(pp.get('nu',8))
    except Exception: continue
    e0=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e0[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    # per-name McNeil-Frey tails on this name's TRAINING residuals only (idx < cp)
    ztr=z[:cp]; lo=GPDTail(ztr,P0_MF,-1); hi=GPDTail(ztr,P0_MF,+1)
    NAME_TAILS[pn]=(lo,hi,ztr)
    NAME_DIAG[pn]={str(p0):GPDTail(ztr,p0,-1) for p0 in P0_GRID}
    # --- benchmark forecasts computed per name on the full history (test rows selected below) ---
    # GJR-GARCH-skew-t (Hansen), fitted on the estimation window, filtered through the history
    try:
        r2=arch_model(y[:sp],vol='Garch',p=1,o=1,q=1,dist='skewt',rescale=False).fit(disp='off',show_warning=False)
        q2=r2.params; om2,al2,ga2,be2,mu2=float(q2['omega']),float(q2['alpha[1]']),float(q2['gamma[1]']),float(q2['beta[1]']),float(q2.get('mu',0))
        eta2,lam2=float(q2['eta']),float(q2['lambda'])
        e2=y-mu2; s22=np.empty(n); s22[0]=np.var(y[:sp])
        for k in range(1,n): s22[k]=max(om2+al2*e2[k-1]**2+ga2*e2[k-1]**2*(e2[k-1]<0)+be2*s22[k-1],1e-8)
        sig2=np.sqrt(s22); skd=r2.model.distribution
        skq={t:float(skd.ppf(np.array([t]),[eta2,lam2])[0]) for t in TAUS}
        sub=np.linspace(0.0005,0.0995,200); ske={a:float(np.mean(skd.ppf(np.array([a*(j+0.5)/200 for j in range(200)]),[eta2,lam2]))) for a in ALPHAS}
    except Exception:
        sig2=None
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().abs().shift(1)
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    # EWMA (RiskMetrics): sigma^2_t = 0.94 sigma^2_{t-1} + 0.06 r^2_{t-1}, Gaussian quantile
    s2e=np.empty(n); s2e[0]=np.var(y[:250]) if n>250 else np.var(y)
    for k in range(1,n): s2e[k]=0.94*s2e[k-1]+0.06*y[k-1]**2
    df['sig_ewma']=np.sqrt(np.maximum(s2e,1e-8))
    if sig2 is not None:
        df['sig_gjr']=sig2; df['mu_gjr']=mu2
        for t in TAUS: df['gjrq_%g'%t]=skq[t]
        for a in ALPHAS: df['gjre_%g'%a]=ske[a]
    else:
        df['sig_gjr']=np.nan; df['mu_gjr']=np.nan
        for t in TAUS: df['gjrq_%g'%t]=np.nan
        for a in ALPHAS: df['gjre_%g'%a]=np.nan
    # rolling 500-day empirical quantiles of returns (HS) and of residuals (rolling FHS), lagged one day
    ys=pd.Series(y); zs=pd.Series(z)
    for t in TAUS:
        df['hs_%g'%t]=ys.rolling(500,min_periods=250).quantile(t).shift(1).values
        df['fhsr_%g'%t]=zs.rolling(500,min_periods=250).quantile(t).shift(1).values
        df['fhsn_%g'%t]=float(np.quantile(ztr,t))
    for a in ALPHAS:
        hs_e=ys.rolling(500,min_periods=250).apply(lambda w: w[w<=np.quantile(w,a)].mean(),raw=True).shift(1).values
        fr_e=zs.rolling(500,min_periods=250).apply(lambda w: w[w<=np.quantile(w,a)].mean(),raw=True).shift(1).values
        df['hse_%g'%a]=hs_e; df['fhsre_%g'%a]=fr_e; df['fhsne_%g'%a]=float(np.mean(ztr[ztr<=np.quantile(ztr,a)]))
    # SAV-CAViaR per level, pinball-estimated on the training window (idx < cp), full-path quantiles
    for t in TAUS: df['cav_%g'%t]=caviar_sav(y[:sp],y,t)     # estimation window [:sp], as for GARCH-t, GJR, GAS and Taylor (frtb_caviar_run.py convention)
    GASROWS.append((pn,y,cp))
    dd=df.dropna(subset=ZX+['mk63','skew63','jump5'])
    trn=dd[dd['idx']<cp]; cal=dd[(dd['idx']>=cp)&(dd['idx']<sp)]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(cal)<60:
        GASROWS.pop(); continue
    TRz.append(trn[ZX+['z']]); CALz.append(cal[ZX+['z']])
    t2=tst.copy(); t2['permno']=pn; rows.append(t2)
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz); CALzc=pd.concat(CALz)
lg("panel %d names %d test rows %.0fs"%(TE.permno.nunique(),len(TE),time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
PN=TE['permno'].values; dates=TE['date'].values
di,udates=pd.factorize(pd.to_datetime(dates),sort=True); di=np.asarray(di)

# ---------------------------------------------------------------- pooled EVT (engine threshold, as job_fz_fullpanel.py) and pooled McNeil-Frey
ztr_all=TRzc['z'].values
ENG_TAIL=GPDTail(ztr_all,P0_ENGINE,-1)
POOL_LO=GPDTail(ztr_all,P0_MF,-1); POOL_HI=GPDTail(ztr_all,P0_MF,+1)
POOL_DIAG={str(p0):GPDTail(ztr_all,p0,-1) for p0 in P0_GRID}
lg("engine GPD u=%.3f xi=%.3f beta=%.3f n_exc=%d | MF pooled lower u=%.3f xi=%.3f beta=%.3f n_exc=%d"%(
   -ENG_TAIL.u,ENG_TAIL.xi,ENG_TAIL.beta,ENG_TAIL.n_exc,-POOL_LO.u,POOL_LO.xi,POOL_LO.beta,POOL_LO.n_exc))

def mf_quantile(tail_lo,tail_hi,ztr,tau):
    if tau<=P0_MF and tail_lo.ok: return tail_lo.q(tau)
    if tau>=1-P0_MF and tail_hi.ok: return tail_hi.q(tau)
    return float(np.quantile(ztr,tau))
def mf_es(tail_lo,ztr,a):
    if tail_lo.ok and tail_lo.xi<1: return tail_lo.es(a)
    q=np.quantile(ztr,a); return float(np.mean(ztr[ztr<=q]))
# per-name z-quantiles (row-wise via permno map)
def per_name_map(fn):
    out=np.empty(len(Y)); cache={}
    for pn in np.unique(PN):
        cache[pn]=fn(pn)
    for pn,v in cache.items(): out[PN==pn]=v
    return out

# ---------------------------------------------------------------- pooled body (engine Stage 2), 11 levels + sub-alpha nodes
ZQ={}; ZQcal={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,random_state=0,**HGB).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=m.predict(TE[ZX].values); ZQcal[t]=m.predict(CALzc[ZX].values)
    lg("  body tau %.3f %.0fs"%(t,time.time()-t0))
ZQSUB={a:{} for a in ALPHAS}
for a in ALPHAS:
    for j in range(SUBN):
        uu=a*(j+0.5)/SUBN
        ZQSUB[a][j]=HistGradientBoostingRegressor(loss='quantile',quantile=uu,random_state=0,**HGB).fit(TRzc[ZX].values,TRzc['z'].values).predict(TE[ZX].values)
    lg("  sub-alpha grid a=%.3f %.0fs"%(a,time.time()-t0))
CONF975=conf_ostat(CALzc['z'].values-ZQcal[0.025],0.025)
lg("conf975 %+.4f"%CONF975)

# ---------------------------------------------------------------- return-space quantile forecasts for every model, 11 levels
G=lambda c: TE[c].values
Qz={'garch_t':{},'evt_name':{},'evt_pool':{},'body':{},'engine':{}}
for t in TAUS:
    Qz['garch_t'][t]=stats.t.ppf(t,NU)/TSC
    Qz['evt_name'][t]=per_name_map(lambda pn: mf_quantile(*NAME_TAILS[pn],t))
    Qz['evt_pool'][t]=np.full(len(Y),mf_quantile(POOL_LO,POOL_HI,ztr_all,t))
    Qz['body'][t]=ZQ[t]
    Qz['engine'][t]=np.minimum(ZQ[t],ENG_TAIL.q(t)) if t<=P0_ENGINE else ZQ[t]
Emat=np.sort(np.stack([Qz['engine'][t] for t in TAUS],axis=1),axis=1)       # monotone rearrangement of the engine curve
for j,t in enumerate(TAUS): Qz['engine'][t]=Emat[:,j]
RQ={m:{t:MU+SIG*Qz[m][t] for t in TAUS} for m in Qz}
RQ['fhs_pool']={t:MU+SIG*float(np.quantile(ztr_all,t)) for t in TAUS}
RQ['fhs_name']={t:MU+SIG*G('fhsn_%g'%t) for t in TAUS}
RQ['fhs_roll500']={t:MU+SIG*G('fhsr_%g'%t) for t in TAUS}
RQ['hs500']={t:G('hs_%g'%t) for t in TAUS}
RQ['ewma']={t:G('sig_ewma')*stats.norm.ppf(t) for t in TAUS}
RQ['gjr_skewt']={t:G('mu_gjr')+G('sig_gjr')*G('gjrq_%g'%t) for t in TAUS}
RQ['sav_caviar']={t:G('cav_%g'%t) for t in TAUS}
PIN_MODELS=list(RQ.keys())
PL={}
for m in PIN_MODELS:
    L=np.zeros(len(Y))
    for t in TAUS: L+=pin(Y,RQ[m][t],t)
    PL[m]=L/len(TAUS)
lg("pinball losses computed for %s; non-finite rows: %s"%(PIN_MODELS,{m:int((~np.isfinite(PL[m])).sum()) for m in PIN_MODELS}))
binds={str(a):round(float(np.mean(ENG_TAIL.q(a)<ZQ[a])),4) for a in ALPHAS}

def edge(Lref,Lm,mask):
    mask=mask&np.isfinite(Lref)&np.isfinite(Lm)
    if mask.sum()<30: return None
    d=(Lref-Lm)[mask]; g=pd.DataFrame({'d':d,'dt':di[mask]}).groupby('dt')['d'].mean()
    return {'edge_pct':round(100*float(d.mean())/float(Lref[mask].mean()),3),'DM':nw_t(g.values),'n':int(mask.sum()),'occupancy_pct':round(100*float(mask.mean()),2)}
def dec(x):
    r=np.full(len(x),-1); m=np.isfinite(x); r[m]=pd.qcut(pd.Series(x[m]),10,labels=False,duplicates='drop').values+1; return r
def pct(x):
    r=np.full(len(x),np.nan); m=np.isfinite(x); r[m]=pd.Series(x[m]).rank(pct=True).values; return r
mk=TE['mk63'].values; sk=TE['skew63'].values; jp=TE['jump5'].values
ok=np.isfinite(mk)&np.isfinite(sk)&np.isfinite(jp)
rk_mk=dec(mk); comp_pct=np.where(ok,np.fmax.reduce([pct(mk),pct(sk),pct(jp)]),np.nan); cdec=dec(comp_pct)
ALL=np.ones(len(Y),bool)
regions={'overall':ALL,'top_mk63_decile':rk_mk==10,'bulk_mk63_d1to9':(rk_mk>=1)&(rk_mk<=9),'top_composite_decile':cdec==10,'bulk_composite_d1to9':(cdec>=1)&(cdec<=9)}
pinball={'vs_garch_t':{m:{r:edge(PL['garch_t'],PL[m],msk) for r,msk in regions.items()} for m in PIN_MODELS if m!='garch_t'},
         'engine_vs':{m:{r:edge(PL[m],PL['engine'],msk) for r,msk in regions.items()} for m in PIN_MODELS if m!='engine'},
         'mk63_decile_profile':{m:{int(d0):edge(PL['garch_t'],PL[m],rk_mk==d0) for d0 in range(1,11)} for m in PIN_MODELS if m!='garch_t'},
         'mean_pinball':{m:round(float(np.nanmean(PL[m])),5) for m in PIN_MODELS}}
lg("top mk63 decile vs garch_t: "+json.dumps({m:pinball['vs_garch_t'][m]['top_mk63_decile'] for m in pinball['vs_garch_t']}))
lg("engine head-to-head (top decile): "+json.dumps({m:pinball['engine_vs'][m]['top_mk63_decile'] for m in pinball['engine_vs']}))

# ---------------------------------------------------------------- GAS (PZC 2019) and Taylor (2019) ES-CAViaR, FZ0-estimated per name, three starts
def gas_filter(y,a,b,om_,be_,ga_,k0,alpha):
    n=len(y); k=np.empty(n); k[0]=k0; v=np.empty(n); e=np.empty(n)
    for i in range(n):
        ex=math.exp(min(k[i],6.0)); v[i]=a*ex; e[i]=b*ex
        if i+1<n:
            hit=1.0 if y[i]<=v[i] else 0.0; H=(1.0/e[i])*((1.0/alpha)*hit*y[i]-e[i]); k[i+1]=om_+be_*k[i]+ga_*H
    return v,e
def taylor_filter(y,b1,b2,b3,delta,v0):
    n=len(y); v=np.empty(n); e=np.empty(n); v[0]=v0; mult=1.0+math.exp(min(delta,4.0))
    for i in range(n):
        if i>0: v[i]=b1+b2*v[i-1]+b3*abs(y[i-1])
        e[i]=v[i]*mult
    return v,e
GVE={a:(np.full(len(Y),np.nan),np.full(len(Y),np.nan)) for a in ALPHAS}; TVE={a:(np.full(len(Y),np.nan),np.full(len(Y),np.nan)) for a in ALPHAS}
gfail=tfail=0
for (pn_,y_,cp_) in GASROWS:
    sp_=int(len(y_)*0.6); tr=y_[max(0,sp_-1200):sp_]; msk=PN==pn_; nsel=int(msk.sum())
    if nsel==0: continue
    for a in ALPHAS:
        qa=float(np.quantile(tr,a)); ea=float(np.mean(tr[tr<=qa])) if (tr<=qa).any() else qa*1.2; eb=min(ea,qa*1.05)
        def obj(th):
            om_,be_,ga_=th
            if not (0.0<=be_<=0.999): return 1e6
            v,e=gas_filter(tr,qa,eb,om_,be_,ga_,0.0,a); L=fz0(tr,v,e,a); return float(np.mean(L)) if np.isfinite(L).all() else 1e6
        best=None
        for x0 in ([0.0,0.95,0.02],[0.0,0.90,0.05],[0.0,0.80,0.10]):
            try:
                res=optimize.minimize(obj,x0=x0,method='Nelder-Mead',options={'maxiter':120,'xatol':1e-3,'fatol':1e-4})
                if np.isfinite(res.fun) and (best is None or res.fun<best.fun): best=res
            except Exception: pass
        if best is None: gfail+=1
        else:
            v,e=gas_filter(y_,qa,eb,*best.x,0.0,a); GVE[a][0][msk]=v[-nsel:]; GVE[a][1][msk]=e[-nsel:]
        mult0=max(ea/qa,1.02) if qa<0 else 1.2; d0=math.log(max(mult0-1.0,1e-3))
        def objt(th):
            b1,b2,b3,dl=th
            if not (0.0<=b2<=0.999): return 1e6
            v,e=taylor_filter(tr,b1,b2,b3,dl,qa)
            if not np.isfinite(v).all(): return 1e6
            L=fz0(tr,v,e,a); return float(np.mean(L)) if np.isfinite(L).all() else 1e6
        best=None
        for x0 in ([qa*0.1,0.9,-0.05,d0],[qa*0.05,0.8,-0.10,d0],[qa*0.2,0.85,-0.02,d0]):
            try:
                res=optimize.minimize(objt,x0=x0,method='Nelder-Mead',options={'maxiter':200,'xatol':1e-3,'fatol':1e-4})
                if np.isfinite(res.fun) and (best is None or res.fun<best.fun): best=res
            except Exception: pass
        if best is None: tfail+=1
        else:
            v,e=taylor_filter(y_,*best.x,qa); TVE[a][0][msk]=v[-nsel:]; TVE[a][1][msk]=e[-nsel:]
lg("GAS/Taylor fitted (%d/%d fails) %.0fs"%(gfail,tfail,time.time()-t0))

# ---------------------------------------------------------------- (VaR, ES) pairs at the regulatory levels for every model
def star(a,use_evt):
    cols=[np.minimum(ZQSUB[a][j],ENG_TAIL.q(a*(j+0.5)/SUBN)) if use_evt else ZQSUB[a][j] for j in range(SUBN)]
    return np.sort(np.stack(cols,axis=1),axis=1)
VE={}
for a in ALPHAS:
    st=star(a,True); zq=np.maximum(np.minimum(ZQ[a],ENG_TAIL.q(a)),st[:,-1]); es=np.minimum(st.mean(axis=1),zq-1e-6)
    stb=star(a,False); zqb=np.maximum(ZQ[a],stb[:,-1]); esb=np.minimum(stb.mean(axis=1),zqb-1e-6)
    sh=CONF975 if a==0.025 else 0.0
    qe=stats.norm.ppf(a)
    VE[a]={'engine':(MU+SIG*zq,MU+SIG*es),
           'engine_overlay':(MU+SIG*(zq+sh),MU+SIG*(es+sh)),
           'body':(MU+SIG*zqb,MU+SIG*esb),
           'garch_t':(MU+SIG*stats.t.ppf(a,NU)/TSC,MU+SIG*t_es(a,NU)/TSC),
           'gjr_skewt':(G('mu_gjr')+G('sig_gjr')*G('gjrq_%g'%a),G('mu_gjr')+G('sig_gjr')*G('gjre_%g'%a)),
           'ewma':(G('sig_ewma')*qe,G('sig_ewma')*(-stats.norm.pdf(qe)/a)),
           'hs500':(G('hs_%g'%a),G('hse_%g'%a)),
           'fhs_pool':(MU+SIG*float(np.quantile(ztr_all,a)),MU+SIG*float(np.mean(ztr_all[ztr_all<=np.quantile(ztr_all,a)]))),
           'fhs_name':(MU+SIG*G('fhsn_%g'%a),MU+SIG*G('fhsne_%g'%a)),
           'fhs_roll500':(MU+SIG*G('fhsr_%g'%a),MU+SIG*G('fhsre_%g'%a)),
           'evt_pool':(MU+SIG*mf_quantile(POOL_LO,POOL_HI,ztr_all,a),MU+SIG*mf_es(POOL_LO,ztr_all,a)),
           'evt_name':(MU+SIG*per_name_map(lambda pn: mf_quantile(*NAME_TAILS[pn],a)),MU+SIG*per_name_map(lambda pn: mf_es(NAME_TAILS[pn][0],NAME_TAILS[pn][2],a))),
           'gas_pzc':GVE[a],'taylor':TVE[a],
           'sav_caviar':(G('cav_%g'%a),None)}
def dm_rows(Lm,Le,mask):
    mask=mask&np.isfinite(Lm)&np.isfinite(Le); d=(Lm-Le)[mask]
    if mask.sum()<30: return None
    g=pd.DataFrame({'d':d,'dt':di[mask]}).groupby('dt')['d'].mean(); t=nw_t(g.values)
    return {'mean_diff':round(float(np.mean(d)),5),'DM_t':t,'p_one_sided':None if t is None else round(float(1-stats.norm.cdf(t)),4),'n':int(mask.sum())}
FZ={}; FZL={}
for a in ALPHAS:
    ve,ee=VE[a]['engine']; Le=fz0(Y,ve,ee,a); out={}; FZL[a]={'engine':Le}
    for m,(vm,em) in VE[a].items():
        if em is None: continue
        Lm=fz0(Y,vm,em,a); FZL[a][m]=Lm; okm=np.isfinite(Lm)&np.isfinite(Le)
        if okm.sum()<1000: out[m]={'meanFZ0':None,'note':'no finite rows'}; continue
        rec={'meanFZ0':round(float(np.nanmean(Lm[okm])),5),'breach':round(float(np.mean((Y<=vm)[okm])),4),'n_finite':int(okm.sum())}
        if m!='engine':
            rec['vs_engine']=dm_rows(Lm,Le,ALL); rec['vs_engine_top_mk63']=dm_rows(Lm,Le,rk_mk==10); rec['vs_engine_bulk_mk63']=dm_rows(Lm,Le,(rk_mk>=1)&(rk_mk<=9))
        out[m]=rec
    FZ[str(a)]=out; lg("FZ0 alpha=%s: "%a+json.dumps({m:(out[m]['meanFZ0'],out[m].get('vs_engine',{}).get('DM_t') if out[m].get('vs_engine') else None) for m in out}))

# ---------------------------------------------------------------- CPA, Murphy, DQ, dispersion for every model
def nw_var(x,l=10):
    x=np.asarray(x,float); dm=x-x.mean(); v=np.mean(dm*dm)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(dm[k:]*dm[:-k])
    return v/len(x)
def cpa(Lref,Lm,score):
    ok=np.isfinite(score)&np.isfinite(Lref)&np.isfinite(Lm)
    if ok.sum()<1000: return None
    d=(Lref-Lm)[ok]; h=np.stack([np.ones(ok.sum()),score[ok]],axis=1); dd=di[ok]
    hd=pd.DataFrame(h*d[:,None]).groupby(dd).sum().values; T=len(hd); m=hd.mean(axis=0); X=hd-m; V=X.T@X/T
    for k in range(1,11): V+=(1-k/11)*((X[k:].T@X[:-k])+(X[:-k].T@X[k:]))/T
    W=float(T*m@np.linalg.solve(V,m))
    sc=score[ok]; xbar=sc.mean(); dbar=d.mean(); num=pd.Series((sc-xbar)*(d-dbar)).groupby(dd).sum().values; den=float(((sc-xbar)**2).sum())
    b=float(num.sum()/den); u=pd.Series((sc-xbar)*(d-b*(sc-xbar)-dbar)).groupby(dd).sum().values; se=len(u)*math.sqrt(max(nw_var(u),1e-30))/den
    return {'GW_wald_chi2_2':round(W,2),'p':round(float(1-stats.chi2.cdf(W,2)),4),'slope_d_on_score':round(b,6),'slope_t':round(b/se,2),'n_dates':int(T)}
CPA={m:cpa(PL[m],PL['engine'],comp_pct) for m in PIN_MODELS if m!='engine'}
CPA['garch_t_vs_engine_mk63pct']=cpa(PL['garch_t'],PL['engine'],pct(mk)); CPA['garch_t_vs_body']=cpa(PL['garch_t'],PL['body'],comp_pct)
lg("CPA: "+json.dumps({m:((v['GW_wald_chi2_2'],v['slope_t']) if v else None) for m,v in CPA.items()}))
def murphy(qA,qB,a,thetas):
    okq=np.isfinite(qA)&np.isfinite(qB)
    if okq.sum()<1000: return None
    yA=Y[okq]; qA=qA[okq]; qB=qB[okq]; out=[]
    for th in thetas:
        sA=np.mean(((yA<qA).astype(float)-a)*((th<qA).astype(float)-(th<yA).astype(float)))
        sB=np.mean(((yA<qB).astype(float)-a)*((th<qB).astype(float)-(th<yA).astype(float)))
        out.append(float(sA-sB))
    return out
THETAS=[float(v) for v in np.quantile(Y,np.linspace(0.001,0.15,40))]
MUR={'theta_grid_return_space':[round(t,4) for t in THETAS]}
for a in ALPHAS:
    qe_=VE[a]['engine'][0]; rec={}
    for m in VE[a]:
        if m=='engine': continue
        dv=murphy(qe_,VE[a][m][0],a,THETAS)
        if dv is None: rec[m]=None; continue
        rec[m]={'engine_minus':[round(v,7) for v in dv],'frac_theta_engine_better':round(float(np.mean(np.array(dv)<0)),3),'max_engine_worse':round(float(max(dv)),7),'min':round(float(min(dv)),7)}
    MUR[str(a)]=rec; lg("Murphy a=%s: "%a+json.dumps({m:(rec[m]['frac_theta_engine_better'] if rec[m] else None) for m in rec}))
def dq(hit,v,a,L=4):
    n=len(hit)
    if n<L+30: return None
    H=hit[L:]-a; X=np.column_stack([np.ones(n-L)]+[hit[L-k:n-k]-a for k in range(1,L+1)]+[v[L:]])
    try:
        b=np.linalg.lstsq(X,H,rcond=None)[0]; st=float(b@X.T@X@b/(a*(1-a))); return float(1-stats.chi2.cdf(st,X.shape[1]))
    except Exception: return None
DQ={}
for a in ALPHAS:
    rec={}
    for m in VE[a]:
        v=VE[a][m][0]; okv=np.isfinite(v); hit=(Y<=v).astype(float); ps=[]
        for pn_ in np.unique(PN):
            msk=(PN==pn_)&okv
            if msk.sum()<100: continue
            p_=dq(hit[msk],v[msk],a)
            if p_ is not None: ps.append(p_)
        rec[m]={'dq_passrate_5pct':round(float(np.mean([x>0.05 for x in ps])),3) if ps else None,'n_names':len(ps),'breach':round(float(hit[okv].mean()),4)}
    DQ[str(a)]=rec; lg("DQ a=%s: "%a+json.dumps({m:rec[m]['dq_passrate_5pct'] for m in rec}))
def disp(Lref,Lm,mask):
    mask=mask&np.isfinite(Lref)&np.isfinite(Lm)
    if mask.sum()<1000: return None
    g=pd.DataFrame({'d':(Lref-Lm)[mask],'dt':di[mask]}).groupby('dt')['d'].mean().values; q=np.percentile(g,[5,25,50,75,95])
    return {'win_rate_dates':round(float(np.mean(g>0)),3),'q05_q25_q50_q75_q95':[round(float(x),6) for x in q],'sd':round(float(g.std()),6),'n_dates':int(len(g))}
DISP={r:{m:disp(PL[m],PL['engine'],msk) for m in PIN_MODELS if m!='engine'} for r,msk in [('overall',ALL),('top_mk63_decile',rk_mk==10),('bulk_mk63_d1to9',(rk_mk>=1)&(rk_mk<=9))]}

# ---------------------------------------------------------------- Model Confidence Set (Hansen, Lunde, Nason 2011), T_max, stationary bootstrap over dates
def mcs(Lmat,names_,B=1000,alpha=0.10,block=10,seed=0):
    T,M=Lmat.shape; rng_=np.random.default_rng(seed)
    idx=np.empty((B,T),dtype=int)
    for b in range(B):                                         # stationary bootstrap: geometric blocks, mean length `block`
        t_=0; pos=rng_.integers(T)
        while t_<T:
            if rng_.uniform()<1.0/block: pos=rng_.integers(T)
            idx[b,t_]=pos; pos=(pos+1)%T; t_+=1
    alive=list(range(M)); pv={}; pmax=0.0
    while len(alive)>1:
        L=Lmat[:,alive]; dbar=L.mean(axis=0)-L.mean(); Lb=L[idx].mean(axis=1); dbarb=Lb-Lb.mean(axis=1,keepdims=True)
        var=((dbarb-dbar)**2).mean(axis=0); tstat=dbar/np.sqrt(np.maximum(var,1e-30)); Tmax=float(tstat.max())
        Tb=((dbarb-dbar)/np.sqrt(np.maximum(var,1e-30))).max(axis=1); p=float(np.mean(Tb>=Tmax)); pmax=max(pmax,p)
        worst=alive[int(np.argmax(tstat))]; pv[names_[worst]]=round(pmax,4)
        if pmax>=alpha: break
        alive.remove(worst)
    for i in alive: pv.setdefault(names_[i],round(max(pmax,1.0) if len(alive)==1 else pmax,4))
    return {'in_90pct_MCS':[names_[i] for i in alive],'mcs_pvalues':pv}
def date_matrix(losses):
    names_=[m for m in losses if np.isfinite(losses[m]).all()]
    dfm=pd.DataFrame({m:losses[m] for m in names_}); dfm['dt']=di
    return dfm.groupby('dt')[names_].mean().values, names_
Lm_,nm_=date_matrix(PL); MCS={'pinball_11tau':mcs(Lm_,nm_)}
MCS['pinball_11tau']['models_with_missing_rows_excluded']=[m for m in PL if m not in nm_]
for a in ALPHAS:
    Lm_,nm_=date_matrix(FZL[a]); MCS['fz0_%g'%a]=mcs(Lm_,nm_); MCS['fz0_%g'%a]['models_with_missing_rows_excluded']=[m for m in FZL[a] if m not in nm_]
lg("MCS: "+json.dumps({k:v['in_90pct_MCS'] for k,v in MCS.items()}))

OUT={'note':('Every standard benchmark on the same rows as job_composite.py / job_fz_fullpanel.py (see header). Pinball block: eleven-level '
  'mean pinball, edge=(ref-model)/ref, per-date NW(10) DM, engine = body/EVT minimum with rearrangement and no shift. FZ0 block: '
  'reference is the unshifted accuracy layer; DM_t>0 means the row model is worse. cpa: Giacomini-White Wald of E[d|1,score]=0 with '
  'd=L_model-L_engine on the lagged composite percentile. murphy: elementary quantile score engine minus model over a return-space '
  'theta grid, negative = engine better. dq: Engle-Manganelli test, 4 hit lags + VaR, per-name pass rate at 5%. mcs: 90% Model '
  'Confidence Set, T_max, stationary bootstrap over dates (mean block 10, B=1000); models with any non-finite row are excluded.'),
 'synthetic':SYN,'garch_backend':GARCH_BACKEND,'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),'conf975':round(CONF975,4),
 'gas_taylor_fails':[gfail,tfail],'pinball':pinball,'fz0':FZ,'cpa':CPA,'murphy':MUR,'dq':DQ,'loss_diff_dispersion':DISP,'mcs':MCS,
 'evt_branch_binds_frac':binds}
fn="bench_all_results_synthetic.json" if SYN else "bench_all_results.json"
json.dump(OUT,open(os.path.join(P,fn),"w"),indent=2)
lg("BENCHALLDONE %.0fs"%(time.time()-t0))
