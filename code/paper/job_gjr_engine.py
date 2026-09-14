# job_gjr_engine.py -- THE ENGINE WITH A GJR-t (LEVERAGE) STAGE-1 FILTER, ON THE CANONICAL ROWS.
# Question: the accuracy layer is third on mean FZ0 at 2.5% behind GJR-GARCH-skew-t and Taylor ES-CAViaR (bench_all_results.json,
# gaps 0.0007 and 0.0004, DM -0.28 and -0.12). The paper's own Stage 1 is a symmetric GARCH(1,1)-t; GJR adds a leverage term,
# "the component the ARCH family already estimates well once a leverage term is allowed" (Section 1). This job rebuilds the
# engine on a GJR(1,1)-t filter, every downstream stage re-estimated on the GJR residuals (features, score, pooled body,
# pooled GPD tail at p0=0.025, conformal shift), and scores it on the identical 221,600 test rows against the same benchmarks.
# Nothing about the benchmarks changes; the paper's GARCH-t engine is re-run alongside as the reference.
#
# PREDICTION, WRITTEN BEFORE THE RUN (2026-09-14): at 2.5% the GJR-filtered engine's mean FZ0 lands within 0.0005 of
# GJR-GARCH-skew-t (DM against it within +/-1.0); at 1% it keeps the GARCH-t engine's lead over GJR (DM >= 1) or widens it;
# its top-mk63-decile pinball edge over GARCH-t stays within 0.5 points of the GARCH-t engine's +2.48% (engine) / +2.98% (body).
# If the 2.5% gap does not close, the leverage term is not the reason the engine is third and the text should say so.
#
# Output: gjr_engine_results.json. Self-test: --synthetic (builtin QML fallback when arch is absent).
import os, sys, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats, optimize
try:
    from arch import arch_model; GARCH_BACKEND="arch"
except ImportError:
    GARCH_BACKEND="builtin_qml"
    class _Res:
        def __init__(s,p): s.params=p
    def _fit(y,o):
        y=np.asarray(y,float); n=len(y); v0=np.var(y)
        def nll(th):
            mu,lom,la,lg_,lb,lnu=th; om=math.exp(lom); a=1/(1+math.exp(-la)); g=(0.3/(1+math.exp(-lg_))) if o else 0.0
            b=(1-a-g/2)/(1+math.exp(-lb)); nu=2.05+math.exp(lnu); e=y-mu; s2=np.empty(n); s2[0]=v0
            for k in range(1,n): s2[k]=om+a*e[k-1]**2+g*e[k-1]**2*(e[k-1]<0)+b*s2[k-1]
            sc=math.sqrt(nu/(nu-2)); zt=e/np.sqrt(s2)*sc; ll=stats.t.logpdf(zt,nu)+math.log(sc)-0.5*np.log(s2)
            return -float(np.sum(ll)) if np.isfinite(ll).all() else 1e12
        x0=[float(np.mean(y)),math.log(0.05*v0),math.log(0.1/0.9),0.0,math.log(0.9/0.1),math.log(6-2.05)]
        r=optimize.minimize(nll,x0,method='Nelder-Mead',options={'maxiter':6000,'xatol':1e-6,'fatol':1e-6})
        mu,lom,la,lg_,lb,lnu=r.x; a=1/(1+math.exp(-la)); g=(0.3/(1+math.exp(-lg_))) if o else 0.0; b=(1-a-g/2)/(1+math.exp(-lb))
        return _Res({'mu':mu,'omega':math.exp(lom),'alpha[1]':a,'gamma[1]':g,'beta[1]':b,'nu':2.05+math.exp(lnu)})
    class _AM:
        def __init__(s,y,o=0,**k): s.y=y; s.o=o
        def fit(s,**k): return _fit(s.y,s.o)
    def arch_model(y,o=0,**k): return _AM(y,o)
