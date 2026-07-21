"""Multi-horizon panel IQN: Q(tau | x, h) per MULTI_HORIZON_DESIGN.md.
- 113-name IV panel, features incl. own ATM IV + skew (matched-information)
- h in {5,10,21,42,63} as log-horizon feature; target = h-day total-return
  scaled by sqrt(h)*sigma_daily(x)  (learns deviation from sqrt-time scaling)
- soft monotonicity-in-h penalty on total width
- annual walk-forward refits from 2016, K=3 warm-started ensemble
Outputs: mh_quantiles_gpu.csv + per-h calibration table. Resumable.
"""
import os, math, time, pickle
import numpy as np, pandas as pd
import torch, torch.nn as nn

DEV="cuda" if torch.cuda.is_available() else "cpu"
HS=[5,10,21,42,63]; K=3
TAUS=np.array([.01,.05,.10,.25,.50,.75,.90,.95,.99])
HERE=os.path.dirname(os.path.abspath(__file__))
VAR=os.environ.get("MHVAR","v1")
LAM=float(os.environ.get("MHLAM","0.30"))
FSET=os.environ.get("MHFEATS","raw9")
PANEL=os.environ.get("MHPANEL","mh_panel.csv.gz")
CKPT=os.path.join(HERE,f"mh_ckpt_{VAR}.pkl")
F9=["lrv21","lewma","ret21","dsh","liv","skw","lvix","slope","basis"]
F17=F9+["v9r","y10","curve","hyoas","igoas","mkt63","dd252","d200"]
FEATS=F9 if FSET=="raw9" else F17

d=pd.read_csv(os.path.join(HERE,PANEL))
d["date"]=pd.to_datetime(d.date)
d=d.sort_values(["tk","date"]).reset_index(drop=True)
sig_d=np.exp(d.lewma/2)/math.sqrt(252)              # daily vol proxy from ewma feature

class IQNH(nn.Module):
    def __init__(self,nf,emb=96,ncos=64,hid=96):
        super().__init__()
        self.register_buffer("ipi",torch.arange(ncos).float()*math.pi)
        self.psi=nn.Sequential(nn.Linear(nf,hid),nn.ReLU(),nn.Linear(hid,emb),nn.ReLU())
        self.phi=nn.Linear(ncos,emb)
        self.head=nn.Sequential(nn.Linear(emb,hid),nn.ReLU(),nn.Linear(hid,1))
    def forward(self,x,tau):
        h=self.psi(x)[:,None,:]
        c=torch.cos(tau[...,None]*self.ipi)
        p=torch.relu(self.phi(c))
        return self.head(h*p)[...,0]

def sample_tau(B,M,lam=LAM,gen=None):
    u=torch.rand(B,M,generator=gen,device=DEV)
    mix=torch.rand(B,M,generator=gen,device=DEV)<lam
    side=torch.rand(B,M,generator=gen,device=DEV)<0.70   # 70% of tail draws LEFT
    lo=0.002+0.098*torch.rand(B,M,generator=gen,device=DEV)
    hi=0.90+0.095*torch.rand(B,M,generator=gen,device=DEV)
    return torch.where(mix,torch.where(side,lo,hi),u).clamp(1e-4,1-1e-4)

def build_xy(df,sig):
    xs,ys=[],[]
    for h in HS:
        ok=df[f"y{h}"].notna()&df[FEATS].notna().all(1)
        X=df.loc[ok,FEATS].values.astype(np.float32)
        lh=np.full((ok.sum(),1),math.log(h/21.0),dtype=np.float32)
        y=(df.loc[ok,f"y{h}"].values/(np.sqrt(h)*sig[ok].values)).astype(np.float32)
        xs.append(np.c_[X,lh]); ys.append(y)
    return np.vstack(xs),np.concatenate(ys)

