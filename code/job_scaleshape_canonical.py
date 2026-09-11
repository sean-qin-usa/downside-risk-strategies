# job_scaleshape_canonical.py -- FATAL-2 FIX. ONE canonical scale-shape pipeline on the 30-stock
# TAQ panel. Every row is scored on the SAME names, SAME test rows, with the SAME dense 20-node ES
# integral, and ALL date-clustered DMs are taken against ONE benchmark: the realized (HHS) scale
# with an unconditional residual quantile. This replaces the split across two scripts:
#   rgarch_bench.py            -- simple RV-GARCH-X scale, closed-form ES, row-1 DM vs a DIFFERENT
#                                 (simple-realized) benchmark; produced the old daily-core DM 6.0/4.5.
#   realized_hybrid_experiment -- proper HHS scale but a SPARSE 2-3 node ES the main table retired.
# Here the realized rows use the proper Hansen-Huang-Shek Realized GARCH (measurement equation), the
# daily core (daily GARCH-t scale + EVT tail) is computed IN THIS SCRIPT on the same names, and ES for
# every row is the 20-node midpoint integral of that row's own quantile curve (matches the tab:frtb
# correction; retires the sparse average). DM is date-clustered Newey-West(5) vs rg_uncond; DM>0 worse.
import os, json, time, math, glob, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats, optimize
from arch import arch_model
from sklearn.ensemble import HistGradientBoostingRegressor
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True); os.chdir(P)
ALPHAS=[0.025,0.01]; NWLAG=5; SUBN=20; ZX=['logsig','zl1','absz5','zstd21','fracdn5']
def fz0(r,v,e,a):
    e=min(e,-1e-6); return (1.0/(a*e))*(1.0 if r<=v else 0.0)*(r-v) + v/e + math.log(-e) - 1.0
def gpd_left_q(ztr,tau,pu=0.05):
    u=np.quantile(ztr,pu); ex=u-ztr[ztr<u]; ex=ex[ex>0]
    if len(ex)<30: return float(np.quantile(ztr,tau))
    try: xi,loc,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return float(np.quantile(ztr,tau))
    if beta<=0: return float(np.quantile(ztr,tau))
    q_ex=-beta*math.log(tau/pu) if abs(xi)<1e-6 else (beta/xi)*(((tau/pu)**(-xi))-1)
    return float(u-q_ex)
def fit_realgarch(r,x,sp):
    # proper HHS log-linear Realized GARCH with measurement equation, Gaussian QML (as in realized_hybrid_experiment.py)
    r=np.asarray(r,float); lx=np.log(np.maximum(np.asarray(x,float),1e-10)); n=len(r); v0=max(np.var(r[:sp]),1e-6)
    def negll(th):
        om,be,ga,xi,phi,t1,t2,lsu,mu=th
        if not(0.0<=be<0.999) or lsu<-6 or lsu>4: return 1e12
        su2=math.exp(2*lsu); lh=math.log(v0); ll=0.0
        for k in range(sp):
            if k>0: lh=om+be*lh+ga*lx[k-1]
            if lh>25 or lh<-25: return 1e12
            h=math.exp(lh); z=(r[k]-mu)/math.sqrt(h)
            ll += 0.5*(lh+z*z)
            mx=xi+phi*lh+t1*z+t2*(z*z-1.0); u=lx[k]-mx
            ll += 0.5*(2*lsu+u*u/su2)
        return ll
    best=None
    for th0 in ([-0.1,0.6,0.35,0.0,1.0,-0.05,0.03,math.log(0.4),float(np.mean(r[:sp]))],
                [0.0,0.4,0.5,-0.2,0.8,-0.1,0.05,math.log(0.5),0.0]):
        try: res=optimize.minimize(negll,np.array(th0),method="Nelder-Mead",options={"maxiter":6000,"xatol":1e-4,"fatol":1e-4})
        except Exception: continue
        if best is None or res.fun<best.fun: best=res
    om,be,ga,xi,phi,t1,t2,lsu,mu=best.x
    lh=np.empty(n); lh[0]=math.log(v0)
    for k in range(1,n): lh[k]=om+be*lh[k-1]+ga*lx[k-1]
    lh=np.clip(lh,-25,25); return np.sqrt(np.exp(lh)), float(mu)
def daily_garch_t(y,sp):
    r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
    p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    n=len(y); e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    return np.sqrt(s2), mu

