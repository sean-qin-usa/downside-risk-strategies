# Modern ES/VaR backtests on the FRTB battery, pooled test panel (CRSP daily).
#  - Kupiec (1995) unconditional-coverage LR test (VaR)
#  - Acerbi-Szekely (2014) Test 2 (Z2) for ES (sign: <0 = ES understates risk); bootstrap SE p-value
#  - McNeil-Frey (2000) exceedance-residual bootstrap test for ES (E[residual]=0 under correct ES)
# These sit in the modern joint-elicitability backtesting framework (Bayer-Dimitriadis 2022; Nolde-Ziegel 2017).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
t0=time.time(); lg=lambda s:print(s,flush=True); rng=np.random.default_rng(12345)
NMAX=int(os.environ.get("NMAX","140")); ALPHAS=[0.025,0.01]
rr=pd.read_csv("crsp_panel_returns.csv",dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:NMAX]
lg("names=%d %.0fs"%(len(names),time.time()-t0))

def t_var_es(a,nu):
    s=math.sqrt((nu-2.0)/nu); q=stats.t.ppf(a,nu); es=-(nu+q*q)/(nu-1.0)*stats.t.pdf(q,nu)/a
    return s*q, s*es
def gpd_var_es(ztr,a,pu=0.075):
    u=np.quantile(ztr,pu); ex=u-ztr[ztr<u]; ex=ex[ex>0]
    if len(ex)<40: return None
    try: xi,_,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return None
    if beta<=0 or xi>=1: return None
    qex=(beta/xi)*(((a/pu)**(-xi))-1) if abs(xi)>1e-6 else -beta*math.log(a/pu)
    return u-qex, u-(qex+beta)/(1-xi)

MODELS=['garch_norm','garch_t','fhs','hybrid_evt']
Z={a:{m:{'z':[],'zq':[],'zes':[]} for m in MODELS} for a in ALPHAS}
nn=0
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); ztr=z[:sp]; ztest=z[sp:]
    if nu<=2.5: nu=2.5
    for a in ALPHAS:
        znz,enz=stats.norm.ppf(a), -stats.norm.pdf(stats.norm.ppf(a))/a
        zt,et=t_var_es(a,nu)
        zf=float(np.quantile(ztr,a)); mask=ztr<=zf; ef=float(ztr[mask].mean()) if mask.any() else zf
        gp=gpd_var_es(ztr,a); zh,eh=(gp if gp else (zf,ef))
        specs={'garch_norm':(znz,enz),'garch_t':(zt,et),'fhs':(zf,ef),'hybrid_evt':(zh,eh)}
        for m,(zq,zes) in specs.items():
            Z[a][m]['z'].extend(ztest.tolist()); Z[a][m]['zq'].extend([zq]*len(ztest)); Z[a][m]['zes'].extend([zes]*len(ztest))
    nn+=1
    if nn%25==0: lg("  %d names %.0fs"%(nn,time.time()-t0))
lg("fitted %d names %.0fs"%(nn,time.time()-t0))

def kupiec(br_ind,a):
    x=np.asarray(br_ind); N=len(x); nb=int(x.sum()); ph=nb/N if N else 0
    if nb==0 or nb==N: return ph, float('nan')
    LR=-2*((nb*math.log(a)+(N-nb)*math.log(1-a))-(nb*math.log(ph)+(N-nb)*math.log(1-ph)))
    return ph, float(1-stats.chi2.cdf(LR,1))
def as_z2(z,zq,zes,a,S=3000):
    z=np.asarray(z); zq=np.asarray(zq); zes=np.asarray(zes); N=len(z)
    stat=lambda zz: 1.0 - np.sum((zz<=zq).astype(float)*zz/(a*zes))/N   # <0 => ES understates risk
    obs=stat(z); sims=np.array([stat(z[rng.integers(0,N,N)]) for _ in range(S)]); se=sims.std()
    p=float(2*(1-stats.norm.cdf(abs(obs)/se))) if se>0 else float('nan')
    return float(obs), p
def mcneil_frey(z,zq,zes,B=5000):
    z=np.asarray(z); zq=np.asarray(zq); zes=np.asarray(zes); m=z<=zq; er=z[m]-zes[m]
    if len(er)<10: return float('nan'),float('nan')
    obs=er.mean(); bs=np.array([er[rng.integers(0,len(er),len(er))].mean() for _ in range(B)])
    p=float(2*min((bs<=0).mean(),(bs>=0).mean()))
    return float(obs), p

out={'note':'Modern ES/VaR backtests, pooled test panel. Kupiec UC (VaR); Acerbi-Szekely 2014 Z2 (ES; <0 understates risk); McNeil-Frey 2000 exceedance-residual bootstrap (ES). Framework: Bayer-Dimitriadis 2022 ESR, Nolde-Ziegel 2017.','n_names':nn,'per_alpha':{}}
for a in ALPHAS:
    A={}
    for m in MODELS:
        zz=np.array(Z[a][m]['z']); zq=np.array(Z[a][m]['zq']); zes=np.array(Z[a][m]['zes'])
        br,kp=kupiec((zz<=zq).astype(float),a); z2,z2p=as_z2(zz,zq,zes,a); mf,mfp=mcneil_frey(zz,zq,zes)
        A[m]={'breach':round(br,4),'kupiec_p':round(kp,4),'AS_Z2':round(z2,4),'AS_Z2_p':round(z2p,4),'MF_exres':round(mf,4),'MF_p':round(mfp,4)}
    out['per_alpha']['alpha_%g'%a]=A
json.dump(out,open("es_backtests_results.json","w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
