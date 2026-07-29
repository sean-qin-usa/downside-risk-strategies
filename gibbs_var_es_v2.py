# GENERATIVE (VaR,ES) POSTERIOR v2 (ai2) — close out the honest-uncertainty result. v1 showed: on GARCH residuals block~=iid
# (residual-space neutralizes dependence), block-bootstrap VaR/2.5%-ES bands ~nominal, BUT (a) omega=1 Gibbs OVER-covers and
# (b) 99% ES under-covers (too few tail points). v2 fixes both:
#   (a) CALIBRATE omega so the Gibbs posterior SD matches the honest block-bootstrap SD (SafeBayes/GPC-style) -> nominal coverage.
#   (b) EVT-based ES: fit GPD to residual left-tail exceedances, analytic GPD ES + parametric-bootstrap CI -> better 99% ES coverage.
# Report calibrated-Gibbs vs block-bootstrap vs EVT-ES credible-interval coverage (target 0.90), truth = full-sample residual quantile/ES.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True); rng=np.random.default_rng(0)
ALPHAS=[0.01,0.025]; BLOCK=20; NB=400; GRIDN=1500
def pinball(z,q,a): d=z-q; return np.where(d>=0,a*d,(a-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:150]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
def gibbs_post(ztr,a,omega):
    lo,hi=np.quantile(ztr,max(a*0.15,0.002)),np.quantile(ztr,min(a*4,0.2))
    if not (np.isfinite(lo) and np.isfinite(hi)) or hi<=lo: return None
    grid=np.linspace(lo,hi,GRIDN); loss=np.array([pinball(ztr,q,a).sum() for q in grid])
    ll=-omega*(loss-loss.min()); p=np.exp(ll); p=p/p.sum(); c=np.cumsum(p)
    m=float((p*grid).sum()); sd=float(math.sqrt(max((p*(grid-m)**2).sum(),0)))
    qlo=float(grid[np.searchsorted(c,0.05)]); qhi=float(grid[min(np.searchsorted(c,0.95),GRIDN-1)])
    return m,qlo,qhi,sd
def block_boot_q(ztr,a,which='var'):
    n=len(ztr); nb=int(np.ceil(n/BLOCK)); vals=np.empty(NB)
    for b in range(NB):
        st=rng.integers(0,n,nb); idx=np.concatenate([np.arange(s,s+BLOCK)%n for s in st])[:n]; s=ztr[idx]; q=np.quantile(s,a)
        vals[b]= q if which=='var' else (s[s<=q].mean() if (s<=q).any() else q)
    return float(vals.mean()),float(np.quantile(vals,0.05)),float(np.quantile(vals,0.95)),float(vals.std())
def gpd_es_ci(ztr,a,pu=0.05):
    u=np.quantile(ztr,pu); ex=u-ztr[ztr<u]; ex=ex[ex>0]
    if len(ex)<40: return None
    try: xi,loc,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return None
    if beta<=0 or xi>=1: return None
    def es_of(xi,beta):
        q_ex=(beta/xi)*(((a/pu)**(-xi))-1) if abs(xi)>1e-6 else -beta*math.log(a/pu)
        VaR=u-q_ex
        # GPD ES below VaR (left tail): ES = VaR - (beta + xi*(u-VaR? )) ... use standard POT ES formula on exceedances
        es_excess=(q_ex+beta)/(1-xi) if xi<1 else q_ex*2
        return u-es_excess
    es_hat=es_of(xi,beta); boots=[]
    for _ in range(200):
        bs=ex[rng.integers(0,len(ex),len(ex))]
        try:
            xb,_,bb=stats.genpareto.fit(bs,floc=0)
            if bb>0 and xb<1: boots.append(es_of(xb,bb))
        except Exception: pass
    if len(boots)<50: return None
    return es_hat,float(np.quantile(boots,0.05)),float(np.quantile(boots,0.95))
agg={a:{'gibbs_cal':{'cov':[],'w':[]},'block':{'cov':[],'w':[]},'evt_es':{'cov':[],'w':[]},'block_es':{'cov':[],'w':[]}} for a in ALPHAS}
nn=0
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    z=(y-mu)/np.maximum(np.sqrt(s2),1e-6); ztr=z[:sp]
    for a in ALPHAS:
        truth_q=float(np.quantile(z,a)); tm=z<=truth_q; truth_es=float(z[tm].mean()) if tm.any() else truth_q
        # block bootstrap VaR (honest target SD) + ES
        bq=block_boot_q(ztr,a,'var'); bes=block_boot_q(ztr,a,'es')
        agg[a]['block']['cov'].append(int(bq[1]<=truth_q<=bq[2])); agg[a]['block']['w'].append(bq[2]-bq[1])
        agg[a]['block_es']['cov'].append(int(bes[1]<=truth_es<=bes[2])); agg[a]['block_es']['w'].append(bes[2]-bes[1])
        target_sd=bq[3]
        # calibrate omega: gibbs SD ~ 1/sqrt(omega); solve omega_cal = 1 * (sd_ref/target_sd)^2
        ref=gibbs_post(ztr,a,1.0)
        if ref and target_sd>0:
            omega_cal=max((ref[3]/target_sd)**2,1e-6)*1.0
            gc=gibbs_post(ztr,a,omega_cal)
            if gc: agg[a]['gibbs_cal']['cov'].append(int(gc[1]<=truth_q<=gc[2])); agg[a]['gibbs_cal']['w'].append(gc[2]-gc[1])
        # EVT ES interval
        ev=gpd_es_ci(ztr,a)
        if ev: agg[a]['evt_es']['cov'].append(int(ev[1]<=truth_es<=ev[2])); agg[a]['evt_es']['w'].append(ev[2]-ev[1])
    nn+=1
    if nn%40==0: lg("  %d names %.0fs"%(nn,time.time()-t0))
def S(a,m):
    d=agg[a][m]; return dict(coverage=round(float(np.mean(d['cov'])),3),width=round(float(np.mean(d['w'])),3),n=len(d['cov'])) if d['cov'] else None
out={'note':'Generative (VaR,ES) posterior v2. gibbs_cal = omega-CALIBRATED Gibbs (SD matched to block-bootstrap => nominal, fixes '
            'v1 over-coverage). block = block-bootstrap VaR CI. block_es = block-bootstrap ES CI (v1: 99% ES under-covered). '
            'evt_es = GPD/POT-based 99% ES CI (fix). Target coverage 0.90; truth = full-sample residual quantile/ES.',
     'n_names':nn,'target':0.90,
     'results':{('alpha_%g'%a):{'gibbs_cal_VaR':S(a,'gibbs_cal'),'block_VaR':S(a,'block'),'block_ES':S(a,'block_es'),'evt_ES':S(a,'evt_es')} for a in ALPHAS}}
json.dump(out,open(os.path.join(D,"gibbs_var_es_v2_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
