# FRTB 10-DAY HORIZON + STRESSED-WINDOW study (ai2) — non-Bloomberg. FRTB capital uses a 10-day liquidity-horizon ES and a
# STRESSED calibration period. Test the residual-hybrid vs GARCH-t and FHS at h=1 AND h=10 (overlapping cumulative returns),
# split by regime: CALM (2014-2019) vs STRESS (2020 COVID + 2022 bear). Metric: avg pinball + ES97.5, per horizon per regime.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]; TAILT=[0.005,0.01,0.025]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1800].index.tolist()[:150]
FEAT=['prv5','prv21','rv63','logsig','absz5']
def build(h):
    TRr=[]; TEr=[]
    for pn in names:
        g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
        if n<1800: continue
        sp=int(n*0.6)
        try:
            r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
            p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
        except Exception: continue
        e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
        for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
        sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
        ycum=pd.Series(y).rolling(h).sum().shift(-(h-1)).values if h>1 else y.copy()   # cumulative h-day forward return
        df=pd.DataFrame({'yc':ycum,'sig':sig,'z':z,'date':dts,'idx':np.arange(n)})
        df['prv5']=pd.Series(y).rolling(5,min_periods=3).std().shift(1); df['prv21']=pd.Series(y).rolling(21,min_periods=8).std().shift(1)
        df['rv63']=pd.Series(y).rolling(63,min_periods=20).std().shift(1); df['logsig']=np.log(np.maximum(sig,1e-6))
        df['absz5']=pd.Series(np.abs(z)).rolling(5,min_periods=3).mean().shift(1)
        df['mu']=mu; df['nu']=nu; df['tsc']=tsc
        fhsq={t:np.quantile(z[:sp],t) for t in TAUS}
        for t in TAUS: df['fhs_%g'%t]=fhsq[t]
        dd=df.dropna(subset=FEAT+['yc']); trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
        if len(tst)<60: continue
        TRr.append(trn[FEAT+['yc']]); t2=tst.copy(); t2['permno']=pn; TEr.append(t2)
    TR=pd.concat(TRr); TE=pd.concat(TEr).reset_index(drop=True)
    GQ={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR[FEAT].values,TR['yc'].values).predict(TE[FEAT].values) for t in TAUS}
    Y=TE['yc'].values; SIG=TE['sig'].values*math.sqrt(h); MU=TE['mu'].values*h; NU=TE['nu'].values; TSC=TE['tsc'].values
    yr=pd.to_datetime(TE['date']).dt.year.values
    Q={'garch_scale':{t:MU+SIG*stats.t.ppf(t,NU)/TSC for t in TAUS},
       'fhs':{t:MU+SIG*TE['fhs_%g'%t].values for t in TAUS},
       'hybrid_GBM':{t:GQ[t] for t in TAUS}}
    def block(mask):
        o={}
        for m in Q:
            pl=np.zeros(mask.sum())
            for t in TAUS: pl+=pin(Y[mask],Q[m][t][mask],t)
            pl/=len(TAUS); esp=np.mean([Q[m][t][mask] for t in TAILT],axis=0); b975=(Y[mask]<Q[m][0.025][mask])
            o[m]=dict(pinball=round(float(pl.mean()),4),ES975_pred=round(float(esp.mean()),3),
                      ES975_real=round(float(Y[mask][b975].mean()),3) if b975.sum() else None,breach975=round(float(b975.mean()),4),n=int(mask.sum()))
        return o
    calm=np.isin(yr,[2014,2015,2016,2017,2018,2019]); stress=np.isin(yr,[2020,2022])
    return {'all':block(np.ones(len(Y),bool)),'calm_2014_2019':block(calm),'stress_2020_2022':block(stress)}
out={'note':'FRTB 10-day horizon + stressed-window (non-Bloomberg, CRSP 2014-2024). hybrid_GBM vs garch_scale (sqrt-h) vs FHS, '
            'h=1 and h=10 overlapping cumulative returns. Split CALM (2014-19) vs STRESS (2020 COVID + 2022 bear). ES97.5+pinball. '
            'Shows whether the nonparam edge holds/grows at the FRTB 10-day horizon and concentrates in the stressed period.',
     'h1':build(1),'h10':build(10)}
json.dump(out,open(os.path.join(D,"frtb_stress_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
