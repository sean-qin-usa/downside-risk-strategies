# job_conformal_strict.py -- STRICT-SPLIT conformal/FZ audit (adversarial review, wave 7).
# The reviewer's point: in job_fz_fullpanel.py the first-stage GARCH is fit on y[:sp]
# (the whole 60% estimation period), so the parameters that filter the calibration
# residuals (indices cp..sp) were estimated USING those calibration returns. The
# calibration split is held out from the shape learner and the EVT tail, but not from
# the filter -- so the split-conformal construction is not strictly held out end to end.
# This job reruns the SAME audit with the engine's filter fit only through cp (45% of
# the sample), recursive filtration thereafter, so calibration outcomes touch no
# estimated component of the engine. Two engine variants on IDENTICAL test rows:
#   eng_orig    filter fit y[:sp]   (replicates the fz_fullpanel construction)
#   eng_strict  filter fit y[:cp]   (strict end-to-end held-out construction)
# Benchmarks (GARCH-t, FHS) use the y[:sp] filter in BOTH cases, exactly as in the
# original audit, so engine-row differences are attributable purely to the split.
# GAS is omitted: it is estimated from raw returns only and is unaffected by the
# engine's split; its rows remain those of fz_fullpanel_results.json.
# Adds per-name Kupiec(5%) pass rates and date-clustered pooled breach t-stats so the
# exception audit itself (not just FZ0) is re-run under the strict construction.
# Also patches results/fz_fullpanel_results.json note: registered -> pre-committed.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
ALPHAS=[0.01,0.025]
def fz0(r,v,e,a):
    v=np.minimum(v,-1e-8); e=np.minimum(e,v)
    hit=(r<=v).astype(float)
    return -(1.0/(a*e))*hit*(v-r)+v/e+np.log(-e)-1.0
def t_es(a,nu):
    q=stats.t.ppf(a,nu)
    return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)
def kupiec_p(x,n,a):
    if n==0: return None
    ph=x/n
    if ph<=0: ll1=0.0
    elif ph>=1: ll1=0.0
    else: ll1=x*math.log(ph)+(n-x)*math.log(1-ph)
    ll0=x*math.log(a)+(n-x)*math.log(1-a)
    lr=-2.0*(ll0-ll1)
    return float(1-stats.chi2.cdf(max(lr,0.0),1))
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return float(x.mean()/math.sqrt(max(v/n,1e-16)))
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
def feats(z,sig,y):
    df=pd.DataFrame({'z':z})
    df['logsig']=np.log(np.maximum(sig,1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(pd.Series(y)<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    return df
def gfit(yw):
    r1=arch_model(yw,vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
    p=r1.params
    return float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)),float(p.get('nu',8))
def filt(y,om,al,be,mu,v0):
    n=len(y); e=y-mu; s2=np.empty(n); s2[0]=v0
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); return sig,(y-mu)/np.maximum(sig,1e-6)
TRB=[]; CALB=[]; TRE=[]; CALE=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6); cp=int(sp*0.75)
    try:
        omB,alB,beB,muB,nuB=gfit(y[:sp]); omE,alE,beE,muE,nuE=gfit(y[:cp])
    except Exception: continue
    sigB,zB=filt(y,omB,alB,beB,muB,np.var(y[:sp])); sigE,zE=filt(y,omE,alE,beE,muE,np.var(y[:cp]))
    tscB=math.sqrt(nuB/(nuB-2)) if nuB>2 else 1.0
    fB=feats(zB,sigB,y).add_suffix('_B'); fE=feats(zE,sigE,y).add_suffix('_E')
    df=pd.concat([pd.DataFrame({'y':y,'date':dts,'idx':np.arange(n),
                                'sigB':sigB,'sigE':sigE}),fB,fE],axis=1)
    df['muB']=muB; df['muE']=muE
    ztrB=zB[:cp]; tscE=math.sqrt(nuE/(nuE-2)) if nuE>2 else 1.0
    for a in ALPHAS:
        df[f'fhs_v{a}']=muB+df['sigB']*np.quantile(ztrB,a)
        df[f'fhs_e{a}']=muB+df['sigB']*float(np.mean(ztrB[ztrB<=np.quantile(ztrB,a)]))
        df[f'g_v{a}']=muB+df['sigB']*stats.t.ppf(a,nuB)/tscB
        df[f'g_e{a}']=muB+df['sigB']*t_es(a,nuB)/tscB
        df[f'gE_v{a}']=muE+df['sigE']*stats.t.ppf(a,nuE)/tscE
        df[f'gE_e{a}']=muE+df['sigE']*t_es(a,nuE)/tscE
    need=[c+'_B' for c in ZX]+[c+'_E' for c in ZX]
    dd=df.dropna(subset=need)
    trn=dd[dd['idx']<cp]; cal=dd[(dd['idx']>=cp)&(dd['idx']<sp)]; tst=dd[dd['idx']>=sp]
    if len(tst)<60 or len(cal)<60: continue
    TRB.append(trn[[c+'_B' for c in ZX]+['z_B']]); CALB.append(cal[[c+'_B' for c in ZX]+['z_B']])
    TRE.append(trn[[c+'_E' for c in ZX]+['z_E']]); CALE.append(cal[[c+'_E' for c in ZX]+['z_E']])
    t2=tst.copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d %.0fs"%(len(rows),time.time()-t0))
