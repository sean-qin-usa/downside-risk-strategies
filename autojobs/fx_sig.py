# FX CRISIS-SIGNIFICANCE STUDY (host, Bloomberg) — P1 of the Bloomberg plan. Upgrades job_fx_study.py with:
#   (1) per-date Diebold-Mariano significance of nonparam(GBM) vs GARCH-t, per pair + pooled per tier (esp. crisis FX);
#   (2) FIXED resid-kurtosis gk() (was None everywhere -> also broke over_time);
#   (3) batched GBM prediction + vectorized OOS sigma -> ~10x faster than the original.
# Deliverable: turn the 12-14% hyperinflation-FX wins (ARS/EGP/NGN) into DM-significant results.
import json, os, time, math, warnings; warnings.filterwarnings("ignore")
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import numpy as np, pandas as pd, datetime as dt
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def series(tk,start,end):
    pdf=to_pd(blp.bdh(tk,'px_last',start,end))
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vc=pdf.columns[cols.index('value')]; dc=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dc,vc]].dropna().copy(); s[dc]=pd.to_datetime(s[dc],errors='coerce'); return s.dropna(subset=[dc]).set_index(dc)[vc].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def feats(r):
    d=pd.DataFrame(index=r.index); d['y']=r.values
    d['lag1']=r.shift(1); d['abs1']=r.abs().shift(1)
    d['rv5']=r.rolling(5,min_periods=3).std().shift(1); d['rv21']=r.rolling(21,min_periods=8).std().shift(1)
    d['mean21']=r.rolling(21,min_periods=8).mean().shift(1); d['dn']=(r.shift(1)<0).astype(float)
    return d.dropna()
XC=['lag1','abs1','rv5','rv21','mean21','dn']
def gk(y):                                       # FIXED residual kurtosis: standardize by conditional vol directly
    from arch import arch_model
    try:
        res=arch_model(y,vol='Garch',p=1,o=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        sr=np.asarray(res.resid,float)/np.asarray(res.conditional_volatility,float); sr=sr[np.isfinite(sr)]
        return float(stats.kurtosis(sr,fisher=False)) if len(sr)>50 else None
    except Exception: return None
def nw_dm(d,lag=10):                              # Diebold-Mariano on loss-diff series d (>0 => nonparam better)
    d=np.asarray(d,float); d=d[np.isfinite(d)]; T=len(d)
    if T<30: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(dd[k:]*dd[:-k])
    if v<=0: return None
    s=d.mean()/math.sqrt(v/T); return dict(DM=round(float(s),2),p_one_sided=round(float(1-stats.norm.cdf(s)),4))
def h2h(r):
    from arch import arch_model
    D=feats(r); y=D['y'].values; n=len(D); sp=int(n*0.6)
    if n<400: return None
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: return None
    tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    # OOS GARCH sigma path (vectorized recursion)
    sig=np.empty(n); e0=y[:sp]-mu; s2=np.empty(sp); s2[0]=e0.var()
    for k in range(1,sp): s2[k]=om+al*e0[k-1]**2+be*s2[k-1]
    cur=s2[-1]
    for i in range(sp,n): cur=om+al*(y[i-1]-mu)**2+be*cur; sig[i]=math.sqrt(max(cur,1e-9))
    # batched GBM quantiles on all test rows
    Xtr=D[XC].values[:sp]; Xte=D[XC].values[sp:]
    gq={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=150,max_depth=3,learning_rate=0.08).fit(Xtr,y[:sp]).predict(Xte) for t in TAUS}
    yte=y[sp:]; gper=np.zeros(len(yte)); nper=np.zeros(len(yte))
    for t in TAUS:
        gper+=pin(yte,mu+sig[sp:]*stats.t.ppf(t,nu)/tsc,t); nper+=pin(yte,gq[t],t)
    gper/=len(TAUS); nper/=len(TAUS); dts=D.index[sp:]
    dm=nw_dm(gper-nper)
    return dict(garch=round(float(gper.mean()),4),nonparam=round(float(nper.mean()),4),ratio=round(float(nper.mean()/gper.mean()),4),
                n_oos=len(yte),DM=dm,_gper=gper,_nper=nper,_dts=dts)