rm=pd.concat([pd.read_csv(f) for f in sorted(glob.glob("panel_rm_*.csv"))],ignore_index=True); rm['date']=pd.to_datetime(rm['date'])
r30=pd.read_csv("crsp_returns_30.csv"); r30['date']=pd.to_datetime(r30['date']); r30['ret']=pd.to_numeric(r30['ret'],errors='coerce')*100.0
RETBYTK={tk:g[['date','ret']].dropna() for tk,g in r30.groupby('ticker')}; NAMES=sorted(RETBYTK.keys())[:30]
lg("names=%d %.0fs"%(len(NAMES),time.time()-t0))

per={}; TR=[]
for tk in NAMES:
    g=RETBYTK[tk]; rvv=rm[rm.ticker==tk][['date','rv']].dropna()
    d=pd.merge(g,rvv,on='date',how='inner').sort_values('date')
    if len(d)<1200: continue
    y=d['ret'].values.astype(float); rv=d['rv'].values.astype(float)*1e4; dts=d['date'].values; n=len(y); sp=int(n*0.6)
    try:
        sig_r,mu_r=fit_realgarch(y,rv,sp); sig_d,mu_d=daily_garch_t(y,sp)
    except Exception as ex: lg("  fail %s %s"%(tk,str(ex)[:40])); continue
    zr=(y-mu_r)/np.maximum(sig_r,1e-6); zd=(y-mu_d)/np.maximum(sig_d,1e-6)
    df=pd.DataFrame({'y':y,'date':dts,'sig_r':sig_r,'sig_d':sig_d,'zr':zr}); df['mu_r']=mu_r; df['mu_d']=mu_d
    df['logsig']=np.log(np.maximum(df['sig_r'],1e-6)); df['zl1']=df['zr'].shift(1)
    df['absz5']=df['zr'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['zr'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['zr'].rolling(63,min_periods=30).apply(lambda s:stats.kurtosis(s,fisher=True),raw=True).shift(1)
    df['ask63']=df['zr'].rolling(63,min_periods=30).apply(lambda s:abs(stats.skew(s)),raw=True).shift(1)
    df['jump5']=df['zr'].abs().rolling(5,min_periods=3).max().shift(1)
    df['idx']=np.arange(n); dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    per[tk]=dict(tst=tst, ztr_r=trn['zr'].values, ztr_d=(d['ret'].values[:sp]-mu_d)/np.maximum(sig_d[:sp],1e-6))
    TR.append(trn[ZX+['zr']].rename(columns={'zr':'z'}))
    lg("  fit %s n=%d %.0fs"%(tk,n,time.time()-t0))
lg("pass1 %d names %.0fs"%(len(per),time.time()-t0))
TRc=pd.concat(TR,ignore_index=True); lg("pooled train rows=%d"%len(TRc))

SUB={a:[a*(j+0.5)/SUBN for j in range(SUBN)] for a in ALPHAS}
levels=sorted(set(list(ALPHAS)+[u for a in ALPHAS for u in SUB[a]]))
gbm={}
for t in levels:
    gbm[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRc[ZX].values,TRc['z'].values)
lg("GBM %d levels %.0fs"%(len(levels),time.time()-t0))

allsc=[per[tk]['tst'][['mk63','ask63','jump5']].assign(tk=tk,idx=per[tk]['tst']['idx']) for tk in per]
Sdf=pd.concat(allsc,ignore_index=True)
for c in ['mk63','ask63','jump5']: Sdf[c+'_p']=Sdf[c].rank(pct=True)
Sdf['score']=Sdf[['mk63_p','ask63_p','jump5_p']].max(axis=1); Sdf['scdec']=pd.qcut(Sdf['score'],10,labels=False,duplicates='drop')
scmap={(row.tk,int(row.idx)):int(row.scdec) for row in Sdf.itertuples()}

ROWS=['daily_core','rg_uncond','rg_evt','rg_shape','rg_hybrid']
byd={a:{m:{} for m in ROWS} for a in ALPHAS}; scal={a:{m:[] for m in ROWS} for a in ALPHAS}
bydecd={a:{m:{sd:{} for sd in range(10)} for m in ROWS} for a in ALPHAS}
for tk in per:
    tst=per[tk]['tst']; ztr_r=per[tk]['ztr_r']; ztr_d=per[tk]['ztr_d']; X=tst[ZX].values
    unc={u:float(np.quantile(ztr_r,u)) for u in levels}
    evtr={u:gpd_left_q(ztr_r,u) for u in levels}; evtd={u:gpd_left_q(ztr_d,u) for u in levels}
    shp={u:gbm[u].predict(X) for u in levels}
    for j,row in enumerate(tst.itertuples()):
        r=row.y; idx=int(row.idx); dd=str(row.date)[:10]; sd=scmap.get((tk,idx),-1)
        sig_r=row.sig_r; mu_r=row.mu_r; sig_d=row.sig_d; mu_d=row.mu_d
        for a in ALPHAS:
            sub=SUB[a]
            defs={
              'daily_core':(sig_d,mu_d, evtd[a], float(np.mean([evtd[u] for u in sub]))),
              'rg_uncond' :(sig_r,mu_r, unc[a],  float(np.mean([unc[u] for u in sub]))),
              'rg_evt'    :(sig_r,mu_r, evtr[a], float(np.mean([evtr[u] for u in sub]))),
              'rg_shape'  :(sig_r,mu_r, float(shp[a][j]), float(np.mean([float(shp[u][j]) for u in sub]))),
              'rg_hybrid' :(sig_r,mu_r, min(float(shp[a][j]),evtr[a]), float(np.mean([min(float(shp[u][j]),evtr[u]) for u in sub]))),
            }
            for m,(sg,mu,zq,zes) in defs.items():
                VaR=mu+sg*zq; ES=mu+sg*min(zes,zq-1e-6)
                L=fz0(r,VaR,ES,a); byd[a][m].setdefault(dd,[]).append(L); scal[a][m].append(L)
                if sd>=0: bydecd[a][m][sd].setdefault(dd,[]).append(L)
    lg("  scored %s %.0fs"%(tk,time.time()-t0))

def dm(ref,alt):
    ds=sorted(set(ref)&set(alt)); dif=np.array([np.mean(alt[d])-np.mean(ref[d]) for d in ds])
    if len(dif)<10: return 0.0,0.0,len(dif)
    m=dif.mean(); nD=len(dif); g0=dif.var()
    v=g0+2*sum((1-l/(NWLAG+1))*np.mean((dif[l:]-m)*(dif[:-l]-m)) for l in range(1,NWLAG+1))
    se=math.sqrt(max(v,1e-12)/nD); return float(m),float(m/se if se>0 else 0),nD
def dm_sub(ref_by,alt_by,decs):
    ref={}; alt={}
    for sd in decs:
        for d,v in ref_by[sd].items(): ref.setdefault(d,[]).extend(v)
        for d,v in alt_by[sd].items(): alt.setdefault(d,[]).extend(v)
    return dm(ref,alt)
OUT={'note':'FATAL-2 fix: ONE canonical scale-shape pipeline. 30 TAQ names, same test rows, dense 20-node '
     'ES for every row, all DMs date-clustered NW(5) vs rg_uncond (proper HHS realized scale + unconditional '
     'residual quantile). daily_core = daily GARCH-t scale + EVT tail (computed here, same names). DM>0 worse than rg_uncond.',
     'n_names':len(per),'per_alpha':{}}
for a in ALPHAS:
    A={'FZ0':{m:round(float(np.mean(scal[a][m])),4) for m in ROWS},'n_scored':int(len(scal[a]['rg_uncond'])),'DM_vs_rg_uncond':{}}
    for m in ROWS:
        if m=='rg_uncond': continue
        mm,st,nD=dm(byd[a]['rg_uncond'],byd[a][m]); A['DM_vs_rg_uncond'][m]={'dFZ0':round(mm,5),'DM':round(st,2),'n':nD}
    A['topdecile_DM_vs_rg_uncond']={}
    for decs,tag in ([[9],'d9'],[[7,8,9],'d789']):
        for m in ['rg_shape','rg_hybrid','daily_core']:
            mm,st,nD=dm_sub(bydecd[a]['rg_uncond'],bydecd[a][m],decs)
            A['topdecile_DM_vs_rg_uncond']['%s_%s'%(m,tag)]={'dFZ0':round(mm,5),'DM':round(st,2),'n':nD}
    OUT['per_alpha']['alpha_%g'%a]=A
    lg("alpha=%g "%a+json.dumps(A))
json.dump(OUT,open(os.path.join(P,"scaleshape_canonical_results.json"),"w"),indent=2)
lg("SCALESHAPEDONE %.0fs"%(time.time()-t0))