def fit(Xw,yw,seed,init=None,epochs=40,M=8,batch=4096,lr=1e-3,patience=6):
    g=torch.Generator(device=DEV); g.manual_seed(seed); torch.manual_seed(seed)
    mu,sd=Xw.mean(0),Xw.std(0)+1e-8
    Xn=torch.tensor((Xw-mu)/sd,device=DEV)
    yn=torch.tensor(np.clip(yw,-8,8),device=DEV)
    n=len(Xn); model=IQNH(Xw.shape[1]).to(DEV)
    if init is not None: model.load_state_dict(init)
    opt=torch.optim.Adam(model.parameters(),lr=lr)
    vstart=int(n*.95)
    vg=torch.linspace(.01,.99,33,device=DEV).repeat(n-vstart,1)
    best,bstate,bad=np.inf,None,0
    hcol=Xn[:,-1]
    for ep in range(epochs):
        perm=torch.randperm(vstart,generator=g,device=DEV)
        model.train()
        for s_ in range(0,vstart,batch):
            i=perm[s_:s_+batch]
            tau=sample_tau(len(i),M,gen=g)
            q=model(Xn[i],tau)
            u=yn[i][:,None]-q
            loss=(u*(tau-(u<0).float())).mean()
            # monotone-in-h: width at larger h (in raw units ~ sqrt(h)*q) must not shrink
            i2=i[:len(i)//2]
            x2=Xn[i2].clone(); x2[:,-1]=x2[:,-1]+0.7   # ~double horizon
            t2=torch.tensor([[.05,.95]],device=DEV).repeat(len(i2),1)
            q1=model(Xn[i2],t2); q2=model(x2,t2)
            w1=(q1[:,1]-q1[:,0]); w2=(q2[:,1]-q2[:,0])*math.sqrt(2.0)
            pen=torch.relu(w1-w2).mean()
            (loss+0.1*pen).backward()
            nn.utils.clip_grad_norm_(model.parameters(),5.0); opt.step(); opt.zero_grad()
        model.eval()
        with torch.no_grad():
            qv=model(Xn[vstart:],vg); uv=yn[vstart:][:,None]-qv
            vl=float((uv*(vg-(uv<0).float())).mean())
        if not np.isfinite(vl): model=IQNH(Xw.shape[1]).to(DEV); opt=torch.optim.Adam(model.parameters(),lr=lr); best,bstate,bad=np.inf,None,0; continue
        if vl<best-1e-5: best,bad=vl,0; bstate={k:v.detach().clone() for k,v in model.state_dict().items()}
        else:
            bad+=1
            if bad>=patience: break
    if bstate: model.load_state_dict(bstate)
    return model,(mu,sd)

@torch.no_grad()
def predict(model,scaler,X):
    mu,sd=scaler
    Xs=np.nan_to_num((X-mu)/sd,nan=0.0,posinf=0.0,neginf=0.0)
    Xn=torch.tensor(Xs.astype(np.float32),device=DEV)
    tg=torch.tensor(TAUS,dtype=torch.float32,device=DEV).repeat(len(Xn),1)
    return model(Xn,tg).cpu().numpy()

refits=pd.date_range("2016-01-01","2026-01-01",freq="YS")
state={"done":[],"preds":[],"warm":[None]*K}
if os.path.exists(CKPT): state=pickle.load(open(CKPT,"rb"))
t0=time.time()
for ri,t in enumerate(refits):
    if str(t.date()) in state["done"]: continue
    tr=d[d.date<t-pd.Timedelta(days=95)]
    Xw,yw=build_xy(tr,sig_d[tr.index])
    te=d[(d.date>=t)&(d.date<t+pd.DateOffset(years=1))]
    te=te.iloc[::5]                                   # thin the eval grid
    QS=[]
    for k in range(K):
        model,scaler=fit(Xw,yw,seed=500*(k+1)+ri,init=state["warm"][k])
        state["warm"][k]={kk:vv.cpu() for kk,vv in model.state_dict().items()}
        # predict for each h
        preds_h=[]
        for h in HS:
            X=np.c_[te[FEATS].values.astype(np.float32),
                    np.full((len(te),1),math.log(h/21.0),dtype=np.float32)]
            preds_h.append(predict(model,scaler,X))
        QS.append(preds_h)
    sg=sig_d[te.index].values
    for hi,h in enumerate(HS):
        Q=np.sort(np.mean([QS[k][hi] for k in range(K)],axis=0),axis=1)
        Q=Q*np.sqrt(h)*sg[:,None]                     # back to raw h-day return units
        for row_i,(idx,row) in enumerate(te.iterrows()):
            state["preds"].append({"tk":row.tk,"date":row.date,"h":h,
                **{f"p{int(tt*100):02d}":Q[row_i,j] for j,tt in enumerate(TAUS)},
                "y":row[f"y{h}"]})
    state["done"].append(str(t.date()))
    pickle.dump(state,open(CKPT+".tmp","wb")); os.replace(CKPT+".tmp",CKPT)
    print(f"{ri+1}/{len(refits)} {t.date()} train={len(Xw)} {time.time()-t0:.0f}s",flush=True)

P=pd.DataFrame(state["preds"])
P.to_csv(os.path.join(HERE,f"mh_quantiles_{VAR}.csv"),index=False)
print("\ncalibration by horizon (target tau -> coverage):")
for h in HS:
    sub=P[(P.h==h)&P.y.notna()]
    line=f"h={h:3d} n={len(sub):6d}  "
    for tt in [.05,.25,.50,.75,.95]:
        line+=f"{tt:.2f}->{float((sub.y<sub[f'p{int(tt*100):02d}']).mean()):.3f}  "
    print(line)
print("DONE",len(P))
