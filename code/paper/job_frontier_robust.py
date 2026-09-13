# job_frontier_robust.py -- DECISIVE EXPERIMENT: is the top-decile misspecification-frontier
# edge genuine residual-shape value, or GARCH(1,1) post-outlier variance overshoot?
#
# Referee hypothesis (JFEC AE sim): the score's top decile follows a ~6-sigma residual; a
# jump-robust GARCH that bounds the squared-innovation news term would NOT overshoot, so its
# residuals lose the post-jump kurtosis and the flexible edge collapses -> the "misspecification
# score" is a daily-scale overshoot artifact, not innovation-shape misspecification.
#
# TEST: rebuild the frontier three ways, on the SAME 200-name design panel and pipeline as
# job_composite.py (GARCH(1,1)-t filter, pooled HistGBM residual-quantile, 11 tau, per-date DM):
#   (1) STD  : flexible engine vs GARCH-t, sorted by std-filter mk63     [the paper's frontier]
#   (2) ROB  : flexible engine vs jump-robust GARCH-t, everything (scale, score, engine, bench)
#              rebuilt on the robust filter, sorted by robust-filter mk63 [the decisive test]
#   (3) MECH : jump-robust GARCH-t vs standard GARCH-t, sorted by std mk63
#              (does the robust filter help MOST in the top decile? = the AE's prediction)
# Robust filter = BIP/bounded-news GARCH: news_{t-1} = min(e^2_{t-1}, K * sigma^2_{t-1}),
# capping a shock at sqrt(K) sigma (K=9 -> 3 sigma; K=16 -> 4 sigma sensitivity).
# If ROB top-decile edge/DM SURVIVES -> shape story defended. If it collapses -> reframe.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; t0=time.time(); lg=lambda s:print(s,flush=True)
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

def build_feats(y,sig,mu,dts):
    z=(y-mu)/np.maximum(sig,1e-6)
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1)
    df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1)
    df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mk63']=df['z'].rolling(63,min_periods=30).kurt().shift(1)
    return df

def run_filter(y,sp,om,al,be,mu,robust,K=9.0):
    e0=y-mu; n=len(y); s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n):
        news=e0[k-1]**2
        if robust: news=min(news, K*s2[k-1])
        s2[k]=max(om+al*news+be*s2[k-1],1e-8)
    return np.sqrt(s2)

def build_panel(K=9.0):
    TR_std=[]; TR_rob=[]; rows=[]
    for pn in names:
        g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
        if n<1500: continue
        sp=int(n*0.6); cp=int(sp*0.75)
        try:
            r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
            pp=r1.params; om,al,be,mu=float(pp['omega']),float(pp['alpha[1]']),float(pp['beta[1]']),float(pp.get('mu',0)); nu=float(pp.get('nu',8))
        except Exception: continue
        tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
        sig_s=run_filter(y,sp,om,al,be,mu,robust=False)
        sig_r=run_filter(y,sp,om,al,be,mu,robust=True,K=K)
        ds=build_feats(y,sig_s,mu,dts); dr=build_feats(y,sig_r,mu,dts)
        for df in (ds,dr): df['idx']=np.arange(n)
        keep=ZX+['mk63']
        ds2=ds.dropna(subset=keep); dr2=dr.dropna(subset=keep)
        common=np.intersect1d(ds2['idx'].values,dr2['idx'].values)
        ds2=ds2[ds2['idx'].isin(common)]; dr2=dr2[dr2['idx'].isin(common)]
        trn_s=ds2[ds2['idx']<cp]; trn_r=dr2[dr2['idx']<cp]
        tst_s=ds2[ds2['idx']>=sp]; tst_r=dr2[dr2['idx']>=sp]
        if len(tst_s)<60: continue
        TR_std.append(trn_s[ZX+['z']]); TR_rob.append(trn_r[ZX+['z']])
        t=pd.DataFrame({'permno':pn,'date':tst_s['date'].values,'y':tst_s['y'].values,
            'sig_s':tst_s['sig'].values,'sig_r':tst_r['sig'].values,
            'mk_s':tst_s['mk63'].values,'mk_r':tst_r['mk63'].values,
            'mu':mu,'nu':nu,'tsc':tsc})
        # feature matrices aligned to test rows for each filter
        for c in ZX: t['s_'+c]=tst_s[c].values
        for c in ZX: t['r_'+c]=tst_r[c].values
        rows.append(t)
    TE=pd.concat(rows).reset_index(drop=True)
    return TE, pd.concat(TR_std), pd.concat(TR_rob)

def gbm_predict(TRzc, Xtest):
    out={}
    for t in TAUS:
        out[t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,
                learning_rate=0.06,random_state=0).fit(TRzc[ZX].values,TRzc['z'].values).predict(Xtest)
    return out

