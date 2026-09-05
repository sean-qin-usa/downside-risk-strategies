# job_fz_fullpanel.py -- PRE-COMMITTED full-panel FZ0 joint (VaR,ES) re-scoring + GAS/PZC benchmark.
# Wave-9 canonical: engine VaR and ES both come from one monotonized min-envelope curve Q*;
# ES is the 20-node numerical integral of that same Q* (retires the GPD-closed-form ES).
# Conformal shift computed with the exact ceil((n+1)tau) order statistic used by
# Proposition 1, replacing interpolated np.quantile, so theorem and code state one rule.
# Two pre-committed items in one shared forecast panel so every comparison is same-rows:
#   (1) FZ0 (Fissler-Ziegler 0-homogeneous, as in Patton-Ziegel-Chen 2019) scoring of the engine
#       vs GARCH-t and FHS on the FULL design-era panel (the paper's earlier FZ run covered a
#       subset; the full-panel re-run was pre-committed in the text).
#   (2) A one-factor score-driven GAS-FZ model (PZC 2019 style) estimated per name by FZ0
#       minimization -- the "modern semiparametric dynamics" benchmark referees will ask for.
# FZ0 loss with v,e<0:  L = -(1/(alpha*e))*1{r<=v}*(v-r) + v/e + log(-e) - 1   (lower = better).
# Engine ES from the GPD tail: ES_tau = q_tau - (beta + xi*(u - q_tau))/(1 - xi), z-space,
# scaled by sigma; conformal location shift at 97.5 applied to BOTH v and e (location shift).
# Sign convention verified against the FZ family with G1=0, G2=-1/e (see console self-test).
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
    hit=(r<=v).astype(float)
    return -(1.0/(a*e))*hit*(v-r)+v/e+np.log(-e)-1.0
# self-test: for iid N(0,1), true (v,e) at alpha=.025 must score better than a too-wide pair
_r=np.random.default_rng(0).standard_normal(200000)
_vt,_et=stats.norm.ppf(0.025),-stats.norm.pdf(stats.norm.ppf(0.025))/0.025
lg("FZ0 self-test (true %.4f vs 1.5x-wide %.4f -- true must be lower): %.4f %.4f"%(
   _vt,1.5*_vt,fz0(_r,_vt,_et,0.025).mean(),fz0(_r,1.5*_vt,1.5*_et,0.025).mean()))
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
    lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
