# job_garch_evt.py -- STANDALONE GARCH-EVT (McNeil-Frey) HEAD-TO-HEAD + FOUR-WAY COMPONENT COMPARISON.
# Fills the missing benchmark flagged by the advisor and the ChatGPT referee rounds: the manuscript
# compares the engine to GARCH-t, FHS, GAS/PZC and CAViaR but never to a conventional GARCH-EVT
# tail on the same rows. This job rebuilds the exact panel, filter and splits of job_composite.py
# (11-level pinball frontier by mk63 decile and composite decile) and job_fz_fullpanel.py (FZ0 joint
# (VaR,ES) at 1% and 2.5%) and adds, on the SAME test rows:
#   garch_t        GARCH(1,1)-t per name (the paper's reference model)
#   evt_name       McNeil-Frey per name: GARCH filter + two-sided GPD tails on that name's own
#                  training residuals, threshold = empirical p0 point of the training residuals,
#                  empirical residual quantiles between the thresholds (FHS body)
#   evt_pool       same construction with ONE pooled threshold and ONE (xi,beta) per tail fitted
#                  on the pooled training residuals of all names (the conventional tail, pooled)
#   body           GARCH + pooled gradient-boosted residual body, no EVT, no rearrangement
#                  (this is the object scored in job_composite.py, i.e. the frontier headline)
#   engine         body/EVT minimum envelope + monotone rearrangement on the tau grid
#                  (Stage 3 of the paper; the FZ0 block scores this unshifted accuracy layer as the reference
#                  at both levels and reports the 97.5% conformal overlay as its own row; the pinball block
#                  carries no shift, matching job_composite.py)
# Thresholds, GPD parameters and body fits use training rows only (idx < cp = 0.45 n); the
# conformal shift uses the calibration split [cp, sp); everything is scored on idx >= sp.
# Reports: 11-tau pinball edge vs garch_t for every method, overall and by mk63 decile and by
# composite decile; head-to-head engine-vs-EVT edges with per-date NW(10) DM (top decile, bulk
# deciles 1-9, overall); FZ0 at 1% and 2.5% with breach rates and DM vs engine; GPD threshold
# diagnostics (exceedance counts, xi, beta over a p0 grid, pooled and per-name spread); how often
# the EVT branch binds inside the engine's minimum at 1% and 2.5%.
# Pre-set write-up rule (TODO C.3): engine beats evt_pool in the top decile at DM > 2 and is within
# noise in the bulk -> the frontier claim stands; top-decile edge within noise -> the estimator
# claim narrows to "the pooled shape learner matches a conventional EVT tail" and the score keeps
# its role as a monitor.
# Self-test: `python job_garch_evt.py --synthetic` builds a 24-name GARCH-t-with-jumps panel in
# memory, runs the whole pipeline and writes garch_evt_results_synthetic.json. Set GBC_PROJ to
# override the project path.
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

# ---------------------------------------------------------------- panel (identical construction to the canonical jobs)
TRz=[]; CALz=[]; rows=[]; NAME_TAILS={}; NAME_DIAG={}
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
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().abs().shift(1)
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=ZX+['mk63','skew63','jump5'])
    trn=dd[dd['idx']<cp]; cal=dd[(dd['idx']>=cp)&(dd['idx']<sp)]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(cal)<60: continue
    # per-name McNeil-Frey tails on this name's TRAINING residuals only (idx < cp)
    ztr=z[:cp]; lo=GPDTail(ztr,P0_MF,-1); hi=GPDTail(ztr,P0_MF,+1)
    NAME_TAILS[pn]=(lo,hi,ztr)
    NAME_DIAG[pn]={str(p0):GPDTail(ztr,p0,-1) for p0 in P0_GRID}
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

# ---------------------------------------------------------------- 11-tau pinball block (job_composite.py convention: engine = body, no shift)
Q={'garch_t':{},'evt_name':{},'evt_pool':{},'body':{},'engine':{}}
for t in TAUS:
    Q['garch_t'][t]=stats.t.ppf(t,NU)/TSC
    Q['evt_name'][t]=per_name_map(lambda pn: mf_quantile(*NAME_TAILS[pn],t))
    Q['evt_pool'][t]=np.full(len(Y),mf_quantile(POOL_LO,POOL_HI,ztr_all,t))
    Q['body'][t]=ZQ[t]
    Q['engine'][t]=np.minimum(ZQ[t],ENG_TAIL.q(t)) if t<=P0_ENGINE else ZQ[t]
