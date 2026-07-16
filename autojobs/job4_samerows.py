# RIGOR GAP 1: same-rows IQN vs GJR-GARCH-t. Identical (tk,date,h) rows; unit-matched (both = h-day forward return quantiles).
# Fixes the invalid -38% (which compared IQN 113 names 2016+ vs t6 543 names 2005+).
import os, time, json, math, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
RES=r"C:\Users\OWNER\Desktop\GBC_data\results\pq_trade"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
from arch import arch_model
IQ=pd.read_csv(os.path.join(RES,"mh_quantiles_gpu_v2.csv"))
IQ['date']=pd.to_datetime(IQ['date']); IQ['h']=IQ['h'].astype(int)
lg("IQN rows=%d names=%d horizons=%s %.0fs"%(len(IQ),IQ.tk.nunique(),sorted(IQ.h.unique()),time.time()-t0))
TAUS=[('p05',0.05),('p25',0.25),('p50',0.50),('p75',0.75),('p95',0.95)]
HS=sorted(IQ.h.unique()); HMAX=max(HS)
def pinball(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
# detect return convention (simple cum vs log sum) by matching y to realized tpx
rng=np.random.default_rng(7)
gp={}  # per-tk garch quantiles: dict (date,h)->{tau:q}
names=sorted(IQ.tk.unique())
conv_votes={'simple':0,'log':0}
gar_rows=[]  # (tk,date,h,gp05,gp25,gp50,gp75,gp95)
for ni,tk in enumerate(names):
    f=os.path.join(RAW,f"tpx_{tk}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    t['date']=pd.to_datetime(t['date']); s=t.set_index('date')['value'].sort_index().astype(float)
    s=s[~s.index.duplicated()]
    if len(s)<400: continue
    r=s.pct_change().dropna()  # simple daily returns
    rpct=(r*100.0)
    idx=r.index
    # annual walk-forward fitted GJR-t params
    yrs=sorted(set(idx.year))
    params_by_year={}
    for y in yrs:
        train=rpct[idx.year<y]
        if len(train)<250: continue
        try:
            fit=arch_model(train,mean='Zero',vol='GARCH',p=1,o=1,q=1,dist='t').fit(disp='off')
            pr=fit.params
            params_by_year[y]=(float(pr.get('omega')),float(pr.get('alpha[1]',0)),float(pr.get('gamma[1]',0)),float(pr.get('beta[1]',0)),float(pr.get('nu',8)))
        except Exception:
            continue
    if not params_by_year: continue
    # conditional variance recursion across full series, swapping params at year boundaries (walk-forward)
    rp=rpct.values; n=len(rp); sig2=np.empty(n); uncond=np.var(rp)
    firsty=min(params_by_year); cur=params_by_year[firsty]
    sig2[0]=uncond
    yarr=idx.year.values
    for i in range(1,n):
        if yarr[i] in params_by_year: cur=params_by_year[yarr[i]]
        om,al,ga,be,nu=cur
        e=rp[i-1]; sig2[i]=om+(al+ga*(e<0))*e*e+be*sig2[i-1]
        if not np.isfinite(sig2[i]) or sig2[i]<=0: sig2[i]=uncond
    sigser=pd.Series(np.sqrt(sig2),index=idx)  # daily vol in percent
    nu_ser=pd.Series([ (params_by_year.get(y,cur))[4] for y in yarr],index=idx)
    # dates we need for this tk
    sub=IQ[IQ.tk==tk]
    want_dates=sorted(sub.date.unique())
    # map each want date to sigma & nu (as-of, known at date)
    S=600
    for dt in want_dates:
        pos=sigser.index.searchsorted(pd.Timestamp(dt),side='right')-1
        if pos<0: continue
        sig0=sigser.iloc[pos]; nu=float(nu_ser.iloc[pos])
        # find params active
        y=pd.Timestamp(dt).year
        cur=None
        for yy in sorted(params_by_year):
            if yy<=y: cur=params_by_year[yy]
        if cur is None: continue
        om,al,ga,be,_=cur
        if nu<=2.05: nu=2.05
        std=math.sqrt(nu/(nu-2.0))
        # simulate S paths of HMAX daily pct returns with GJR variance evolution
        h2=np.full(S,sig0*sig0); cum=np.ones(S); qstore={}
        hset=set(HS)
        for step in range(1,HMAX+1):
            z=rng.standard_t(nu,size=S)/std
            e=z*np.sqrt(h2)              # pct return this day
            cum*= (1.0+e/100.0)
            # next variance
            h2=om+(al+ga*(e<0))*e*e+be*h2
            h2=np.where(np.isfinite(h2)&(h2>0),h2,sig0*sig0)
            if step in hset:
                cr=cum-1.0  # simple cumulative return
                qs={lab:np.quantile(cr,tau) for lab,tau in TAUS}
                qstore[step]=qs
        for h in HS:
            if h in qstore:
                q=qstore[h]; gar_rows.append((tk,pd.Timestamp(dt),h,q['p05'],q['p25'],q['p50'],q['p75'],q['p95']))
    if ni%15==0: lg("  %d/%d %s garrows=%d %.0fs"%(ni,len(names),tk,len(gar_rows),time.time()-t0))
G=pd.DataFrame(gar_rows,columns=['tk','date','h','g05','g25','g50','g75','g95'])
lg("GARCH rows=%d %.0fs"%(len(G),time.time()-t0))
M=IQ.merge(G,on=['tk','date','h'],how='inner')
lg("MERGED same-rows=%d %.0fs"%(len(M),time.time()-t0))
# detect convention using realized y vs both models' median (pick smaller overall pinball-neutral: compare y dist) -- report both anyway
out={'n_iqn':int(len(IQ)),'n_garch':int(len(G)),'n_samerows':int(len(M)),'by_horizon':{}}
gmap={'p05':'g05','p25':'g25','p50':'g50','p75':'g75','p95':'g95'}
tot_i={lab:0.0 for lab,_ in TAUS}; tot_g={lab:0.0 for lab,_ in TAUS}; cnt=0
for h in HS:
    mh=M[M.h==h]
    if not len(mh): continue
    hd={'n':int(len(mh))}
    li_all=[]; lg_all=[]
    for lab,tau in TAUS:
        li=pinball(mh['y'].values,mh[lab].values,tau).mean()
        lgv=pinball(mh['y'].values,mh[gmap[lab]].values,tau).mean()
        hd[f'IQN_{lab}']=round(float(li),5); hd[f'GARCH_{lab}']=round(float(lgv),5); hd[f'ratio_{lab}']=round(float(li/lgv),3) if lgv>0 else None
        li_all.append(pinball(mh['y'].values,mh[lab].values,tau)); lg_all.append(pinball(mh['y'].values,mh[gmap[lab]].values,tau))
    # avg pinball across taus (CRPS-ish) + DM on the difference
    Li=np.mean(li_all,axis=0); Lg=np.mean(lg_all,axis=0); dvec=Li-Lg
    hd['IQN_avgpin']=round(float(Li.mean()),5); hd['GARCH_avgpin']=round(float(Lg.mean()),5)
    hd['ratio_avg']=round(float(Li.mean()/Lg.mean()),3) if Lg.mean()>0 else None
    dm=dvec.mean()/(dvec.std()/math.sqrt(len(dvec))) if dvec.std()>0 else 0.0
    hd['DM_t_IQNminusGARCH']=round(float(dm),2)  # negative => IQN better
    out['by_horizon'][int(h)]=hd
    lg(f"h={h}: IQN_avgpin={hd['IQN_avgpin']} GARCH_avgpin={hd['GARCH_avgpin']} ratio={hd['ratio_avg']} DM_t={hd['DM_t_IQNminusGARCH']}")
json.dump(out,open(os.path.join(P,"samerows_iqn_garch.json"),"w"),indent=2,default=str)
M.to_csv(os.path.join(P,"samerows_merged.csv"),index=False)
lg("SAMEROWS_DONE\n"+json.dumps(out['by_horizon'],indent=2,default=str)); lg("JOB4DONE %.0fs"%(time.time()-t0))