P=os.environ.get("GBC_PROJ",r"C:\Users\OWNER\Claude\Projects\GBC Project"); t0=time.time(); lg=lambda s:print(s,flush=True)
SYN="--synthetic" in sys.argv
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]; ALPHAS=[0.01,0.025]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']; P0_ENGINE=0.025; SUBN=20
HGB=dict(max_iter=250,max_depth=3,learning_rate=0.06)

if SYN:
    rng=np.random.default_rng(7); recs=[]; dates=pd.bdate_range("2004-01-01",periods=2600)
    for pn in range(24):
        om,al,ga,be,nu=0.04,0.04,0.08,0.90,5.0+rng.uniform(-1,3); s2=np.empty(2600); e=np.empty(2600); s2[0]=om/(1-al-ga/2-be)
        for k in range(2600):
            if k: s2[k]=om+al*e[k-1]**2+ga*e[k-1]**2*(e[k-1]<0)+be*s2[k-1]
            z=stats.t.rvs(nu,random_state=rng)/math.sqrt(nu/(nu-2))
            if rng.uniform()<0.02: z-=rng.exponential(2.5)
            e[k]=math.sqrt(s2[k])*z
        recs.append(pd.DataFrame({'permno':pn,'date':dates,'ret':(0.02+e)/100.0}))
    rr=pd.concat(recs); NMAX=24
else:
    rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'}); NMAX=200
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:NMAX]

def pin(y,q,t): dd=y-q; return np.where(dd>=0,t*dd,(t-1)*dd)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    dm=x-x.mean(); v=np.mean(dm*dm)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(dm[k:]*dm[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
def conf_ostat(sc,tau):
    n=len(sc); k=min(max(int(math.ceil((n+1)*tau)),1),n); return float(np.sort(np.asarray(sc,float))[k-1])
def fz0(r,v,e,a):
    v=np.minimum(v,-1e-8); e=np.minimum(e,v); hit=(r<=v).astype(float)
    return -(1.0/(a*e))*hit*(v-r)+v/e+np.log(-e)-1.0
def t_es(a,nu):
    q=stats.t.ppf(a,nu); return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)
class GPDTail:
    def __init__(self,z,p0):
        z=np.asarray(z,float); z=z[np.isfinite(z)]; zz=-z
        self.u=float(np.quantile(zz,1-p0)); exc=zz[zz>self.u]-self.u; self.p0=p0; self.n_exc=int(len(exc))
        self.xi,_,self.beta=stats.genpareto.fit(exc,floc=0.0)
    def q(self,tau):
        xi,b,u,p0=self.xi,self.beta,self.u,self.p0
        return -(u+(b/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u+b*math.log(p0/tau))
def feats(y,sig,mu,dts):
    z=(y-mu)/np.maximum(sig,1e-6); df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1); df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1); df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    return df
def taylor_filter(y,b1,b2,b3,delta,v0):
    n=len(y); v=np.empty(n); e=np.empty(n); v[0]=v0; mult=1.0+math.exp(min(delta,4.0))
    for i in range(n):
        if i>0: v[i]=b1+b2*v[i-1]+b3*abs(y[i-1])
        e[i]=v[i]*mult
    return v,e

