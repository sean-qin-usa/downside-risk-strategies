# CROSS-COUNTRY STABILITY GRADIENT (host, Bloomberg) — P2 of the plan. Does the nonparam edge scale developed -> frontier?
# Pull ~26 equity indices stratified by development tier; per country: GBM vs GARCH-t pinball ratio + per-date Diebold-Mariano +
# post-GARCH residual kurtosis. KEY figure: per-country edge vs per-country resid_kurt (extends the misspecification frontier to
# the COUNTRY level). Prediction: edge ~0/insignificant for developed (low resid_kurt), larger/significant for frontier (high).
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
    d['lag1']=r.shift(1); d['abs1']=r.abs().shift(1); d['rv5']=r.rolling(5,min_periods=3).std().shift(1)
    d['rv21']=r.rolling(21,min_periods=8).std().shift(1); d['mean21']=r.rolling(21,min_periods=8).mean().shift(1); d['dn']=(r.shift(1)<0).astype(float)
    return d.dropna()
XC=['lag1','abs1','rv5','rv21','mean21','dn']
def rkurt(r):
    from arch import arch_model
    try:
        res=arch_model(r,vol='Garch',p=1,o=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        sr=np.asarray(res.resid,float)/np.asarray(res.conditional_volatility,float); sr=sr[np.isfinite(sr)]
        return float(stats.kurtosis(sr,fisher=False)) if len(sr)>50 else None
    except Exception: return None
def nw_dm(d,lag=10):
    d=np.asarray(d,float); d=d[np.isfinite(d)]; T=len(d)
    if T<30: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(dd[k:]*dd[:-k])
    if v<=0: return None
    s=d.mean()/math.sqrt(v/T); return dict(DM=round(float(s),2),p=round(float(1-stats.norm.cdf(s)),4))
def h2h(r):
    from arch import arch_model
    D=feats(r); y=D['y'].values; n=len(D); sp=int(n*0.6)
    if n<500: return None
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: return None
    tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    e=y[:sp]-mu; s2=np.empty(sp); s2[0]=e.var()
    for k in range(1,sp): s2[k]=om+al*e[k-1]**2+be*s2[k-1]
    sig=np.empty(n); cur=s2[-1]
    for i in range(sp,n): cur=om+al*(y[i-1]-mu)**2+be*cur; sig[i]=math.sqrt(max(cur,1e-9))
    gq={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=150,max_depth=3,learning_rate=0.08).fit(D[XC].values[:sp],y[:sp]).predict(D[XC].values[sp:]) for t in TAUS}
    yte=y[sp:]; gper=np.zeros(len(yte)); nper=np.zeros(len(yte))
    for t in TAUS: gper+=pin(yte,mu+sig[sp:]*stats.t.ppf(t,nu)/tsc,t); nper+=pin(yte,gq[t],t)
    gper/=len(TAUS); nper/=len(TAUS)
    return dict(garch=round(float(gper.mean()),4),nonparam=round(float(nper.mean()),4),ratio=round(float(nper.mean()/gper.mean()),4),n_oos=len(yte),DM=nw_dm(gper-nper))
TIERS={
 'developed':[('US_SPX','SPX Index'),('EU_SX5E','SX5E Index'),('UK_UKX','UKX Index'),('JP_NKY','NKY Index'),('CA_SPTSX','SPTSX Index'),('AU_AS51','AS51 Index'),('DE_DAX','DAX Index'),('CH_SMI','SMI Index')],
 'emerging':[('KR_KOSPI','KOSPI Index'),('TW_TWSE','TWSE Index'),('IN_NIFTY','NIFTY Index'),('BR_IBOV','IBOV Index'),('MX_MEXBOL','MEXBOL Index'),('ZA_TOP40','TOP40 Index'),('CN_SHCOMP','SHCOMP Index'),('PL_WIG','WIG Index'),('TR_XU100','XU100 Index'),('ID_JCI','JCI Index')],
 'frontier':[('VN_VNINDEX','VNINDEX Index'),('EG_EGX30','EGX30 Index'),('PK_KSE100','KSE100 Index'),('NG_NGSE','NGSEINDX Index'),('SA_SASEIDX','SASEIDX Index'),('PH_PCOMP','PCOMP Index'),('LK_CSEALL','CSEALL Index'),('KE_NSE20','KNSMIDX Index')],
}
start=dt.date(2000,1,1); end=dt.date.today()
out={'note':'Cross-country stability gradient: GBM vs GARCH-t on equity indices by development tier, with per-date Diebold-Mariano '
            '(DM>0 & p<0.05 => nonparam sig better) and post-GARCH residual kurtosis. Tests whether the nonparam edge scales '
            'developed->frontier with country-level misspecification (resid_kurt). Extends the misspec frontier to the country level.',
     'per_country':{},'by_tier':{}}
allpairs=[]
for tier,lst in TIERS.items():
    rows=[]
    for nm,tk in lst:
        try:
            s=series(tk,start,end)
            if s is None or len(s)<500: lg("%s NO DATA (%s)"%(nm,tk)); continue
            r=(np.log(s/s.shift(1)).dropna())*100.0; hh=h2h(r); rk=rkurt(r.values)
            if hh is None: continue
            rec=dict(tier=tier,ticker=tk,n_days=len(r),ann_vol=round(float(r.std()*np.sqrt(252)),1),resid_kurt=round(rk,1) if rk else None,ratio=hh['ratio'],DM=hh['DM'])
            out['per_country'][nm]=rec; rows.append(rec)
            if rk is not None and hh['DM'] is not None: allpairs.append((rk,hh['garch']-hh['nonparam']))
            lg("%-12s [%s] ratio %s DM %s rkurt %s annvol %s  %.0fs"%(nm,tier,hh['ratio'],hh['DM'],rec['resid_kurt'],rec['ann_vol'],time.time()-t0))
            json.dump(out,open(os.path.join(P,"cross_country.json"),"w"),indent=2,default=str)
        except Exception as ex: lg("%s ERR %s"%(nm,str(ex)[:70]))
    if rows:
        rr=[x['ratio'] for x in rows]; rk=[x['resid_kurt'] for x in rows if x['resid_kurt'] is not None]
        out['by_tier'][tier]=dict(n=len(rows),mean_ratio=round(float(np.mean(rr)),4),nonparam_wins=int(sum(1 for x in rr if x<1.0)),
                                  sig_wins=int(sum(1 for x in rows if isinstance(x.get('DM'),dict) and x['DM'].get('DM') is not None and x['DM']['DM']>1.64)),mean_resid_kurt=round(float(np.mean(rk)),1) if rk else None)
        lg("TIER %s %s"%(tier,json.dumps(out['by_tier'][tier])))
if len(allpairs)>=6:
    rk_arr=np.array([a for a,_ in allpairs]); ed_arr=np.array([b for _,b in allpairs])
    out['edge_vs_residkurt_corr']=round(float(np.corrcoef(np.log(np.clip(rk_arr,1,None)),ed_arr)[0,1]),3)  # log-kurt vs edge
json.dump(out,open(os.path.join(P,"cross_country.json"),"w"),indent=2,default=str)
lg("BY TIER:\n"+json.dumps(out['by_tier'],indent=2)); lg("corr(log resid_kurt, edge)=%s"%out.get('edge_vs_residkurt_corr')); lg("DONE %.0fs"%(time.time()-t0))