# monotone rearrangement of the engine curve across the 11-level grid
Emat=np.sort(np.stack([Q['engine'][t] for t in TAUS],axis=1),axis=1)
for j,t in enumerate(TAUS): Q['engine'][t]=Emat[:,j]
PL={}
for m in Q:
    L=np.zeros(len(Y))
    for t in TAUS: L+=pin(Y,MU+SIG*Q[m][t],t)
    PL[m]=L/len(TAUS)
binds={str(a):round(float(np.mean(ENG_TAIL.q(a)<ZQ[a])),4) for a in ALPHAS}   # EVT branch binds inside the minimum

def edge(Lref,Lm,mask):
    if mask.sum()<30: return None
    d=(Lref-Lm)[mask]
    g=pd.DataFrame({'d':d,'dt':di[mask]}).groupby('dt')['d'].mean()
    return {'edge_pct':round(100*float(d.mean())/float(Lref[mask].mean()),3),'DM':nw_t(g.values),
            'n':int(mask.sum()),'occupancy_pct':round(100*float(mask.mean()),2)}
def dec(x):
    r=np.full(len(x),-1); m=np.isfinite(x)
    r[m]=pd.qcut(pd.Series(x[m]),10,labels=False,duplicates='drop').values+1
    return r
def pct(x):
    r=np.full(len(x),np.nan); m=np.isfinite(x); r[m]=pd.Series(x[m]).rank(pct=True).values
    return r
mk=TE['mk63'].values; sk=TE['skew63'].values; jp=TE['jump5'].values
ok=np.isfinite(mk)&np.isfinite(sk)&np.isfinite(jp)
rk_mk=dec(mk)
comp_pct=np.where(ok,np.fmax.reduce([pct(mk),pct(sk),pct(jp)]),np.nan); cdec=dec(comp_pct)
ALL=np.ones(len(Y),bool)
regions={'overall':ALL,'top_mk63_decile':rk_mk==10,'bulk_mk63_d1to9':(rk_mk>=1)&(rk_mk<=9),
         'top_composite_decile':cdec==10,'bulk_composite_d1to9':(cdec>=1)&(cdec<=9)}
pinball={'vs_garch_t':{m:{r:edge(PL['garch_t'],PL[m],msk) for r,msk in regions.items()} for m in Q if m!='garch_t'},
         'engine_vs_evt_pool':{r:edge(PL['evt_pool'],PL['engine'],msk) for r,msk in regions.items()},
         'engine_vs_evt_name':{r:edge(PL['evt_name'],PL['engine'],msk) for r,msk in regions.items()},
         'body_vs_evt_pool':{r:edge(PL['evt_pool'],PL['body'],msk) for r,msk in regions.items()},
         'engine_vs_body':{r:edge(PL['body'],PL['engine'],msk) for r,msk in regions.items()},
         'mk63_decile_profile':{m:{int(d0):edge(PL['garch_t'],PL[m],rk_mk==d0) for d0 in range(1,11)} for m in ['evt_pool','evt_name','body','engine']},
         'composite_decile_profile':{m:{int(d0):edge(PL['garch_t'],PL[m],cdec==d0) for d0 in range(1,11)} for m in ['evt_pool','evt_name','body','engine']},
         'mean_pinball':{m:round(float(PL[m].mean()),5) for m in Q}}
lg("pinball top mk63 decile: "+json.dumps({m:pinball['vs_garch_t'][m]['top_mk63_decile'] for m in pinball['vs_garch_t']}))
lg("engine vs evt_pool: "+json.dumps(pinball['engine_vs_evt_pool']))

# ---------------------------------------------------------------- FZ0 block (job_fz_fullpanel.py convention: coherent Q*, conformal at 97.5%)
def star(a,use_evt):
    cols=[np.minimum(ZQSUB[a][j],ENG_TAIL.q(a*(j+0.5)/SUBN)) if use_evt else ZQSUB[a][j] for j in range(SUBN)]
    return np.sort(np.stack(cols,axis=1),axis=1)
