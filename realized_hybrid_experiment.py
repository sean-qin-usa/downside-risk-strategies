# THE EXPERIMENT (GPT-5 review): replace ONLY Stage-1 scale (daily GARCH -> proper Hansen-Huang-Shek
# Realized GARCH with measurement equation), keep the paper's pooled state-conditioned shape learner +
# EVT + misspecification score, recompute standardized residuals, and test whether the SHAPE stage still
# adds FZ0 value conditional on a strong (realized) scale -- overall and in the top realized score decile.
# Four objects on the 30-stock TAQ panel, all on the realized-measure scale:
#   (1) rg_uncond  realized scale + unconditional residual quantile (FHS-on-realized)  [benchmark]
#   (2) rg_evt     realized scale + EVT (GPD) tail
#   (3) rg_shape   realized scale + pooled state-conditioned GBM shape quantile         [adds shape]
#   (4) rg_hybrid  realized scale + GBM shape (body) with EVT far tail (min)            [realized-hybrid]
import os, json, time, math, glob, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats, optimize
try:
    from sklearn.ensemble import HistGradientBoostingRegressor as QGBM; _HIST=True
except Exception:
    from sklearn.ensemble import GradientBoostingRegressor as QGBM; _HIST=False
t0=time.time(); lg=lambda s:print(s,flush=True)
ALPHAS=[0.025,0.01]; NWLAG=5; TAILT=[0.005,0.01,0.025]; ZX=['logsig','zl1','absz5','zstd21','fracdn5']
GRID={0.025:[0.005,0.01,0.025], 0.01:[0.005,0.01]}

rm=pd.concat([pd.read_csv(f) for f in sorted(glob.glob("panel_rm_*.csv"))],ignore_index=True); rm['date']=pd.to_datetime(rm['date'])
r30=pd.read_csv("crsp_returns_30.csv"); r30['date']=pd.to_datetime(r30['date']); r30['ret']=pd.to_numeric(r30['ret'],errors='coerce')*100.0
RETBYTK={tk:g[['date','ret']].dropna() for tk,g in r30.groupby('ticker')}; NAMES=sorted(RETBYTK.keys())[:int(os.environ.get('NMAX','30'))]
lg("names=%d hist_gbm=%s %.0fs"%(len(NAMES),_HIST,time.time()-t0))

def fz0(r,q,e,a):
    e=min(e,-1e-6); return (1.0/(a*e))*(1.0 if r<=q else 0.0)*(r-q) + q/e + math.log(-e) - 1.0
def gpd_left_q(ztr,tau,pu=0.05):
    u=np.quantile(ztr,pu); ex=u-ztr[ztr<u]; ex=ex[ex>0]
    if len(ex)<30: return float(np.quantile(ztr,tau))
    try: xi,loc,beta=stats.genpareto.fit(ex,floc=0)
    except Exception: return float(np.quantile(ztr,tau))
    if beta<=0: return float(np.quantile(ztr,tau))
    q_ex=-beta*math.log(tau/pu) if abs(xi)<1e-6 else (beta/xi)*(((tau/pu)**(-xi))-1)
    return float(u-q_ex)
def mkQ(t):
    if _HIST: return QGBM(loss="quantile",quantile=t,max_iter=300,max_depth=3,learning_rate=0.05,min_samples_leaf=200,l2_regularization=1.0)
    return QGBM(loss="quantile",alpha=t,n_estimators=300,max_depth=3,learning_rate=0.05,min_samples_leaf=200)

# ---- proper HHS log-linear Realized GARCH (measurement equation), Gaussian QML ----
def fit_realgarch(r,x,sp):
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
    lh=np.clip(lh,-25,25); return np.sqrt(np.exp(lh)), float(mu), (float(be),float(ga))

per={}; TR=[]; betas=[]; gammas=[]
for tk in NAMES:
    g=RETBYTK[tk]; rr=rm[rm.ticker==tk][['date','rv']].dropna()
    d=pd.merge(g,rr,on='date',how='inner').sort_values('date')
    if len(d)<1200: continue
    y=d['ret'].values.astype(float); rv=d['rv'].values.astype(float)*1e4; dts=d['date'].values; n=len(y); sp=int(n*0.6)
    try: sig,mu,(be,ga)=fit_realgarch(y,rv,sp)
    except Exception as ex: lg("  rg fail %s %s"%(tk,str(ex)[:40])); continue
    betas.append(be); gammas.append(ga)
    z=(y-mu)/np.maximum(sig,1e-6)
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts}); df['mu']=mu
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).apply(lambda s:stats.kurtosis(s,fisher=True),raw=True).shift(1)
    df['ask63']=df['z'].rolling(63,min_periods=30).apply(lambda s:abs(stats.skew(s)),raw=True).shift(1)
    df['jump5']=df['z'].abs().rolling(5,min_periods=3).max().shift(1)
    df['idx']=np.arange(n); dd=df.dropna(subset=ZX)
    trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    per[tk]=dict(tst=tst,ztr=trn['z'].values,sp=sp); TR.append(trn[ZX+['z']])
    lg("  fit %s n=%d be=%.2f ga=%.2f %.0fs"%(tk,n,be,ga,time.time()-t0))
lg("pass1 %d names %.0fs; beta med=%.2f gamma med=%.2f"%(len(per),time.time()-t0,np.median(betas),np.median(gammas)))

TRc=pd.concat(TR,ignore_index=True); lg("pooled train rows=%d"%len(TRc))
gbm={}
for t in TAILT:
    m=mkQ(t); m.fit(TRc[ZX].values,TRc['z'].values); gbm[t]=m
lg("GBM(%s) fit %.0fs"%("hist" if _HIST else "grad",time.time()-t0))

