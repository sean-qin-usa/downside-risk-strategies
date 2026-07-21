# KOREA DEEP + SIGNIFICANCE (host, Bloomberg) — P1#2 of the Bloomberg plan. Upgrades job_korea_deep.py:
#   (1) FIXED resid-kurtosis (was None everywhere); (2) per-date Diebold-Mariano significance of nonparam(GBM) vs GARCH-t,
#   full-history AND the 2026 crisis slice; (3) batched GBM prediction (~10x faster). Places Korea on the misspecification frontier.
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
def rkurt(r):                                     # FIXED
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
    s=d.mean()/math.sqrt(v/T); return dict(DM=round(float(s),2),p_one_sided=round(float(1-stats.norm.cdf(s)),4))
def h2h(D,sp):
    from arch import arch_model
    y=D['y'].values; n=len(D)
    if sp<250 or n-sp<40: return None
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
KO={
 'index':[('KOSPI','KOSPI Index'),('KOSDAQ','KOSDAQ Index'),('KOSPI200','KOSPI2 Index')],
 'volatility':[('VKOSPI','VKOSPI Index')],'fx':[('USDKRW','USDKRW Curncy')],
 'rates':[('KTB3Y','GVSK3YR Index'),('KTB10Y','GVSK10YR Index')],
 'ai_memory':[('SamsungElec','005930 KS Equity'),('SKHynix','000660 KS Equity')],
 'retail_volatile':[('Naver','035420 KS Equity'),('Kakao','035720 KS Equity'),('Krafton','259960 KS Equity'),('EcoPro','086520 KS Equity'),('EcoProBM','247540 KS Equity'),('KakaoGames','293490 KS Equity')],
 'defense':[('HanwhaAero','012450 KS Equity'),('KoreaAero','047810 KS Equity'),('HyundaiRotem','064350 KS Equity')],
 'bio':[('SamsungBio','207940 KS Equity'),('Alteogen','196170 KS Equity')],
 'kcontent_ship':[('HYBE','352820 KS Equity'),('HanwhaOcean','042660 KS Equity'),('HDHyundaiHeavy','329180 KS Equity')],
}
start=dt.date(2010,1,1); end=dt.date.today(); crisis=pd.Timestamp('2026-01-01')
out={'note':'Korea deep + significance: GBM vs GARCH-t across Korean data types with per-date Diebold-Mariano (DM>0 & p<0.05 => '
            'nonparam significantly better). full = 60/40 split; crisis2026 = train<2026,test=2026. resid_kurt FIXED. Places Korea '
            'on the misspecification frontier (edge vs post-GARCH residual kurtosis).','per_asset':{},'by_type':{}}
for typ,lst in KO.items():
    rows=[]
    for nm,tk in lst:
        try:
            s=series(tk,start,end)
            if s is None or len(s)<300: lg("%s NO DATA (%s)"%(nm,tk)); continue
            r=(s.diff().dropna()*100.0) if typ=='rates' else (np.log(s/s.shift(1)).dropna())*100.0
            D=feats(r); full=h2h(D,int(len(D)*0.6))
            sp2=int((D.index<crisis).sum()); cri=h2h(D,sp2) if (len(D)-sp2)>=40 else None
            rk=rkurt(r.values)
            rec=dict(type=typ,ticker=tk,n_days=len(r),ann_vol=round(float(r.std()*np.sqrt(252)),1),resid_kurt=round(rk,1) if rk else None,
                     full_ratio=full['ratio'] if full else None,full_DM=full['DM'] if full else None,
                     ratio_2026=cri['ratio'] if cri else None,crisis2026_DM=cri['DM'] if cri else None)
            out['per_asset'][nm]=rec; rows.append(rec)
            lg("%-14s [%s] full %s DM %s | 2026 %s DM %s | rkurt %s  %.0fs"%(nm,typ,rec['full_ratio'],rec['full_DM'],rec['ratio_2026'],rec['crisis2026_DM'],rec['resid_kurt'],time.time()-t0))
            json.dump(out,open(os.path.join(P,"korea_sig.json"),"w"),indent=2,default=str)
        except Exception as ex: lg("%s ERR %s"%(nm,str(ex)[:70]))
    fr=[x['full_ratio'] for x in rows if x['full_ratio'] is not None]; rk=[x['resid_kurt'] for x in rows if x['resid_kurt'] is not None]
    if rows: out['by_type'][typ]=dict(n=len(rows),mean_full_ratio=round(float(np.mean(fr)),4) if fr else None,mean_resid_kurt=round(float(np.mean(rk)),1) if rk else None)
out['n_assets']=len(out['per_asset'])
json.dump(out,open(os.path.join(P,"korea_sig.json"),"w"),indent=2,default=str)
lg("DONE assets=%d %.0fs"%(out['n_assets'],time.time()-t0)); lg(json.dumps(out['by_type'],indent=2))
