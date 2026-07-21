# GIBBS-POSTERIOR OVERCONFIDENCE TEST (ai2) — turns Prof. Jiang's caution into a measurement.
# Claim (GIBBS_FINANCE_FIRST_PRINCIPLES.md): a Gibbs posterior exp{-w*sum pinball(r,q)} over a VaR level q
# treats dependent returns as if iid -> effective sample size << n -> posterior SD too small -> OVERCONFIDENT bands.
# Fix: run it on GARCH-standardized residuals z=(r-mu)/sigma (~iid by construction), or calibrate w by BLOCK resampling.
#
# Measurement: for tau=0.05, compare the Gibbs posterior SD of q against the TRUE sampling SD of the same
# pinball-minimizing quantile, estimated two ways:
#   - IID bootstrap SD  (ignores dependence, like the naive Gibbs)
#   - BLOCK bootstrap SD (respects dependence = the honest sampling variability)
# Ratio R = SD_bootstrap / SD_gibbs.  R>>1 == Gibbs is overconfident.
# PREDICTION: on RAW returns  R_block >> 1  and R_iid ~ 1  (Gibbs matches iid, both under-account for dependence);
#             on GARCH RESID   R_block ~ 1   (dependence filtered out -> Gibbs honest by construction).
import os, json, time, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
rng=np.random.default_rng(0)
TAU=0.05
def pinball(r,q,t=TAU): d=r-q; return np.where(d>=0,t*d,(t-1)*d)

def gibbs_posterior_sd(x, w=1.0, ngrid=1200):
    # 1-D Gibbs posterior over VaR level q: p(q) propto exp(-w * sum_i pinball_tau(x_i,q)), flat prior.
    lo,hi=np.quantile(x,0.005),np.quantile(x,0.30)             # bracket the 5% quantile generously
    if not np.isfinite(lo) or not np.isfinite(hi) or hi<=lo: return None
    grid=np.linspace(lo,hi,ngrid)
    loss=np.array([pinball(x,q).sum() for q in grid])          # sum of pinball at each candidate q
    ll=-w*(loss-loss.min())                                    # stabilize
    p=np.exp(ll); p=p/p.sum()
    m=(p*grid).sum(); v=(p*(grid-m)**2).sum()
    return float(np.sqrt(max(v,0)))

def emp_q(x): return float(np.quantile(x,TAU))

def boot_sd(x, block, B=300):
    n=len(x); nb=int(np.ceil(n/block)); out=np.empty(B)
    for b in range(B):
        if block==1:
            idx=rng.integers(0,n,n)                            # iid bootstrap
        else:
            starts=rng.integers(0,n,nb)                        # moving-block bootstrap
            idx=np.concatenate([np.arange(s,s+block)%n for s in starts])[:n]
        out[b]=emp_q(x[idx])
    return float(out.std())

# ---- load panel, pick names with long clean history ----
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False)
names=cnt[cnt>=2500].index.tolist()[:80]
lg("names=%d  %.0fs"%(len(names),time.time()-t0))
BLOCK=20                                                       # ~ one trading month; integrated-autocorr scale for |r|
rows=[]
for k,pn in enumerate(names):
    x=rr[rr.permno==pn].sort_values('date')['ret'].dropna().values
    if len(x)<2500: continue
    x=x[-2500:]
    # GARCH-t filter -> standardized residuals
    try:
        res=arch_model(x,vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        z=(x-float(res.params.get('mu',0)))/np.maximum(res.conditional_volatility,1e-8)
    except Exception:
        continue
    for tag,s in (('raw',x),('resid',z)):
        sd_g=gibbs_posterior_sd(s)
        if sd_g is None or sd_g<=0: continue
        rows.append(dict(permno=int(pn),series=tag,
                         sd_gibbs=sd_g,
                         sd_iid=boot_sd(s,1),
                         sd_block=boot_sd(s,BLOCK)))
    if (k+1)%20==0: lg("  %d/%d  %.0fs"%(k+1,len(names),time.time()-t0))

df=pd.DataFrame(rows)
def summ(tag):
    d=df[df.series==tag]
    r_iid=(d.sd_iid/d.sd_gibbs); r_blk=(d.sd_block/d.sd_gibbs)
    return dict(n=int(len(d)),
                sd_gibbs=round(float(d.sd_gibbs.mean()),4),
                sd_iid=round(float(d.sd_iid.mean()),4),
                sd_block=round(float(d.sd_block.mean()),4),
                R_iid_over_gibbs=round(float(r_iid.mean()),3),
                R_block_over_gibbs=round(float(r_blk.mean()),3),
                R_block_over_gibbs_median=round(float(r_blk.median()),3))
out={'note':'Gibbs-posterior overconfidence test. tau=0.05 VaR level q. Gibbs posterior SD of q vs sampling SD from '
            'iid bootstrap and moving-block bootstrap (block=%d). R=SD_boot/SD_gibbs; R>>1 => Gibbs overconfident. '
            'PREDICTION: raw R_block>>1 (dependence), resid R_block~1 (GARCH-filtered ~iid). Turns Jiang caution into a number.'%BLOCK,
     'tau':TAU,'block':BLOCK,'n_names':int(df.permno.nunique()),
     'raw':summ('raw'),'resid':summ('resid'),
     'interpretation':'If raw.R_block_over_gibbs > resid.R_block_over_gibbs and raw.R_block>1, the memo is confirmed: '
                      'naive Gibbs on raw returns understates uncertainty; GARCH-residual (or block-w) calibration restores honesty.'}
json.dump(out,open(os.path.join(D,"gibbs_coverage_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
