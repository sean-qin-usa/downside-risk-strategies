# TAIL-AWARE MONOTONE NEURAL IQN + CONFORMAL RECAL (ai2, torch) — closes gaps (a) neural IQN vs trees and (b) 97.5% calibration.
# v1 neural IQN lost to trees AND its tail under-covered. Fixes: (1) TAIL-AWARE tau sampling (half uniform, half Beta(0.3,0.3)
# U-shaped -> oversample extreme tau); (2) MONOTONE output via rearrangement; (3) longer training. Plus SPLIT-CONFORMAL
# recalibration per level (additive shift learned on TEST_A) so breach hits nominal at BOTH 99% and 97.5% (the FRTB gap).
# Compare hybrid_GBM(+recal) vs hybrid_IQN_v2(+recal) vs garch_t, fhs. Backtests at 99% AND 97.5%; DM + MCS.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
from arch import arch_model
import torch, torch.nn as nn
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True); rng=np.random.default_rng(0)
dev='cuda' if torch.cuda.is_available() else 'cpu'; torch.manual_seed(0); np.random.seed(0)
TAUS=[0.005,0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:140]
ZX=['logsig','zl1','absz5','zstd21','fracdn5']
TR_z=[]; rows=[]
for pn in names:
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); dts=g['date'].values; n=len(y)
    if n<1500: continue
    sp=int(n*0.6)
    try:
        r1=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=r1.params; om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nu=float(p.get('nu',8))
    except Exception: continue
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    sig=np.sqrt(s2); z=(y-mu)/np.maximum(sig,1e-6); tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    fhsq={t:np.quantile(z[:sp],t) for t in TAUS}
    df=pd.DataFrame({'y':y,'sig':sig,'z':z,'date':dts,'idx':np.arange(n)})
    df['logsig']=np.log(np.maximum(df['sig'],1e-6)); df['zl1']=df['z'].shift(1); df['absz5']=df['z'].abs().rolling(5,min_periods=3).mean().shift(1)
    df['zstd21']=df['z'].rolling(21,min_periods=8).std().shift(1); df['fracdn5']=(df['y']<0).rolling(5,min_periods=3).mean().shift(1)
    df['mu']=mu; df['nu']=nu; df['tsc']=tsc
    for t in TAUS: df['fhs_%g'%t]=fhsq[t]
    dd=df.dropna(subset=ZX+['sig']); trn=dd[dd['idx']<sp]; tst=dd[dd['idx']>=sp]
    if len(tst)<60: continue
    TR_z.append(trn[ZX+['z']]); t2=tst.copy(); t2['permno']=pn; rows.append(t2)
lg("panels %d names %.0fs dev=%s"%(len(rows),time.time()-t0,dev))
TE=pd.concat(rows).reset_index(drop=True); TRzc=pd.concat(TR_z)
Xtr=TRzc[ZX].values.astype(np.float32); ytr=TRzc['z'].values.astype(np.float32)
mX=Xtr.mean(0); sX=Xtr.std(0)+1e-6; Xtr=(Xtr-mX)/sX; Xte=((TE[ZX].values.astype(np.float32))-mX)/sX
class IQN(nn.Module):
    def __init__(s,din,ne=64,h=192):
        super().__init__(); s.ne=ne
        s.psi=nn.Sequential(nn.Linear(din,h),nn.ReLU(),nn.Linear(h,h),nn.ReLU())
        s.phi=nn.Sequential(nn.Linear(ne,h),nn.ReLU()); s.out=nn.Sequential(nn.Linear(h,h),nn.ReLU(),nn.Linear(h,1)); s.reg=torch.arange(1,ne+1,dtype=torch.float32)
    def forward(s,x,tau): cos=torch.cos(math.pi*s.reg.to(x.device)[None,:]*tau); return s.out(s.psi(x)*s.phi(cos)).squeeze(-1)
net=IQN(len(ZX)).to(dev); opt=torch.optim.Adam(net.parameters(),1e-3)
Xt=torch.tensor(Xtr).to(dev); yt=torch.tensor(ytr).to(dev); N=len(yt)
for step in range(12000):
    bi=torch.randint(0,N,(512,),device=dev); x=Xt[bi]; yy=yt[bi]
    # TAIL-AWARE tau: half uniform, half U-shaped Beta(0.3,0.3)
    u=torch.rand(512,device=dev); bshape=torch.distributions.Beta(0.3,0.3).sample((512,)).to(dev)
    mask=torch.rand(512,device=dev)<0.5; tau=torch.where(mask,u,bshape).clamp(0.005,0.995).unsqueeze(1)
    q=net(x,tau); d=yy-q; loss=torch.maximum(tau.squeeze(1)*d,(tau.squeeze(1)-1)*d).mean()
    opt.zero_grad(); loss.backward(); opt.step()
    if step%3000==0: lg("  step %d loss %.4f %.0fs"%(step,loss.item(),time.time()-t0))
net.eval()
with torch.no_grad():
    xte=torch.tensor(Xte).to(dev); IQNraw=np.stack([net(xte,torch.full((len(Xte),1),float(t),device=dev)).cpu().numpy() for t in TAUS],axis=1)
IQNraw=np.sort(IQNraw,axis=1)                              # MONOTONE rearrangement across tau
IQNq={t:IQNraw[:,i] for i,t in enumerate(TAUS)}
GBMq={}
for t in TAUS:
    mz=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=3,learning_rate=0.06).fit(TRzc[ZX].values,ytr); GBMq[t]=mz.predict(TE[ZX].values)
