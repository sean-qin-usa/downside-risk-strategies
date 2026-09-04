# GENERATIVE JOINT SAMPLER v2 (ai2, torch) — the covariance-ingesting fix. v1 failed (PIT KS 0.30) because the net had to learn
# portfolio SCALE from raw state and couldn't. Fix = the residual-hybrid recipe, for portfolios: let DCC give the scale
# (portfolio vol sigma_w), and let the generative net learn only the SHAPE of the STANDARDIZED portfolio residual
# eps = port_ret / sigma_w, conditioned on concentration + state. VaR_w(tau) = sigma_w * Qz(tau | features, w). One net, every w.
# Test PIT calibration across the simplex vs Gaussian(eps~N(0,1)). Predict: IQN now CALIBRATED (KS low) AND fatter-tailed than
# Gaussian = the multivariate GBC win (covariance scale + nonparametric shape).
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
import torch, torch.nn as nn
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
dev='cuda' if torch.cuda.is_available() else 'cpu'; torch.manual_seed(0); rng=np.random.default_rng(0)
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
ch=pd.read_csv(os.path.join(D,"crsp_panel_chars.csv")); lc=ch[ch['cohort']=='largecap']['permno'].tolist() if 'cohort' in ch else ch['permno'].tolist()
piv=rr[rr.permno.isin(lc)].pivot_table(index='date',columns='permno',values='ret')
W=piv.dropna(axis=1,thresh=int(0.9*len(piv))).dropna()
if W.shape[1]>20: W=W.iloc[:,:20]
A=W.values.astype(np.float64); n,N=A.shape; sp=int(n*0.6)
lg("panel %d x %d dev=%s %.0fs"%(n,N,dev,time.time()-t0))
# per-name EWMA vol + DCC-lite EWMA corr -> portfolio sigma_w engine
ew=np.zeros_like(A); lam=0.94
for j in range(N):
    v=np.zeros(n); v[0]=A[:sp,j].var()
    for i in range(1,n): v[i]=lam*v[i-1]+(1-lam)*A[i-1,j]**2
    ew[:,j]=np.sqrt(v)
Z=A/np.maximum(ew,1e-6); Qbar=np.corrcoef(Z[:sp].T); Qt=Qbar.copy(); lam2=0.97; R=[None]*n
for i in range(n):
    if i>0: z=Z[i-1]; Qt=(1-lam2)*np.outer(z,z)+lam2*Qt; dd=np.sqrt(np.clip(np.diag(Qt),1e-8,None)); R[i]=Qt/np.outer(dd,dd)
    else: R[i]=Qbar
def sigma_w(i,w): return math.sqrt(max(w@(np.outer(ew[i],ew[i])*R[i])@w,1e-12))
def simplex(b,conc): a=np.random.gamma(conc,1,size=(b,N)).astype(np.float64); return a/a.sum(1,keepdims=True)
# state features (market-level, at day i): cross-sec dispersion, avg |z|, breadth
disp=A.std(1); avgabsz=np.abs(Z).mean(1); fracdn=(A<0).mean(1)
def feats(i,w):
    herf=float((w**2).sum())
    return np.array([herf, math.log(disp[i]+1e-6), avgabsz[i], fracdn[i]],np.float64)
class IQN(nn.Module):
    def __init__(s,din,ne=64,h=128):
        super().__init__(); s.psi=nn.Sequential(nn.Linear(din,h),nn.ReLU(),nn.Linear(h,h),nn.ReLU())
        s.phi=nn.Sequential(nn.Linear(ne,h),nn.ReLU()); s.out=nn.Sequential(nn.Linear(h,h),nn.ReLU(),nn.Linear(h,1)); s.reg=torch.arange(1,ne+1,dtype=torch.float32)
    def forward(s,x,tau): return s.out(s.psi(x)*s.phi(torch.cos(math.pi*s.reg.to(x.device)[None,:]*tau))).squeeze(-1)
din=4+N; net=IQN(din).to(dev); opt=torch.optim.Adam(net.parameters(),1e-3)
tr_idx=np.arange(0,sp-1)
def batch(bs):
    xs=np.empty((bs,din),np.float32); ys=np.empty(bs,np.float32)
    for b in range(bs):
        i=int(np.random.choice(tr_idx)); conc=float(np.random.choice([0.2,0.5,1.0,3.0])); w=simplex(1,conc)[0]
        sw=sigma_w(i,w); eps=float((w*A[i+1]).sum()/max(sw,1e-6))     # standardized next-day portfolio residual
        xs[b]=np.concatenate([feats(i,w),w]); ys[b]=eps
    return torch.tensor(xs).to(dev),torch.tensor(ys).to(dev)
for step in range(6000):
    x,y=batch(256); tau=torch.rand(256,1,device=dev); q=net(x,tau); d=y-q
    loss=torch.maximum(tau.squeeze(1)*d,(tau.squeeze(1)-1)*d).mean(); opt.zero_grad(); loss.backward(); opt.step()
    if step%2000==0: lg("  step %d loss %.4f %.0fs"%(step,loss.item(),time.time()-t0))
net.eval()
TAUG=np.linspace(0.01,0.99,99); teidx=np.arange(sp,n-1)
def pit(w):
    w=w/w.sum(); eps=np.array([ (w*A[i+1]).sum()/max(sigma_w(i,w),1e-6) for i in teidx])
    xs=np.array([np.concatenate([feats(i,w),w]) for i in teidx],np.float32); xt=torch.tensor(xs).to(dev)
    with torch.no_grad():
        Qg=np.sort(np.stack([net(xt,torch.full((len(teidx),1),float(t),device=dev)).cpu().numpy() for t in TAUG],1),1)
    u_iqn=(Qg<eps[:,None]).mean(1); u_g=stats.norm.cdf(eps)          # Gaussian: eps~N(0,1)
    ks=lambda u: float(np.max(np.abs(np.sort(u)-np.linspace(0,1,len(u)))))
    cov=lambda u,a:float((u<a).mean())
    return dict(iqn_ks=round(ks(u_iqn),4),g_ks=round(ks(u_g),4),iqn_cov05=round(cov(u_iqn,0.05),4),g_cov05=round(cov(u_g,0.05),4),
                iqn_cov01=round(cov(u_iqn,0.01),4),g_cov01=round(cov(u_g,0.01),4))
schemes={'equal':np.ones(N)/N}
for k in (1,3,5):
    w=np.zeros(N); w[:k]=1.0; schemes['top%d'%k]=w
res={k:pit(w) for k,w in schemes.items()}
randres=[pit(rng.dirichlet(np.ones(N))) for _ in range(20)]
res['random_mean']={m:round(float(np.mean([r[m] for r in randres])),4) for m in randres[0]}
out={'note':'Joint sampler v2 (covariance-ingesting): DCC gives portfolio scale sigma_w; generative IQN learns the SHAPE of the '
            'standardized portfolio residual eps=port_ret/sigma_w, conditioned on concentration (herfindahl)+state+w. PIT vs '
            'Gaussian(eps~N(0,1)). Win = IQN PIT-KS << v1 (0.30) and < Gaussian, with better tail cov05/cov01. Tests whether '
            'covariance-scale + nonparametric-shape finally calibrates the multivariate/joint tail (the residual-hybrid recipe for portfolios).',
     'n_names':N,'n_test':int(len(teidx)),'dev':dev,'results':res}
json.dump(out,open(os.path.join(D,"joint_sampler_v2_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
