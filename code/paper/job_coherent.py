# job_coherent.py -- IS THE IMPLEMENTED HYBRID ONE COHERENT DISTRIBUTION? (adversarial wave 9)
# The objection: the displayed equation splices EVT below p0 and body above, but the code
# takes a pointwise minimum envelope min(body, EVT) and computes hybrid ES from the GPD
# closed form, so the reported (VaR, ES) pair is not obviously the VaR and ES of ONE
# monotone predictive quantile curve. This job (1) defines the implemented final curve
# Q*(u) = min(body_q(u), evt_q(u)) for u <= p0 (body alone above p0), (2) enforces
# monotonicity by rearrangement (sorting node values in u), (3) computes VaR_a = Q*(a) and
# ES_a as the 20-node midpoint integral of the SAME rearranged curve, (4) reruns FZ0 vs
# GARCH-t on identical rows and against the shipped convention, and (5) reports how often
# the body branch binds (body < EVT) inside the tail. Also: p0 threshold sensitivity for
# the EVT splice at p0 in {1.5%, 2.5%, 5%}. Panel and engine as job_fz_fullpanel.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
rr=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:200]
ALPHAS=[0.01,0.025]; P0S=[0.015,0.025,0.05]; NN=20
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
def fz0(r,v,e,a):
    v=np.minimum(v,-1e-8); e=np.minimum(e,v)
    hit=(r<=v).astype(float)
    return -(1.0/(a*e))*hit*(v-r)+v/e+np.log(-e)-1.0
def t_es(a,nu):
    q=stats.t.ppf(a,nu)
    return -stats.t.pdf(q,nu)*(nu+q*q)/((nu-1)*a)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)
TRz=[]; rows=[]
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
    df['idx']=np.arange(n); df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<cp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TRz.append(trn[ZX+['z']]); t2=tst.copy(); t2['permno']=pn; rows.append(t2)
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TRz)
lg("panel %d names %d rows %.0fs"%(TE.permno.nunique(),len(TE),time.time()-t0))
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
dates=TE['date'].values
ztr=TRzc['z'].values
# body quantile fits at every needed node (union over alphas), plus the alpha levels
def fit_node(u):
    return HistGradientBoostingRegressor(loss='quantile',quantile=u,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,TRzc['z'].values).predict(TE[ZX].values)
NODE={}
for a in ALPHAS:
    for j in range(NN):
        u=a*(j+0.5)/NN
        NODE[round(u,6)]=None
    NODE[round(a,6)]=None
for u in sorted(NODE):
    NODE[u]=fit_node(u); lg("  node %.5f %.0fs"%(u,time.time()-t0))
def evt_maker(p0):
    uthr=np.quantile(ztr,p0); exc=uthr-ztr[ztr<uthr]
    xi,loc,beta=stats.genpareto.fit(exc,floc=0.0)
    def evt_q(tau):
        if tau>p0: return None
        return uthr-(beta/xi)*((tau/p0)**(-xi)-1.0) if abs(xi)>1e-6 else uthr-beta*math.log(p0/tau)
    def evt_es(tau):
        q=evt_q(tau); return q-(beta+xi*(uthr-q))/(1.0-xi)
    return evt_q,evt_es,float(xi),float(beta),float(uthr)
# GARCH benchmark losses once per alpha (vectorized over unique fitted nu)
LGCACHE={}
for a in ALPHAS:
    unu=np.unique(NU)
    qmap={nu_:stats.t.ppf(a,nu_) for nu_ in unu}; emap={nu_:t_es(a,nu_) for nu_ in unu}
    qv=np.array([qmap[nu_] for nu_ in NU]); ev=np.array([emap[nu_] for nu_ in NU])
    LGCACHE[a]=fz0(Y,MU+SIG*qv/TSC,MU+SIG*ev/TSC,a)
OUT={'note':('Coherent-curve audit: final implemented quantile curve Q*(u)=min(body,EVT) for u<=p0 '
 '(body alone above p0), monotonized by rearrangement per observation; VaR_a=Q*(a); ES_a = 20-node '
 'midpoint integral of the SAME rearranged curve. Compared on identical rows with the shipped '
 'convention (VaR=min at a, ES=GPD closed form capped below VaR) and with GARCH-t closed forms. '
 'bind_frac = fraction of (row,node) pairs in u<=min(p0,a) where the body branch is the minimum. '
 'Also p0 splice sensitivity. All DMs date-clustered NW(10); positive DM favors the second-named.'),
 'xi_guard':'ES formula requires xi<1; fitted xi reported per p0.',
 'per_p0':{}}
for p0 in P0S:
    evt_q,evt_es,xi,beta,uthr=evt_maker(p0)
    res={'gpd':{'xi':round(xi,4),'beta':round(beta,4),'u':round(uthr,4)}}
    for a in ALPHAS:
        nodes=[a*(j+0.5)/NN for j in range(NN)]
        BQ=np.stack([NODE[round(u,6)] for u in nodes],axis=1)   # rows x NN body nodes
        EQ=np.array([evt_q(u) if u<=p0 else np.inf for u in nodes])
        Qstar=np.minimum(BQ,EQ[None,:])
        Qstar=np.sort(Qstar,axis=1)                              # monotone rearrangement in u
        inevt=np.array([u<=p0 for u in nodes])
        bind=float(np.mean((BQ<=EQ[None,:])[:,inevt])) if inevt.any() else None  # body binds, EVT domain only
        # alpha level
        bq_a=NODE[round(a,6)]
        ev_a=evt_q(a) if a<=p0 else np.inf
        v_z=np.minimum(bq_a,ev_a)
        v_z=np.maximum(v_z,Qstar[:,-1])                          # curve consistency at the endpoint
        es_z=Qstar.mean(axis=1)
        Vc=MU+SIG*v_z; Ec=MU+SIG*es_z
        # shipped convention
        if a<=p0:
            ze_ship=np.minimum(evt_es(a),v_z-1e-6)
        else:
            ze_ship=np.minimum(es_z,v_z-1e-6)                    # no GPD form above p0
        Vs=MU+SIG*v_z; Es=MU+SIG*ze_ship
        Lg=LGCACHE[a]
        Lc=fz0(Y,Vc,Ec,a); Ls=fz0(Y,Vs,Es,a)
        def dm(L1,L2):
            dd_=pd.DataFrame({'d':L1-L2,'date':dates}).groupby('date')['d'].mean()
            return nw_t(dd_.values)
        res['alpha_%g'%a]={'bind_frac_body_min':round(bind,4),
            'breach':round(float(np.mean(Y<=Vc)),4),
            'meanFZ0_coherent':round(float(np.mean(Lc)),5),
            'meanFZ0_shipped':round(float(np.mean(Ls)),5),
            'shipped_minus_coherent_DM':dm(Ls,Lc),
            'garch_minus_coherent_DM':dm(Lg,Lc),
            'garch_minus_shipped_DM':dm(Lg,Ls),
            'mean_ES_coherent':round(float(np.mean(Ec)),3),
            'mean_ES_shipped':round(float(np.mean(Es)),3)}
        lg("p0=%g a=%g %s"%(p0,a,json.dumps(res['alpha_%g'%a])))
    OUT['per_p0']['p0_%g'%p0]=res
json.dump(OUT,open(os.path.join(P,"coherent_results.json"),"w"),indent=2)
lg("COHERENTDONE %.0fs"%(time.time()-t0))
