# job_horizon_purged.py -- the OA horizon-ratio figure, WITH THE h-1 BOUNDARY PURGE.
# The direct-learning horizon study (nonparam/GARCH pinball ratio at h=1,5,10,20)
# shares the boundary defect found in adversarial review: h-day cumulative training
# labels at indices sp-(h-1)..sp-1 contained test-era returns. This rerun requires
# the whole label window to precede the split (idx < sp-(h-1)) and regenerates the
# four ratios so Online Appendix Figure OA.3 can be updated. Design panel, mirrors
# the original horizon.py methodology (direct h-day quantile GBM vs sqrt-h GARCH-t).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
FEAT=['prv5','prv21','rv63','logsig','absz5']
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1800].index.tolist()[:150]
def run_h(h):
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
        ycum=pd.Series(y).rolling(h).sum().shift(-(h-1)).values if h>1 else y.copy()
        df=pd.DataFrame({'yc':ycum,'sig':sig,'idx':np.arange(n)})
        df['prv5']=pd.Series(y).rolling(5,min_periods=3).std().shift(1); df['prv21']=pd.Series(y).rolling(21,min_periods=8).std().shift(1)
        df['rv63']=pd.Series(y).rolling(63,min_periods=20).std().shift(1); df['logsig']=np.log(np.maximum(sig,1e-6))
        df['absz5']=pd.Series(np.abs(z)).rolling(5,min_periods=3).mean().shift(1)
        df['mu']=mu; df['nu']=nu; df['tsc']=tsc
        dd=df.dropna(subset=FEAT+['yc'])
        trn=dd[dd['idx']<sp-(h-1)]        # PURGE
        tst=dd[dd['idx']>=sp]
        if len(tst)<60: continue
        TRr.append(trn[FEAT+['yc']]); TEr.append(tst)
    TR=pd.concat(TRr); TE=pd.concat(TEr).reset_index(drop=True)
    GQ={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR[FEAT].values,TR['yc'].values).predict(TE[FEAT].values) for t in TAUS}
    Y=TE['yc'].values; SIGh=TE['sig'].values*math.sqrt(h); MUh=TE['mu'].values*h; NU=TE['nu'].values; TSC=TE['tsc'].values
    pl_g=np.mean([pin(Y,MUh+SIGh*stats.t.ppf(t,NU)/TSC,t) for t in TAUS],axis=0)
    pl_b=np.mean([pin(Y,GQ[t],t) for t in TAUS],axis=0)
    r={'n':int(len(Y)),'garch':round(float(pl_g.mean()),4),'gbm':round(float(pl_b.mean()),4),
       'ratio':round(float(pl_b.mean())/float(pl_g.mean()),4)}
    lg("h=%d: %s %.0fs"%(h,json.dumps(r),time.time()-t0))
    return r
OUT={'note':'PURGED horizon-ratio rerun (idx < sp-(h-1)): direct h-day quantile GBM vs sqrt-h GARCH-t, design panel, for OA Figure 3. ratio<1 = nonparam better.',
     'by_horizon':{('h%d'%h):run_h(h) for h in (1,5,10,20)}}
json.dump(OUT,open(os.path.join(P,"horizon_purged_results.json"),"w"),indent=2)
lg("HORIZONPURGEDDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1))
