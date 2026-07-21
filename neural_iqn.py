# Neural Implicit Quantile Network (IQN) vs gradient-boosted quantile (GBM), amortized on the full CRSP panel. Runs on ai2 GPU.
import os, json, time, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, torch, torch.nn as nn
from sklearn.ensemble import HistGradientBoostingRegressor
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
dev='cuda' if torch.cuda.is_available() else 'cpu'; lg("device=%s"%dev)
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin_np(y,q,t): e=y-q; return np.where(e>=0,t*e,(t-1)*e)
# ---- features (same pipeline as amort_full) ----
r=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),usecols=['permno','ret'],dtype={'permno':'int32','ret':'float32'})
ch=pd.read_csv(os.path.join(D,"crsp_panel_chars.csv")); r['ret']=r['ret'].astype(float)*100.0
g=r.groupby('permno',sort=False); r['age']=g.cumcount()
r['lag1']=g['ret'].shift(1); r['abs1']=r['lag1'].abs()
r['rv5']=g['ret'].transform(lambda x:x.rolling(5,min_periods=3).std().shift(1))
r['rv21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).std().shift(1))
r['mean21']=g['ret'].transform(lambda x:x.rolling(21,min_periods=8).mean().shift(1))
r['dn']=(r['lag1']<0).astype(float)
ch['logmcap']=np.log(np.maximum(pd.to_numeric(ch['mcap_mm'],errors='coerce').fillna(300.0),1.0))
for c in ['sector','beta','annvol']: ch[c]=pd.to_numeric(ch[c],errors='coerce')
r=r.merge(ch[['permno','logmcap','sector','beta','annvol']],on='permno',how='left')
r['sector']=r['sector'].fillna(-1); r['beta']=r['beta'].fillna(1.0); r['annvol']=r['annvol'].fillna(0.3)
r['rv5']=r['rv5'].fillna(r['rv21']).fillna(2.0); r['rv21']=r['rv21'].fillna(2.0); r['mean21']=r['mean21'].fillna(0.0)
r=r.dropna(subset=['lag1']); r['abs1']=r['abs1'].fillna(r['abs1'].median())
XC=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
rng=np.random.default_rng(11); names=r['permno'].unique(); rng.shuffle(names); hold=set(names[:int(len(names)*0.4)])
tr=r[~r.permno.isin(hold)]; te=r[r.permno.isin(hold)].reset_index(drop=True)
Xtr=tr[XC].values.astype('float32'); ytr=tr['ret'].values.astype('float32'); Xte=te[XC].values.astype('float32'); yte=te['ret'].values.astype('float32')
age=te['age'].values.astype(float)
mu=Xtr.mean(0); sd=Xtr.std(0)+1e-6; Xtrs=(Xtr-mu)/sd; Xtes=(Xte-mu)/sd
lg("features ready tr=%d te=%d %.0fs"%(len(Xtr),len(Xte),time.time()-t0))
# ---- IQN model (Dabney et al. cosine tau-embedding) ----
class IQN(nn.Module):
    def __init__(s,din,nc=64,h=128):
        super().__init__(); s.nc=nc
        s.phi=nn.Sequential(nn.Linear(din,h),nn.ReLU(),nn.Linear(h,h),nn.ReLU())
        s.cos=nn.Linear(nc,h)
        s.out=nn.Sequential(nn.ReLU(),nn.Linear(h,h),nn.ReLU(),nn.Linear(h,1))
        s.register_buffer('ii',torch.arange(1,nc+1).float()*np.pi)
    def forward(s,x,tau):
        f=s.phi(x); c=torch.relu(s.cos(torch.cos(tau.unsqueeze(1)*s.ii))); return s.out(f*c).squeeze(1)
torch.manual_seed(0); model=IQN(len(XC)).to(dev); opt=torch.optim.Adam(model.parameters(),1e-3)
Xt=torch.tensor(Xtrs,device=dev); yt=torch.tensor(ytr,device=dev); B=16384
for ep in range(12):
    perm=torch.randperm(len(Xt),device=dev)
    for i in range(0,len(Xt),B):
        idx=perm[i:i+B]; xb=Xt[idx]; yb=yt[idx]; tau=torch.rand(len(idx),device=dev)
        q=model(xb,tau); e=yb-q; loss=torch.mean(torch.maximum(tau*e,(tau-1)*e))
        opt.zero_grad(); loss.backward(); opt.step()
    lg("epoch %d loss %.4f %.0fs"%(ep,loss.item(),time.time()-t0))
# eval neural on 7 taus
model.eval(); Xe=torch.tensor(Xtes,device=dev); NP={}
with torch.no_grad():
    for t in TAUS:
        tt=torch.full((len(Xe),),t,device=dev); NP[t]=model(Xe,tt).cpu().numpy()
# ---- GBM baseline (same split, 7 taus) ----
GB={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=250,max_depth=4,learning_rate=0.06,max_bins=128); m.fit(Xtr,ytr); GB[t]=m.predict(Xte)
lg("GBM baseline trained %.0fs"%(time.time()-t0))
def avgpin(P,mask=None):
    tot=0.0
    for t in TAUS:
        d=pin_np(yte,P[t],t); tot+=np.mean(d[mask]) if mask is not None else np.mean(d)
    return tot/len(TAUS)
BUCK=[('d15_60',15,60),('d60_250',60,250),('d250_1000',250,1000),('d1000_2700',1000,2700)]
out={'note':'Neural IQN (tau-conditioned MLP, Dabney-style cosine embedding) vs gradient-boosted quantile (GBM), amortized on full CRSP panel. Avg pinball over 7 taus, held-out names. Lower=better; ratio<1 means neural better.','device':dev,'n_train':int(len(Xtr)),'n_test':int(len(Xte)),
 'overall':{'neural_iqn':round(avgpin(NP),4),'gbm':round(avgpin(GB),4),'neural_vs_gbm':round(avgpin(NP)/avgpin(GB),4)},'by_age':{}}
for bn,lo,hi in BUCK:
    m=(age>=lo)&(age<hi)&(age>=12)
    if m.sum()<50: continue
    n=avgpin(NP,m); gb=avgpin(GB,m); out['by_age'][bn]=dict(n=int(m.sum()),neural_iqn=round(n,4),gbm=round(gb,4),neural_vs_gbm=round(n/gb,4))
json.dump(out,open(os.path.join(D,"neural_iqn_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
