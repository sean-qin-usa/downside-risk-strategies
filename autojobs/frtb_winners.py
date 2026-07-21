# FRTB-GRADE WINNERS TABLE (host, Bloomberg) — full battery on the nonparam-winning classes + controls.
# Per asset: GARCH-t vs FHS vs residual-hybrid vs hybrid+EVT-tail. Metrics: avg pinball, ES97.5, Kupiec+Christoffersen at
# BOTH 99% and 97.5%, Diebold-Mariano (hybrid_EVT vs GARCH), resid_kurt. Power/credit/rates use price DIFFERENCES (log-returns
# invalid for near-zero/negative levels -> fixes the PJM artifact). This is the industry-standard-and-above cross-asset table.
import json, os, time, math, warnings; warnings.filterwarnings("ignore")
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import numpy as np, pandas as pd, datetime as dt
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def series(tk,start,end):
    pdf=to_pd(blp.bdh(tk,'px_last',start,end))
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vc=pdf.columns[cols.index('value')]; dc=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dc,vc]].dropna().copy(); s[dc]=pd.to_datetime(s[dc],errors='coerce'); return s.dropna(subset=[dc]).set_index(dc)[vc].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]; TAIL=[0.005,0.01,0.025]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def gpd_left_q(ztr,tau,pu=0.05):
    u=np.quantile(ztr,pu); ex=u-ztr[ztr<u]; ex=ex[ex>0]
    if len(ex)<30: return np.quantile(ztr,tau)
    try: xi,loc,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return np.quantile(ztr,tau)
    if beta<=0: return np.quantile(ztr,tau)
    q_ex=-beta*math.log(tau/pu) if abs(xi)<1e-6 else (beta/xi)*(((tau/pu)**(-xi))-1)
    return u-q_ex
def _llb(pp,k0,k1):
    if k0+k1==0: return 0.0
    if pp<=0: return 0.0 if k1==0 else -1e300
    if pp>=1: return 0.0 if k0==0 else -1e300
    return k0*math.log(1-pp)+k1*math.log(pp)
def kupiec(x,T,p):
    if x==0 or x==T: return None
    pi=x/T; return round(float(1-stats.chi2.cdf(max(-2*(_llb(p,T-x,x)-_llb(pi,T-x,x)),0),1)),3)
def christ(b,p):
    b=b.astype(int); T=len(b); x=int(b.sum()); n00=n01=n10=n11=0
    for i in range(1,T):
        a,c=b[i-1],b[i]
        if a==0 and c==0:n00+=1
        elif a==0 and c==1:n01+=1
        elif a==1 and c==0:n10+=1
        else:n11+=1
    if x==0: return None
    pi=x/T; pi0=n01/max(n00+n01,1); pi1=n11/max(n10+n11,1)
    lr=-2*(_llb(p,T-x,x)-_llb(pi,T-x,x))-2*(_llb(pi,n00+n10,n01+n11)-(_llb(pi0,n00,n01)+_llb(pi1,n10,n11)))
    return round(float(1-stats.chi2.cdf(max(lr,0),2)),3)
def nw_dm(d,lag=10):
    d=np.asarray(d,float); d=d[np.isfinite(d)]; T=len(d)
    if T<30: return None
    dd=d-d.mean(); v=np.mean(dd*dd)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(dd[k:]*dd[:-k])
    if v<=0: return None
    s=d.mean()/math.sqrt(v/T); return dict(DM=round(float(s),2),p=round(float(1-stats.norm.cdf(s)),4))
