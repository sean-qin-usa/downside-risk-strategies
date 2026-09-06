# job_engine_esbt.py -- FATAL-1 FIX. Recompute the direct ES CALIBRATION backtests
# (Kupiec UC; Acerbi-Szekely 2014 Z2; McNeil-Frey 2000 exceedance-residual) on the REAL
# engine's own per-day (VaR,ES) forecasts -- the coherent min-envelope curve Q* used in the
# full-panel FZ0 (job_fz_fullpanel.py) -- NOT the GARCH-t+GPD proxy that es_backtests.py
# labeled 'hybrid_evt'. Same 200-name panel and same forecast construction as the FZ0 table,
# so FZ0 and the ES backtests are same-rows on ONE forecast set.
#
# Inference: STATIONARY BLOCK BOOTSTRAP over calendar dates (Politis-Romano 1994, mean block
# ~10 dates). Resampling whole dates respects cross-sectional dependence (names share a day's
# shock); geometric blocks add robustness to any residual serial dependence across dates. This
# replaces the iid date resample in es_backtests.py (whose comment mis-called it 'block'; MAJOR-4).
#
# Reports the engine ACCURACY LAYER (no conformal, == the FZ0 'engine') and the DEPLOYED engine
# (conformal shift at 97.5%) side by side, plus GARCH-normal, GARCH-t, FHS on the identical rows.
# FZ0 means + date-clustered DM are recomputed too as an internal cross-check vs fz_fullpanel_results.json.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rng=np.random.default_rng(20260906)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
ALPHAS=[0.01,0.025]
def conf_ostat(sc,tau):
    n=len(sc); k=int(math.ceil((n+1)*tau)); k=min(max(k,1),n)
    return float(np.sort(np.asarray(sc,float))[k-1])
def t_es(a,nu):
    q=stats.t.ppf(a,nu); return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)
def fz0(r,v,e,a):
    v=np.minimum(v,-1e-8); e=np.minimum(e,v)
    hit=(r<=v).astype(float)
    return -(1.0/(a*e))*hit*(v-r)+v/e+np.log(-e)-1.0
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
TRz=[]; CALz=[]; rows=[]
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
    ztr=z[:cp]
    for a in ALPHAS:
        zfa=float(np.quantile(ztr,a)); efa=float(np.mean(ztr[ztr<=zfa]))
        df[f'fhs_v{a}']=mu+df['sig']*zfa; df[f'fhs_e{a}']=mu+df['sig']*efa
        df[f'g_v{a}']=mu+df['sig']*stats.t.ppf(a,nu)/tsc; df[f'g_e{a}']=mu+df['sig']*t_es(a,nu)/tsc
        znz=float(stats.norm.ppf(a)); enz=float(-stats.norm.pdf(stats.norm.ppf(a))/a)
        df[f'n_v{a}']=mu+df['sig']*znz; df[f'n_e{a}']=mu+df['sig']*enz
    df['idx']=np.arange(n); df['mu']=mu
    dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<cp]; cal=dd[(dd['idx']>=cp)&(dd['idx']<sp)]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(cal)<60: continue
    TRz.append(trn[ZX+['z']]); CALz.append(cal[ZX+['z']])
    keep=['y','sig','date','mu']+ZX+[c for c in df.columns if c.startswith(('fhs_','g_','n_'))]
    t2=tst[keep].copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz); CALzc=pd.concat(CALz)
ZQ={}; ZQcal={}
for t in ALPHAS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
    ZQ[t]=m.predict(TE[ZX].values); ZQcal[t]=m.predict(CALzc[ZX].values)
    lg("  ztau %.3f %.0fs"%(t,time.time()-t0))
