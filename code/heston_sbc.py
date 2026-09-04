# SIMULATION-BASED CALIBRATION of the HESTON model (ai2, torch) — the FULL GBC pitch: likelihood-free Bayesian parameter
# inference. Heston's likelihood is intractable (latent stochastic vol), so MLE/GARCH cannot do this. GBC can: simulate many
# (theta, path) pairs from the prior + forward model, then learn the amortized posterior quantiles Q(tau | summary(path)) with a
# deep quantile net (IQN = the canonical GBC estimator). Deliverable: honest, sharp posteriors validated by SIMULATION-BASED
# CALIBRATION coverage (does the tau-credible interval contain the true theta at rate tau?). Compare IQN vs GBM vs prior-only.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import torch, torch.nn as nn
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
dev='cuda' if torch.cuda.is_available() else 'cpu'; torch.manual_seed(0); rng=np.random.default_rng(0)
NPATH=40000; NDAYS=252; dt=1.0/252
PARAMS=['kappa','theta','xi','rho','v0']
# ---- priors ----
def sample_prior(n):
    return np.stack([rng.uniform(0.5,5.0,n),rng.uniform(0.01,0.09,n),rng.uniform(0.1,1.0,n),
                     rng.uniform(-0.9,-0.05,n),rng.uniform(0.01,0.09,n)],axis=1).astype(np.float64)
# ---- Heston simulate (Euler, full truncation), vectorized across paths ----
def simulate(theta):
    n=theta.shape[0]; kappa,th,xi,rho,v0=[theta[:,i] for i in range(5)]
    v=v0.copy(); logret=np.empty((n,NDAYS))
    for t in range(NDAYS):
        z1=rng.standard_normal(n); z2=rho*z1+np.sqrt(1-rho**2)*rng.standard_normal(n)
        vp=np.maximum(v,0.0)
        logret[:,t]=-0.5*vp*dt+np.sqrt(vp*dt)*z1
        v=v+kappa*(th-vp)*dt+xi*np.sqrt(vp*dt)*z2
    return logret
def summaries(lr):                                    # path -> observed feature vector (what the posterior conditions on)
    r=lr*100.0; n=r.shape[0]; out=[]
    mean=r.mean(1); std=r.std(1)+1e-8
    zc=(r-mean[:,None]); sk=(zc**3).mean(1)/std**3; ku=(zc**4).mean(1)/std**4-3
    def acf(x,lag):
        a=x[:,lag:]; b=x[:,:-lag]; am=a.mean(1,keepdims=True); bm=b.mean(1,keepdims=True)
        num=((a-am)*(b-bm)).mean(1); den=(a.std(1)*b.std(1))+1e-8; return num/den
    r2=r**2; ac1=acf(r2,1); ac5=acf(r2,5); acr1=acf(r,1)
    tail=(np.abs(zc)>2*std[:,None]).mean(1)
    cum=np.cumsum(r,1); dd=(np.maximum.accumulate(cum,1)-cum).max(1)
    volvol=np.stack([r[:,i:i+21].std(1) for i in range(0,NDAYS-21,21)],1).std(1)
    ann=std*math.sqrt(252)
    return np.stack([ann,sk,ku,ac1,ac5,acr1,tail,dd,volvol,mean],1).astype(np.float32)
lg("simulating %d paths..."%NPATH)
TH=sample_prior(NPATH); LR=simulate(TH); Y=summaries(LR)
mY=Y.mean(0); sY=Y.std(0)+1e-6; Yn=(Y-mY)/sY
sp=int(NPATH*0.8); Ytr,Yte=Yn[:sp],Yn[sp:]; Ttr,Tte=TH[:sp],TH[sp:]
lg("sim+summ done %.0fs; features=%d"%(time.time()-t0,Y.shape[1]))
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
# ---- IQN posterior per param (amortized): Q(tau | y) ----
class IQN(nn.Module):
    def __init__(s,din,ne=64,h=128):
        super().__init__(); s.psi=nn.Sequential(nn.Linear(din,h),nn.ReLU(),nn.Linear(h,h),nn.ReLU())
        s.phi=nn.Sequential(nn.Linear(ne,h),nn.ReLU()); s.out=nn.Sequential(nn.Linear(h,h),nn.ReLU(),nn.Linear(h,1)); s.reg=torch.arange(1,ne+1,dtype=torch.float32)
    def forward(s,x,tau): return s.out(s.psi(x)*s.phi(torch.cos(math.pi*s.reg.to(x.device)[None,:]*tau))).squeeze(-1)