Y=TE['y'].values; SIG=TE['sig'].values; MU=TE['mu'].values; NU=TE['nu'].values; TSC=TE['tsc'].values
raw={'garch_t':{t:MU+SIG*stats.t.ppf(t,NU)/TSC for t in TAUS},'fhs':{t:MU+SIG*TE['fhs_%g'%t].values for t in TAUS},
     'hybrid_GBM':{t:MU+SIG*GBMq[t] for t in TAUS},'hybrid_IQN_v2':{t:MU+SIG*IQNq[t] for t in TAUS}}
# split-conformal recal: additive per-level shift learned on TEST_A so breach=tau; apply on TEST_B (report on B)
nT=len(Y); cut=nT//2; A=slice(0,cut); B=slice(cut,nT)
def recal(qd):
    out={}
    for t in TAUS:
        qa=qd[t][A]; ya=Y[A]
        # find shift s so mean(ya < qa+s)=t
        resid=ya-qa; s=np.quantile(resid,t)               # split-conformal: t-quantile of (y-qhat) on calib
        out[t]=qd[t]+s
    # monotone across tau on B
    M=np.stack([out[t] for t in TAUS],axis=1); M=np.sort(M,axis=1)
    return {t:M[:,i] for i,t in enumerate(TAUS)}
models={**raw,'hybrid_GBM_recal':recal(raw['hybrid_GBM']),'hybrid_IQN_v2_recal':recal(raw['hybrid_IQN_v2'])}
def _llb(pp,k0,k1):
    if k0+k1==0: return 0.0
    if pp<=0: return 0.0 if k1==0 else -1e300
    if pp>=1: return 0.0 if k0==0 else -1e300
    return k0*math.log(1-pp)+k1*math.log(pp)
def kupiec(x,T,p):
    if x==0 or x==T: return None
    pi=x/T; return round(float(1-stats.chi2.cdf(max(-2*(_llb(p,T-x,x)-_llb(pi,T-x,x)),0),1)),4)
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
    return round(float(1-stats.chi2.cdf(max(lr,0),2)),4)
YB=Y[B]; Tb=len(YB); summ={}; PLm={}
for m in models:
    pl=np.zeros(Tb)
    for t in TAUS: pl+=pin(YB,models[m][t][B],t)
    pl/=len(TAUS); PLm[m]=pl; b99=(YB<models[m][0.01][B]); b975=(YB<models[m][0.025][B])
    summ[m]=dict(avg_pinball=round(float(pl.mean()),4),
                 breach99=round(float(b99.mean()),4),kupiec99_p=kupiec(int(b99.sum()),Tb,0.01),christ99_p=christ(b99,0.01),
                 breach975=round(float(b975.mean()),4),kupiec975_p=kupiec(int(b975.sum()),Tb,0.025),christ975_p=christ(b975,0.025))
best=min(summ,key=lambda k:summ[k]['avg_pinball'])
Ld=pd.DataFrame({m:PLm[m] for m in models}); Ld['date']=TE['date'].values[B]; Lm=Ld.groupby('date').mean(); L=Lm.values; cols=list(Lm.columns)
def nwv(d,lag=10):
    d=d-d.mean(); v=np.mean(d*d)
    for k in range(1,lag+1): v+=2*(1-k/(lag+1))*np.mean(d[k:]*d[:-k])
    return v/len(d)
bi=cols.index(best); dm={}
for m in cols:
    if m==best: continue
    d=L[:,cols.index(m)]-L[:,bi]; s=d.mean()/math.sqrt(max(nwv(d),1e-12)); dm[m]=dict(DM=round(float(s),2),p=round(float(1-stats.norm.cdf(s)),4))
def mcs(L,alpha=0.10,B_=600,blk=10):
    surv=list(range(L.shape[1])); pv={}
    def bidx(T):
        idx=np.empty(T,int); i=0
        while i<T:
            s=rng.integers(0,T); l=rng.geometric(1/blk)
            for j in range(l):
                if i<T: idx[i]=(s+j)%T; i+=1
        return idx
    while len(surv)>1:
        Ls=L[:,surv]; means=Ls.mean(0); M=len(surv); dij=means[:,None]-means[None,:]
        bd=np.zeros((B_,M,M))
        for bb in range(B_): ix=bidx(Ls.shape[0]); mb=Ls[ix].mean(0); bd[bb]=mb[:,None]-mb[None,:]
        varij=bd.var(0)+1e-12; TR=np.nanmax(np.abs(dij)/np.sqrt(varij))
        bt=np.array([np.nanmax(np.abs(bd[bb]-dij)/np.sqrt(varij)) for bb in range(B_)])
        pval=float(np.mean(bt>=TR)); worst=surv[int(np.argmax(means))]; pv[cols[worst]]=round(pval,3)
        if pval>=alpha: break
        surv.remove(worst)
    return {'in_MCS_90':[cols[i] for i in surv],'elim_pvals':pv}
out={'note':'Tail-aware monotone neural IQN (v2) + split-conformal recal at BOTH 99% & 97.5%. Models: garch_t, fhs, '
            'hybrid_GBM(+recal), hybrid_IQN_v2(+recal). Q: does tail-aware neural close the gap to trees, and does conformal '
            'recal pass Kupiec/Christoffersen at both 99% and 97.5%? Eval on held-out TEST_B. DM vs best + MCS.',
     'n_names':int(TE['permno'].nunique()),'n_testB':int(Tb),'dev':dev,'per_model':summ,'best_model':best,'DM_vs_best':dm,'MCS':mcs(L)}
json.dump(out,open(os.path.join(D,"frtb_neural_v2_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
