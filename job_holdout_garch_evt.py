# job_holdout_garch_evt.py -- GARCH-EVT competitor on the 2000-2013 holdout, SAME ROWS as job_wrds_holdout.py
# and job_holdout_frozen.py (TODO C.4). The holdout engine is the frozen misspec_frontier.py spec: a pooled
# gradient-boosted RETURN quantile on RAWX=[lag1,abs1,prv5,prv21,rv63], fitted on idx<sp (60%) of each name,
# scored on idx>=sp. This job adds, on the same test rows, McNeil-Frey GARCH-EVT per name and pooled
# (GARCH(1,1)-t filter, two-sided GPD tails at p0=0.10 on the training standardized residuals, empirical
# residual quantiles in between) and reports the 11-tau pinball edge over GARCH-t for each, by holdout mk63
# decile (holdout-era qcut, as job_wrds_holdout.py) and by the frozen design-era bins (holdout_frozen_results.json),
# plus engine-vs-EVT head-to-head DM in the top bucket, the bulk and overall. Output holdout_garch_evt_results.json.
# Self-test: `--synthetic` builds a small in-memory panel and uses synthetic frozen edges.
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
RAWX=['lag1','abs1','prv5','prv21','rv63']; P0_MF=0.10
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
class GPDTail:
    def __init__(self,z,p0,sign=-1):
        z=np.asarray(z,float); z=z[np.isfinite(z)]; self.sign=sign; zz=sign*z
        self.u=float(np.quantile(zz,1-p0)); exc=zz[zz>self.u]-self.u
        self.p0=p0; self.n_exc=int(len(exc)); self.ok=self.n_exc>=20
        if self.ok: self.xi,_,self.beta=stats.genpareto.fit(exc,floc=0.0)
        else: self.xi,self.beta=np.nan,np.nan
    def q(self,tau):
        p=tau if self.sign<0 else 1-tau; xi,b,u,p0=self.xi,self.beta,self.u,self.p0
        loss=u+(b/xi)*((p/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u+b*math.log(p0/p)
        return self.sign*loss
def mf_quantile(lo,hi,ztr,tau):
    if tau<=P0_MF and lo.ok: return lo.q(tau)
    if tau>=1-P0_MF and hi.ok: return hi.q(tau)
    return float(np.quantile(ztr,tau))

if SYN:
    rng=np.random.default_rng(11); recs=[]; dates=pd.bdate_range("2000-01-03",periods=2400)
    for pn in range(16):
        om,al,be,nu=0.05,0.09,0.89,4.5+rng.uniform(0,3); s2=np.empty(2400); e=np.empty(2400); s2[0]=om/(1-al-be)
        for k in range(2400):
            if k: s2[k]=om+al*e[k-1]**2+be*s2[k-1]
            z=stats.t.rvs(nu,random_state=rng)/math.sqrt(nu/(nu-2))
            if rng.uniform()<0.02: z-=rng.exponential(2.5)
            e[k]=math.sqrt(s2[k])*z
        recs.append(pd.DataFrame({'permno':pn,'date':dates,'ret':(0.02+e)/100.0}))
    rr=pd.concat(recs); EDGES=None
else:
    rr=pd.read_csv(os.path.join(P,"holdout_panel_2000_2013.csv"),dtype={'permno':'int32'})
    EDGES=json.load(open(os.path.join(P,"holdout_frozen_results.json")))['design_edges_mk63']
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
TR=[]; TE=[]; TAILS={}; ZTR=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['lag1']=df['y'].shift(1); df['abs1']=df['y'].abs().shift(1)
    df['prv5']=df['y'].rolling(5,min_periods=3).std().shift(1); df['prv21']=df['y'].rolling(21,min_periods=8).std().shift(1); df['rv63']=df['y'].rolling(63,min_periods=20).std().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['idx']=np.arange(n); df=df.dropna(subset=RAWX+['mk63'])
    trn=df[df['idx']<sp]; tst=df[df['idx']>=sp]
    if len(tst)<30: continue
    ztr=z[:sp]; TAILS[pn]=(GPDTail(ztr,P0_MF,-1),GPDTail(ztr,P0_MF,+1),ztr); ZTR.append(ztr)
    TR.append(trn[RAWX+['y']])
    te=tst[RAWX+['y','sig','mk63','date']].copy(); te['mu']=mu; te['nu']=nu; te['tsc']=tsc; te['permno']=pn; TE.append(te)
TRc=pd.concat(TR); TEc=pd.concat(TE).reset_index(drop=True)
lg("holdout panel %d names %d test rows %.0fs"%(TEc.permno.nunique(),len(TEc),time.time()-t0))
GQ={}
for t in TAUS:
    GQ[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[RAWX].values,TRc['y'].values).predict(TEc[RAWX].values)
Y=TEc['y'].values; SIG=TEc['sig'].values; MU=TEc['mu'].values; NU=TEc['nu'].values; TSC=TEc['tsc'].values; PN=TEc['permno'].values
zall=np.concatenate(ZTR); PLO=GPDTail(zall,P0_MF,-1); PHI=GPDTail(zall,P0_MF,+1)
def per_name_map(fn):
    out=np.empty(len(Y))
    for pn in np.unique(PN): out[PN==pn]=fn(pn)
    return out
PL={'garch_t':np.zeros(len(Y)),'engine':np.zeros(len(Y)),'evt_name':np.zeros(len(Y)),'evt_pool':np.zeros(len(Y))}
for t in TAUS:
    PL['garch_t']+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t); PL['engine']+=pin(Y,GQ[t],t)
    PL['evt_name']+=pin(Y,MU+SIG*per_name_map(lambda pn: mf_quantile(*TAILS[pn],t)),t)
    PL['evt_pool']+=pin(Y,MU+SIG*mf_quantile(PLO,PHI,zall,t),t)
for m in PL: PL[m]/=len(TAUS)
dates=TEc['date'].values
def edge(Lref,Lm,mask):
    if mask.sum()<30: return None
    d=(Lref-Lm)[mask]; g=pd.DataFrame({'d':d,'date':dates[mask]}).groupby('date')['d'].mean().values; g=g[np.isfinite(g)]
    if len(g)<20: return None
    dd=g-g.mean(); v=np.mean(dd*dd)
    for k in range(1,11): v+=2*(1-k/11)*np.mean(dd[k:]*dd[:-k])
    s=g.mean()/math.sqrt(max(v/len(g),1e-12))
    return dict(edge_pct=round(100*float(d.mean())/float(Lref[mask].mean()),3),DM=round(float(s),2),n=int(mask.sum()),n_dates=int(len(g)))
mk=TEc['mk63'].values; okm=np.isfinite(mk)
decq=np.full(len(Y),-1); decq[okm]=pd.qcut(mk[okm],10,labels=False,duplicates='drop')+1
if EDGES is None: EDGES=[float(np.percentile(mk[okm],q)) for q in range(10,100,10)]
binf=np.full(len(Y),-1); binf[okm]=np.digitize(mk[okm],EDGES)+1
ALL=np.ones(len(Y),bool)
regions={'overall':ALL,'top_decile_qcut':decq==10,'bulk_qcut_1to9':(decq>=1)&(decq<=9),
         'top_bucket_frozen':binf==10,'bulk_frozen_1to9':(binf>=1)&(binf<=9)}
OUT={'note':('GARCH-EVT (McNeil-Frey per name and pooled, p0=0.10, training residuals only) on the 2000-2013 holdout, same rows as '
  'job_wrds_holdout.py / job_holdout_frozen.py. engine = frozen misspec_frontier.py raw-return GBM. edge=(ref-model)/ref 11-tau pinball, '
  'per-date NW(10) DM. Frozen buckets use design_edges_mk63 from holdout_frozen_results.json.'),
 'synthetic':SYN,'garch_backend':GARCH_BACKEND,'n_names':int(TEc.permno.nunique()),'n_test':int(len(Y)),
 'design_edges_mk63':[round(float(e),4) for e in EDGES],
 'pooled_tail':{'u_z':round(-PLO.u,4),'xi':round(float(PLO.xi),4),'beta':round(float(PLO.beta),4),'n_exc':PLO.n_exc},
 'vs_garch_t':{m:{r:edge(PL['garch_t'],PL[m],msk) for r,msk in regions.items()} for m in ['engine','evt_name','evt_pool']},
 'engine_vs_evt_pool':{r:edge(PL['evt_pool'],PL['engine'],msk) for r,msk in regions.items()},
 'engine_vs_evt_name':{r:edge(PL['evt_name'],PL['engine'],msk) for r,msk in regions.items()},
 'decile_profile_qcut':{m:{int(d0):edge(PL['garch_t'],PL[m],decq==d0) for d0 in range(1,11)} for m in ['engine','evt_name','evt_pool']},
 'mean_pinball':{m:round(float(PL[m].mean()),5) for m in PL}}
json.dump(OUT,open(os.path.join(P,"holdout_garch_evt_results_synthetic.json" if SYN else "holdout_garch_evt_results.json"),"w"),indent=2)
lg("HOLDOUTGARCHEVTDONE %.0fs "%(time.time()-t0)+json.dumps({'engine_vs_evt_pool':OUT['engine_vs_evt_pool'],'top_frozen':{m:OUT['vs_garch_t'][m]['top_bucket_frozen'] for m in OUT['vs_garch_t']}}))