# ---------------------------------------------------------------- panel: both filters per name
FILT={'t':dict(vol='Garch',p=1,q=1,dist='t'),'gjr':dict(vol='Garch',p=1,o=1,q=1,dist='t')}
TR={'t':[],'gjr':[]}; CAL={'t':[],'gjr':[]}; rows=[]; TROWS=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75); D={}
    try:
        for f,kw in FILT.items():
            r=arch_model(y[:sp],rescale=False,**kw).fit(disp='off',show_warning=False); pp=r.params
            om,al,be,mu=float(pp['omega']),float(pp['alpha[1]']),float(pp['beta[1]']),float(pp.get('mu',0)); nu=float(pp.get('nu',8))
            ga=float(pp['gamma[1]']) if f=='gjr' else 0.0
            e0=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
            for k in range(1,n): s2[k]=max(om+al*e0[k-1]**2+ga*e0[k-1]**2*(e0[k-1]<0)+be*s2[k-1],1e-8)
            df=feats(y,np.sqrt(s2),mu,dts); df['mu']=mu; df['nu']=nu; df['tsc']=math.sqrt(nu/(nu-2)) if nu>2 else 1.0; df['gamma']=ga; D[f]=df
        r2=arch_model(y[:sp],vol='Garch',p=1,o=1,q=1,dist='skewt',rescale=False).fit(disp='off',show_warning=False); q2=r2.params
        om2,al2,ga2,be2,mu2=float(q2['omega']),float(q2['alpha[1]']),float(q2['gamma[1]']),float(q2['beta[1]']),float(q2.get('mu',0)); eta2,lam2=float(q2['eta']),float(q2['lambda'])
        e2=y-mu2; s22=np.empty(n); s22[0]=np.var(y[:sp])
        for k in range(1,n): s22[k]=max(om2+al2*e2[k-1]**2+ga2*e2[k-1]**2*(e2[k-1]<0)+be2*s22[k-1],1e-8)
        skd=r2.model.distribution; skq={t:float(skd.ppf(np.array([t]),[eta2,lam2])[0]) for t in TAUS}
        ske={a:float(np.mean(skd.ppf(np.array([a*(j+0.5)/200 for j in range(200)]),[eta2,lam2]))) for a in ALPHAS}
    except Exception as ex:
        if GARCH_BACKEND=="arch": continue
        skq={t:float(stats.t.ppf(t,5)/math.sqrt(5/3)) for t in TAUS}; ske={a:float(t_es(a,5)/math.sqrt(5/3)) for a in ALPHAS}; sig2=D['gjr']['sig'].values; mu2=float(D['gjr']['mu'].iloc[0]); s22=sig2**2
    dt=D['t']; dg=D['gjr']; dt['idx']=np.arange(n); dt['sig_gjrskt']=np.sqrt(s22); dt['mu_gjrskt']=mu2
    for t in TAUS: dt['gjrq_%g'%t]=skq[t]
    for a in ALPHAS: dt['gjre_%g'%a]=ske[a]
    for c in ['sig','z']+ZX+['mk63','mu','nu','tsc','gamma']: dt[c+'_g']=dg[c].values
    ok=dt.dropna(subset=ZX+['mk63']+[c+'_g' for c in ZX+['mk63']])
    trn=ok[ok['idx']<cp]; cal=ok[(ok['idx']>=cp)&(ok['idx']<sp)]; tst=ok[ok['idx']>=sp]
    if len(tst)<60 or len(cal)<60: continue
    TR['t'].append(trn[ZX+['z']]); CAL['t'].append(cal[ZX+['z']])
    TR['gjr'].append(trn[[c+'_g' for c in ZX+['z']]].rename(columns=lambda c:c[:-2])); CAL['gjr'].append(cal[[c+'_g' for c in ZX+['z']]].rename(columns=lambda c:c[:-2]))
    t2=tst.copy(); t2['permno']=pn; rows.append(t2); TROWS.append((pn,y,sp))
TE=pd.concat(rows).reset_index(drop=True); TRc={f:pd.concat(TR[f]) for f in TR}; CALc={f:pd.concat(CAL[f]) for f in CAL}
lg("panel %d names %d test rows %.0fs; median gamma %.3f"%(TE.permno.nunique(),len(TE),time.time()-t0,float(TE.groupby('permno')['gamma_g'].first().median())))
Y=TE['y'].values; PN=TE['permno'].values; di,_=pd.factorize(pd.to_datetime(TE['date'].values),sort=True); di=np.asarray(di); ALL=np.ones(len(Y),bool)
G=lambda c: TE[c].values