def train_iqn(Xtr,ytr):
    net=IQN(Xtr.shape[1]).to(dev); opt=torch.optim.Adam(net.parameters(),1e-3)
    X=torch.tensor(Xtr).to(dev); yv=torch.tensor(ytr.astype(np.float32)).to(dev); N=len(yv)
    for step in range(4000):
        bi=torch.randint(0,N,(512,),device=dev); tau=torch.rand(512,1,device=dev)*0.98+0.01
        q=net(X[bi],tau); d=yv[bi]-q; loss=torch.maximum(tau.squeeze(1)*d,(tau.squeeze(1)-1)*d).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    net.eval(); return net
def iqn_predict(net,Xte):
    with torch.no_grad():
        x=torch.tensor(Xte).to(dev); return {t:net(x,torch.full((len(Xte),1),float(t),device=dev)).cpu().numpy() for t in TAUS}
res={}
for pi,pname in enumerate(PARAMS):
    ytr=Ttr[:,pi]; yte=Tte[:,pi]
    net=train_iqn(Ytr,ytr); IQ=iqn_predict(net,Yte)
    GB={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=200,max_depth=3,learning_rate=0.07).fit(Ytr,ytr).predict(Yte) for t in TAUS}
    def cover(Q,lo,hi): return float(((yte>=Q[lo])&(yte<=Q[hi])).mean())
    def rmse(Q): return float(np.sqrt(np.mean((yte-Q[0.50])**2)))
    def width(Q,lo,hi): return float(np.mean(Q[hi]-Q[lo]))
    prior_lo,prior_hi=np.quantile(ytr,0.05),np.quantile(ytr,0.95); prior_rmse=float(np.sqrt(np.mean((yte-np.median(ytr))**2)))
    res[pname]=dict(
        IQN=dict(cov50=round(cover(IQ,0.25,0.75),3),cov80=round(cover(IQ,0.10,0.90),3),cov90=round(cover(IQ,0.05,0.95),3),
                 rmse=round(rmse(IQ),4),width90=round(width(IQ,0.05,0.95),4)),
        GBM=dict(cov50=round(cover(GB,0.25,0.75),3),cov80=round(cover(GB,0.10,0.90),3),cov90=round(cover(GB,0.05,0.95),3),
                 rmse=round(rmse(GB),4),width90=round(width(GB,0.05,0.95),4)),
        prior_only=dict(rmse=round(prior_rmse,4),width90=round(float(prior_hi-prior_lo),4)),
        info_gain_rmse_vs_prior=dict(IQN=round(1-rmse(IQ)/prior_rmse,3),GBM=round(1-rmse(GB)/prior_rmse,3)))
    lg("  %s done IQN cov90=%.2f rmse=%.4f (prior %.4f) %.0fs"%(pname,res[pname]['IQN']['cov90'],res[pname]['IQN']['rmse'],prior_rmse,time.time()-t0))
out={'note':'Simulation-Based Calibration of Heston stochastic-vol via GBC (likelihood-free). Simulate (theta,path) from prior+model; '
            'learn amortized posterior quantiles Q(tau|summary(path)) with IQN (canonical GBC neural estimator) and GBM. Validate by '
            'SBC coverage: central 50/80/90 credible-interval coverage should hit nominal; rmse=posterior-median error; width90=sharpness; '
            'info_gain=1-rmse/prior_rmse (fraction of prior uncertainty removed by the data). GARCH/MLE CANNOT do this (intractable likelihood).',
     'n_paths':NPATH,'n_days':NDAYS,'n_features':int(Y.shape[1]),'dev':dev,'params':res}
json.dump(out,open(os.path.join(D,"heston_sbc_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
