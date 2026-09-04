"""FROZEN-cutoff variant of gpu_iqn_mh.py: train ONE ensemble on data <= FROZEN_CUTOFF,
then predict ALL rows from 2016 onward with that frozen model (no refitting).
Lets us compare a pre-COVID-trained model vs a 2024-trained model out-of-sample.
Env: FROZEN_CUTOFF (e.g. 2019-12-31), FROZEN_TAG (e.g. c2019), MHPANEL, MHFEATS."""
import os, math, time, pickle
import numpy as np, pandas as pd
import torch, torch.nn as nn

DEV="cuda" if torch.cuda.is_available() else "cpu"
HS=[5,10,21,42,63]; K=3
TAUS=np.array([.01,.05,.10,.25,.50,.75,.90,.95,.99])
HERE=os.path.dirname(os.path.abspath(__file__))
FSET=os.environ.get("MHFEATS","raw9")
PANEL=os.environ.get("MHPANEL","mh_panel_v2.csv.gz")
CUTOFF=pd.Timestamp(os.environ.get("FROZEN_CUTOFF","2019-12-31"))
TAG=os.environ.get("FROZEN_TAG","c2019")
F9=["lrv21","lewma","ret21","dsh","liv","skw","lvix","slope","basis"]
F17=F9+["v9r","y10","curve","hyoas","igoas","mkt63","dd252","d200"]
FEATS=F9 if FSET=="raw9" else F17

d=pd.read_csv(os.path.join(HERE,PANEL)); d["date"]=pd.to_datetime(d.date)
d=d.sort_values(["tk","date"]).reset_index(drop=True)
sig_d=np.exp(d.lewma/2)/math.sqrt(252)

class IQNH(nn.Module):
    def __init__(self,nf,emb=96,ncos=64,hid=96):
        super().__init__()
        self.register_buffer("ipi",torch.arange(ncos).float()*math.pi)
        self.psi=nn.Sequential(nn.Linear(nf,hid),nn.ReLU(),nn.Linear(hid,emb),nn.ReLU())
        self.phi=nn.Linear(ncos,emb); self.head=nn.Sequential(nn.Linear(emb,hid),nn.ReLU(),nn.Linear(hid,1))
    def forward(self,x,tau):
        h=self.psi(x)[:,None,:]; c=torch.cos(tau[...,None]*self.ipi); p=torch.relu(self.phi(c))
        return self.head(h*p)[...,0]

def sample_tau(B,M,lam=0.30,gen=None):
    u=torch.rand(B,M,generator=gen,device=DEV); mix=torch.rand(B,M,generator=gen,device=DEV)<lam
    side=torch.rand(B,M,generator=gen,device=DEV)<0.70
    lo=0.002+0.098*torch.rand(B,M,generator=gen,device=DEV); hi=0.90+0.095*torch.rand(B,M,generator=gen,device=DEV)
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

def fit(Xw,yw,seed,epochs=40,M=8,batch=4096,lr=1e-3,patience=6):
    g=torch.Generator(device=DEV); g.manual_seed(seed); torch.manual_seed(seed)
    mu,sd=Xw.mean(0),Xw.std(0)+1e-8
    Xn=torch.tensor((Xw-mu)/sd,device=DEV); yn=torch.tensor(np.clip(yw,-8,8),device=DEV)
    n=len(Xn); model=IQNH(Xw.shape[1]).to(DEV); opt=torch.optim.Adam(model.parameters(),lr=lr)
    vstart=int(n*.95); vg=torch.linspace(.01,.99,33,device=DEV).repeat(n-vstart,1)
    best,bstate,bad=np.inf,None,0
    for ep in range(epochs):
        perm=torch.randperm(vstart,generator=g,device=DEV); model.train()
        for s_ in range(0,vstart,batch):
            i=perm[s_:s_+batch]; tau=sample_tau(len(i),M,gen=g); q=model(Xn[i],tau)
            u=yn[i][:,None]-q; loss=(u*(tau-(u<0).float())).mean()
            i2=i[:len(i)//2]; x2=Xn[i2].clone(); x2[:,-1]=x2[:,-1]+0.7
            t2=torch.tensor([[.05,.95]],device=DEV).repeat(len(i2),1)
            q1=model(Xn[i2],t2); q2=model(x2,t2)
            pen=torch.relu((q1[:,1]-q1[:,0])-(q2[:,1]-q2[:,0])*math.sqrt(2.0)).mean()
            (loss+0.1*pen).backward(); nn.utils.clip_grad_norm_(model.parameters(),5.0); opt.step(); opt.zero_grad()
        model.eval()
        with torch.no_grad():
            qv=model(Xn[vstart:],vg); uv=yn[vstart:][:,None]-qv; vl=float((uv*(vg-(uv<0).float())).mean())
        if not np.isfinite(vl): model=IQNH(Xw.shape[1]).to(DEV); opt=torch.optim.Adam(model.parameters(),lr=lr); best,bstate,bad=np.inf,None,0; continue
        if vl<best-1e-5: best,bad=vl,0; bstate={k:v.detach().clone() for k,v in model.state_dict().items()}
        else:
            bad+=1
            if bad>=patience: break
    if bstate: model.load_state_dict(bstate)
    return model,(mu,sd)

@torch.no_grad()
def predict(model,scaler,X):
    mu,sd=scaler; Xs=np.nan_to_num((X-mu)/sd,nan=0.0,posinf=0.0,neginf=0.0)
    Xn=torch.tensor(Xs.astype(np.float32),device=DEV); tg=torch.tensor(TAUS,dtype=torch.float32,device=DEV).repeat(len(Xn),1)
    return model(Xn,tg).cpu().numpy()

t0=time.time()
tr=d[d.date<=CUTOFF]
Xw,yw=build_xy(tr,sig_d[tr.index])
print(f"[{TAG}] train rows={len(Xw)} cutoff={CUTOFF.date()}",flush=True)
models=[fit(Xw,yw,seed=500*(k+1)) for k in range(K)]
te=d[d.date>=pd.Timestamp("2016-01-01")].iloc[::5]
sg=sig_d[te.index].values
QS=[[predict(m,s,np.c_[te[FEATS].values.astype(np.float32),np.full((len(te),1),math.log(h/21.0),dtype=np.float32)]) for h in HS] for (m,s) in models]
preds=[]
for hi,h in enumerate(HS):
    Q=np.sort(np.mean([QS[k][hi] for k in range(K)],axis=0),axis=1)*np.sqrt(h)*sg[:,None]
    for ri,(idx,row) in enumerate(te.iterrows()):
        preds.append({"tk":row.tk,"date":row.date,"h":h,**{f"p{int(tt*100):02d}":Q[ri,j] for j,tt in enumerate(TAUS)},"y":row[f"y{h}"]})
P=pd.DataFrame(preds); P.to_csv(os.path.join(HERE,f"mh_quantiles_frozen_{TAG}.csv"),index=False)
print(f"[{TAG}] DONE rows={len(P)} {time.time()-t0:.0f}s",flush=True)
for h in [21,63]:
    sub=P[(P.h==h)&P.y.notna()]
    line=f"[{TAG}] h={h} n={len(sub)} "
    for tt in [.05,.50,.95]: line+=f"{tt:.2f}->{float((sub.y<sub[f'p{int(tt*100):02d}']).mean()):.3f} "
    print(line,flush=True)
