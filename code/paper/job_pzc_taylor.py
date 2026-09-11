# job_pzc_taylor.py -- Dynamic-ES benchmarks the referee named: Patton-Ziegel-Chen (2019) one-factor
# score-driven GAS-FZ AND Taylor (2019) ES-CAViaR (SAV VaR + multiplicative ES). Both estimated per
# name by FZ0 minimization (the strictly consistent joint (VaR,ES) loss, the PZC estimation route),
# multi-start to remove the earlier optimizer instability. Same shared forecast panel, same rows,
# same fz0() and engine construction as job_fz_fullpanel.py, so every DM is apples-to-apples.
# FZ0 loss with v,e<0:  L = -(1/(alpha*e))*1{r<=v}*(v-r) + v/e + log(-e) - 1   (lower = better).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats, optimize
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
ALPHAS=[0.01,0.025]
def conf_ostat(sc,tau):
    n=len(sc); k=int(math.ceil((n+1)*tau)); k=min(max(k,1),n)
    return float(np.sort(np.asarray(sc,float))[k-1])
def fz0(r,v,e,a):
    v=np.minimum(v,-1e-8); e=np.minimum(e,v)   # enforce e<=v<0
    return -(1.0/(a*e))*(r<=v)*(v-r)+v/e+np.log(-e)-1.0
def t_es(a,nu):  # ES of standardized Student-t (unit variance after /tsc applied by caller)
    q=stats.t.ppf(a,nu)
    return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
TRz=[]; CALz=[]; rows=[]; gasrows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e0=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e0[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    ztr=z[:cp]
    for a in ALPHAS:
        df[f'fhs_v{a}']=mu+df['sig']*np.quantile(ztr,a)
        df[f'fhs_e{a}']=mu+df['sig']*float(np.mean(ztr[ztr<=np.quantile(ztr,a)]))
        df[f'g_v{a}']=mu+df['sig']*stats.t.ppf(a,nu)/tsc
        df[f'g_e{a}']=mu+df['sig']*t_es(a,nu)/tsc
    df['idx']=np.arange(n); df['mu']=mu
    dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<cp]; cal=dd[(dd['idx']>=cp)&(dd['idx']<sp)]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(cal)<60: continue
    TRz.append(trn[ZX+['z']]); CALz.append(cal[ZX+['z']])
    keep=['y','sig','date','mu','mk63']+ZX+[c for c in df.columns if c.startswith(('fhs_','g_'))]
    t2=tst[keep].copy(); t2['permno']=pn; rows.append(t2)
    gasrows.append((pn,y,dts,sp))