def pinball_engine(Y,SIG,MU,ZQ):
    pl=np.zeros(len(Y))
    for t in TAUS: pl+=pin(Y,MU+SIG*ZQ[t],t)
    return pl/len(TAUS)

def pinball_garch(Y,SIG,MU,NU,TSC):
    pl=np.zeros(len(Y))
    for t in TAUS: pl+=pin(Y,MU+SIG*stats.t.ppf(t,NU)/TSC,t)
    return pl/len(TAUS)

def frontier(d, base, score, di, tag):
    # edge = mean(base - alt)/mean(base); positive => alt better than base
    out={'tag':tag}
    def edge(mask):
        if mask.sum()<30: return None
        gg=pd.DataFrame({'d':d[mask],'dt':di[mask]}).groupby('dt')['d'].mean()
        return {'edge_pct':round(100*float(d[mask].mean())/float(base[mask].mean()),3),
                'DM':nw_t(gg.values),'n':int(mask.sum())}
    m=np.isfinite(score)
    rk=np.full(len(score),-1); rk[m]=pd.qcut(pd.Series(score[m]),10,labels=False,duplicates='drop').values+1
    out['overall']=edge(m)
    out['top_decile']=edge(rk==10)
    out['bottom_decile']=edge(rk==1)
    prof={}
    for dd in range(1,11):
        e=edge(rk==dd); prof[dd]=e['edge_pct'] if e else None
    out['decile_profile']=prof
    return out

def full_run(K):
    lg("=== K=%.0f (%.1f-sigma cap) ==="%(K,math.sqrt(K)))
    TE,TRs,TRr=build_panel(K=K)
    lg("panel %d names %d rows %.0fs"%(TE.permno.nunique(),len(TE),time.time()-t0))
    Xs=TE[['s_'+c for c in ZX]].values; Xs=pd.DataFrame(Xs,columns=ZX)
    Xr=TE[['r_'+c for c in ZX]].values; Xr=pd.DataFrame(Xr,columns=ZX)
    ZQs=gbm_predict(TRs,Xs.values); lg("  std GBM %.0fs"%(time.time()-t0))
    ZQr=gbm_predict(TRr,Xr.values); lg("  rob GBM %.0fs"%(time.time()-t0))
    Y=TE['y'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
    SIGs=TE['sig_s'].values; SIGr=TE['sig_r'].values
    plEs=pinball_engine(Y,SIGs,MU,ZQs); plGs=pinball_garch(Y,SIGs,MU,NU,TSC)
    plEr=pinball_engine(Y,SIGr,MU,ZQr); plGr=pinball_garch(Y,SIGr,MU,NU,TSC)
    di,_=pd.factorize(pd.to_datetime(TE['date'].values),sort=True); di=np.asarray(di)
    res={}
    # (1) STD frontier: engine_std vs GARCH-t_std, by std mk63
    res['STD_engine_vs_garch']=frontier(plGs-plEs, plGs, TE['mk_s'].values, di, "engine_std - garch_std by std mk63")
    # (2) ROB frontier (decisive): engine_rob vs GARCH-t_rob, by robust mk63
    res['ROB_engine_vs_garch']=frontier(plGr-plEr, plGr, TE['mk_r'].values, di, "engine_rob - garch_rob by rob mk63")
    # (3) MECH: robust GARCH vs standard GARCH, by std mk63 (does robust help most in top decile?)
    res['MECH_robgarch_vs_stdgarch']=frontier(plGs-plGr, plGs, TE['mk_s'].values, di, "garch_rob - garch_std by std mk63")
    # (4) cross-check: engine_rob vs GARCH-t_STD by robust mk63 (flexible+robust scale vs paper benchmark)
    res['ROBENGINE_vs_stdgarch']=frontier(plGs-plEr, plGs, TE['mk_r'].values, di, "engine_rob - garch_std by rob mk63")
    res['levels']={'plE_std':round(float(plEs.mean()),5),'plG_std':round(float(plGs.mean()),5),
                   'plE_rob':round(float(plEr.mean()),5),'plG_rob':round(float(plGr.mean()),5)}
    return res

OUT={'note':'Decisive jump-robust GARCH frontier test. ROB_engine_vs_garch top_decile is the '
     'key number: if edge_pct and DM stay large, the top-decile edge is NOT standard-GARCH '
     'post-outlier overshoot (shape story defended); if they collapse toward 0, the score was '
     'a daily-scale overshoot artifact (reframe). MECH shows how much of the raw frontier the '
     'robust filter alone explains. Robust=BIP bounded-news GARCH, news=min(e^2, K*sig^2).',
     'n_names_target':200,'taus':TAUS}
OUT['K9_3sigma']=full_run(9.0)
OUT['K16_4sigma']=full_run(16.0)
json.dump(OUT,open(os.path.join(P,"frontier_robust_results.json"),"w"),indent=1)
lg("DONE %.0fs -> frontier_robust_results.json"%(time.time()-t0))
