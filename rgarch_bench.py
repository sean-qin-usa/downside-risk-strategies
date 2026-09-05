# Modern-comparator robustness: Realized GARCH (RV-driven conditional variance, Hansen-Huang-Shek 2012 family)
# vs the paper's classical benchmarks, on the intraday-covered 2014-2024 subsample of 30 large-cap US equities,
# scored under the SAME Fissler-Ziegel FZ0 joint (VaR,ES) loss and date-clustered DM used in fz_score.py.
import os, json, time, math, glob, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats, optimize
from arch import arch_model
t0=time.time(); lg=lambda s:print(s,flush=True)
ALPHAS=[0.025,0.01]; NWLAG=5
NMAX=int(os.environ.get("NMAX","30"))

# ---------- data ----------
rm=pd.concat([pd.read_csv(f) for f in sorted(glob.glob("panel_rm_*.csv"))], ignore_index=True)
rm["date"]=pd.to_datetime(rm["date"])
ret=pd.read_csv("crsp_panel_returns.csv"); ret["date"]=pd.to_datetime(ret["date"]); ret["ret"]=pd.to_numeric(ret["ret"],errors="coerce")*100.0
import os as _os
BYTK = _os.path.exists("crsp_returns_30.csv")
if BYTK:
    r30=pd.read_csv("crsp_returns_30.csv"); r30["date"]=pd.to_datetime(r30["date"]); r30["ret"]=pd.to_numeric(r30["ret"],errors="coerce")*100.0
    RETBYTK={tk:g[["date","ret"]].dropna() for tk,g in r30.groupby("ticker")}
    names_all=sorted(RETBYTK.keys())
    lg("BY-TICKER returns: %d tickers %d rows %.0fs"%(len(names_all),len(r30),time.time()-t0))
else:
    tmap=pd.read_csv("ticker_permno_map.csv"); t2p=dict(zip(tmap["ticker"].astype(str), tmap["permno"].astype(int)))
    names_all=list(t2p.keys())
    lg("PERMNO-MAP returns: rm rows=%d ret rows=%d map=%d %.0fs"%(len(rm),len(ret),len(t2p),time.time()-t0))

# ---------- scoring primitives (identical to fz_score.py) ----------
def fz0(r,q,e,a):
    e=min(e,-1e-6)
    return (1.0/(a*e))*(1.0 if r<=q else 0.0)*(r-q) + q/e + math.log(-e) - 1.0
def t_var_es(a,nu):
    s=math.sqrt((nu-2.0)/nu); qraw=stats.t.ppf(a,nu)
    es_raw=-(nu+qraw*qraw)/(nu-1.0)*stats.t.pdf(qraw,nu)/a
    return s*qraw, s*es_raw
def gpd_var_es(ztr,a,pu=0.075):
    u=np.quantile(ztr,pu); ex=u-ztr[ztr<u]; ex=ex[ex>0]
    if len(ex)<40: return None
    try: xi,_,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return None
    if beta<=0 or xi>=1: return None
    qex=(beta/xi)*(((a/pu)**(-xi))-1) if abs(xi)>1e-6 else -beta*math.log(a/pu)
    return float(u-qex), float(u-(qex+beta)/(1-xi))

# ---------- Realized GARCH: log h_t = om + be*log h_{t-1} + ga*log RV_{t-1}, Gaussian return QMLE ----------
def rgarch_sigma(y, rv, sp):
    # y: returns(%), rv: realized variance in %^2 aligned to y; fit on [:sp], return full sigma path
    ly=np.log(np.maximum(rv,1e-10)); n=len(y); v0=max(np.var(y[:sp]),1e-6)
    def negll(th):
        om,be,ga,mu=th
        if not(0.0<be<0.999): return 1e10
        lh=math.log(v0); ll=0.0
        for k in range(sp):
            if k>0: lh=om+be*lh+ga*ly[k-1]
            if lh>25 or lh<-25: return 1e10
            h=math.exp(lh); e=y[k]-mu
            ll+= -0.5*(math.log(2*math.pi)+lh+e*e/h)
        return -ll
    best=None
    for th0 in ([ -0.2,0.9,0.08, float(np.mean(y[:sp]))],[0.0,0.85,0.12,0.0]):
        r=optimize.minimize(negll,np.array(th0),method="Nelder-Mead",options={"maxiter":2500,"xatol":1e-4,"fatol":1e-4})
        if best is None or r.fun<best.fun: best=r
    om,be,ga,mu=best.x
    lh=np.empty(n); lh[0]=math.log(v0)
    for k in range(1,n): lh[k]=om+be*lh[k-1]+ga*ly[k-1]
    lh=np.clip(lh,-25,25)
    return np.sqrt(np.exp(lh)), float(mu), (float(om),float(be),float(ga))