lg("panels %d %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz); CALzc=pd.concat(CALz)
ZQ={}; ZQcal={}
for t in ALPHAS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=m.predict(TE[ZX].values); ZQcal[t]=m.predict(CALzc[ZX].values)
SUBN=20; ZQSUB={a:{} for a in ALPHAS}
for a in ALPHAS:
    for j in range(SUBN):
        u=a*(j+0.5)/SUBN
        mz=HistGradientBoostingRegressor(loss='quantile',quantile=u,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
        ZQSUB[a][j]=mz.predict(TE[ZX].values)
def coherent_star(a):
    cols=[np.minimum(ZQSUB[a][j], evt_q(a*(j+0.5)/SUBN)) for j in range(SUBN)]
    return np.sort(np.stack(cols,axis=1),axis=1)
ztr=TRzc['z'].values; u=np.quantile(ztr,0.025); exc=u-ztr[ztr<u]
xi,loc,beta=stats.genpareto.fit(exc,floc=0.0)
def evt_q(tau,p0=0.025):
    return u-(beta/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u-beta*math.log(p0/tau)
def evt_es(tau):
    q=evt_q(tau); return q-(beta+xi*(u-q))/(1.0-xi)
s975=CALzc['z'].values-ZQcal[0.025]; CONF975=conf_ostat(s975,0.025)
lg(f"GPD u={u:.3f} xi={xi:.3f} beta={beta:.3f}; conf975 {CONF975:+.4f}")
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values
ENG={}
star01=coherent_star(0.01); star025=coherent_star(0.025)
zq01=np.minimum(ZQ[0.01],evt_q(0.01)); zq025=np.minimum(ZQ[0.025],evt_q(0.025))
zq01=np.maximum(zq01,star01[:,-1]); zq025=np.maximum(zq025,star025[:,-1])
es01=star01.mean(axis=1); es025=star025.mean(axis=1)
ENG[0.01]=(MU+SIG*zq01, MU+SIG*np.minimum(es01,zq01-1e-6))
ENG[0.025]=(MU+SIG*zq025, MU+SIG*np.minimum(es025,zq025-1e-6))
# ---------------- PZC (2019) one-factor score-driven GAS, FZ0-estimated, multi-start ----------------
def gas_filter(y,a,b,om_,be_,ga_,k0,alpha):
    n=len(y); k=np.empty(n); k[0]=k0; v=np.empty(n); e=np.empty(n)
    for i in range(n):
        ex=math.exp(min(k[i],6.0)); v[i]=a*ex; e[i]=b*ex
        if i+1<n:
            hit=1.0 if y[i]<=v[i] else 0.0
            H=(1.0/e[i])*((1.0/alpha)*hit*y[i]-e[i])
            k[i+1]=om_+be_*k[i]+ga_*H
    return v,e
GVE={a:(np.full(len(Y),np.nan),np.full(len(Y),np.nan)) for a in ALPHAS}
gfail=0
for (pn,y,dts,sp) in gasrows:
    tr=y[max(0,sp-1200):sp]
    for a in ALPHAS:
        qa=np.quantile(tr,a); ea=float(np.mean(tr[tr<=qa])) if (tr<=qa).any() else qa*1.2
        eb=min(ea,qa*1.05)
        def obj(th):
            om_,be_,ga_=th
            if not (0.0<=be_<=0.999): return 1e6
            v,e=gas_filter(tr,qa,eb,om_,be_,ga_,0.0,a)
            L=fz0(tr,v,e,a); return float(np.mean(L)) if np.isfinite(L).all() else 1e6
        best=None
        for x0 in ([0.0,0.95,0.02],[0.0,0.90,0.05],[0.0,0.80,0.10]):
            try:
                res=optimize.minimize(obj,x0=x0,method='Nelder-Mead',options={'maxiter':120,'xatol':1e-3,'fatol':1e-4})
                if np.isfinite(res.fun) and (best is None or res.fun<best.fun): best=res
            except Exception: pass
        if best is None: gfail+=1; continue
        om_,be_,ga_=best.x
        v,e=gas_filter(y,qa,eb,om_,be_,ga_,0.0,a)
        msk=TE['permno'].values==pn; nsel=int(msk.sum())
        GVE[a][0][msk]=v[-nsel:]; GVE[a][1][msk]=e[-nsel:]
lg("GAS fitted (%d fails) %.0fs"%(gfail,time.time()-t0))
# ---------------- Taylor (2019) ES-CAViaR: SAV VaR + multiplicative ES, FZ0-estimated, multi-start ----
def taylor_filter(y,b1,b2,b3,delta,v0):
    n=len(y); v=np.empty(n); e=np.empty(n); v[0]=v0
    mult=1.0+math.exp(min(delta,4.0))
    for i in range(n):
        if i>0: v[i]=b1+b2*v[i-1]+b3*abs(y[i-1])
        e[i]=v[i]*mult
    return v,e
TVE={a:(np.full(len(Y),np.nan),np.full(len(Y),np.nan)) for a in ALPHAS}
tfail=0
for (pn,y,dts,sp) in gasrows:
    tr=y[max(0,sp-1200):sp]
    for a in ALPHAS:
        qa=float(np.quantile(tr,a)); ea=float(np.mean(tr[tr<=qa])) if (tr<=qa).any() else qa*1.2
        mult0=max(ea/qa,1.02) if qa<0 else 1.2; d0=math.log(max(mult0-1.0,1e-3))
        def objt(th):
            b1,b2,b3,dl=th
            if not (0.0<=b2<=0.999): return 1e6
            v,e=taylor_filter(tr,b1,b2,b3,dl,qa)
            if not np.isfinite(v).all(): return 1e6
            L=fz0(tr,v,e,a); return float(np.mean(L)) if np.isfinite(L).all() else 1e6
        best=None
        for x0 in ([qa*0.1,0.9,-0.05,d0],[qa*0.05,0.8,-0.10,d0],[qa*0.2,0.85,-0.02,d0]):
            try:
                res=optimize.minimize(objt,x0=x0,method='Nelder-Mead',options={'maxiter':200,'xatol':1e-3,'fatol':1e-4})
                if np.isfinite(res.fun) and (best is None or res.fun<best.fun): best=res
            except Exception: pass
        if best is None: tfail+=1; continue
        b1,b2,b3,dl=best.x
        v,e=taylor_filter(y,b1,b2,b3,dl,qa)
        msk=TE['permno'].values==pn; nsel=int(msk.sum())
        TVE[a][0][msk]=v[-nsel:]; TVE[a][1][msk]=e[-nsel:]
lg("Taylor fitted (%d fails) %.0fs"%(tfail,time.time()-t0))
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return float(x.mean()/math.sqrt(max(v/n,1e-16)))
dates=TE['date'].values
def dm_vs_engine(Lm,Le):
    dd=pd.DataFrame({'d':Lm-Le,'date':dates}).groupby('date')['d'].mean()
    t=nw_t(dd.values)
    return {'mean_diff':round(float(np.nanmean(Lm-Le)),5),'DM_t':None if t is None else round(t,2),
            'p_one_sided':None if t is None else round(float(1-stats.norm.cdf(t)),4)}
OUT={'note':'Dynamic-ES benchmarks (PZC-2019 GAS + Taylor-2019 ES-CAViaR), FZ0-estimated per name with '
     'multi-start, scored on the SAME full-panel forecast rows as the engine. DM_t>0 means the row model '
     'has HIGHER (worse) FZ0 loss than the engine, date-clustered NW(10), one-sided p.',
     'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),
     'gpd':{'u':round(float(u),4),'xi':round(float(xi),4),'beta':round(float(beta),4)},'conf975':round(CONF975,4),
     'gas_fails':int(gfail),'taylor_fails':int(tfail),'per_alpha':{}}
for a in ALPHAS:
    ve,ee=ENG[a]; Le=fz0(Y,ve,ee,a)
    rows_out={'engine_meanFZ0':round(float(np.mean(Le)),5),'engine_breach':round(float(np.mean(Y<=ve)),4)}
    for nm,(vm,em) in [('garch_t',(TE[f'g_v{a}'].values,TE[f'g_e{a}'].values)),
                       ('fhs',(TE[f'fhs_v{a}'].values,TE[f'fhs_e{a}'].values)),
                       ('gas_pzc',GVE[a]),('taylor_al',TVE[a])]:
        Lm=fz0(Y,vm,em,a); ok=np.isfinite(Lm)&np.isfinite(Le)
        r=dm_vs_engine(np.where(ok,Lm,np.nan),np.where(ok,Le,np.nan))
        r['meanFZ0']=round(float(np.nanmean(Lm)),5); r['breach']=round(float(np.nanmean((Y<=vm)[ok])),4)
        r['n_scored']=int(ok.sum())
        rows_out[nm]=r
    OUT['per_alpha'][str(a)]=rows_out
    lg(f"alpha={a}: {json.dumps(rows_out)}")
json.dump(OUT,open(os.path.join(P,"pzc_taylor_acc_results.json"),"w"),indent=2)
lg("PZCTAYLOR2DONE %.0fs"%(time.time()-t0))