def analyze(r):
    from arch import arch_model
    y=r.values.astype(float); n=len(y); sp=int(n*0.6)
    if n<800: return None
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: return None
    tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); ztr=z[:sp]
    rk=float(stats.kurtosis(ztr[np.isfinite(ztr)],fisher=False))
    df=pd.DataFrame({'z':z}); df['logsig']=np.log(np.maximum(sig,1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1); df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    ZX=['logsig','zl1','absz5','zstd21']; df['idx']=np.arange(n); dd=df.dropna(); tr=dd[dd['idx']<sp]; te=dd[dd['idx']>=sp]
    if len(te)<60: return None
    ti=te['idx'].values; yte=y[ti]; sg=sig[ti]
    fhsq={t:np.quantile(ztr,t) for t in TAUS}; evtq={t:gpd_left_q(ztr,t) for t in TAIL}
    zq={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=200,max_depth=3,learning_rate=0.07).fit(tr[ZX].values,tr['z'].values).predict(te[ZX].values) for t in TAUS}
    Q={'garch_t':{t:mu+sg*stats.t.ppf(t,nu)/tsc for t in TAUS},'fhs':{t:mu+sg*fhsq[t] for t in TAUS},'hybrid':{t:mu+sg*zq[t] for t in TAUS},
       'hybrid_EVT':{t:(mu+sg*evtq[t]) if t in TAIL else (mu+sg*zq[t]) for t in TAUS}}
    res_={}
    for m in Q:
        pl=np.zeros(len(yte))
        for t in TAUS: pl+=pin(yte,Q[m][t],t)
        pl/=len(TAUS); es=np.mean([Q[m][t] for t in TAIL],axis=0); b99=(yte<Q[m][0.01]); b975=(yte<Q[m][0.025])
        res_[m]=dict(pinball=round(float(pl.mean()),4),ES975=round(float(es.mean()),3),
                     breach99=round(float(b99.mean()),4),kupiec99=kupiec(int(b99.sum()),len(yte),0.01),christ99=christ(b99,0.01),
                     breach975=round(float(b975.mean()),4),kupiec975=kupiec(int(b975.sum()),len(yte),0.025),christ975=christ(b975,0.025),_pl=pl)
    dm=nw_dm(res_['garch_t']['_pl']-res_['hybrid_EVT']['_pl'])
    for m in res_: res_[m].pop('_pl')
    return dict(resid_kurt=round(rk,1),n_oos=len(yte),DM_hybridEVT_vs_garch=dm,models=res_)
WIN=[('VIX','VIX Index','vol','log'),('VVIX','VVIX Index','vol','log'),('V2X','V2X Index','vol','log'),('MOVE','MOVE Index','rates_vol','log'),
     ('BALTIC_DRY','BDIY Index','freight','log'),('IG_OAS','LUACOAS Index','credit','diff'),('HY_OAS','LF98OAS Index','credit','diff'),
     ('ERCOT_POWER','ERN1 Comdty','power','diff'),('PJM_POWER','PW1 Comdty','power','diff'),
     ('SPX','SPX Index','equity_control','log'),('GOLD','GC1 Comdty','commodity_control','log')]
start=dt.date(2005,1,1); end=dt.date.today()
out={'note':'FRTB-grade winners table: full battery (GARCH-t/FHS/hybrid/hybrid+EVT) on nonparam-winning classes + controls. '
            'ES97.5 + Kupiec/Christoffersen at 99% AND 97.5% + DM(hybrid_EVT vs GARCH). Power/credit use price DIFFERENCES (fixes '
            'PJM log-return artifact). resid_kurt included.','per_asset':{}}
for nm,tk,cls,tf in WIN:
    try:
        s=series(tk,start,end)
        if s is None or len(s)<800: lg("%s NO DATA"%nm); continue
        r=(np.log(s/s.shift(1)).replace([np.inf,-np.inf],np.nan).dropna()*100.0) if tf=='log' else (s.diff().dropna())
        if tf=='diff' and cls=='power': r=r*1.0                      # power price change in native units
        a=analyze(r)
        if a is None: lg("%s SKIP"%nm); continue
        a['class']=cls; a['transform']=tf; out['per_asset'][nm]=a
        he=a['models']['hybrid_EVT']; gt=a['models']['garch_t']
        lg("%-11s [%s] rkurt %s | EVT pin %s K99 %s C99 %s K975 %s C975 %s | garch pin %s | DM %s  %.0fs"%(
            nm,cls,a['resid_kurt'],he['pinball'],he['kupiec99'],he['christ99'],he['kupiec975'],he['christ975'],gt['pinball'],a['DM_hybridEVT_vs_garch'],time.time()-t0))
        json.dump(out,open(os.path.join(P,"frtb_winners.json"),"w"),indent=2,default=str)
    except Exception as ex: lg("%s ERR %s"%(nm,str(ex)[:80]))
json.dump(out,open(os.path.join(P,"frtb_winners.json"),"w"),indent=2,default=str)
lg("DONE assets=%d %.0fs"%(len(out['per_asset']),time.time()-t0))