# ---------------------------------------------------------------- the two engines
def build_engine(f):
    suf='' if f=='t' else '_g'
    X=TE[[c+suf for c in ZX]].values; ztr=TRc[f]['z'].values; tail=GPDTail(ztr,P0_ENGINE)
    ZQ={}; ZQc={}
    for t in TAUS:
        m=HistGradientBoostingRegressor(loss='quantile',quantile=t,random_state=0,**HGB).fit(TRc[f][ZX].values,ztr)
        ZQ[t]=m.predict(X); ZQc[t]=m.predict(CALc[f][ZX].values)
    SUB={a:[HistGradientBoostingRegressor(loss='quantile',quantile=a*(j+0.5)/SUBN,random_state=0,**HGB).fit(TRc[f][ZX].values,ztr).predict(X) for j in range(SUBN)] for a in ALPHAS}
    c975=conf_ostat(CALc[f]['z'].values-ZQc[0.025],0.025)
    MU=G('mu'+suf); SIG=G('sig'+suf)
    eng={t:(np.minimum(ZQ[t],tail.q(t)) if t<=P0_ENGINE else ZQ[t]) for t in TAUS}
    E=np.sort(np.stack([eng[t] for t in TAUS],axis=1),axis=1); eng={t:E[:,j] for j,t in enumerate(TAUS)}
    RQ_e={t:MU+SIG*eng[t] for t in TAUS}; RQ_b={t:MU+SIG*ZQ[t] for t in TAUS}; VE={}
    for a in ALPHAS:
        st=np.sort(np.stack([np.minimum(SUB[a][j],tail.q(a*(j+0.5)/SUBN)) for j in range(SUBN)],axis=1),axis=1)
        zq=np.maximum(np.minimum(ZQ[a],tail.q(a)),st[:,-1]); es=np.minimum(st.mean(axis=1),zq-1e-6)
        stb=np.sort(np.stack(SUB[a],axis=1),axis=1); zqb=np.maximum(ZQ[a],stb[:,-1]); esb=np.minimum(stb.mean(axis=1),zqb-1e-6)
        sh=c975 if a==0.025 else 0.0
        VE[a]={'engine':(MU+SIG*zq,MU+SIG*es),'overlay':(MU+SIG*(zq+sh),MU+SIG*(es+sh)),'body':(MU+SIG*zqb,MU+SIG*esb)}
    lg("engine[%s] built: GPD xi=%.3f beta=%.3f n_exc=%d conf975=%+.4f %.0fs"%(f,tail.xi,tail.beta,tail.n_exc,c975,time.time()-t0))
    return RQ_e,RQ_b,VE,{'xi':round(tail.xi,4),'beta':round(tail.beta,4),'n_exc':tail.n_exc,'conf975':round(c975,4)}
RQ={}; VEa={a:{} for a in ALPHAS}; DIAG={}
for f,lab in [('t','engine'),('gjr','engine_gjr')]:
    RQ_e,RQ_b,VE,dg_=build_engine(f); RQ[lab]=RQ_e; RQ[lab.replace('engine','body')]=RQ_b; DIAG[lab]=dg_
    for a in ALPHAS:
        VEa[a][lab]=VE[a]['engine']; VEa[a][lab+'_overlay']=VE[a]['overlay']; VEa[a][lab.replace('engine','body')]=VE[a]['body']