VE={}
for a in ALPHAS:
    st=star(a,True); zq=np.maximum(np.minimum(ZQ[a],ENG_TAIL.q(a)),st[:,-1]); es=np.minimum(st.mean(axis=1),zq-1e-6)
    stb=star(a,False); zqb=np.maximum(ZQ[a],stb[:,-1]); esb=np.minimum(stb.mean(axis=1),zqb-1e-6)
    sh=CONF975 if a==0.025 else 0.0
    # accuracy layer (no shift) is the reference at BOTH levels, as in the paper; the overlay is its own row
    VE[a]={'engine':(MU+SIG*zq,MU+SIG*es),
           'engine_overlay':(MU+SIG*(zq+sh),MU+SIG*(es+sh)),
           'body':(MU+SIG*zqb,MU+SIG*esb),
           'garch_t':(MU+SIG*stats.t.ppf(a,NU)/TSC,MU+SIG*t_es(a,NU)/TSC),
           'evt_pool':(MU+SIG*mf_quantile(POOL_LO,POOL_HI,ztr_all,a),MU+SIG*mf_es(POOL_LO,ztr_all,a)),
           'evt_name':(MU+SIG*per_name_map(lambda pn: mf_quantile(*NAME_TAILS[pn],a)),
                       MU+SIG*per_name_map(lambda pn: mf_es(NAME_TAILS[pn][0],NAME_TAILS[pn][2],a)))}
def dm_rows(Lm,Le,mask):
    d=(Lm-Le)[mask]; g=pd.DataFrame({'d':d,'dt':di[mask]}).groupby('dt')['d'].mean(); t=nw_t(g.values)
    return {'mean_diff':round(float(np.nanmean(d)),5),'DM_t':t,'p_one_sided':None if t is None else round(float(1-stats.norm.cdf(t)),4)}
FZ={}
for a in ALPHAS:
    ve,ee=VE[a]['engine']; Le=fz0(Y,ve,ee,a); out={}
    for m,(vm,em) in VE[a].items():
        Lm=fz0(Y,vm,em,a); okm=np.isfinite(Lm)&np.isfinite(Le)
        rec={'meanFZ0':round(float(np.nanmean(Lm[okm])),5),'breach':round(float(np.mean((Y<=vm)[okm])),4)}
        if m!='engine':
            rec['vs_engine']=dm_rows(Lm,Le,okm)
            rec['vs_engine_top_mk63']=dm_rows(Lm,Le,okm&(rk_mk==10))
            rec['vs_engine_bulk_mk63']=dm_rows(Lm,Le,okm&(rk_mk>=1)&(rk_mk<=9))
        out[m]=rec
    # engine vs evt_pool as an edge in FZ0 units too
    Lp=fz0(Y,*VE[a]['evt_pool'],a)
    out['engine_vs_evt_pool_top_mk63']=dm_rows(Lp,Le,rk_mk==10)
    FZ[str(a)]=out; lg("FZ0 alpha=%s: "%a+json.dumps({m:out[m].get('vs_engine') for m in out if isinstance(out[m],dict) and 'vs_engine' in out[m]}))

# ---------------------------------------------------------------- GPD threshold diagnostics
def tail_rec(t): return {'u_z':round(-t.u,4),'n_exc':t.n_exc,'xi':None if not t.ok else round(float(t.xi),4),'beta':None if not t.ok else round(float(t.beta),4)}
diag={'engine_pooled_p0_0.025':tail_rec(ENG_TAIL),
      'pooled_grid':{k:tail_rec(v) for k,v in POOL_DIAG.items()},
      'per_name_grid':{},
      'evt_branch_binds_frac':binds,
      'n_names_lower_tail_fit_ok_p0_0.10':int(sum(1 for pn in NAME_TAILS if NAME_TAILS[pn][0].ok)),
      'n_names_xi_ge_1_p0_0.10':int(sum(1 for pn in NAME_TAILS if NAME_TAILS[pn][0].ok and NAME_TAILS[pn][0].xi>=1))}
for p0 in P0_GRID:
    xs=np.array([NAME_DIAG[pn][str(p0)].xi for pn in NAME_DIAG if NAME_DIAG[pn][str(p0)].ok])
    bs=np.array([NAME_DIAG[pn][str(p0)].beta for pn in NAME_DIAG if NAME_DIAG[pn][str(p0)].ok])
    ns=np.array([NAME_DIAG[pn][str(p0)].n_exc for pn in NAME_DIAG])
    diag['per_name_grid'][str(p0)]={'n_fit_ok':int(len(xs)),'n_exc_median':int(np.median(ns)),
        'xi_q25_50_75':[round(float(v),4) for v in np.percentile(xs,[25,50,75])] if len(xs) else None,
        'beta_q25_50_75':[round(float(v),4) for v in np.percentile(bs,[25,50,75])] if len(bs) else None}

