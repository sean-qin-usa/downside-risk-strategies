# KOREA DEEP: nonparametric (GBM) vs GARCH-t across MANY Korean data types, with a 2026-crisis-window slice (the AI-rally crash / circuit-breaker year).
# Types: indices, KOSPI vol (VKOSPI), USDKRW, rates, AI-memory leaders, retail-volatile, defense, bio, K-content/shipbuilding.
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
    try: return float(stats.kurtosis(arch_model(r,vol='Garch',p=1,o=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False).std_resid.dropna(),fisher=False))
    except Exception: return None
def h2h(D,sp):
    from arch import arch_model
    y=D['y'].values; n=len(D)
    if sp<250 or n-sp<40: return None
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: return None
    e=y[:sp]-mu; s2=np.empty(len(e)); s2[0]=e.var()
    for k in range(1,len(e)): s2[k]=om+al*e[k-1]**2+be*s2[k-1]
    sig2=s2[-1]; tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    gbm={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=150,max_depth=3,learning_rate=0.08).fit(D[XC].values[:sp],y[:sp]) for t in TAUS}
    Xte=D[XC].values; gl=nl=0.0; cnt=0
    for i in range(sp,n):
        sig2=om+al*(y[i-1]-mu)**2+be*sig2; sig=math.sqrt(max(sig2,1e-9)); yi=y[i]
        gl+=np.mean([pin(yi,mu+sig*stats.t.ppf(t,nu)/tsc,t) for t in TAUS]); nl+=np.mean([pin(yi,float(gbm[t].predict(Xte[i:i+1])[0]),t) for t in TAUS]); cnt+=1
    return dict(garch=round(gl/cnt,4),nonparam=round(nl/cnt,4),ratio=round(nl/gl,4),n_oos=cnt)
KO={
 'index':[('KOSPI','KOSPI Index'),('KOSDAQ','KOSDAQ Index'),('KOSPI200','KOSPI2 Index')],
 'volatility':[('VKOSPI','VKOSPI Index')],
 'fx':[('USDKRW','USDKRW Curncy')],
 'rates':[('KTB3Y','GVSK3YR Index'),('KTB10Y','GVSK10YR Index')],
 'ai_memory':[('SamsungElec','005930 KS Equity'),('SKHynix','000660 KS Equity')],
 'retail_volatile':[('Naver','035420 KS Equity'),('Kakao','035720 KS Equity'),('Krafton','259960 KS Equity'),('EcoPro','086520 KS Equity'),('EcoProBM','247540 KS Equity'),('KakaoGames','293490 KS Equity')],
 'defense':[('HanwhaAero','012450 KS Equity'),('KoreaAero','047810 KS Equity'),('HyundaiRotem','064350 KS Equity')],
 'bio':[('SamsungBio','207940 KS Equity'),('Alteogen','196170 KS Equity')],
 'kcontent_ship':[('HYBE','352820 KS Equity'),('HanwhaOcean','042660 KS Equity'),('HDHyundaiHeavy','329180 KS Equity')],
}
start=dt.date(2010,1,1); end=dt.date.today(); crisis=pd.Timestamp('2026-01-01')
out={'note':'Korea deep: GBM(IQN-family) vs GARCH-t across Korean data types. ratio=nonparam/garch pinball (<1=nonparam better) full-history (60/40 split); ratio_2026 uses train<2026,test=2026 (the AI-rally crash / circuit-breaker year). resid_kurt=GARCH-t std-resid kurtosis. n_types_predicted counts data types with a valid result.','per_asset':{},'by_type':{}}
for typ,lst in KO.items():
    rows=[]
    for nm,tk in lst:
        try:
            s=series(tk,start,end)
            if s is None or len(s)<300: lg("%s NO DATA (%s)"%(nm,tk)); continue
            if typ=='rates': r=s.diff().dropna()*100.0     # yields: daily change (bp*100 scale ~)
            else: r=(np.log(s/s.shift(1)).dropna())*100.0
            D=feats(r); full=h2h(D,int(len(D)*0.6))
            sp2=int((D.index<crisis).sum()); cri=h2h(D,sp2) if (len(D)-sp2)>=40 else None
            rk=rkurt(r.values)
            rec=dict(type=typ,ticker=tk,start=str(r.index.min().date()),n_days=len(r),ann_vol=round(float(r.std()*np.sqrt(252)),1),worst=round(float(r.min()),1),resid_kurt=round(rk,1) if rk else None,
                     full_ratio=full['ratio'] if full else None,ratio_2026crisis=cri['ratio'] if cri else None,full=full,crisis2026=cri)
            out['per_asset'][nm]=rec; rows.append(rec)
            lg("%-14s [%s] full_ratio %s  2026_ratio %s  resid_kurt %s  annvol %s  %.0fs"%(nm,typ,rec['full_ratio'],rec['ratio_2026crisis'],rec['resid_kurt'],rec['ann_vol'],time.time()-t0))
            json.dump(out,open(os.path.join(P,"korea_deep.json"),"w"),indent=2,default=str)
        except Exception as ex: lg("%s ERR %s"%(nm,str(ex)[:70]))
    fr=[x['full_ratio'] for x in rows if x['full_ratio'] is not None]; cr=[x['ratio_2026crisis'] for x in rows if x['ratio_2026crisis'] is not None]; rk=[x['resid_kurt'] for x in rows if x['resid_kurt'] is not None]
    if rows: out['by_type'][typ]=dict(n=len(rows),mean_full_ratio=round(float(np.mean(fr)),4) if fr else None,mean_2026_ratio=round(float(np.mean(cr)),4) if cr else None,mean_resid_kurt=round(float(np.mean(rk)),1) if rk else None,mean_annvol=round(float(np.mean([x['ann_vol'] for x in rows])),1))
out['n_types_predicted']=len(out['by_type']); out['n_assets_predicted']=len(out['per_asset'])
json.dump(out,open(os.path.join(P,"korea_deep.json"),"w"),indent=2,default=str)
lg("TYPES PREDICTED: %d, assets: %d"%(out['n_types_predicted'],out['n_assets_predicted'])); lg(json.dumps(out['by_type'],indent=2)); lg("DONE %.0fs"%(time.time()-t0))
