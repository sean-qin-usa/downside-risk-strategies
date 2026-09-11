# ROUGH-VOLATILITY SIMULATION-BASED CALIBRATION via GBC (ai2, torch) — the marquee likelihood-free chapter.
# Rough Bergomi has a NON-Markovian fractional-Brownian vol driver: NO tractable likelihood, GARCH/MLE cannot fit it. GBC can:
# simulate (theta, path) from the prior + model, learn amortized posterior quantiles Q(tau|summary(path)) with a neural IQN
# (and GBM), validate by Simulation-Based Calibration coverage. Recovering the ROUGHNESS (Hurst H) from a single price path is
# the headline — it is exactly the parameter classical methods struggle with and the reason rough-vol needs likelihood-free inference.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import torch, torch.nn as nn
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
dev='cuda' if torch.cuda.is_available() else 'cpu'; torch.manual_seed(0); rng=np.random.default_rng(0)
NPATH=30000; NDAYS=252; dt=1.0/252
PARAMS=['H','eta','rho','xi0']
def sample_prior(n):
    return np.stack([rng.uniform(0.05,0.45,n),rng.uniform(0.5,3.0,n),rng.uniform(-0.9,-0.1,n),rng.uniform(0.01,0.09,n)],1).astype(np.float64)
# fBm covariance Cholesky (computed once per H is too slow; instead build per-path fBm via a shared grid using the Hurst of each path).
# Efficient trick: precompute standardized fBm increments for a set of H buckets, then scale. To keep it exact-ish and fast, we
# simulate fBm by the Hosking/Cholesky method on a downsampled grid (NG points) and interpolate — NG=64 keeps Cholesky cheap.
NG=64; tg=np.linspace(1e-6,1.0,NG)
def fbm_paths(H,n):
    C=0.5*(tg[:,None]**(2*H)+tg[None,:]**(2*H)-np.abs(tg[:,None]-tg[None,:])**(2*H))
    try: L=np.linalg.cholesky(C+1e-10*np.eye(NG))
    except Exception: L=np.linalg.cholesky(C+1e-6*np.eye(NG))
    Z=rng.standard_normal((NG,n)); return (L@Z)  # (NG,n) fBm on coarse grid
def simulate(theta):
    n=theta.shape[0]; H,eta,rho,xi0=[theta[:,i] for i in range(4)]
    lr=np.empty((n,NDAYS))
    # group by H bucket for shared Cholesky (speed): 15 buckets
    order=np.argsort(H); buckets=np.array_split(order,15)
    W=np.empty((NG,n))
    for bk in buckets:
        if len(bk)==0: continue
        Hb=float(H[bk].mean()); W[:,bk]=fbm_paths(Hb,len(bk))
    # interpolate coarse fBm to daily grid
    day_t=np.linspace(1e-6,1.0,NDAYS)
    Wf=np.empty((NDAYS,n))
    for j in range(n): Wf[:,j]=np.interp(day_t,tg,W[:,j])
    for j in range(n):
        wt=Wf[:,j]; v=xi0[j]*np.exp(eta[j]*wt-0.5*eta[j]**2*day_t**(2*H[j]))
        z1=rng.standard_normal(NDAYS); # correlate spot with vol driver increments
        dW=rho[j]*np.diff(np.concatenate([[0],wt]))/np.sqrt(np.maximum(np.diff(np.concatenate([[0],day_t])),1e-9)) + math.sqrt(max(1-rho[j]**2,0))*z1
        lr[j]=-0.5*v*dt+np.sqrt(np.maximum(v,0)*dt)*dW
    return lr
def summaries(lr):
    r=lr*100.0; mean=r.mean(1); std=r.std(1)+1e-8; zc=r-mean[:,None]
    sk=(zc**3).mean(1)/std**3; ku=(zc**4).mean(1)/std**4-3
    def acf(x,lag):
        a=x[:,lag:]; b=x[:,:-lag]; return ((a-a.mean(1,keepdims=True))*(b-b.mean(1,keepdims=True))).mean(1)/((a.std(1)*b.std(1))+1e-8)
    ar2_1=acf(r**2,1); ar2_5=acf(r**2,5); ar2_20=acf(r**2,20); arabs1=acf(np.abs(r),1)
    # roughness proxy: scaling of realized-vol increments across lags (rough vol -> faster decay of |r| autocorr)
    rvq=np.stack([np.abs(r[:,i:i+5]).mean(1) for i in range(0,NDAYS-5,5)],1)
    rv_ac1=acf(rvq,1)
    ann=std*math.sqrt(252); tail=(np.abs(zc)>2.5*std[:,None]).mean(1)
    return np.stack([ann,sk,ku,ar2_1,ar2_5,ar2_20,arabs1,rv_ac1,tail,mean],1).astype(np.float32)
lg("simulating %d rough-vol paths (dev=%s)..."%(NPATH,dev))
TH=sample_prior(NPATH); LR=simulate(TH); Y=summaries(LR)
ok=np.all(np.isfinite(Y),1); TH=TH[ok]; Y=Y[ok]; lg("valid=%d sim+summ %.0fs"%(len(Y),time.time()-t0))
mY=Y.mean(0); sY=Y.std(0)+1e-6; Yn=(Y-mY)/sY; sp=int(len(Y)*0.8)
Ytr,Yte=Yn[:sp],Yn[sp:]; Ttr,Tte=TH[:sp],TH[sp:]
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
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
res={}
for pi,pname in enumerate(PARAMS):
    ytr=Ttr[:,pi]; yte=Tte[:,pi]
    net=train_iqn(Ytr,ytr)
    with torch.no_grad():
        x=torch.tensor(Yte).to(dev); IQ={t:net(x,torch.full((len(Yte),1),float(t),device=dev)).cpu().numpy() for t in TAUS}
    GB={t:HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=200,max_depth=3,learning_rate=0.07).fit(Ytr,ytr).predict(Yte) for t in TAUS}
    def cov(Q,lo,hi): return float(((yte>=Q[lo])&(yte<=Q[hi])).mean())
    def rmse(Q): return float(np.sqrt(np.mean((yte-Q[0.50])**2)))
    prior_rmse=float(np.sqrt(np.mean((yte-np.median(ytr))**2)))
    res[pname]=dict(IQN=dict(cov80=round(cov(IQ,0.10,0.90),3),cov90=round(cov(IQ,0.05,0.95),3),rmse=round(rmse(IQ),4)),
                    GBM=dict(cov80=round(cov(GB,0.10,0.90),3),cov90=round(cov(GB,0.05,0.95),3),rmse=round(rmse(GB),4)),
                    prior_rmse=round(prior_rmse,4),info_gain=dict(IQN=round(1-rmse(IQ)/prior_rmse,3),GBM=round(1-rmse(GB)/prior_rmse,3)))
    lg("  %s IQN cov90=%.2f info_gain=%.2f (H is the roughness) %.0fs"%(pname,res[pname]['IQN']['cov90'],res[pname]['info_gain']['IQN'],time.time()-t0))
out={'note':'Rough Bergomi (rough-volatility) SBC via GBC — likelihood-free amortized posterior over (H roughness, eta vol-of-vol, '
            'rho leverage, xi0) from a single price path. NON-Markovian fBm vol => intractable likelihood, GARCH/MLE cannot do this. '
            'SBC coverage ~nominal = honest posterior; info_gain=fraction of prior RMSE removed. Headline: recover the Hurst roughness H.',
     'n_paths':int(len(Y)),'n_days':NDAYS,'dev':dev,'params':res}
json.dump(out,open(os.path.join(D,"roughvol_sbc_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