OUT={'note':('Standalone GARCH-EVT (McNeil-Frey) benchmark on the SAME rows as job_composite.py and job_fz_fullpanel.py. '
  'evt_name = per-name two-sided GPD at p0=0.10 on training residuals; evt_pool = one pooled threshold and (xi,beta) per tail. '
  'body = GARCH + pooled boosted residual quantile, no EVT (the job_composite.py engine); engine = body/EVT minimum + rearrangement '
  '(pooled p0=0.025 tail, as job_fz_fullpanel.py). Pinball block: 11-tau mean pinball, edge=(ref-method)/ref, per-date NW(10) DM, no conformal shift. '
  'FZ0 block: (VaR,ES) at 1% and 2.5%; the reference engine is the unshifted accuracy layer at both levels (as in the paper), engine_overlay adds the 97.5% conformal shift; DM_t>0 means the row model is WORSE than the accuracy layer. '
  'Write-up rule pre-set in the script header.'),
 'synthetic':SYN,'garch_backend':GARCH_BACKEND,'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),'conf975':round(CONF975,4),
 'pinball':pinball,'fz0':FZ,'gpd_diagnostics':diag}
fn="garch_evt_results_synthetic.json" if SYN else "garch_evt_results.json"
json.dump(OUT,open(os.path.join(P,fn),"w"),indent=2)
lg("GARCHEVTDONE %.0fs"%(time.time()-t0))

# ---------------------------------------------------------------- extras: CPA regression, Murphy diagrams, DQ test, loss-differential dispersion
# (a) Giacomini-White conditional predictive ability. Asset-day loss differential d_it = L_ref - L_engine (11-tau pinball),
#     instruments h_it = (1, lagged composite percentile). Per-date sums of h_it d_it give a T x 2 series; Wald statistic
#     with a Newey-West(10) covariance is the GW test of E[d | score] = 0. Also reported: the slope of d on the score.
def cpa(Lref,Lm,score):
    ok=np.isfinite(score); d=(Lref-Lm)[ok]; h=np.stack([np.ones(ok.sum()),score[ok]],axis=1); dd=di[ok]
    hd=pd.DataFrame(h*d[:,None]).groupby(dd).sum().values           # per-date sums of h*d
    T=len(hd); m=hd.mean(axis=0); X=hd-m; V=X.T@X/T
    for k in range(1,11): V+=(1-k/11)*((X[k:].T@X[:-k])+(X[:-k].T@X[k:]))/T
    W=float(T*m@np.linalg.solve(V,m))
    # slope of d on the score, date-clustered t
    cnt=pd.Series(np.ones(ok.sum())).groupby(dd).sum().values; xbar=score[ok].mean(); dbar=d.mean()
    sc=score[ok]; num=pd.Series((sc-xbar)*(d-dbar)).groupby(dd).sum().values; den=float(((sc-xbar)**2).sum())
    b=float(num.sum()/den); u=pd.Series((sc-xbar)*(d-b*(sc-xbar)-dbar)).groupby(dd).sum().values
    se=len(u)*math.sqrt(max(nw_var(u),1e-30))/den            # Var(sum_t u_t) = T^2 * nw_var(u)
    return {'GW_wald_chi2_2':round(W,2),'p':round(float(1-stats.chi2.cdf(W,2)),4),'slope_d_on_score':round(b,6),'slope_t':round(b/se,2),'n_dates':int(T)}
def nw_var(x,l=10):
    x=np.asarray(x,float); dm=x-x.mean(); v=np.mean(dm*dm)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(dm[k:]*dm[:-k])
    return v/len(x)
CPA={'garch_t_vs_engine':cpa(PL['garch_t'],PL['engine'],comp_pct),'evt_pool_vs_engine':cpa(PL['evt_pool'],PL['engine'],comp_pct),
     'garch_t_vs_body':cpa(PL['garch_t'],PL['body'],comp_pct),'garch_t_vs_engine_mk63pct':cpa(PL['garch_t'],PL['engine'],pct(mk))}