SUBN=20; ZQSUB={a:{} for a in ALPHAS}
for a in ALPHAS:
    for j in range(SUBN):
        u=a*(j+0.5)/SUBN
        mz=HistGradientBoostingRegressor(loss='quantile',quantile=u,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
        ZQSUB[a][j]=mz.predict(TE[ZX].values)
    lg("  sub-alpha grid a=%.3f %.0fs"%(a,time.time()-t0))
ztr=TRzc['z'].values; uu=np.quantile(ztr,0.025); exc=uu-ztr[ztr<uu]
xi,loc,beta=stats.genpareto.fit(exc,floc=0.0)
def evt_q(tau,p0=0.025):
    return uu-(beta/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else uu-beta*math.log(p0/tau)
def coherent_star(a):
    cols=[np.minimum(ZQSUB[a][j], evt_q(a*(j+0.5)/SUBN)) for j in range(SUBN)]
    return np.sort(np.stack(cols,axis=1),axis=1)
s975=CALzc['z'].values-ZQcal[0.025]; CONF975=conf_ostat(s975,0.025)
lg(f"GPD u={uu:.3f} xi={xi:.3f} beta={beta:.3f}; conf975 {CONF975:+.4f}")
MU=TE['mu'].values; SIG=TE['sig'].values; Y=TE['y'].values
star01=coherent_star(0.01); star025=coherent_star(0.025)
zq01=np.minimum(ZQ[0.01],evt_q(0.01)); zq025=np.minimum(ZQ[0.025],evt_q(0.025))
zq01=np.maximum(zq01,star01[:,-1]); zq025=np.maximum(zq025,star025[:,-1])
es01=star01.mean(axis=1); es025=star025.mean(axis=1)
ENGNC={0.01:(MU+SIG*zq01, MU+SIG*np.minimum(es01,zq01-1e-6)),
       0.025:(MU+SIG*zq025, MU+SIG*np.minimum(es025,zq025-1e-6))}
ENG={0.01:ENGNC[0.01],
     0.025:(MU+SIG*(zq025+CONF975), MU+SIG*(np.minimum(es025,zq025-1e-6)+CONF975))}
def model_ve(a,m):
    if m=='garch_norm': return TE[f'n_v{a}'].values, TE[f'n_e{a}'].values
    if m=='garch_t':    return TE[f'g_v{a}'].values, TE[f'g_e{a}'].values
    if m=='fhs':        return TE[f'fhs_v{a}'].values, TE[f'fhs_e{a}'].values
    if m=='engine_noconf': return ENGNC[a]
    if m=='engine_conf':   return ENG[a]
MODELS=['garch_norm','garch_t','fhs','engine_noconf','engine_conf']

# ---- date clustering + stationary block bootstrap ----
dates=TE['date'].values.astype('datetime64[D]').astype('int64')
udates=np.unique(dates); Dn=len(udates); pos=pd.Series(np.arange(Dn),index=udates)
rowdatepos=pos.reindex(dates).values   # position of each obs's date in ordered unique-date list
def date_agg(vals,dpos):
    out=np.zeros(Dn); np.add.at(out,dpos,np.asarray(vals,float)); return out
def stat_boot_ratio(S,C,B=4000,mean_block=10.0):
    # bootstrap replicates of sum(S)/sum(C) resampling Dn date-slots via stationary geometric blocks
    prob=1.0/mean_block; reps=np.empty(B)
    for b in range(B):
        idx=np.empty(Dn,dtype=np.int64); f=0
        while f<Dn:
            st=int(rng.integers(0,Dn)); L=int(rng.geometric(prob)); L=min(L,Dn-f)
            idx[f:f+L]=(st+np.arange(L))%Dn; f+=L
        cc=C[idx].sum(); reps[b]=S[idx].sum()/cc if cc>1e-12 else np.nan
    return reps
def kupiec(brind,a):
    N=len(brind); nb=int(brind.sum()); ph=nb/N if N else 0.0
    if nb==0 or nb==N: return ph,float('nan')
    LR=-2*((nb*math.log(a)+(N-nb)*math.log(1-a))-(nb*math.log(ph)+(N-nb)*math.log(1-ph)))
    return ph,float(1-stats.chi2.cdf(LR,1))
def z2_test(z,zq,zes,a,dpos):
    t=(z<=zq).astype(float)*z/(a*zes)          # per-obs contribution; E=1 under correct ES
    obs=1.0-t.sum()/len(t)
    S=date_agg(t,dpos); C=date_agg(np.ones(len(t)),dpos)
    boot=1.0-stat_boot_ratio(S,C); se=np.nanstd(boot)
    p=float(2*(1-stats.norm.cdf(abs(obs)/se))) if se>0 else float('nan')
    return float(obs),p
def mf_test(z,zq,zes,dpos):
    m=z<=zq; er=(z-zes); erm=np.where(m,er,0.0)
    nb=int(m.sum())
    if nb<10: return float('nan'),float('nan'),nb
    obs=erm.sum()/nb
    S=date_agg(erm,dpos); C=date_agg(m.astype(float),dpos)
    boot=stat_boot_ratio(S,C); se=np.nanstd(boot)
    p=float(2*(1-stats.norm.cdf(abs(obs)/se))) if se>0 else float('nan')
    return float(obs),p,nb
def dclust_dm(Lm,Le,dpos):
    d=Lm-Le; sd=date_agg(d,dpos); cd=date_agg(np.ones(len(d)),dpos)
    dd=(sd/np.maximum(cd,1e-12))[cd>0]; nD=len(dd); mbar=dd.mean()
    L=10; v=dd.var()
    for k in range(1,L+1): v+=2*(1-k/(L+1))*np.mean((dd[k:]-mbar)*(dd[:-k]-mbar))
    se=math.sqrt(max(v,1e-16)/nD); return float(mbar),float(mbar/se if se>0 else 0.0),nD

OUT={'note':'FATAL-1 fix: direct ES calibration backtests (Kupiec UC, Acerbi-Szekely 2014 Z2, '
     'McNeil-Frey 2000) computed on the REAL engine (coherent min-envelope Q*) per-day (VaR,ES), '
     'same 200-name panel/rows as the full-panel FZ0. Engine reported as ACCURACY LAYER (no conformal, '
     '== FZ0 engine) and DEPLOYED (conformal at 97.5%). Inference = STATIONARY BLOCK BOOTSTRAP over '
     'calendar dates (mean block 10). Z2<0 => ES understates the tail. MF exceedance residual =0 under '
     'correct ES. FZ0/DM recomputed as internal cross-check vs fz_fullpanel_results.json.',
     'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),'n_dates':int(Dn),
     'gpd':{'u':round(float(uu),4),'xi':round(float(xi),4),'beta':round(float(beta),4)},
     'conf975':round(CONF975,4),'per_alpha':{}}
for a in ALPHAS:
    A={}
    ve_e,ee_e=ENGNC[a]; Le=fz0(Y,ve_e,ee_e,a)
    for m in MODELS:
        v,e=model_ve(a,m); v=np.asarray(v,float); e=np.asarray(e,float)
        z=(Y-MU)/SIG; zq=(v-MU)/SIG; zes=(e-MU)/SIG
        ok=np.isfinite(zq)&np.isfinite(zes)&np.isfinite(z)&(zes<0); dpos=rowdatepos[ok]
        br,kp=kupiec((Y[ok]<=v[ok]).astype(float),a)
        z2,z2p=z2_test(z[ok],zq[ok],zes[ok],a,dpos)
        mf,mfp,nb=mf_test(z[ok],zq[ok],zes[ok],dpos)
        Lm=fz0(Y,v,e,a); md,dmt,nD=dclust_dm(Lm,Le,rowdatepos)
        A[m]={'breach':round(br,4),'kupiec_p':round(kp,4),'AS_Z2':round(z2,4),'AS_Z2_p':round(z2p,4),
              'MF_exres':round(mf,4),'MF_p':round(mfp,4),'n_breach':int(nb),
              'meanFZ0':round(float(np.nanmean(Lm)),5),'DM_vs_engine_noconf':round(dmt,2),'n_dates':int(nD)}
    OUT['per_alpha'][str(a)]=A
    lg(f"alpha={a}: "+json.dumps(A))
json.dump(OUT,open(os.path.join(P,"engine_esbt_results.json"),"w"),indent=2)
lg("ENGINEESBTDONE %.0fs"%(time.time()-t0))