# ---------------------------------------------------------------- benchmarks (as in job_bench_all.py)
MU=G('mu'); SIG=G('sig'); NU=G('nu'); TSC=G('tsc'); ztr_all=TRc['t']['z'].values
RQ['garch_t']={t:MU+SIG*stats.t.ppf(t,NU)/TSC for t in TAUS}
RQ['gjr_t']={t:G('mu_g')+G('sig_g')*stats.t.ppf(t,G('nu_g'))/G('tsc_g') for t in TAUS}
RQ['gjr_skewt']={t:G('mu_gjrskt')+G('sig_gjrskt')*G('gjrq_%g'%t) for t in TAUS}
RQ['fhs_pool']={t:MU+SIG*float(np.quantile(ztr_all,t)) for t in TAUS}
for a in ALPHAS:
    VEa[a]['garch_t']=(MU+SIG*stats.t.ppf(a,NU)/TSC,MU+SIG*t_es(a,NU)/TSC)
    VEa[a]['gjr_t']=(G('mu_g')+G('sig_g')*stats.t.ppf(a,G('nu_g'))/G('tsc_g'),G('mu_g')+G('sig_g')*t_es(a,G('nu_g'))/G('tsc_g'))
    VEa[a]['gjr_skewt']=(G('mu_gjrskt')+G('sig_gjrskt')*G('gjrq_%g'%a),G('mu_gjrskt')+G('sig_gjrskt')*G('gjre_%g'%a))
    VEa[a]['fhs_pool']=(MU+SIG*float(np.quantile(ztr_all,a)),MU+SIG*float(np.mean(ztr_all[ztr_all<=np.quantile(ztr_all,a)])))
TV={a:(np.full(len(Y),np.nan),np.full(len(Y),np.nan)) for a in ALPHAS}; tfail=0
for (pn_,y_,sp_) in TROWS:
    tr=y_[max(0,sp_-1200):sp_]; msk=PN==pn_; nsel=int(msk.sum())
    for a in ALPHAS:
        qa=float(np.quantile(tr,a)); ea=float(np.mean(tr[tr<=qa])) if (tr<=qa).any() else qa*1.2
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
        else: v,e=taylor_filter(y_,*best.x,qa); TV[a][0][msk]=v[-nsel:]; TV[a][1][msk]=e[-nsel:]
for a in ALPHAS: VEa[a]['taylor']=TV[a]
lg("Taylor fitted (%d fails) %.0fs"%(tfail,time.time()-t0))

# ---------------------------------------------------------------- pinball by region, two sorts
PL={m:sum(pin(Y,RQ[m][t],t) for t in TAUS)/len(TAUS) for m in RQ}
def dec(x):
    r=np.full(len(x),-1); m=np.isfinite(x); r[m]=pd.qcut(pd.Series(x[m]),10,labels=False,duplicates='drop').values+1; return r
def edge(Lref,Lm,mask):
    mask=mask&np.isfinite(Lref)&np.isfinite(Lm)
    if mask.sum()<30: return None
    d=(Lref-Lm)[mask]; g=pd.DataFrame({'d':d,'dt':di[mask]}).groupby('dt')['d'].mean()
    return {'edge_pct':round(100*float(d.mean())/float(Lref[mask].mean()),3),'DM':nw_t(g.values),'n':int(mask.sum())}
rk={'mk63_garch_t':dec(G('mk63')),'mk63_gjr':dec(G('mk63_g'))}
pinball={}
for sname,r in rk.items():
    regions={'top_decile':r==10,'deciles_1to9':(r>=1)&(r<=9),'overall':ALL}
    pinball[sname]={'vs_garch_t':{m:{rg:edge(PL['garch_t'],PL[m],msk) for rg,msk in regions.items()} for m in PL if m!='garch_t'},
                    'engine_gjr_vs':{m:{rg:edge(PL[m],PL['engine_gjr'],msk) for rg,msk in regions.items()} for m in PL if m!='engine_gjr'},
                    'decile_profile_vs_garch_t':{m:{int(d0):edge(PL['garch_t'],PL[m],r==d0) for d0 in range(1,11)} for m in ['engine','engine_gjr','body','body_gjr']}}
    lg("[%s] top decile vs garch_t: "%sname+json.dumps({m:pinball[sname]['vs_garch_t'][m]['top_decile'] for m in pinball[sname]['vs_garch_t']}))
overlap=float(np.mean((rk['mk63_garch_t']==10)==(rk['mk63_gjr']==10)))

