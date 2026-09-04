# GIBBS ACI COVERAGE ARM (ai2) — closes gap (d): the promised Adaptive Conformal Inference comparison from the Gibbs memo.
# Claim: honest uncertainty/coverage under drift should come from ACI (Gibbs-Candes 2021), NOT the naive Gibbs/fixed model.
# Measure realized VaR coverage at target 1% and 5% for: garch_t (parametric), empirical (rolling 250d quantile = naive/'Gibbs-
# like' fixed), and ACI (online-adjust the level). Report realized breach vs nominal + rolling-coverage stability (max abs dev).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
LEVELS=[0.01,0.05]; W=250; GAMMA=0.02
def roll_emp(y,i,lvl,w=W):
    lo=max(0,i-w); s=y[lo:i]
    return np.quantile(s,lvl) if len(s)>=50 else np.nan
agg={lvl:{m:{'br':[],'roll':[]} for m in ['garch_t','empirical','ACI']} for lvl in LEVELS}
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    for lvl in LEVELS:
        a_t=lvl; br_g=[]; br_e=[]; br_a=[]
        for i in range(sp,n):
            yi=y[i]
            qg=mu+sig[i]*stats.t.ppf(lvl,nu)/tsc
            qe=roll_emp(y,i,lvl)
            a_use=min(max(a_t,0.001),0.20); qa=roll_emp(y,i,a_use)     # ACI: empirical quantile at adapted level a_t
            if not np.isfinite(qe) or not np.isfinite(qa): continue
            bg=int(yi<qg); be=int(yi<qe); ba=int(yi<qa)
            br_g.append(bg); br_e.append(be); br_a.append(ba)
            a_t=a_t+GAMMA*(lvl-ba)                                     # ACI update: raise level after no-breach, lower after breach
        def rollcov(br):
            b=np.array(br,float);
            if len(b)<120: return None
            rc=pd.Series(b).rolling(120).mean().dropna().values
            return float(np.max(np.abs(rc-lvl))) if len(rc) else None
        for m,br in (('garch_t',br_g),('empirical',br_e),('ACI',br_a)):
            if br: agg[lvl][m]['br'].append(np.mean(br));
            rc=rollcov(br)
            if rc is not None: agg[lvl][m]['roll'].append(rc)
out={'note':'ACI coverage arm. Target VaR levels 1%/5%. garch_t (parametric), empirical (rolling 250d quantile, naive fixed), '
            'ACI (online-adapt the level, gamma=0.02). realized_breach should equal the level; roll_maxdev = mean over names of '
            'the max abs deviation of 120-day rolling coverage from nominal (lower=more stable under drift). Prediction: ACI '
            'closest to nominal & most stable; parametric/naive drift more.','W':W,'gamma':GAMMA}
for lvl in LEVELS:
    out['level_%g'%lvl]={m:dict(realized_breach=round(float(np.mean(agg[lvl][m]['br'])),4),
                                abs_err_vs_nominal=round(abs(float(np.mean(agg[lvl][m]['br']))-lvl),4),
                                roll_maxdev=round(float(np.mean(agg[lvl][m]['roll'])),4) if agg[lvl][m]['roll'] else None)
                         for m in ['garch_t','empirical','ACI']}
json.dump(out,open(os.path.join(D,"gibbs_aci_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
