# CO-CRASH / JOINT-TAIL PROTOTYPE (ai2): can a nonparametric portfolio-quantile model beat multivariate GARCH on portfolio tail risk,
# especially in crises when correlations spike? Direct GBM portfolio-quantiles vs CCC-GARCH (constant-corr) and DCC-lite (dynamic corr).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'}); rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
ch=pd.read_csv(os.path.join(D,"crsp_panel_chars.csv"))
lc=ch[ch['cohort']=='largecap']['permno'].tolist() if 'cohort' in ch else ch['permno'].tolist()
W=rr[rr.permno.isin(lc)].pivot_table(index='date',columns='permno',values='ret')
W=W.dropna(axis=1,thresh=int(0.9*len(W))).dropna()          # aligned panel of names with near-full history
if W.shape[1]>25: W=W.iloc[:,:25]
A=W.values; dates=W.index; N=A.shape[1]; port=A.mean(1)      # equal-weight portfolio daily return (%)
lg("portfolio: %d days x %d names %.0fs"%(len(port),N,time.time()-t0))
n=len(port); sp=int(n*0.6)
# ---- per-asset GARCH-t vol paths (for CCC) ----
from arch import arch_model
vol=np.zeros((n,N)); nus=[]
for j in range(N):
    y=A[:,j]
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nus.append(float(p.get('nu',8)))
    except Exception:
        om,al,be,mu=0.1,0.05,0.9,0.0; nus.append(8)
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    vol[:,j]=np.sqrt(s2)
nu_p=float(np.mean(nus))
# standardized residuals (train) for correlation
Z=A/np.maximum(vol,1e-6)
R_ccc=np.corrcoef(Z[:sp].T)                                  # constant correlation (train)
w=np.ones(N)/N
def port_sigma(Vt,Rt): return math.sqrt(max(w@(np.outer(Vt,Vt)*Rt)@w,1e-10))
# DCC-lite: EWMA correlation of standardized resids
Qbar=R_ccc.copy(); lam=0.97; Qt=Qbar.copy()
dcc_sig=np.zeros(n)
for i in range(n):
    if i>0:
        z=Z[i-1]; Qt=(1-lam)*np.outer(z,z)+lam*Qt
        dd=np.sqrt(np.clip(np.diag(Qt),1e-8,None)); Rt=Qt/np.outer(dd,dd)
    else: Rt=R_ccc
    dcc_sig[i]=port_sigma(vol[i],Rt)
ccc_sig=np.array([port_sigma(vol[i],R_ccc) for i in range(n)])
# ---- direct nonparametric portfolio-quantile (GBM) ----
pf=pd.DataFrame({'y':port},index=dates)
pf['lag1']=pf['y'].shift(1); pf['abs1']=pf['y'].abs().shift(1)
pf['prv5']=pf['y'].rolling(5,min_periods=3).std().shift(1); pf['prv21']=pf['y'].rolling(21,min_periods=8).std().shift(1)
disp=pd.Series(A.std(1),index=dates); pf['disp21']=disp.rolling(21,min_periods=8).mean().shift(1)   # cross-sectional dispersion
avgabs=pd.Series(np.abs(A).mean(1),index=dates); pf['avgabs5']=avgabs.rolling(5,min_periods=3).mean().shift(1)
fracdn=pd.Series((A<0).mean(1),index=dates); pf['fracdn1']=fracdn.shift(1)                            # breadth (comovement proxy)
comov=pd.Series((np.abs(A).mean(1))/(A.std(1)+1e-6),index=dates); pf['comov21']=comov.rolling(21,min_periods=8).mean().shift(1)  # |mean|/dispersion ~ correlation proxy
PXC=['lag1','abs1','prv5','prv21','disp21','avgabs5','fracdn1','comov21']
pf=pf.dropna(); yv=pf['y'].values; nn=len(pf); s2=int(nn*0.6)
gbm={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=200,max_depth=3,learning_rate=0.06).fit(pf[PXC].values[:s2],yv[:s2]) for t in TAUS}
GBMq={t:gbm[t].predict(pf[PXC].values[s2:]) for t in TAUS}
# align test index between the two representations (use the pf test window)
test_dates=pf.index[s2:]; di={d:i for i,d in enumerate(dates)}
tsc=math.sqrt(nu_p/(nu_p-2)) if nu_p>2 else 1.0
def metrics(qfun):
    plss=0.0; b025=0; b01=0; es_pred=[]; es_real=[]; cnt=0
    for jj,dt_ in enumerate(test_dates):
        i=di[dt_]; yi=port[i]
        qs={t:qfun(t,jj,i) for t in TAUS}
        plss+=np.mean([pin(yi,qs[t],t) for t in TAUS]); cnt+=1
        b025+=(yi<qs[0.025]); b01+=(yi<qs[0.01])
        es_pred.append(np.mean([qs[t] for t in TAUS if t<=0.025]));
        if yi<qs[0.025]: es_real.append(yi)
    return dict(pinball=round(plss/cnt,4),breach_2p5=round(b025/cnt,4),breach_1p=round(b01/cnt,4),
                ES975_pred=round(float(np.mean(es_pred)),3),ES975_real=round(float(np.mean(es_real)),3) if es_real else None,n=cnt)
q_ccc=lambda t,jj,i: 0.0+ccc_sig[i]*stats.t.ppf(t,nu_p)/tsc
q_dcc=lambda t,jj,i: 0.0+dcc_sig[i]*stats.t.ppf(t,nu_p)/tsc
q_gbm=lambda t,jj,i: GBMq[t][jj]
out={'note':'Co-crash/joint-tail prototype: equal-weight CRSP largecap portfolio. Direct nonparametric portfolio-quantile (GBM) vs CCC-GARCH (constant-correlation multivariate GARCH) vs DCC-lite (EWMA dynamic correlation). Metrics: portfolio pinball(11 taus), 2.5%/1% VaR breach (targets .025/.01), 97.5% ES pred vs realized. Hypothesis: static-corr CCC underestimates crisis tail (corr spikes); DCC & nonparametric capture it.','n_names':N,'n_test':len(test_dates),'nu_p':round(nu_p,1),
 'models':{'CCC_GARCH':metrics(q_ccc),'DCC_lite':metrics(q_dcc),'GBM_direct':metrics(q_gbm)}}
# crisis slice: worst-decile portfolio-vol test days
pv=ccc_sig[[di[d] for d in test_dates]]; thr=np.quantile(pv,0.9); crisis_mask=pv>=thr
def metrics_mask(qfun,mask):
    plss=0.0; b025=0; cnt=0; es_r=[]
    for jj,dt_ in enumerate(test_dates):
        if not mask[jj]: continue
        i=di[dt_]; yi=port[i]; qs={t:qfun(t,jj,i) for t in TAUS}
        plss+=np.mean([pin(yi,qs[t],t) for t in TAUS]); cnt+=1; b025+=(yi<qs[0.025])
        if yi<qs[0.025]: es_r.append(yi)
    return dict(pinball=round(plss/cnt,4),breach_2p5=round(b025/cnt,4),n=cnt) if cnt else None
out['crisis_high_vol_decile']={'CCC_GARCH':metrics_mask(q_ccc,crisis_mask),'DCC_lite':metrics_mask(q_dcc,crisis_mask),'GBM_direct':metrics_mask(q_gbm,crisis_mask)}
json.dump(out,open(os.path.join(D,"joint_tail_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