# ---------------------------------------------------------------- FZ0 with DM against both engines, MCS
def dm_rows(Lm,Le,mask):
    mask=mask&np.isfinite(Lm)&np.isfinite(Le); d=(Lm-Le)[mask]
    if mask.sum()<30: return None
    g=pd.DataFrame({'d':d,'dt':di[mask]}).groupby('dt')['d'].mean(); t=nw_t(g.values)
    return {'mean_diff':round(float(np.mean(d)),5),'DM_t':t,'n':int(mask.sum())}
def mcs(Lmat,names_,B=1000,alpha=0.10,block=10,seed=0):
    T,M=Lmat.shape; rng_=np.random.default_rng(seed); idx=np.empty((B,T),dtype=int)
    for b in range(B):
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
FZ={}; MCS={}
for a in ALPHAS:
    L={}; out={}
    for m,(v,e) in VEa[a].items():
        Lm=fz0(Y,v,e,a); okm=np.isfinite(Lm)
        if okm.sum()<1000: continue
        L[m]=Lm; out[m]={'meanFZ0':round(float(np.nanmean(Lm[okm])),5),'breach':round(float(np.mean((Y<=v)[okm])),4)}
    for m in out:
        out[m]['vs_engine']=dm_rows(L[m],L['engine'],ALL) if m!='engine' else None
        out[m]['vs_engine_gjr']=dm_rows(L[m],L['engine_gjr'],ALL) if m!='engine_gjr' else None
        out[m]['vs_engine_gjr_top_decile']=dm_rows(L[m],L['engine_gjr'],rk['mk63_gjr']==10) if m!='engine_gjr' else None
    names_=[m for m in L if np.isfinite(L[m]).all()]
    dfm=pd.DataFrame({m:L[m] for m in names_}); dfm['dt']=di; Lmat=dfm.groupby('dt')[names_].mean().values
    MCS['fz0_%g'%a]=mcs(Lmat,names_); FZ[str(a)]=out
    lg("FZ0 a=%s: "%a+json.dumps({m:(out[m]['meanFZ0'],out[m]['vs_engine_gjr']['DM_t'] if out[m]['vs_engine_gjr'] else None) for m in out})+" MCS "+json.dumps(MCS['fz0_%g'%a]['in_90pct_MCS']))
names_=[m for m in PL if np.isfinite(PL[m]).all()]; dfm=pd.DataFrame({m:PL[m] for m in names_}); dfm['dt']=di
MCS['pinball_11tau']=mcs(dfm.groupby('dt')[names_].mean().values,names_)

OUT={'note':'Engine rebuilt on a GJR(1,1)-t Stage-1 filter (engine_gjr, body_gjr) beside the paper GARCH(1,1)-t engine (engine, body), same rows, same benchmarks; see header prediction. Sorts: mk63 from the GARCH-t residuals (paper frontier) and from the GJR residuals. FZ0: DM_t>0 means the row model is worse than the named engine.',
     'prediction_written_before_run':'2.5%: engine_gjr mean FZ0 within 0.0005 of gjr_skewt, DM within +/-1; 1%: lead over gjr_skewt kept (DM>=1); top-decile pinball edge within 0.5pp of the GARCH-t engine.',
     'synthetic':SYN,'garch_backend':GARCH_BACKEND,'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),'taylor_fails':tfail,
     'median_gamma_gjr_t':round(float(TE.groupby('permno')['gamma_g'].first().median()),4),'top_decile_overlap_two_sorts':round(overlap,4),
     'engine_diagnostics':DIAG,'mean_pinball':{m:round(float(np.nanmean(PL[m])),5) for m in PL},'pinball':pinball,'fz0':FZ,'mcs':MCS}
fn="gjr_engine_results_synthetic.json" if SYN else "gjr_engine_results.json"
json.dump(OUT,open(os.path.join(P,fn),"w"),indent=2); lg("GJRENGINEDONE %.0fs"%(time.time()-t0))
