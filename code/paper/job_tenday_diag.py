# job_tenday_diag.py -- why the ten-day edge is era-dependent (Section 5.2, Figure OA.3).
#
# Same purged pipeline as job_stress_dm.py / job_stress_purged.py: per-name GARCH(1,1)-t fitted on
# the first 60% of each name's history, filtered forward, features FEAT, h-day cumulative label,
# training labels whose window crosses the split purged, pooled HistGradientBoosting quantile
# model ("direct") on the test rows. Design era crsp_panel_returns.csv (>=1800 obs, 150 names),
# holdout holdout_panel_2000_2013.csv (>=1500 obs, 200 names). h = 10.
#
# Adds three benchmarks that the paper's sqrt(h)-scaled GARCH-t lacks, and three diagnostics.
#   sqrt_h   : mu*h + sqrt(h)*sigma_t * t_q(nu)/tsc                (the paper's benchmark)
#   iter_var : mu*h + sqrt(V_h)*t_q(nu)/tsc, V_h = sum_k E_t[sigma^2_{t+k}]  (iterated variance, one-day t shape)
#   mc_t     : empirical quantile of NPATH simulated h-day sums from the fitted GARCH-t (iterated GARCH-t)
#   fhs_path : same paths with standardized residuals bootstrapped from the training window (iterated FHS)
#   direct   : the pooled GBM of the paper
# D1  term-structure ratio V_h/(h*sigma^2_t) by calendar year, both eras.
# D2  1% and 2.5% ten-day coverage by calendar year for every model, both eras.
# D4  pinball over TAUS and per-date DM (NW lag 10) of direct against each benchmark, and of sqrt_h
#     against each iterated benchmark; a non-overlapping subsample (every h-th test date) repeats the DM.
# Mechanism 3 (design-era tuning) is not tested here: the GBM hyperparameters were frozen before the
# holdout was opened and are identical in both eras, so the only design-era degree of freedom left is
# the overlap in the labels, which the non-overlapping subsample addresses.
#
# PREDICTIONS, written before the run (2026-09-22):
#   P1 (benchmark got better): D1 ratio well below 1 in 2020-2024, near 1 in 2008-2009; direct's edge
#      over iter_var and mc_t in the design era much smaller than its edge over sqrt_h, and within
#      noise in the holdout.
#   P2 (direct tail cannot extrapolate): direct 1% coverage in 2008-2009 well above 1% while
#      sqrt_h/mc_t stay near 1%; other years fine.
#   P3 (overlap inflation): DM on the non-overlapping subsample lower in absolute value than the
#      overlapping DM by more than the sqrt(1/h) loss of sample would explain.
#   Expected outcome: P1 and P2 confirmed, P3 not; if the design-era edge over mc_t or fhs_path
#      is within noise, the ten-day extension is a statement about sqrt(h) scaling and the text
#      should say so.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
P=os.environ.get("GBC_PROJ",os.environ.get("GBC_PROJECT_DIR",r"C:\Users\OWNER\Claude\Projects\GBC Project"))
t0=time.time(); lg=lambda s:print(s,flush=True)
H=10; NPATH=4000; SEED=2022
TAUS=[0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
FEAT=['prv5','prv21','rv63','logsig','absz5']
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
def nw_t(x,l=10):
    x=np.asarray(x,float); x=x[np.isfinite(x)]; n=len(x)
    if n<30: return None
    d=x-x.mean(); v=np.mean(d*d)
    for k in range(1,l+1): v+=2*(1-k/(l+1))*np.mean(d[k:]*d[:-k])
    return round(float(x.mean()/math.sqrt(max(v/n,1e-16))),2)

def simulate(s2_0,om,al,be,mu,draw,rng):
    """h-day sums of simulated returns from each row's current variance; draw(size)->unit-variance innovations."""
    n=len(s2_0); tot=np.zeros((n,NPATH)); s2=np.repeat(s2_0[:,None],NPATH,axis=1)
    for k in range(H):
        z=draw((n,NPATH)); e=np.sqrt(s2)*z; tot+=mu+e; s2=np.maximum(om+al*e*e+be*s2,1e-8)
    return tot

def run_era(name,csv,minobs,ncap):
    rng=np.random.default_rng(SEED)
    rr=pd.read_csv(csv,dtype={'permno':'int32'})
    rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
    rr=rr.dropna(subset=['ret'])
    cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=minobs].index.tolist()[:ncap]
    TRr=[]; TEr=[]; nfit=0
    for pn in names:
        g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
        if n<minobs: continue
        sp=int(n*0.6)
        try:
            r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
            p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
        except Exception: continue
        nfit+=1
        e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
        for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
        sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
        ycum=pd.Series(y).rolling(H).sum().shift(-(H-1)).values
        df=pd.DataFrame({'yc':ycum,'sig':sig,'date':dts,'idx':np.arange(n)})
        df['prv5']=pd.Series(y).rolling(5,min_periods=3).std().shift(1); df['prv21']=pd.Series(y).rolling(21,min_periods=8).std().shift(1)
        df['rv63']=pd.Series(y).rolling(63,min_periods=20).std().shift(1); df['logsig']=np.log(np.maximum(sig,1e-6))
        df['absz5']=pd.Series(np.abs(z)).rolling(5,min_periods=3).mean().shift(1)
        df['mu']=mu; df['nu']=nu; df['tsc']=tsc
        dd=df.dropna(subset=FEAT+['yc'])
        trn=dd[dd['idx']<sp-(H-1)]
        tst=dd[dd['idx']>=sp].copy()
        if len(tst)<60: continue
        # iterated variance, closed form: E_t[s2_{t+k}] = sbar2 + (al+be)^(k-1) (s2_t - sbar2)
        s2t=tst['sig'].values**2; per=al+be
        if per<1:
            sbar2=om/(1-per); Vh=np.zeros(len(tst))
            for k in range(1,H+1): Vh+=sbar2+per**(k-1)*(s2t-sbar2)
        else: Vh=H*s2t
        tst['Vh']=Vh
        # simulated paths: GARCH-t innovations and bootstrapped training residuals
        ztr=z[:sp]; ztr=ztr[np.isfinite(ztr)]
        draw_t=lambda size: rng.standard_t(nu,size=size)/tsc
        draw_f=lambda size: rng.choice(ztr,size=size,replace=True)
        pt=simulate(s2t,om,al,be,mu,draw_t,rng); pf=simulate(s2t,om,al,be,mu,draw_f,rng)
        for t in TAUS:
            tst['mc_%g'%t]=np.quantile(pt,t,axis=1); tst['fhs_%g'%t]=np.quantile(pf,t,axis=1)
        del pt,pf
        tst['permno']=pn
        TRr.append(trn[FEAT+['yc']]); TEr.append(tst)
        if nfit%25==0: lg("  %s: %d names %.0fs"%(name,nfit,time.time()-t0))
    TR=pd.concat(TRr); TE=pd.concat(TEr).reset_index(drop=True)
    lg("%s panel: %d names, %d test rows, %d train rows %.0fs"%(name,TE['permno'].nunique(),len(TE),len(TR),time.time()-t0))
    Y=TE['yc'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values; VH=TE['Vh'].values
    Q={m:{} for m in ['sqrt_h','iter_var','mc_t','fhs_path','direct']}
    for t in TAUS:
        tq=stats.t.ppf(t,NU)/TSC
        Q['sqrt_h'][t]=MU*H+math.sqrt(H)*SIG*tq
        Q['iter_var'][t]=MU*H+np.sqrt(VH)*tq
        Q['mc_t'][t]=TE['mc_%g'%t].values; Q['fhs_path'][t]=TE['fhs_%g'%t].values
        Q['direct'][t]=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TR[FEAT].values,TR['yc'].values).predict(TE[FEAT].values)
    lg("%s: GBM done %.0fs"%(name,time.time()-t0))
    PL={m:np.mean([pin(Y,Q[m][t],t) for t in TAUS],axis=0) for m in Q}
    dates=TE['date'].values; years=pd.DatetimeIndex(dates).year
    def dm(a,b,mask=None):
        d=PL[a]-PL[b]
        if mask is not None: d=d[mask]; dts=dates[mask]
        else: dts=dates
        s=pd.DataFrame({'d':d,'date':dts}).groupby('date')['d'].mean(); return nw_t(s.values)
    ud=np.sort(np.unique(dates)); keep=set(ud[::H]); nov=np.isin(dates,list(keep))
    out={'n_names':int(TE['permno'].nunique()),'n_test':int(len(Y)),'n_dates':int(len(ud)),'n_dates_nonoverlap':int(len(keep)),
         'pinball':{m:round(float(PL[m].mean()),4) for m in PL},
         'edge_pct_direct_vs':{m:round(100*float((PL[m]-PL['direct']).mean())/float(PL[m].mean()),2) for m in PL if m!='direct'},
         'DM_direct_vs':{m:dm(m,'direct') for m in PL if m!='direct'},
         'DM_direct_vs_nonoverlap':{m:dm(m,'direct',nov) for m in PL if m!='direct'},
         'edge_pct_sqrt_h_vs':{m:round(100*float((PL['sqrt_h']-PL[m]).mean())/float(PL['sqrt_h'].mean()),2) for m in ['iter_var','mc_t','fhs_path']},
         'DM_sqrt_h_vs':{m:dm('sqrt_h',m) for m in ['iter_var','mc_t','fhs_path']},
         'coverage_all':{m:{'1%':round(float((Y<=Q[m][0.01]).mean()),4),'2.5%':round(float((Y<=Q[m][0.025]).mean()),4)} for m in Q},
         'D1_term_structure_ratio_by_year':{},'D2_coverage_by_year':{},'D4_edge_pct_direct_vs_sqrt_h_by_year':{}}
    ratio=VH/(H*SIG**2)
    for yr in sorted(set(years)):
        mk=years==yr
        out['D1_term_structure_ratio_by_year'][int(yr)]={'mean':round(float(ratio[mk].mean()),4),'p10':round(float(np.quantile(ratio[mk],0.1)),4),'n':int(mk.sum())}
        out['D2_coverage_by_year'][int(yr)]={m:{'1%':round(float((Y[mk]<=Q[m][0.01][mk]).mean()),4),'2.5%':round(float((Y[mk]<=Q[m][0.025][mk]).mean()),4)} for m in Q}
        out['D4_edge_pct_direct_vs_sqrt_h_by_year'][int(yr)]=round(100*float((PL['sqrt_h'][mk]-PL['direct'][mk]).mean())/float(PL['sqrt_h'][mk].mean()),2)
    return out

