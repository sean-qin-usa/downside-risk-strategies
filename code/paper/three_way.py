# THREE-WAY side-by-side: GARCH-t vs GBM(boosted-tree quantile) vs IQN(neural, GBC) on the full CRSP panel, overall + by volatility regime. Runs on ai2 GPU.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, torch, torch.nn as nn
from sklearn.ensemble import HistGradientBoostingRegressor
from scipy import stats
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
dev='cuda' if torch.cuda.is_available() else 'cpu'; lg("device=%s"%dev)
TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
def pin(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
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
r=r.dropna(subset=['lag1','rv21']); r['abs1']=r['abs1'].fillna(r['abs1'].median())
XC=['lag1','abs1','rv5','rv21','mean21','dn','age','logmcap','sector','beta','annvol']
rng=np.random.default_rng(11); names=r['permno'].unique(); rng.shuffle(names); hold=set(names[:int(len(names)*0.4)])
tr=r[~r.permno.isin(hold)]
Xtr=tr[XC].values.astype('float32'); ytr=tr['ret'].values.astype('float32')
mu=Xtr.mean(0); sd=Xtr.std(0)+1e-6
# amortized GBM
GBM={}
for t in TAUS:
    m=HistGradientBoostingRegressor(loss='quantile',quantile=t,max_iter=200,max_depth=4,learning_rate=0.06); m.fit(Xtr,ytr); GBM[t]=m
lg("GBM trained %.0fs"%(time.time()-t0))
# amortized neural IQN
class IQN(nn.Module):
    def __init__(s,din,nc=64,h=128):
        super().__init__(); s.phi=nn.Sequential(nn.Linear(din,h),nn.ReLU(),nn.Linear(h,h),nn.ReLU()); s.cos=nn.Linear(nc,h)
        s.out=nn.Sequential(nn.ReLU(),nn.Linear(h,h),nn.ReLU(),nn.Linear(h,1)); s.register_buffer('ii',torch.arange(1,nc+1).float()*np.pi)
    def forward(s,x,tau): f=s.phi(x); c=torch.relu(s.cos(torch.cos(tau.unsqueeze(1)*s.ii))); return s.out(f*c).squeeze(1)
torch.manual_seed(0); model=IQN(len(XC)).to(dev); opt=torch.optim.Adam(model.parameters(),1e-3)
Xt=torch.tensor((Xtr-mu)/sd,device=dev); yt=torch.tensor(ytr,device=dev); B=16384
for ep in range(12):
    perm=torch.randperm(len(Xt),device=dev)
    for i in range(0,len(Xt),B):
        idx=perm[i:i+B]; tau=torch.rand(len(idx),device=dev); q=model(Xt[idx],tau); e=yt[idx]-q
        loss=torch.mean(torch.maximum(tau*e,(tau-1)*e)); opt.zero_grad(); loss.backward(); opt.step()
lg("IQN trained %.0fs"%(time.time()-t0)); model.eval()
from arch import arch_model
recs=[]  # (rv21, garch_pin, gbm_pin, iqn_pin)
done=0
for pn in [p for p in names if p in hold]:
    d=r[r.permno==pn]
    if len(d)<500: continue
    y=d['ret'].values; n=len(d); sp=int(n*0.6)
    try:
        res=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False)
        p=res.params; om,al,be,nu,muu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('nu',8)),float(p.get('mu',0))
    except Exception: continue
    e=y[:sp]-muu; s2=np.empty(len(e)); s2[0]=e.var()
    for k in range(1,len(e)): s2[k]=om+al*e[k-1]**2+be*s2[k-1]
    sig2=s2[-1]; tsc=math.sqrt(nu/(nu-2)) if nu>2 else 1.0
    X=d[XC].values.astype('float32'); rv=d['rv21'].values
    gbmp={t:GBM[t].predict(X[sp:]) for t in TAUS}
    with torch.no_grad():
        Xe=torch.tensor((X[sp:]-mu)/sd,device=dev); iqnp={t:model(Xe,torch.full((len(Xe),),float(t),device=dev)).cpu().numpy() for t in TAUS}
    for j,i in enumerate(range(sp,n)):
        sig2=om+al*(y[i-1]-muu)**2+be*sig2; sig=math.sqrt(max(sig2,1e-9)); yi=y[i]
        gp=np.mean([pin(yi,muu+sig*stats.t.ppf(t,nu)/tsc,t) for t in TAUS])
        gm=np.mean([pin(yi,gbmp[t][j],t) for t in TAUS]); iq=np.mean([pin(yi,iqnp[t][j],t) for t in TAUS])
        recs.append((rv[i],gp,gm,iq))
    done+=1
    if done%30==0: lg("processed %d names, %d days %.0fs"%(done,len(recs),time.time()-t0))
A=np.array(recs); rv=A[:,0]; gp=A[:,1]; gm=A[:,2]; iq=A[:,3]
qs=np.quantile(rv,[0.2,0.4,0.6,0.8]); idx=np.digitize(rv,qs); lab=['Q1_calm','Q2','Q3','Q4','Q5_turbulent']
out={'note':'THREE-WAY side by side: GARCH-t (parametric) vs GBM (boosted-tree quantile) vs IQN (neural, GBC/Polson), amortized on full CRSP panel, per test-day pinball, overall + by realized-vol quintile. Lower=better.','device':dev,'n_names':int(done),'n_testdays':int(len(A)),
 'overall':{'garch':round(float(gp.mean()),4),'gbm':round(float(gm.mean()),4),'iqn':round(float(iq.mean()),4)},'by_vol_quintile':{}}
for qi in range(5):
    m=idx==qi
    if m.sum()<100: continue
    out['by_vol_quintile'][lab[qi]]=dict(n=int(m.sum()),garch=round(float(gp[m].mean()),4),gbm=round(float(gm[m].mean()),4),iqn=round(float(iq[m].mean()),4),gbm_vs_garch=round(float(gm[m].mean()/gp[m].mean()),4),iqn_vs_garch=round(float(iq[m].mean()/gp[m].mean()),4))
json.dump(out,open(os.path.join(D,"three_way_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
