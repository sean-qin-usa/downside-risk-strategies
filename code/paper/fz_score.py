# FISSLER-ZIEGEL joint (VaR,ES) scoring + economic (capital-bps / certainty-equivalent) translation.
# Rescores the FRTB-style battery with the STRICTLY CONSISTENT joint (VaR,ES) FZ0 loss (Patton-Ziegel-Chen 2019,
# 0-homogeneous) instead of pinball-only, and runs per-date Diebold-Mariano tests. Then translates the ES edge into
# FRTB ES-capital basis points and a mean-ES certainty-equivalent. Runs in-sandbox on local CRSP panel (CPU).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
D=os.path.dirname(os.path.abspath(__file__)); t0=time.time(); lg=lambda s:print(s,flush=True)
NAMES_MAX=int(os.environ.get("NMAX","90")); ALPHAS=[0.025,0.01]; NWLAG=5
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False)
elig=cnt[cnt>=1500].index.tolist()
SEL=os.environ.get("SEL","largecap")
if SEL=="highkurt":     # high-misspecification proxy: top raw excess-kurtosis names (frontier regime)
    ku=rr[rr.permno.isin(elig)].groupby('permno')['ret'].apply(lambda s:float(stats.kurtosis(s.dropna(),fisher=True)))
    names=ku.sort_values(ascending=False).index.tolist()[:NAMES_MAX]
else:
    names=elig[:NAMES_MAX]
lg("SEL=%s names=%d %.0fs"%(SEL,len(names),time.time()-t0))
def t_var_es(a,nu):
    # standardized (unit-var) Student-t: VaR & ES at lower tail prob a (both negative)
    s=math.sqrt((nu-2.0)/nu); qraw=stats.t.ppf(a,nu)
    es_raw=-(nu+qraw*qraw)/(nu-1.0)*stats.t.pdf(qraw,nu)/a      # E[T|T<=qraw], standard t_nu
    return s*qraw, s*es_raw
def fz0(r,q,e,a):
    # Patton-Ziegel-Chen (2019) FZ0 loss, e<0, q<0; lower=better. Indicator term uses (r-q) so breaches ADD loss
    # (validated by Monte Carlo: true (VaR,ES) is the unique minimizer at alpha=0.025 & 0.01).
    e=min(e,-1e-6)
    return (1.0/(a*e))*(1.0 if r<=q else 0.0)*(r-q) + q/e + math.log(-e) - 1.0
MODELS=['garch_norm','garch_t','fhs','hybrid_evt']
# per-date accumulation of loss (for DM) and scalar sums
byd={a:{m:{} for m in MODELS} for a in ALPHAS}      # date-> list of fz losses
scal={a:{m:{'fz':[],'pin':[],'br':[],'esabs':[],'es_real':[]} for m in MODELS} for a in ALPHAS}
def gpd_var_es(ztr,a,pu=0.075):
    u=np.quantile(ztr,pu); ex=u-ztr[ztr<u]; ex=ex[ex>0]
    if len(ex)<40: return None
    try: xi,_,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return None
    if beta<=0 or xi>=1: return None
    qex=(beta/xi)*(((a/pu)**(-xi))-1) if abs(xi)>1e-6 else -beta*math.log(a/pu)
    VaRz=u-qex; ESz=u-(qex+beta)/(1-xi)
    return float(VaRz),float(ESz)