TE=pd.concat(rows).reset_index(drop=True)
TRBc=pd.concat(TRB); CALBc=pd.concat(CALB); TREc=pd.concat(TRE); CALEc=pd.concat(CALE)
Y=TE['y'].values; dates=TE['date'].values; PN=TE['permno'].values
def build_engine(TRc,CALc,suf,SIG,MU):
    cols=[c+suf for c in ZX]; zcol='z'+suf
    ZQ={}; ZQcal={}
    for a in ALPHAS:
        m=HistGradientBoostingRegressor(loss='quantile',quantile=a,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[cols].values,TRc[zcol].values)
        ZQ[a]=m.predict(TE[cols].values); ZQcal[a]=m.predict(CALc[cols].values)
    ztr=TRc[zcol].values; u=np.quantile(ztr,0.025); exc=u-ztr[ztr<u]
    xi,loc,beta=stats.genpareto.fit(exc,floc=0.0)
    def evt_q(tau,p0=0.025):
        return u-(beta/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else u-beta*math.log(p0/tau)
    def evt_es(tau):
        q=evt_q(tau); return q-(beta+xi*(u-q))/(1.0-xi)
    s975=CALc[zcol].values-ZQcal[0.025]; CONF=float(np.quantile(s975,0.025*(1+1/len(s975))))
    zq01=np.minimum(ZQ[0.01],evt_q(0.01)); zq025=np.minimum(ZQ[0.025],evt_q(0.025))
    V={}; E={}
    V[(0.01,'ns')]=MU+SIG*zq01; E[(0.01,'ns')]=MU+SIG*np.minimum(evt_es(0.01),zq01-1e-6)
    V[(0.025,'ns')]=MU+SIG*zq025; E[(0.025,'ns')]=MU+SIG*np.minimum(evt_es(0.025),zq025-1e-6)
    V[(0.025,'st')]=MU+SIG*(zq025+CONF); E[(0.025,'st')]=MU+SIG*(np.minimum(evt_es(0.025),zq025-1e-6)+CONF)
    meta={'gpd':{'u':round(float(u),4),'xi':round(float(xi),4),'beta':round(float(beta),4)},'conf975':round(CONF,4)}
    return V,E,meta
VB,EB,metaB=build_engine(TRBc,CALBc,'_B',TE['sigB'].values,TE['muB'].values)
lg("orig engine built %.0fs"%(time.time()-t0))
VE,EE,metaE=build_engine(TREc,CALEc,'_E',TE['sigE'].values,TE['muE'].values)
lg("strict engine built %.0fs"%(time.time()-t0))
def dmrow(Lm,Le):
    d=pd.DataFrame({'d':Lm-Le,'date':dates}).groupby('date')['d'].mean()
    t=nw_t(d.values)
    return {'mean_diff':round(float(np.nanmean(Lm-Le)),5),'DM_t':None if t is None else round(t,2)}
def audit(v,e,a):
    L=fz0(Y,v,e,a); hit=(Y<=v)
    dts_=pd.DataFrame({'h':hit.astype(float),'date':dates}).groupby('date')['h'].mean()
    bt=nw_t(dts_.values-a)
    ps=[]
    for pn in np.unique(PN):
        m=PN==pn; p=kupiec_p(int(hit[m].sum()),int(m.sum()),a)
        if p is not None: ps.append(p>0.05)
    return L,{'meanFZ0':round(float(np.mean(L)),5),'breach':round(float(hit.mean()),4),
              'breach_dateclust_t':None if bt is None else round(bt,2),
              'kupiec_passrate':round(float(np.mean(ps)),3)}
OUT={'note':('STRICT-SPLIT conformal/FZ audit: engine variant with first-stage GARCH fit only through cp '
     '(45% of sample) so the calibration window cp..sp is held out from EVERY estimated engine component '
     '(filter, shape learner, EVT tail); recursive filtration thereafter. eng_orig replicates the '
     'fz_fullpanel construction (filter fit through sp) on identical test rows; benchmarks use the '
     'sp-fit filter in both, so engine-row differences are attributable purely to the split. GAS is '
     'unaffected (raw-returns estimation) -- see fz_fullpanel_results.json. DM_t>0 in benchmark rows = '
     'benchmark worse than that engine variant, date-clustered NW(10).'),
     'n_names':int(TE.permno.nunique()),'n_test':int(len(Y)),
     'eng_orig':metaB,'eng_strict':metaE,'per_alpha':{}}
for a in ALPHAS:
    variants={}
    LB_ns,rB_ns=audit(VB[(a,'ns')],EB[(a,'ns')],a); variants['orig_noshift']=rB_ns
    LE_ns,rE_ns=audit(VE[(a,'ns')],EE[(a,'ns')],a); variants['strict_noshift']=rE_ns
    Lg=fz0(Y,TE[f'g_v{a}'].values,TE[f'g_e{a}'].values,a)
    Lf=fz0(Y,TE[f'fhs_v{a}'].values,TE[f'fhs_e{a}'].values,a)
    LgE=fz0(Y,TE[f'gE_v{a}'].values,TE[f'gE_e{a}'].values,a)
    _,rgE=audit(TE[f'gE_v{a}'].values,TE[f'gE_e{a}'].values,a); variants['garch_cpfit']=rgE
    variants['strict_vs_orig_noshift']=dmrow(LE_ns,LB_ns)
    variants['garch_minus_orig_noshift']=dmrow(Lg,LB_ns)
    variants['garch_minus_strict_noshift']=dmrow(Lg,LE_ns)
    variants['garchcp_minus_strict_noshift']=dmrow(LgE,LE_ns)   # same-information-set control
    variants['garch_minus_garchcp']=dmrow(Lg,LgE)               # pure filter-window handicap
    variants['fhs_minus_strict_noshift']=dmrow(Lf,LE_ns)
    if a==0.025:
        LB_st,rB_st=audit(VB[(a,'st')],EB[(a,'st')],a); variants['orig_static']=rB_st
        LE_st,rE_st=audit(VE[(a,'st')],EE[(a,'st')],a); variants['strict_static']=rE_st
        variants['strict_vs_orig_static']=dmrow(LE_st,LB_st)
        variants['garch_minus_strict_static']=dmrow(Lg,LE_st)
    mk=TE['mk63_E'].values; okm=np.isfinite(mk)
    thr=np.nanquantile(mk[okm],0.9); top=okm&(mk>=thr)
    dtop=pd.DataFrame({'d':(Lg-LE_ns)[top],'date':dates[top]}).groupby('date')['d'].mean()
    tt=nw_t(dtop.values)
    variants['top_mk63_decile_garch_minus_strict_noshift']={'mean_diff':round(float(np.nanmean((Lg-LE_ns)[top])),5),
        'DM_t':None if tt is None else round(tt,2),'n_dates':int(len(dtop))}
    OUT['per_alpha'][str(a)]=variants
    lg(f"alpha={a}: {json.dumps(variants)}")
json.dump(OUT,open(os.path.join(P,"fz_strict_results.json"),"w"),indent=2)
# patch the old audit JSON's stale 'registered' note wording in place
fp=os.path.join(P,"results","fz_fullpanel_results.json")
try:
    j=json.load(open(fp)); j['note']=j['note'].replace('re-scoring, registered','re-scoring, pre-committed')
    json.dump(j,open(fp,"w"),indent=2); lg("patched results/fz_fullpanel_results.json note")
except Exception as ex: lg("note patch skipped: %r"%ex)
lg("CONFSTRICTDONE %.0fs"%(time.time()-t0))