TIERS={
 'fx_major':[('EURUSD','EURUSD Curncy'),('USDJPY','USDJPY Curncy'),('GBPUSD','GBPUSD Curncy'),('USDCHF','USDCHF Curncy'),('AUDUSD','AUDUSD Curncy'),('USDCAD','USDCAD Curncy'),('USDSEK','USDSEK Curncy')],
 'fx_em':[('USDMXN','USDMXN Curncy'),('USDBRL','USDBRL Curncy'),('USDZAR','USDZAR Curncy'),('USDINR','USDINR Curncy'),('USDIDR','USDIDR Curncy'),('USDTHB','USDTHB Curncy'),('USDKRW','USDKRW Curncy'),('USDPHP','USDPHP Curncy'),('USDCLP','USDCLP Curncy'),('USDPLN','USDPLN Curncy')],
 'fx_crisis':[('USDTRY','USDTRY Curncy'),('USDARS','USDARS Curncy'),('USDRUB','USDRUB Curncy'),('USDEGP','USDEGP Curncy'),('USDNGN','USDNGN Curncy'),('USDUAH','USDUAH Curncy'),('USDPKR','USDPKR Curncy')],
}
start=dt.date(2000,1,1); end=dt.date.today()
out={'note':'FX crisis-significance: GBM-quantile vs GARCH-t per USD pair by tier, WITH per-date Diebold-Mariano significance '
            '(DM>0 & p<0.05 => nonparam significantly better). resid_kurt fixed. Pooled per-tier DM aligns per-date loss diffs '
            'across pairs. Goal: make the hyperinflation-FX wins (ARS/EGP/NGN) statistically significant.','per_pair':{},'by_tier':{},'over_time':{}}
for tier,lst in TIERS.items():
    rows=[]; diffpanel={}
    for nm,tk in lst:
        try:
            s=series(tk,start,end)
            if s is None or len(s)<400: lg("%s NO DATA"%nm); continue
            r=(np.log(s/s.shift(1)).dropna())*100.0
            hh=h2h(r); rk=gk(r.values)
            if hh is None: continue
            diffpanel[nm]=pd.Series(hh.pop('_gper')-hh.pop('_nper'),index=hh.pop('_dts'))
            rec=dict(tier=tier,start=str(r.index.min().date()),n_days=len(r),ann_vol=round(float(r.std()*np.sqrt(252)),1),worst=round(float(r.min()),1),resid_kurt=round(rk,1) if rk else None,**hh)
            out['per_pair'][nm]=rec; rows.append(rec)
            lg("%-8s [%s] ratio %s DM %s resid_kurt %s  %.0fs"%(nm,tier,hh['ratio'],hh['DM'],rec['resid_kurt'],time.time()-t0))
            json.dump(out,open(os.path.join(P,"fx_sig.json"),"w"),indent=2,default=str)
        except Exception as ex: lg("%s ERR %s"%(nm,str(ex)[:70]))
    if rows:
        rr=[x['ratio'] for x in rows]; rk=[x['resid_kurt'] for x in rows if x['resid_kurt'] is not None]
        pooled=pd.DataFrame(diffpanel).mean(axis=1).dropna().values if diffpanel else np.array([])   # per-date mean loss-diff across tier pairs
        out['by_tier'][tier]=dict(n=len(rows),mean_ratio=round(float(np.mean(rr)),4),nonparam_wins=int(sum(1 for x in rr if x<1.0)),
                                  mean_resid_kurt=round(float(np.mean(rk)),1) if rk else None,pooled_DM=nw_dm(pooled))
        lg("TIER %s %s"%(tier,json.dumps(out['by_tier'][tier])))
for nm,tk in [('EURUSD','EURUSD Curncy'),('USDBRL','USDBRL Curncy'),('USDTRY','USDTRY Curncy'),('USDRUB','USDRUB Curncy')]:
    try:
        s=series(tk,start,end); r=(np.log(s/s.shift(1)).dropna())*100.0; y=r.values; idx=r.index; ts=[]; W=500
        for i in range(W,len(y),20):
            k=gk(y[i-W:i])
            if k is not None: ts.append((str(idx[i].date()),round(k,1)))
        out['over_time'][nm]=ts; lg("over_time %s: %d windows peak %s"%(nm,len(ts),max((k for _,k in ts),default=None)))
    except Exception as ex: lg("over_time %s ERR %s"%(nm,str(ex)[:60]))
json.dump(out,open(os.path.join(P,"fx_sig.json"),"w"),indent=2,default=str)
lg("BY TIER:\n"+json.dumps(out['by_tier'],indent=2)); lg("DONE %.0fs"%(time.time()-t0))