# realized-residual score deciles (pooled percentiles, max of three)
allsc=[per[tk]['tst'][['mk63','ask63','jump5']].assign(tk=tk,idx=per[tk]['tst']['idx']) for tk in per]
S=pd.concat(allsc,ignore_index=True)
for c in ['mk63','ask63','jump5']: S[c+'_p']=S[c].rank(pct=True)
S['score']=S[['mk63_p','ask63_p','jump5_p']].max(axis=1); S['scdec']=pd.qcut(S['score'],10,labels=False,duplicates='drop')
scmap={(row.tk,int(row.idx)):int(row.scdec) for row in S.itertuples()}

MODELS=['rg_uncond','rg_evt','rg_shape','rg_hybrid']
byd={a:{m:{} for m in MODELS} for a in ALPHAS}; scal={a:{m:[] for m in MODELS} for a in ALPHAS}
bydec={a:{m:{sd:[] for sd in range(10)} for m in MODELS} for a in ALPHAS}
bydecd={a:{m:{sd:{} for sd in range(10)} for m in MODELS} for a in ALPHAS}
for tk in per:
    tst=per[tk]['tst']; ztr=per[tk]['ztr']; X=tst[ZX].values
    unc={u:float(np.quantile(ztr,u)) for u in TAILT}; evt={u:gpd_left_q(ztr,u) for u in TAILT}
    shp={u:gbm[u].predict(X) for u in TAILT}
    rows=list(tst.itertuples())
    for j,row in enumerate(rows):
        r=row.y; sig=row.sig; mu=row.mu; idx=int(row.idx); dd=str(row.date)[:10]; sd=scmap.get((tk,idx),-1)
        for a in ALPHAS:
            grid=GRID[a]
            sh_a=float(shp[a][j]); sh_grid=[float(shp[u][j]) for u in grid]
            qz={'rg_uncond':(unc[a],float(np.mean([unc[u] for u in grid]))),
                'rg_evt':(evt[a],float(np.mean([evt[u] for u in grid]))),
                'rg_shape':(sh_a,float(np.mean(sh_grid))),
                'rg_hybrid':(min(sh_a,evt[a]),float(np.mean([min(sh_grid[i],evt[grid[i]]) for i in range(len(grid))])))}
            for m,(zq,zes) in qz.items():
                VaR=mu+sig*zq; ES=mu+sig*min(zes,zq-1e-6)
                L=fz0(r,VaR,ES,a); byd[a][m].setdefault(dd,[]).append(L); scal[a][m].append(L)
                if sd>=0: bydec[a][m][sd].append(L); bydecd[a][m][sd].setdefault(dd,[]).append(L)
    lg("  scored %s %.0fs"%(tk,time.time()-t0))

def dm(ref,alt):
    ds=sorted(set(ref)&set(alt)); dif=np.array([np.mean(alt[d])-np.mean(ref[d]) for d in ds])
    if len(dif)<10: return 0.0,0.0,len(dif)
    m=dif.mean(); nD=len(dif); g0=dif.var()
    v=g0+2*sum((1-l/(NWLAG+1))*np.mean((dif[l:]-m)*(dif[:-l]-m)) for l in range(1,NWLAG+1))
    se=math.sqrt(max(v,1e-12)/nD); return float(m),float(m/se if se>0 else 0),nD
out={'note':'Realized-hybrid experiment (GPT test). proper HHS Realized GARCH scale; pooled GBM shape + EVT + score on realized residuals. Key: rg_shape/rg_hybrid vs rg_uncond overall and in top score decile (9). Negative DM = beats rg_uncond.','n_names':len(per),'hist_gbm':_HIST,'per_alpha':{}}
for a in ALPHAS:
    A={'FZ0_overall':{m:round(float(np.mean(scal[a][m])),4) for m in MODELS},'DM_vs_rg_uncond':{}}
    for m in MODELS:
        if m=='rg_uncond': continue
        mm,st,nD=dm(byd[a]['rg_uncond'],byd[a][m]); A['DM_vs_rg_uncond'][m]={'dFZ0':round(mm,5),'DM':round(st,2),'n':nD}
    A['FZ0_topdecile9']={m:round(float(np.mean(bydec[a][m][9])),4) if bydec[a][m][9] else None for m in MODELS}
    A['FZ0_botdecile0']={m:round(float(np.mean(bydec[a][m][0])),4) if bydec[a][m][0] else None for m in MODELS}
    def dm_sub(ref_by,alt_by,decs):
        ref={}; alt={}
        for sd in decs:
            for d,v in ref_by[sd].items(): ref.setdefault(d,[]).extend(v)
            for d,v in alt_by[sd].items(): alt.setdefault(d,[]).extend(v)
        return dm(ref,alt)
    A['topdecile_DM']={}
    for decs,tag in ([[9],'d9'],[[8,9],'d89'],[[7,8,9],'d789']):
        for m in ['rg_shape','rg_hybrid']:
            mm,st,nD=dm_sub(bydecd[a]['rg_uncond'],bydecd[a][m],decs)
            A['topdecile_DM']['%s_%s'%(m,tag)]={'dFZ0':round(mm,5),'DM':round(st,2),'n':nD}
    A['shapeGain_uncond_minus_hybrid_by_decile']={sd:(round(float(np.mean(bydec[a]['rg_uncond'][sd]))-float(np.mean(bydec[a]['rg_hybrid'][sd])),4) if bydec[a]['rg_uncond'][sd] and bydec[a]['rg_hybrid'][sd] else None) for sd in range(10)}
    out['per_alpha']['alpha_%g'%a]=A
json.dump(out,open("realized_hybrid_results.json","w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