nn=0
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
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); ztr=z[:sp]
    if nu<=2.5: nu=2.5
    for a in ALPHAS:
        znz,enz=stats.norm.ppf(a), -stats.norm.pdf(stats.norm.ppf(a))/a           # normal std VaR/ES
        zt,et=t_var_es(a,nu)                                                       # t std VaR/ES
        zf=np.quantile(ztr,a); mask=ztr<=zf; ef=ztr[mask].mean() if mask.any() else zf  # FHS residual VaR/ES
        gp=gpd_var_es(ztr,a)                                                        # EVT tail on residuals
        zh,eh=(gp if gp else (zf,ef))
        specs={'garch_norm':(znz,enz),'garch_t':(zt,et),'fhs':(zf,ef),'hybrid_evt':(zh,eh)}
        for k in range(sp,n-0):
            r=y[k]
            for m,(zq,zes) in specs.items():
                VaR=mu+sig[k]*zq; ES=mu+sig[k]*zes
                L=fz0(r,VaR,ES,a); d=str(dts[k])[:10]
                byd[a][m].setdefault(d,[]).append(L)
                sc=scal[a][m]; sc['fz'].append(L)
                sc['pin'].append((a-(1.0 if r<=VaR else 0.0))*(VaR-r)*-1.0 if False else max(a*(r-VaR),(a-1)*(r-VaR)))
                sc['br'].append(1.0 if r<=VaR else 0.0); sc['esabs'].append(abs(ES))
                if r<=VaR: sc['es_real'].append(r)
    nn+=1
    if nn%20==0: lg("  %d names %.0fs"%(nn,time.time()-t0))
def dm(ref_by,alt_by):
    ds=sorted(set(ref_by)&set(alt_by)); diffs=np.array([np.mean(alt_by[d])-np.mean(ref_by[d]) for d in ds])
    m=diffs.mean(); nD=len(diffs)
    g0=diffs.var()
    v=g0+2*sum((1-l/(NWLAG+1))*np.mean((diffs[l:]-m)*(diffs[:-l]-m)) for l in range(1,NWLAG+1))
    se=math.sqrt(max(v,1e-12)/nD); return float(m),float(m/se if se>0 else 0.0),nD
out={'note':'Fissler-Ziegel FZ0 joint (VaR,ES) scoring (Patton-Ziegel-Chen 2019) + economic translation. FZ0 lower=better; '
            'DM alt-vs-hybrid_evt positive stat => alt WORSE (hybrid better). capital_bps = mean |ES97.5| in bps (FRTB capital base); '
            'ce_bps = mean-ES certainty-equivalent gap vs hybrid at lambda=0.1. In-sandbox CRSP subset.',
     'n_names':nn,'alphas':ALPHAS,'per_alpha':{}}
for a in ALPHAS:
    A={'models':{},'DM_vs_hybrid_evt':{}}
    for m in MODELS:
        sc=scal[a][m]
        A['models'][m]={'avg_FZ0':round(float(np.mean(sc['fz'])),4),'avg_pinball':round(float(np.mean(sc['pin'])),4),
                        'breach':round(float(np.mean(sc['br'])),4),'target':a,
                        'avg_absES_bps':round(float(np.mean(sc['esabs']))*100,1),
                        'realized_tail_mean':round(float(np.mean(sc['es_real'])) if sc['es_real'] else float('nan'),3)}
    for m in MODELS:
        if m=='hybrid_evt': continue
        mm,st,nD=dm(byd[a]['hybrid_evt'],byd[a][m]); A['DM_vs_hybrid_evt'][m]={'dFZ0':round(mm,5),'DM_stat':round(st,2),'p_one_sided':round(1-stats.norm.cdf(st),4),'n_dates':nD}
    # economic: capital bps vs hybrid + mean-ES certainty-equivalent (lambda*Delta|ES|)
    lam=0.1; base=np.mean(scal[a]['hybrid_evt']['esabs'])
    A['economic']={m:{'capital_bps_vs_hybrid':round((np.mean(scal[a][m]['esabs'])-base)*100,1),
                      'ce_bps_vs_hybrid':round(lam*(np.mean(scal[a][m]['esabs'])-base)*100,2)} for m in MODELS}
    out['per_alpha']['alpha_%g'%a]=A
out['selection']=SEL
outname="fz_score_results.json" if SEL=="largecap" else "fz_score_%s_results.json"%SEL
json.dump(out,open(os.path.join(D,outname),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