OUT={'note':'Ten-day (h=10) diagnostics for Section 5.2 / Figure OA.3 under the purged pipeline of job_stress_dm.py. Benchmarks: sqrt_h (paper), iter_var (closed-form iterated GARCH variance, one-day t shape), mc_t (4000 simulated GARCH-t paths), fhs_path (4000 bootstrap-residual paths), direct (pooled GBM). edge_pct>0 = first model worse than second. DM = per-date NW(10) t-stat of first minus second loss; nonoverlap = every 10th test date. D1 = model-implied V_h/(h sigma_t^2) by year. D2 = coverage by year at 1% and 2.5%. Predictions in the script header.',
     'h':H,'npath':NPATH,'seed':SEED,'taus':TAUS}
OUT['design_2014_2024']=run_era('design',os.path.join(P,"crsp_panel_returns.csv"),1800,150)
json.dump(OUT,open(os.path.join(P,"tenday_diag_results.json"),"w"),indent=2)
OUT['holdout_2000_2013']=run_era('holdout',os.path.join(P,"holdout_panel_2000_2013.csv"),1500,200)
json.dump(OUT,open(os.path.join(P,"tenday_diag_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0))
for era in ['design_2014_2024','holdout_2000_2013']:
    o=OUT[era]; lg(era); lg("  pinball %s"%o['pinball']); lg("  direct edge %s DM %s nonoverlap %s"%(o['edge_pct_direct_vs'],o['DM_direct_vs'],o['DM_direct_vs_nonoverlap']))
    lg("  sqrt_h vs iterated %s DM %s"%(o['edge_pct_sqrt_h_vs'],o['DM_sqrt_h_vs'])); lg("  coverage %s"%o['coverage_all'])
    lg("  D1 %s"%{y:v['mean'] for y,v in o['D1_term_structure_ratio_by_year'].items()})