lg("CPA: "+json.dumps(CPA))
# (b) Murphy diagrams (Ehm, Gneiting, Jordan, Kruger 2016): elementary quantile score S_theta(q,y)=(1{y<q}-a)(1{theta<q}-1{theta<y}),
#     averaged over the panel on a theta grid of return-space quantiles; engine minus competitor, negative = engine better.
def murphy(qA,qB,a,thetas):
    out=[]
    for th in thetas:
        sA=np.mean((( (Y<qA).astype(float)-a)*((th<qA).astype(float)-(th<Y).astype(float))))
        sB=np.mean((( (Y<qB).astype(float)-a)*((th<qB).astype(float)-(th<Y).astype(float))))
        out.append(float(sA-sB))
    return out
THETAS=[float(v) for v in np.quantile(Y,np.linspace(0.001,0.15,40))]
MUR={'theta_grid_return_space':[round(t,4) for t in THETAS]}
for a in ALPHAS:
    qe=VE[a]['engine'][0]; rec={}
    for m in ['garch_t','evt_pool','evt_name','body']:
        dv=murphy(qe,VE[a][m][0],a,THETAS); rec[m]={'engine_minus_%s'%m:[round(v,7) for v in dv],
            'frac_theta_engine_better':round(float(np.mean(np.array(dv)<0)),3),'max_engine_worse':round(float(max(dv)),7)}
    MUR[str(a)]=rec
    lg("Murphy a=%s: "%a+json.dumps({m:(rec[m]['frac_theta_engine_better'],rec[m]['max_engine_worse']) for m in rec}))
# (c) Engle-Manganelli dynamic quantile test per name (4 hit lags plus the VaR), pass rate at 5% across names; pooled version too.
def dq(hit,v,a,L=4):
    n=len(hit); 
    if n<L+30: return None
    H=hit[L:]-a; X=np.column_stack([np.ones(n-L)]+[hit[L-k:n-k]-a for k in range(1,L+1)]+[v[L:]])
    try:
        b=np.linalg.lstsq(X,H,rcond=None)[0]; st=float(b@X.T@X@b/(a*(1-a)))
        return float(1-stats.chi2.cdf(st,X.shape[1]))
    except Exception: return None
DQ={}
for a in ALPHAS:
    rec={}
    for m in ['engine','engine_overlay','garch_t','evt_pool','evt_name','body']:
        v=VE[a][m][0]; hit=(Y<=v).astype(float); ps=[]
        for pn_ in np.unique(PN):
            msk=PN==pn_; p_=dq(hit[msk],v[msk],a)
            if p_ is not None: ps.append(p_)
        rec[m]={'dq_passrate_5pct':round(float(np.mean([x>0.05 for x in ps])),3),'n_names':len(ps),'pooled_dq_p':dq(hit,v,a)}
    DQ[str(a)]=rec; lg("DQ a=%s: "%a+json.dumps({m:rec[m]['dq_passrate_5pct'] for m in rec}))
# (d) dispersion of the per-date loss differential (engine over reference), 11-tau pinball
def disp(Lref,Lm,mask):
    g=pd.DataFrame({'d':(Lref-Lm)[mask],'dt':di[mask]}).groupby('dt')['d'].mean().values
    q=np.percentile(g,[5,25,50,75,95])
    return {'win_rate_dates':round(float(np.mean(g>0)),3),'q05_q25_q50_q75_q95':[round(float(x),6) for x in q],'sd':round(float(g.std()),6),'n_dates':int(len(g))}
DISP={r:{'garch_t':disp(PL['garch_t'],PL['engine'],msk),'evt_pool':disp(PL['evt_pool'],PL['engine'],msk)} for r,msk in regions.items()}
OUT['extras']={'cpa':CPA,'murphy':MUR,'dq':DQ,'loss_diff_dispersion':DISP,
  'note':'cpa: Giacomini-White Wald test of E[d|1,score]=0 with d=L_ref-L_engine per asset-day, NW(10) over per-date sums; murphy: mean elementary quantile score engine minus competitor over a return-space theta grid (negative = engine better at that theta); dq: Engle-Manganelli test with 4 hit lags and the VaR, per-name pass rate at 5% and pooled p; dispersion: per-date loss differential engine over reference.'}
json.dump(OUT,open(os.path.join(P,fn),"w"),indent=2)
lg("EXTRASDONE %.0fs"%(time.time()-t0))
