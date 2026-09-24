# job_arcd_bench.py -- a state-adaptive PARAMETRIC benchmark: does a fixed-family shape that moves with
# the state capture the frontier? GARCH(1,1)-t scale as in the paper; the innovation law is Student-t with
# a time-varying degrees-of-freedom nu_t = 2.1 + exp(h_t), h_t = c + a|z_{t-1}| + b h_{t-1} (an
# autoregressive conditional density in the spirit of Hansen 1994), fitted by maximum likelihood on each
# name's training residuals with the scale held fixed. Forecast quantile mu + sigma_t t_q(nu_t)/tsc(nu_t).
# Scored on the Table 1 rows against GARCH-t (constant nu) and against the paper's pooled residual learner,
# by decile of mk63 and of the composite score; 11 levels, per-date NW(10) DM.
# PREDICTIONS (2026-09-24, before the run): the adaptive-nu benchmark improves on GARCH-t in the top mk63
# decile by less than one third of the learner's +2.98% (i.e. under +1.0%), and the learner keeps an edge
# over it above +2.0% (DM > 6) there, because most of the top-decile edge is post-shock scale
# overstatement that a shape parameter cannot repair; overall the two parametric models are within 0.2%.
# If the adaptive-nu model instead closes more than half the gap, the frontier is largely a shape effect a
# richer parametric family captures, and the decomposition text must be revised.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
from scipy.optimize import minimize
from scipy.signal import lfilter
P=os.environ.get("GBC_PROJ",os.environ.get("GBC_PROJECT_DIR",r"C:\Users\OWNER\Claude\Projects\GBC Project")); t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
def pin(y,q,t): dd=y-q; return np.where(dd>=0,t*dd,(t-1)*dd)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    dm=x-x.mean(); v=np.mean(dm*dm)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(dm[k:]*dm[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
TRz=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        pp=r1.params; om,al,be,mu=float(pp['omega']),float(pp['alpha[1]']),float(pp['beta[1]']),float(pp.get('mu',0)); nu=float(pp.get('nu',8))
    except Exception: continue
    e0=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e0[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); zz=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    # state-adaptive shape: nu_t = 2.1 + exp(h_t), h_t = c + a*|z_{t-1}| + b*h_{t-1}, fitted by ML on the
    # training residuals with the GARCH scale held fixed (two-step, as for the shape learner)
    absz_lag=np.concatenate([[np.abs(zz[:sp]).mean()],np.abs(zz[:-1])])
    def hpath(th):
        c,a,b=th; b=max(min(b,0.999),-0.999)
        return lfilter([1.0],[1.0,-b],c+a*absz_lag)
    def nll(th,upto):
        h=hpath(th)[:upto]; nu=2.1+np.exp(np.clip(h,-8,8)); tsc_=np.sqrt(nu/(nu-2))
        return -np.sum(np.log(tsc_)+stats.t.logpdf(zz[:upto]*tsc_,nu))
    best=None
    for th0 in [(math.log(max(nu-2.1,0.5))*0.1,0.0,0.9),(math.log(max(nu-2.1,0.5)),0.0,0.0),(0.2,-0.3,0.85)]:
        try:
            r=minimize(nll,th0,args=(sp,),method='Nelder-Mead',options={'maxiter':600,'xatol':1e-4,'fatol':1e-3})
            if best is None or r.fun<best.fun: best=r
        except Exception: pass
    nut=2.1+np.exp(np.clip(hpath(best.x),-8,8)) if best is not None else np.full(n,nu)
    ll_const=-nll((math.log(max(nu-2.1,0.5)),0.0,0.0),sp); ll_arcd=-best.fun if best is not None else ll_const
    df=pd.DataFrame({'y':y,'sig':sig,'z':zz,'date':dts,'nut':nut}); df['ll_gain']=ll_arcd-ll_const; df['arcd_a']=best.x[1] if best is not None else 0.0; df['arcd_b']=best.x[2] if best is not None else 0.0
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['skew63']=df['z'].rolling(63,min_periods=30).skew().abs().shift(1)
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=ZX+['mk63','skew63','jump5'])
    trn=dd[dd['idx']<cp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TRz.append(trn[ZX+['z']]); t2=tst.copy(); t2['permno']=pn; rows.append(t2)
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz)
lg("panel %d names %d rows %.0fs"%(TE.permno.nunique(),len(TE),time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values; NUT=TE['nut'].values; TSCT=np.sqrt(NUT/(NUT-2))
ZQ={}
for t in TAUS:
    ZQ[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06,random_state=0).fit(TRzc[ZX].values,TRzc['z'].values).predict(TE[ZX].values)
lg("learner done %.0fs"%(time.time()-t0))
plE=np.zeros(len(Y)); plG=np.zeros(len(Y)); plA=np.zeros(len(Y))
for t in TAUS:
    plE+=pin(Y,MU+SIG*ZQ[t],t); plG+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t); plA+=pin(Y,MU+SIG*stats.t.ppf(t,NUT)/TSCT,t)
plE/=len(TAUS); plG/=len(TAUS); plA/=len(TAUS)
di,udates=pd.factorize(pd.to_datetime(TE['date'].values),sort=True); di=np.asarray(di)
def dec(x):
    r=np.full(len(x),-1); m=np.isfinite(x)
    r[m]=pd.qcut(pd.Series(x[m]),10,labels=False,duplicates='drop').values+1
    return r
def pct(x):
    r=np.full(len(x),np.nan); m=np.isfinite(x); r[m]=pd.Series(x[m]).rank(pct=True).values
    return r
mk=TE['mk63'].values; sk=TE['skew63'].values; jp=TE['jump5'].values
ok=np.isfinite(mk)&np.isfinite(sk)&np.isfinite(jp)
rk_mk=dec(mk); comp_pct=np.where(ok, np.fmax.reduce([pct(mk),pct(sk),pct(jp)]), np.nan); cdec=dec(comp_pct)
def edge_of(d,base,mask):
    if mask.sum()<30: return None
    g=pd.DataFrame({'d':d[mask],'dt':di[mask]}).groupby('dt')['d'].mean()
    return {'edge_pct':round(100*float(d[mask].mean())/float(base[mask].mean()),3),'DM':nw_t(g.values),'n':int(mask.sum())}
def block(d,base):
    return {'top_mk63':edge_of(d,base,rk_mk==10),'top_composite':edge_of(d,base,cdec==10),'deciles_1to9_mk63':edge_of(d,base,(rk_mk>=1)&(rk_mk<=9)),
            'mk63_decile_profile':{int(k):edge_of(d,base,rk_mk==k) for k in range(1,11)},'overall':edge_of(d,base,np.ones(len(Y),bool))}
pername=TE.groupby('permno').agg(ll_gain=('ll_gain','first'),a=('arcd_a','first'),b=('arcd_b','first'),nut_mean=('nut','mean'),nut_p10=('nut',lambda x: float(np.quantile(x,0.1))),nut_p90=('nut',lambda x: float(np.quantile(x,0.9))))
OUT={'note':'State-adaptive parametric benchmark (time-varying-nu GARCH-t, see header) on the Table 1 rows. edge blocks: (first model pinball - second model pinball)/first, 11 levels, per-date NW(10) DM; positive = second model better.',
     'n_rows':int(len(Y)),'n_names':int(TE.permno.nunique()),
     'fit_summary':{'median_train_loglik_gain_vs_constant_nu':round(float(pername['ll_gain'].median()),2),'share_names_gain_gt_3':round(float((pername['ll_gain']>3).mean()),3),
                    'median_a':round(float(pername['a'].median()),3),'median_b':round(float(pername['b'].median()),3),
                    'nu_t_median_of_name_means':round(float(pername['nut_mean'].median()),2),'nu_t_median_p10':round(float(pername['nut_p10'].median()),2),'nu_t_median_p90':round(float(pername['nut_p90'].median()),2)},
     'adaptive_nu_over_garch_t':block(plG-plA,plG),
     'learner_over_garch_t':block(plG-plE,plG),
     'learner_over_adaptive_nu':block(plA-plE,plA)}
json.dump(OUT,open(os.path.join(P,"arcd_bench_results.json"),"w"),indent=2)
lg("ARCDDONE %.0fs"%(time.time()-t0)); lg(json.dumps({k:OUT[k] for k in ['fit_summary','adaptive_nu_over_garch_t','learner_over_adaptive_nu']},indent=1)[:3000])
