# Modern ES/VaR backtests on the FRTB battery, pooled test panel (CRSP daily).
#  - Kupiec (1995) unconditional-coverage LR test (VaR)
#  - Acerbi-Szekely (2014) Test 2 (Z2) for ES (sign: <0 = ES understates risk)
#  - McNeil-Frey (2000) exceedance-residual test for ES (E[residual]=0 under correct ES)
# Inference is DATE-CLUSTERED (block bootstrap over calendar dates) to respect
# cross-sectional dependence: 140 equities share market shocks on the same day, so
# pooled asset-days are NOT independent. Clusters = calendar dates (the same unit the
# paper's Diebold-Mariano tests cluster on). Point estimates are unchanged; only the
# bootstrap p-values differ from an i.i.d.-over-asset-days resample.
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
Z={a:{m:{'z':[],'zq':[],'zes':[],'dt':[]} for m in MODELS} for a in ALPHAS}
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
    dtest=(g['date'].values[sp:].astype('datetime64[D]').astype('int64')).tolist()  # calendar-date cluster id
    if nu<=2.5: nu=2.5
    for a in ALPHAS:
        znz,enz=stats.norm.ppf(a), -stats.norm.pdf(stats.norm.ppf(a))/a
        zt,et=t_var_es(a,nu)
        zf=float(np.quantile(ztr,a)); mask=ztr<=zf; ef=float(ztr[mask].mean()) if mask.any() else zf
        gp=gpd_var_es(ztr,a); zh,eh=(gp if gp else (zf,ef))
        specs={'garch_norm':(znz,enz),'garch_t':(zt,et),'fhs':(zf,ef),'hybrid_evt':(zh,eh)}
        for m,(zq,zes) in specs.items():
            Z[a][m]['z'].extend(ztest.tolist()); Z[a][m]['zq'].extend([zq]*len(ztest))
            Z[a][m]['zes'].extend([zes]*len(ztest)); Z[a][m]['dt'].extend(dtest)
    nn+=1
    if nn%25==0: lg("  %d names %.0fs"%(nn,time.time()-t0))
lg("fitted %d names %.0fs"%(nn,time.time()-t0))

def _by_date(vals, dates):
    order=np.argsort(dates,kind='stable'); d=dates[order]; v=vals[order]
    ud, idx = np.unique(d, return_index=True)
    sums=np.add.reduceat(v, idx); cnts=np.diff(np.append(idx,len(v)))
    return ud, sums, cnts

def kupiec(br_ind,a):
    x=np.asarray(br_ind); N=len(x); nb=int(x.sum()); ph=nb/N if N else 0
    if nb==0 or nb==N: return ph, float('nan')
    LR=-2*((nb*math.log(a)+(N-nb)*math.log(1-a))-(nb*math.log(ph)+(N-nb)*math.log(1-ph)))
    return ph, float(1-stats.chi2.cdf(LR,1))

def as_z2(z,zq,zes,dt,a,B=5000):
    # Z2 = 1 - mean_i [ z_i 1{z_i<=zq_i} / (a zes_i) ];  <0 => ES understates risk.
    z=np.asarray(z); zq=np.asarray(zq); zes=np.asarray(zes); dt=np.asarray(dt)
    t=(z<=zq).astype(float)*z/(a*zes)                 # per-obs contribution
    N=len(t); obs=1.0-t.sum()/N
    ud,S,C=_by_date(t,dt); K=len(ud)
    boot=np.empty(B)
    for b in range(B):
        sel=rng.integers(0,K,K); boot[b]=1.0 - S[sel].sum()/C[sel].sum()
    se=boot.std()
    p=float(2*(1-stats.norm.cdf(abs(obs)/se))) if se>0 else float('nan')
    return float(obs), p, K

def mcneil_frey(z,zq,zes,dt,B=5000):
    # Mean standardized exceedance residual er=z-zes over breaches; 0 under correct ES.
    z=np.asarray(z); zq=np.asarray(zq); zes=np.asarray(zes); dt=np.asarray(dt)
    m=z<=zq; er=z[m]-zes[m]; erd=dt[m]
    if len(er)<10: return float('nan'),float('nan'),0
    obs=er.mean()
    ud,S,C=_by_date(er,erd); K=len(ud)                # cluster by exceedance date
    boot=np.empty(B)
    for b in range(B):
        sel=rng.integers(0,K,K); boot[b]=S[sel].sum()/C[sel].sum()
    p=float(2*min((boot<=0).mean(),(boot>=0).mean()))
    return float(obs), p, K

out={'note':'Modern ES/VaR backtests, pooled test panel; inference DATE-CLUSTERED (block bootstrap over calendar dates) to respect cross-sectional dependence across the 140 names. Kupiec UC (VaR); Acerbi-Szekely 2014 Z2 (ES; <0 understates risk); McNeil-Frey 2000 exceedance-residual (ES). Point estimates unchanged vs an iid resample; only p-values differ. Framework distinction: these are ES CALIBRATION backtests (Nolde-Ziegel 2017; Bayer-Dimitriadis 2022 describe MF/NZ as calibration tests) complementing the FZ0 comparative loss.','n_names':nn,'per_alpha':{}}
for a in ALPHAS:
    A={}
    for m in MODELS:
        zz=np.array(Z[a][m]['z']); zq=np.array(Z[a][m]['zq']); zes=np.array(Z[a][m]['zes']); dd=np.array(Z[a][m]['dt'])
        br,kp=kupiec((zz<=zq).astype(float),a); z2,z2p,ndates=as_z2(zz,zq,zes,dd,a); mf,mfp,nxd=mcneil_frey(zz,zq,zes,dd)
        A[m]={'breach':round(br,4),'kupiec_p':round(kp,4),'AS_Z2':round(z2,4),'AS_Z2_p':round(z2p,4),
              'MF_exres':round(mf,4),'MF_p':round(mfp,4),'n_test_dates':int(ndates),'n_breach_dates':int(nxd)}
    out['per_alpha']['alpha_%g'%a]=A
json.dump(out,open("es_backtests_results.json","w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
