# GIBBS LOSS-IN-EXPONENT ABLATION. The honest-uncertainty posterior is p(q) ~ exp(-omega * sum loss(z,q)) * prior.
# Which loss belongs in the exponent? Pinball targets the alpha-QUANTILE (=VaR); expectile targets the alpha-EXPECTILE
# (a DIFFERENT functional) so its posterior is biased for VaR; quantile-Huber is a smooth surrogate. We compare, for each
# loss, the posterior BIAS vs the true full-sample alpha-quantile and the credible-band COVERAGE (omega calibrated to the
# block-bootstrap SD, as in v2, so widths are comparable). Message: only pinball (the FZ/quantile-consistent loss) gives an
# unbiased, nominally-covering VaR posterior; quadratic/expectile surrogates bias it. In-sandbox CRSP subset (CPU).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
D=os.path.dirname(os.path.abspath(__file__)); t0=time.time(); lg=lambda s:print(s,flush=True); rng=np.random.default_rng(0)
NMAX=int(os.environ.get("NMAX","80")); ALPHAS=[0.025,0.01]; BLOCK=20; NB=300; GRIDN=1400
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:NMAX]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
def loss_sum(z,q,a,kind):
    u=z-q
    if kind=='pinball':   return np.where(u>=0,a*u,(a-1)*u).sum()
    if kind=='expectile': w=np.where(u>=0,a,1-a); return (w*u*u).sum()
    if kind=='qhuber':    # quantile-Huber, kappa=0.5: smooth pinball
        k=0.5; au=np.abs(u); quad=0.5*u*u/k; lin=au-0.5*k; h=np.where(au<=k,quad,lin); return (np.where(u>=0,a,1-a)*h).sum()
    raise ValueError(kind)
def gibbs(z,a,kind,omega):
    lo,hi=np.quantile(z,max(a*0.15,0.002)),np.quantile(z,min(a*4,0.2))
    if not (np.isfinite(lo) and np.isfinite(hi)) or hi<=lo: return None
    grid=np.linspace(lo,hi,GRIDN); L=np.array([loss_sum(z,q,a,kind) for q in grid])
    ll=-omega*(L-L.min()); p=np.exp(ll); s=p.sum()
    if not np.isfinite(s) or s<=0: return None
    p/=s; c=np.cumsum(p); m=float((p*grid).sum()); sd=float(math.sqrt(max((p*(grid-m)**2).sum(),0)))
    qlo=float(grid[np.searchsorted(c,0.05)]); qhi=float(grid[min(np.searchsorted(c,0.95),GRIDN-1)])
    return m,qlo,qhi,sd
def block_sd(z,a):
    n=len(z); nb=int(np.ceil(n/BLOCK)); vals=np.empty(NB)
    for b in range(NB):
        st=rng.integers(0,n,nb); idx=np.concatenate([np.arange(s,s+BLOCK)%n for s in st])[:n]; vals[b]=np.quantile(z[idx],a)
    return float(vals.std())
KINDS=['pinball','expectile','qhuber']
agg={a:{k:{'cov':[],'w':[],'bias':[]} for k in KINDS} for a in ALPHAS}
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
        truth=float(np.quantile(z,a)); bsd=block_sd(ztr,a)
        for kind in KINDS:
            ref=gibbs(ztr,a,kind,1.0)
            if not ref or bsd<=0: continue
            omega=max((ref[3]/bsd)**2,1e-6); gc=gibbs(ztr,a,kind,omega)
            if not gc: continue
            agg[a][kind]['cov'].append(int(gc[1]<=truth<=gc[2])); agg[a][kind]['w'].append(gc[2]-gc[1])
            agg[a][kind]['bias'].append(gc[0]-truth)
    nn+=1
    if nn%20==0: lg("  %d names %.0fs"%(nn,time.time()-t0))
def S(a,k):
    d=agg[a][k]
    return dict(coverage=round(float(np.mean(d['cov'])),3),width=round(float(np.mean(d['w'])),3),
                mean_bias=round(float(np.mean(d['bias'])),4),n=len(d['cov'])) if d['cov'] else None
out={'note':'Gibbs loss-in-exponent ablation. Posterior p(q)~exp(-omega*sum loss(z,q)), omega calibrated to block-bootstrap SD. '
            'truth=full-sample residual alpha-quantile; target coverage 0.90. pinball->alpha-quantile (correct VaR); expectile->'
            'alpha-expectile (WRONG functional, expect bias + miscoverage); qhuber=smooth pinball surrogate. In-sandbox CRSP subset.',
     'n_names':nn,'target':0.90,
     'results':{('alpha_%g'%a):{k:S(a,k) for k in KINDS} for a in ALPHAS}}
json.dump(out,open(os.path.join(D,"gibbs_loss_ablation_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