MODELS=["garch_t","fhs","hybrid_evt","rgarch_t","rgarch_evt"]
byd={a:{m:{} for m in MODELS} for a in ALPHAS}
scal={a:{m:{"fz":[],"br":[],"esabs":[]} for m in MODELS} for a in ALPHAS}
used=[]; RGPARS=[]
names=names_all[:NMAX]
for tk in names:
    if BYTK:
        g=RETBYTK.get(tk)
        if g is None: continue
    else:
        pn=t2p.get(tk)
        if pn is None: continue
        g=ret[ret.permno==pn][["date","ret"]].dropna()
    r=rm[rm.ticker==tk][["date","rv"]].dropna()
    d=pd.merge(g,r,on="date",how="inner").sort_values("date")
    if len(d)<1200: lg("  skip %s n=%d"%(tk,len(d))); continue
    y=d["ret"].values.astype(float); rv=d["rv"].values.astype(float)*1e4  # raw^2 -> %^2
    dts=d["date"].values; n=len(y); sp=int(n*0.6)
    # --- classical GARCH-t (as in fz_score.py) ---
    try:
        res=arch_model(y[:sp],vol="Garch",p=1,q=1,dist="t",rescale=False).fit(disp="off",show_warning=False)
        p=res.params; om,al,be,mu=float(p["omega"]),float(p["alpha[1]"]),float(p["beta[1]"]),float(p.get("mu",0)); nu=float(p.get("nu",8))
    except Exception as ex: lg("  garch fail %s %s"%(tk,str(ex)[:40])); continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); ztr=z[:sp]
    if nu<=2.5: nu=2.5
    # --- Realized GARCH sigma path ---
    try:
        sig_rg, mu_rg, rgpar = rgarch_sigma(y, rv, sp); RGPARS.append((tk,)+rgpar)
        zrg=(y-mu_rg)/np.maximum(sig_rg,1e-6); zrgtr=zrg[:sp]
    except Exception as ex:
        lg("  rgarch fail %s %s"%(tk,str(ex)[:40])); sig_rg=sig; mu_rg=mu; zrg=z; zrgtr=ztr
    for a in ALPHAS:
        zt,et=t_var_es(a,nu)
        zf=np.quantile(ztr,a); mask=ztr<=zf; ef=ztr[mask].mean() if mask.any() else zf
        gp=gpd_var_es(ztr,a); zh,eh=(gp if gp else (zf,ef))
        # rgarch tails on its own standardized residuals
        nurg=max(4.0, 1.0/max(stats.kurtosis(zrgtr,fisher=True)/6.0,1e-3)+4.0) if len(zrgtr)>50 else 8.0
        zrt,ert=t_var_es(a, min(nurg,50))
        gprg=gpd_var_es(zrgtr,a); zre,ere=(gprg if gprg else (np.quantile(zrgtr,a), zrgtr[zrgtr<=np.quantile(zrgtr,a)].mean()))
        specs={"garch_t":(mu,sig,zt,et),"fhs":(mu,sig,zf,ef),"hybrid_evt":(mu,sig,zh,eh),
               "rgarch_t":(mu_rg,sig_rg,zrt,ert),"rgarch_evt":(mu_rg,sig_rg,zre,ere)}
        for k in range(sp,n):
            rr=y[k]
            for m,(mm,ss,zq,zes) in specs.items():
                VaR=mm+ss[k]*zq; ES=mm+ss[k]*zes
                L=fz0(rr,VaR,ES,a); dd=str(dts[k])[:10]
                byd[a][m].setdefault(dd,[]).append(L)
                sc=scal[a][m]; sc["fz"].append(L); sc["br"].append(1.0 if rr<=VaR else 0.0); sc["esabs"].append(abs(ES))
    used.append(tk); lg("  ok %s n=%d sp=%d %.0fs"%(tk,n,sp,time.time()-t0))
lg("used %d names %.0fs"%(len(used),time.time()-t0))

def dm(ref_by,alt_by):
    ds=sorted(set(ref_by)&set(alt_by)); diffs=np.array([np.mean(alt_by[d])-np.mean(ref_by[d]) for d in ds])
    if len(diffs)<10: return 0.0,0.0,len(diffs)
    m=diffs.mean(); nD=len(diffs); g0=diffs.var()
    v=g0+2*sum((1-l/(NWLAG+1))*np.mean((diffs[l:]-m)*(diffs[:-l]-m)) for l in range(1,NWLAG+1))
    se=math.sqrt(max(v,1e-12)/nD); return float(m),float(m/se if se>0 else 0.0),nD
out={"note":"Realized GARCH (RV-driven log-variance, Gaussian return QMLE; t and EVT tails) vs classical battery, "
            "2014-2024 intraday-covered 30-name subsample, FZ0 joint (VaR,ES) loss, date-clustered DM (NW lag 5). "
            "DM alt-vs-hybrid_evt: positive => alt WORSE than the paper's EVT-hybrid core.",
     "n_names":len(used),"names":used,"alphas":ALPHAS,"per_alpha":{}}
for a in ALPHAS:
    A={"models":{},"DM_vs_hybrid_evt":{},"DM_rgarch_evt_vs_garch_t":{}}
    for m in MODELS:
        sc=scal[a][m]
        A["models"][m]={"avg_FZ0":round(float(np.mean(sc["fz"])),4),"breach":round(float(np.mean(sc["br"])),4),
                        "target":a,"avg_absES_pct":round(float(np.mean(sc["esabs"])),3)}
    for m in MODELS:
        if m=="hybrid_evt": continue
        mm,st,nD=dm(byd[a]["hybrid_evt"],byd[a][m]); A["DM_vs_hybrid_evt"][m]={"dFZ0":round(mm,5),"DM_stat":round(st,2),"n_dates":nD}
    mm,st,nD=dm(byd[a]["garch_t"],byd[a]["rgarch_evt"]); A["DM_rgarch_evt_vs_garch_t"]={"dFZ0":round(mm,5),"DM_stat":round(st,2),"n_dates":nD}
    out["per_alpha"]["alpha_%g"%a]=A
out["rgarch_params"]=[{"ticker":t,"omega":round(o,4),"beta":round(b,4),"gamma":round(g,4)} for (t,o,b,g) in RGPARS]
json.dump(out,open("rgarch_bench_results.json","w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
