# KOREA STUDY: does the nonparametric (IQN-family) edge over GARCH-t grow for less-stable / retail-driven / newer Korean names?
# Three tiers: indices, new/volatile (Naver/Kakao/Krafton/KakaoGames/EcoPro...), stable blue-chips (Samsung/SKHynix/Hyundai...).
# Per name: GARCH-t vs GBM-quantile pinball (walk-forward), ratio (<1 = nonparam wins), residual-kurtosis-after-GARCH (misspecification), + COVID/2022-23 crisis windows.
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
def pin(y,q,t): d=y-q; return tau*d if False else np.where(d>=0,t*d,(t-1)*d)
def feats(r):
    d=pd.DataFrame(index=r.index); d['y']=r.values
    d['lag1']=r.shift(1); d['abs1']=r.abs().shift(1)
    d['rv5']=r.rolling(5,min_periods=3).std().shift(1); d['rv21']=r.rolling(21,min_periods=8).std().shift(1)
    d['mean21']=r.rolling(21,min_periods=8).mean().shift(1); d['dn']=(r.shift(1)<0).astype(float)
    return d.dropna()
XC=['lag1','abs1','rv5','rv21','mean21','dn']
def garch_resid_kurt(r):
    try:
        from arch import arch_model
        res=arch_model(r,vol='Garch',p=1,o=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        z=res.std_resid.dropna(); return float(stats.kurtosis(z,fisher=False))
    except Exception: return None
def h2h(r):
    # walk-forward-ish single 60/40 split: GARCH-t vs GBM quantile, avg pinball on OOS
    D=feats(r); y=D['y'].values; n=len(D); sp=int(n*0.6)
    if n<400: return None
    from arch import arch_model
    gp=None
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: return None
    e=y[:sp]-mu; s2=np.empty(len(e)); s2[0]=e.var()
    for k in range(1,len(e)): s2[k]=om+al*e[k-1]**2+be*s2[k-1]
    sig2=s2[-1]; tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    gbm={}
    for t in TAUS:
        m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=150,max_depth=3,learning_rate=0.08); m.fit(D[XC].values[:sp],y[:sp]); gbm[t]=m
    gl=nl=0.0; cnt=0
    for i in range(sp,n):
        sig2=om+al*(y[i-1]-mu)**2+be*sig2; sig=math.sqrt(max(sig2,1e-9)); yi=y[i]
        gl+=np.mean([pin(yi,mu+sig*stats.t.ppf(t,nu)/tsc,t) for t in TAUS])
        xr=D[XC].values[i:i+1]; nl+=np.mean([pin(yi,float(gbm[t].predict(xr)[0]),t) for t in TAUS]); cnt+=1
    return dict(garch=round(gl/cnt,4),nonparam=round(nl/cnt,4),ratio=round(nl/gl,4),n_oos=cnt)
TIERS={
 'index':[('KOSPI','KOSPI Index'),('KOSDAQ','KOSDAQ Index')],
 'new_volatile':[('Naver','035420 KS Equity'),('Kakao','035720 KS Equity'),('Krafton','259960 KS Equity'),('KakaoGames','293490 KS Equity'),('Netmarble','251270 KS Equity'),('EcoProBM','247540 KS Equity'),('EcoPro','086520 KS Equity'),('SamsungBio','207940 KS Equity')],
 'stable_bluechip':[('SamsungElec','005930 KS Equity'),('SKHynix','000660 KS Equity'),('HyundaiMotor','005380 KS Equity'),('POSCO','005490 KS Equity'),('LGChem','051910 KS Equity'),('Kia','000270 KS Equity'),('Shinhan','055550 KS Equity'),('KT','030200 KS Equity')],
}
start=dt.date(2005,1,1); end=dt.date.today()
out={'note':'Korea study: GBM-quantile (IQN-family, nonparametric) vs GARCH-t. ratio=nonparam/garch pinball (<1 = nonparam better). resid_kurt=kurtosis of GJR-GARCH-t standardized residuals (misspecification; higher=GARCH fails more). Thesis: less-stable/newer names -> lower ratio + higher resid_kurt.','per_name':{},'by_tier':{}}
for tier,lst in TIERS.items():
    rows=[]
    for nm,tk in lst:
        try:
            s=series(tk,start,end)
            if s is None or len(s)<400: lg("%s NO DATA"%nm); continue
            r=(np.log(s/s.shift(1)).dropna())*100.0
            hh=h2h(r); rk=garch_resid_kurt(r)
            if hh is None: continue
            rec=dict(tier=tier,ticker=tk,start=str(r.index.min().date()),n_days=len(r),ann_vol=round(float(r.std()*np.sqrt(252)),1),worst=round(float(r.min()),1),resid_kurt=round(rk,1) if rk else None,**hh)
            out['per_name'][nm]=rec; rows.append(rec)
            lg("%s [%s] ratio %s garch %s nonparam %s resid_kurt %s annvol %s  %.0fs"%(nm,tier,hh['ratio'],hh['garch'],hh['nonparam'],rec['resid_kurt'],rec['ann_vol'],time.time()-t0))
            json.dump(out,open(os.path.join(P,"korea_study.json"),"w"),indent=2,default=str)
        except Exception as ex:
            lg("%s ERR %s"%(nm,str(ex)[:80]))
    if rows:
        rr=[x['ratio'] for x in rows]; rk=[x['resid_kurt'] for x in rows if x['resid_kurt'] is not None]
        out['by_tier'][tier]=dict(n=len(rows),mean_ratio=round(float(np.mean(rr)),4),median_ratio=round(float(np.median(rr)),4),
                                  n_nonparam_wins=int(sum(1 for x in rr if x<1.0)),mean_resid_kurt=round(float(np.mean(rk)),1) if rk else None,mean_annvol=round(float(np.mean([x['ann_vol'] for x in rows])),1))
json.dump(out,open(os.path.join(P,"korea_study.json"),"w"),indent=2,default=str)
lg("BY TIER:\n"+json.dumps(out['by_tier'],indent=2)); lg("DONE %.0fs"%(time.time()-t0))
