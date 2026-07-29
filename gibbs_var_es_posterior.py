# GENERATIVE / GIBBS POSTERIOR ON CONDITIONAL (VaR, ES) — the thesis-central result (ai2).
# No standard risk model (GARCH-t, CAViaR, our residual-hybrid) gives UNCERTAINTY on the risk number itself — they output a
# POINT VaR/ES. GBC/generalized-Bayes can: form a posterior over the tail quantile in GARCH-residual space and put calibrated
# credible bands on VaR/ES. Prof. Jiang's caution: naive (i.i.d.) Gibbs bands UNDER-cover because dependence -> n_eff << n.
# Fix: block-calibrated omega / block bootstrap. We MEASURE credible-interval coverage using the full-sample residual quantile
# as ground truth (an SBC-style check), for alpha = 1% and 2.5%, across CRSP names. Prediction: iid bands under-cover; block bands ~nominal.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True); rng=np.random.default_rng(0)
ALPHAS=[0.01,0.025]; BLOCK=20; NB=400; GRIDN=1500
def pinball(z,q,a): d=z-q; return np.where(d>=0,a*d,(a-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:150]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
def gibbs_ci_var(ztr,a,omega):
    # 1-D Gibbs posterior over the alpha-quantile q: p(q) prop exp(-omega * sum pinball_a(z,q)); flat prior. Return (mean, lo, hi 90% CI).
    lo,hi=np.quantile(ztr,max(a*0.15,0.002)),np.quantile(ztr,min(a*4,0.2))
    if not (np.isfinite(lo) and np.isfinite(hi)) or hi<=lo: return None
    grid=np.linspace(lo,hi,GRIDN)
    loss=np.array([pinball(ztr,q,a).sum() for q in grid])
    ll=-omega*(loss-loss.min()); p=np.exp(ll); p=p/p.sum()
    c=np.cumsum(p); m=float((p*grid).sum())
    qlo=float(grid[np.searchsorted(c,0.05)]); qhi=float(grid[min(np.searchsorted(c,0.95),GRIDN-1)])
    return m,qlo,qhi
def boot_ci(ztr,a,block,which='var'):
    n=len(ztr); nb=int(np.ceil(n/block)); vals=np.empty(NB)
    for b in range(NB):
        if block==1: idx=rng.integers(0,n,n)
        else:
            st=rng.integers(0,n,nb); idx=np.concatenate([np.arange(s,s+block)%n for s in st])[:n]
        s=ztr[idx]; q=np.quantile(s,a)
        vals[b]= q if which=='var' else s[s<=q].mean() if (s<=q).any() else q
    return float(vals.mean()),float(np.quantile(vals,0.05)),float(np.quantile(vals,0.95))
agg={a:{m:{'cov_var':[],'w_var':[],'cov_es':[],'w_es':[]} for m in ['gibbs_iid','gibbs_block','boot_iid','boot_block']} for a in ALPHAS}
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
    # inflation factor from block vs iid bootstrap SD of the quantile (measures dependence)
    for a in ALPHAS:
        truth_q=float(np.quantile(z,a)); tm=z<=truth_q; truth_es=float(z[tm].mean()) if tm.any() else truth_q
        # bootstrap intervals
        for tag,blk in (('boot_iid',1),('boot_block',BLOCK)):
            mv,lv,hv=boot_ci(ztr,a,blk,'var'); me,le,he=boot_ci(ztr,a,blk,'es')
            agg[a][tag]['cov_var'].append(int(lv<=truth_q<=hv)); agg[a][tag]['w_var'].append(hv-lv)
            agg[a][tag]['cov_es'].append(int(le<=truth_es<=he)); agg[a][tag]['w_es'].append(he-le)
        # gibbs intervals: iid (omega=1 on the sum) and block (omega scaled by iid/block variance ratio)
        sd_i=(boot_ci(ztr,a,1,'var')[2]-boot_ci(ztr,a,1,'var')[1]); sd_b=(boot_ci(ztr,a,BLOCK,'var')[2]-boot_ci(ztr,a,BLOCK,'var')[1])
        infl=max(sd_b/max(sd_i,1e-9),1.0)
        gi=gibbs_ci_var(ztr,a,1.0); gb=gibbs_ci_var(ztr,a,1.0/(infl**2))
        if gi:
            agg[a]['gibbs_iid']['cov_var'].append(int(gi[1]<=truth_q<=gi[2])); agg[a]['gibbs_iid']['w_var'].append(gi[2]-gi[1])
        if gb:
            agg[a]['gibbs_block']['cov_var'].append(int(gb[1]<=truth_q<=gb[2])); agg[a]['gibbs_block']['w_var'].append(gb[2]-gb[1])
    nn+=1
    if nn%40==0: lg("  %d names %.0fs"%(nn,time.time()-t0))
def summ(a,m):
    d=agg[a][m]; o={}
    if d['cov_var']: o['coverage_VaR']=round(float(np.mean(d['cov_var'])),3); o['width_VaR']=round(float(np.mean(d['w_var'])),3)
    if d['cov_es']: o['coverage_ES']=round(float(np.mean(d['cov_es'])),3); o['width_ES']=round(float(np.mean(d['w_es'])),3)
    return o
out={'note':'Generative/Gibbs posterior credible-band coverage for conditional (VaR,ES) in GARCH-residual space. Ground truth = '
            'full-sample residual quantile/ES (SBC-style). 90% credible interval should cover ~0.90. gibbs_iid & boot_iid assume '
            'independence (predict UNDER-coverage); gibbs_block & boot_block respect dependence (predict ~nominal). This is the '
            'honest-uncertainty-on-the-risk-number result no GARCH/CAViaR/hybrid provides (they give a POINT VaR). alpha=1% & 2.5%.',
     'n_names':nn,'target_coverage':0.90,'block':BLOCK,
     'results':{('alpha_%g'%a):{m:summ(a,m) for m in ['gibbs_iid','gibbs_block','boot_iid','boot_block']} for a in ALPHAS}}
json.dump(out,open(os.path.join(D,"gibbs_var_es_posterior_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
