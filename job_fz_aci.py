# job_fz_aci.py -- CAN AN ADAPTIVE SHIFT KEEP COVERAGE WITHOUT THE FZ0 CONCESSION?
# The deployed engine's static conformal shift at 97.5% buys coverage but loses the
# joint FZ0 score to GARCH-t at 2.5% (DM -2.0; top decile -7.1) because the shift,
# calibrated on a split containing the 2020 crash, over-widens out of era. This job
# tests the adaptive escalation (Gibbs-Candes ACI style, pooled): the scalar shift
# c_t updates daily from the cross-sectional breach frequency,
#     c_{t+1} = c_t - gamma * (b_t - alpha),  b_t = panel breach freq on date t,
# warm-started at the static conformal value, clipped to [-3, 1]. Reported for
# gamma in {0.02, 0.05}: breach rate, date-clustered breach t, per-name Kupiec975
# pass rate, and FZ0 vs GARCH-t (overall and top mk63 decile) -- same panel,
# same engine, same GPD tail as the registered fz_fullpanel run.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
A=0.025
def fz0(r,v,e,a):
    v=np.minimum(v,-1e-8); e=np.minimum(e,v)
    hit=(r<=v).astype(float)
    return -(1.0/(a*e))*hit*(v-r)+v/e+np.log(-e)-1.0
def t_es(a,nu):
    q=stats.t.ppf(a,nu)
    return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)
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
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    df['g_v']=mu+df['sig']*stats.t.ppf(A,nu)/tsc
    df['g_e']=mu+df['sig']*t_es(A,nu)/tsc
    df['idx']=np.arange(n); df['mu']=mu
    dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<cp]; cal=dd[(dd['idx']>=cp)&(dd['idx']<sp)]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(cal)<60: continue
    TRz.append(trn[ZX+['z']]); CALz.append(cal[ZX+['z']])
    keep=['y','sig','date','mu','mk63','g_v','g_e']+ZX
    t2=tst[keep].copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz); CALzc=pd.concat(CALz)
m=HistGradientBoostingRegressor(loss='quantile',quantile=A,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values)
ZQ=m.predict(TE[ZX].values); ZQcal=m.predict(CALzc[ZX].values)
ztr=TRzc['z'].values; u=np.quantile(ztr,0.025); exc=u-ztr[ztr<u]
xi,loc,beta=stats.genpareto.fit(exc,floc=0.0)
def evt_q(tau,p0=0.025): return u-(beta/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u-beta*math.log(p0/tau)
def evt_es(tau):
    q=evt_q(tau); return q-(beta+xi*(u-q))/(1.0-xi)
s975=CALzc['z'].values-ZQcal; C0=float(np.quantile(s975,A*(1+1/len(s975))))
lg(f"GPD u={u:.3f} xi={xi:.3f} beta={beta:.3f}; static conf {C0:+.4f}")
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values
zq=np.minimum(ZQ,evt_q(A)); ze=np.minimum(evt_es(A),zq-1e-6)
dvals=pd.to_datetime(TE['date'].values).values
udates=np.sort(np.unique(dvals)); didx=np.searchsorted(udates,dvals)
nT=len(udates)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
def kupiec_p(x,T,p):
    if x==0 or x==T: return None
    pi=x/T
    def llb(pp,k0,k1):
        if pp<=0 or pp>=1: return -1e300
        return k0*math.log(1-pp)+k1*math.log(pp)
    lr=-2*(llb(p,T-x,x)-llb(pi,T-x,x)); return float(1-stats.chi2.cdf(max(lr,0),1))
def eval_variant(cvec):
    # cvec: shift per ROW (already aligned)
    v=MU+SIG*(zq+cvec); e=MU+SIG*(ze+cvec)
    br=(Y<=v)
    Le=fz0(Y,v,e,A); Lg=fz0(Y,TE['g_v'].values,TE['g_e'].values,A)
    d=pd.DataFrame({'d':Lg-Le,'date':TE['date'].values}).groupby('date')['d'].mean()
    mk=TE['mk63'].values; okm=np.isfinite(mk); thr=np.nanquantile(mk[okm],0.9); top=okm&(mk>=thr)
    dt=pd.DataFrame({'d':(Lg-Le)[top],'date':TE['date'].values[top]}).groupby('date')['d'].mean()
    bd=pd.DataFrame({'b':br.astype(float),'date':TE['date'].values}).groupby('date')['b'].mean()
    # per-name kupiec pass rate
    dfp=pd.DataFrame({'pn':TE['permno'].values,'b':br.astype(int)})
    passr=[]
    for pn,gg in dfp.groupby('pn'):
        pv=kupiec_p(int(gg['b'].sum()),len(gg),A)
        if pv is not None: passr.append(pv>0.05)
    return {'breach':round(float(br.mean()),4),
            'breach_dateclust_t':nw_t(bd.values-A),
            'kupiec975_passrate':round(float(np.mean(passr)),3),
            'meanFZ0':round(float(np.mean(Le)),5),
            'garch_minus_this_DM':nw_t(d.values),
            'top_decile_garch_minus_this_DM':nw_t(dt.values)}
OUT={'note':'Adaptive (ACI-style, pooled) conformal shift at 97.5% vs static shift and no shift. c updates daily from panel breach freq, warm start at static conf, clip [-3,1]. Same engine/panel/GPD as fz_fullpanel. garch_minus_this_DM>0 means this variant beats GARCH-t on FZ0.',
     'static_conf':round(C0,4),'n_test':int(len(Y)),'n_dates':int(nT),
     'variants':{}}
OUT['variants']['no_shift']=eval_variant(np.zeros(len(Y)))
OUT['variants']['static_shift']=eval_variant(np.full(len(Y),C0))
for gam in (0.02,0.05):
    c=np.empty(nT); c[0]=C0
    rowshift=np.empty(len(Y))
    for i in range(nT):
        msk=didx==i
        rowshift[msk]=c[i]
        v=MU[msk]+SIG[msk]*(zq[msk]+c[i])
        b=float(np.mean(Y[msk]<=v))
        if i+1<nT: c[i+1]=min(max(c[i]-gam*(b-A),-3.0),1.0)
    OUT['variants']['aci_gamma_%g'%gam]=eval_variant(rowshift)
    OUT['variants']['aci_gamma_%g'%gam]['c_final']=round(float(c[-1]),4)
    OUT['variants']['aci_gamma_%g'%gam]['c_range']=[round(float(c.min()),4),round(float(c.max()),4)]
json.dump(OUT,open(os.path.join(P,"fz_aci_results.json"),"w"),indent=2)
lg("FZACIDONE %.0fs"%(time.time()-t0)); lg(json.dumps(OUT,indent=1))
