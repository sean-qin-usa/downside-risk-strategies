# job_stress_es.py -- TRUE ES for the ten-day sections (both eras).
# Adversarial review: the h=10 stress battery and the 2000-2013 horizon rerun computed
# the nonparametric model's ES as a 3- or 5-node tail-quantile average while GARCH's ES
# was (in the holdout job) already the closed form -- an inconsistent and non-integral
# proxy. This job recomputes BOTH eras with uniform, genuine ES97.5:
#   garch (sqrt-h scaled):  closed-form standardized-t ES
#   fhs (per-name):         exact empirical tail mean of train z, scaled by sigma*sqrt(h)
#   hybrid/direct GBM:      20-node midpoint integral over sub-alpha quantile fits
# Section A: design era 2014-2024 (150 names >=1800 obs; h=1 and h=10; all/calm/stress).
# Section B: holdout era 2000-2013 (200 names; h=10) -- the era-reversal check.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
A=0.025
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
SUB=[A*(i+0.5)/20.0 for i in range(20)]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def t_es(a,nu):
    q=stats.t.ppf(a,nu)
    return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)

def run_panel(csv,minobs,ncap,h,calmyears=None,stressyears=None):
    rr=pd.read_csv(csv,dtype={'permno':'int32'})
    rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
    rr=rr.dropna(subset=['ret'])
    cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=minobs].index.tolist()[:ncap]
    FEAT=['prv5','prv21','rv63','logsig','absz5']
    TRr=[]; TEr=[]
    for pn in names:
        g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
        if n<minobs: continue
        sp=int(n*0.6)
        try:
            r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
            p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
        except Exception: continue
        e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
        for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
        sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
        ycum=pd.Series(y).rolling(h).sum().shift(-(h-1)).values if h>1 else y.copy()
        df=pd.DataFrame({'yc':ycum,'sig':sig,'date':dts,'idx':np.arange(n)})
        df['prv5']=pd.Series(y).rolling(5,min_periods=3).std().shift(1); df['prv21']=pd.Series(y).rolling(21,min_periods=8).std().shift(1)
        df['rv63']=pd.Series(y).rolling(63,min_periods=20).std().shift(1); df['logsig']=np.log(np.maximum(sig,1e-6))
        df['absz5']=pd.Series(np.abs(z)).rolling(5,min_periods=3).mean().shift(1)
        df['mu']=mu; df['nu']=nu; df['tsc']=tsc
        ztr=z[:sp]
        for t in TAUS: df['fhs_%g'%t]=float(np.quantile(ztr,t))
        qa=np.quantile(ztr,A); df['fhsES']=float(np.mean(ztr[ztr<=qa]))
        dd=df.dropna(subset=FEAT+['yc']); trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
        if len(tst)<60: continue
        TRr.append(trn[FEAT+['yc']]); t2=tst.copy(); t2['permno']=pn; TEr.append(t2)
    TR=pd.concat(TRr); TE=pd.concat(TEr).reset_index(drop=True)
    lg("  panel h=%d: %d names, %d test rows %.0fs"%(h,TE['permno'].nunique(),len(TE),time.time()-t0))
    GQ={}
    for t in TAUS:
        GQ[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR[FEAT].values,TR['yc'].values).predict(TE[FEAT].values)
    GES=[]
    for u in SUB:
        GES.append(HistGradientBoostingRegressor(loss='quantile',quantile=u,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR[FEAT].values,TR['yc'].values).predict(TE[FEAT].values))
    ES_gbm=np.mean(GES,axis=0)
    Y=TE['yc'].values; SIGh=TE['sig'].values*math.sqrt(h); MUh=TE['mu'].values*h; NU=TE['nu'].values; TSC=TE['tsc'].values
    yr=pd.to_datetime(TE['date']).dt.year.values
    Q={'garch_scale':{t:MUh+SIGh*stats.t.ppf(t,NU)/TSC for t in TAUS},
       'fhs':{t:MUh+SIGh*TE['fhs_%g'%t].values for t in TAUS},
       'hybrid_GBM':{t:GQ[t] for t in TAUS}}
    ES={'garch_scale':MUh+SIGh*np.array([t_es(A,nu_)/ts_ for nu_,ts_ in zip(NU,TSC)]),
        'fhs':MUh+SIGh*TE['fhsES'].values,
        'hybrid_GBM':ES_gbm}
    def block(mask):
        o={}
        for m in Q:
            pl=np.zeros(int(mask.sum()))
            for t in TAUS: pl+=pin(Y[mask],Q[m][t][mask],t)
            pl/=len(TAUS); b975=(Y[mask]<Q[m][A][mask])
            o[m]=dict(pinball=round(float(pl.mean()),4),
                      ES975_pred_true=round(float(ES[m][mask].mean()),3),
                      ES975_real_ownVaR=round(float(Y[mask][b975].mean()),3) if b975.sum() else None,
                      breach975=round(float(b975.mean()),4),n=int(mask.sum()))
        return o
    out={'all':block(np.ones(len(Y),bool))}
    if calmyears is not None:
        out['calm']=block(np.isin(yr,calmyears)); out['stress']=block(np.isin(yr,stressyears))
    return out

OUT={'note':'TRUE ES97.5 for the ten-day sections, both eras, uniform methods: closed-form t ES for sqrt-h GARCH, exact empirical train-z tail mean for per-name FHS, 20-node midpoint sub-alpha GBM integral for the direct/hybrid model. Replaces the 3-node (design) and 5-node (holdout) tail-average proxies. Overlapping h-day targets as before.',
     'design_2014_2024':{}}
lg("design era h=1...")
OUT['design_2014_2024']['h1']=run_panel(os.path.join(P,"crsp_panel_returns.csv"),1800,150,1,
                                        calmyears=[2014,2015,2016,2017,2018,2019],stressyears=[2020,2022])
lg("design era h=10...")
OUT['design_2014_2024']['h10']=run_panel(os.path.join(P,"crsp_panel_returns.csv"),1800,150,10,
                                         calmyears=[2014,2015,2016,2017,2018,2019],stressyears=[2020,2022])
lg("holdout era h=10...")
OUT['holdout_2000_2013_h10']=run_panel(os.path.join(P,"holdout_panel_2000_2013.csv"),1500,200,10)
json.dump(OUT,open(os.path.join(P,"stress_es_results.json"),"w"),indent=2)
lg("STRESSESDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1)[:2600])