# sub-alpha grids for the coherent Q* ES integral (20-node midpoint on (0,alpha])
SUBN=20; ZQSUB={a:{} for a in ALPHAS}
for a in ALPHAS:
    for j in range(SUBN):
        u=a*(j+0.5)/SUBN
        mz=HistGradientBoostingRegressor(loss='quantile',quantile=u,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
        ZQSUB[a][j]=mz.predict(TE[ZX].values)
    lg("  sub-alpha grid a=%.3f %.0fs"%(a,time.time()-t0))
def coherent_star(a):
    # z*(u)=min(body,EVT) on the 20 sub-alpha nodes, then monotone rearrangement (sort asc)
    cols=[np.minimum(ZQSUB[a][j], evt_q(a*(j+0.5)/SUBN)) for j in range(SUBN)]
    return np.sort(np.stack(cols,axis=1),axis=1)   # rows x 20, ascending
ztr=TRzc['z'].values; u=np.quantile(ztr,0.025); exc=u-ztr[ztr<u]
xi,loc,beta=stats.genpareto.fit(exc,floc=0.0)
def evt_q(tau,p0=0.025):
    return u-(beta/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u-beta*math.log(p0/tau)
def evt_es(tau):
    q=evt_q(tau); return q-(beta+xi*(u-q))/(1.0-xi)
s975=CALzc['z'].values-ZQcal[0.025]; CONF975=conf_ostat(s975,0.025)   # exact ceil((n+1)tau) order statistic (Prop. 1)
lg(f"GPD u={u:.3f} xi={xi:.3f} beta={beta:.3f}; conf975 {CONF975:+.4f}; evt_es01={evt_es(0.01):.3f} evt_es025={evt_es(0.025):.3f}")
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values
ENG={}; ENGNC={}
# CANONICAL coherent construction: both VaR and ES from one monotonized min-envelope Q*.
star01=coherent_star(0.01); star025=coherent_star(0.025)
zq01=np.minimum(ZQ[0.01],evt_q(0.01)); zq025=np.minimum(ZQ[0.025],evt_q(0.025))
zq01=np.maximum(zq01,star01[:,-1]); zq025=np.maximum(zq025,star025[:,-1])   # VaR node = curve endpoint
es01=star01.mean(axis=1); es025=star025.mean(axis=1)                         # ES = numerical integral of Q*
ENG[0.01]=(MU+SIG*zq01, MU+SIG*np.minimum(es01,zq01-1e-6))
ENG[0.025]=(MU+SIG*(zq025+CONF975), MU+SIG*(np.minimum(es025,zq025-1e-6)+CONF975))
ENGNC[0.01]=ENG[0.01]
ENGNC[0.025]=(MU+SIG*zq025, MU+SIG*np.minimum(es025,zq025-1e-6))
# ---------------- GAS one-factor (PZC 2019) per name, FZ0-estimated ----------------
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
        def obj(th):
            om_,be_,ga_=th
            if not (0.0<=be_<=0.999): return 1e6
            v,e=gas_filter(tr,qa,min(ea,qa*1.05),om_,be_,ga_,0.0,a)
            L=fz0(tr,v,e,a); return float(np.mean(L)) if np.isfinite(L).all() else 1e6
        try:
            res=optimize.minimize(obj,x0=[0.0,0.95,0.02],method='Nelder-Mead',
                                  options={'maxiter':80,'xatol':1e-3,'fatol':1e-4})
            om_,be_,ga_=res.x
            v,e=gas_filter(y,qa,min(ea,qa*1.05),om_,be_,ga_,0.0,a)
            msk=TE['permno'].values==pn
            # align: test rows for this name are the last len(msk.sum()) obs of the series
            v_t=v[-int(msk.sum()):]; e_t=e[-int(msk.sum()):]
            GVE[a][0][msk]=v_t; GVE[a][1][msk]=e_t
        except Exception:
            gfail+=1
lg("GAS fitted (%d fails) %.0fs"%(gfail,time.time()-t0))
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return float(x.mean()/math.sqrt(max(v/n,1e-16)))
dates=TE['date'].values
def dm_vs_engine(Lm,Le):
    dd=pd.DataFrame({'d':Lm-Le,'date':dates}).groupby('date')['d'].mean()
    t=nw_t(dd.values);
    return {'mean_diff':round(float(np.nanmean(Lm-Le)),5),'DM_t':None if t is None else round(t,2),
            'p_one_sided':None if t is None else round(float(1-stats.norm.cdf(t)),4)}
OUT={'note':'Full-panel FZ0 (VaR,ES) re-scoring, pre-committed. DM_t>0 means the row model has HIGHER (worse) FZ0 loss than the engine, date-clustered NW(10), one-sided p. GAS = one-factor score-driven (PZC-2019-style) FZ0-estimated per name.',
     'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),
     'gpd':{'u':round(float(u),4),'xi':round(float(xi),4),'beta':round(float(beta),4)},'conf975':round(CONF975,4),
     'per_alpha':{}}
for a in ALPHAS:
    ve,ee=ENG[a]; Le=fz0(Y,ve,ee,a)
    rows_out={'engine_meanFZ0':round(float(np.mean(Le)),5),
              'engine_breach':round(float(np.mean(Y<=ve)),4)}
    vnc,enc=ENGNC[a]; Lnc=fz0(Y,vnc,enc,a)
    rows_out['engine_noconf_meanFZ0']=round(float(np.mean(Lnc)),5)
    rows_out['engine_noconf_breach']=round(float(np.mean(Y<=vnc)),4)
    rows_out['engine_noconf_vs_engine']=dm_vs_engine(Lnc,Le)
    Lg_=fz0(Y,TE[f'g_v{a}'].values,TE[f'g_e{a}'].values,a)
    dgn=pd.DataFrame({'d':Lg_-Lnc,'date':dates}).groupby('date')['d'].mean(); tgn=nw_t(dgn.values)
    rows_out['garch_minus_engine_noconf']={'mean_diff':round(float(np.nanmean(Lg_-Lnc)),5),
        'DM_t':None if tgn is None else round(tgn,2)}
    for nm,(vm,em) in [('garch_t',(TE[f'g_v{a}'].values,TE[f'g_e{a}'].values)),
                       ('fhs',(TE[f'fhs_v{a}'].values,TE[f'fhs_e{a}'].values)),
                       ('gas_pzc',GVE[a])]:
        Lm=fz0(Y,vm,em,a); ok=np.isfinite(Lm)&np.isfinite(Le)
        r=dm_vs_engine(np.where(ok,Lm,np.nan),np.where(ok,Le,np.nan))
        r['meanFZ0']=round(float(np.nanmean(Lm)),5); r['breach']=round(float(np.nanmean((Y<=vm)[ok])),4)
        rows_out[nm]=r
    # frontier cut: engine-vs-garch FZ0 edge in top mk63 decile
    mk=TE['mk63'].values; okm=np.isfinite(mk)
    thr=np.nanquantile(mk[okm],0.9); top=okm&(mk>=thr)
    Lg=fz0(Y,TE[f'g_v{a}'].values,TE[f'g_e{a}'].values,a)
    dtop=pd.DataFrame({'d':(Lg-Le)[top],'date':dates[top]}).groupby('date')['d'].mean()
    tt=nw_t(dtop.values)
    rows_out['top_mk63_decile_garch_minus_engine']={'mean_diff':round(float(np.nanmean((Lg-Le)[top])),5),
        'DM_t':None if tt is None else round(tt,2),'n_dates':int(len(dtop))}
    OUT['per_alpha'][str(a)]=rows_out
    lg(f"alpha={a}: {json.dumps(rows_out)}")
json.dump(OUT,open(os.path.join(P,"fz_fullpanel_results.json"),"w"),indent=2)
lg("FZFULLPANELDONE %.0fs"%(time.time()-t0))
