# TAIL-AWARE NEURAL IQN (ai2 GPU) — close the neural-vs-tree gap on the headline conditional-VaR pinball table.
# Hypothesis: plain IQN (uniform tau) underfits the deep tail vs gradient-boosted trees; TAIL-WEIGHTED tau sampling +
# loss weighting + monotone (sorted) output narrows/closes the gap at tau in {0.01,0.025,0.05}. Amortized conditional
# quantile model over per-name features; temporal OOS. Baselines: GARCH-t (parametric anchor), GBM (trees), IQN-uniform.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
NMAX=int(os.environ.get("NMAX","120")); TAILS=[0.01,0.025,0.05]
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
cnt=rr.groupby('permno')['ret'].count().sort_values(ascending=False); names=cnt[cnt>=1500].index.tolist()[:NMAX]
lg("names=%d %.0fs"%(len(names),time.time()-t0))
# ---- build pooled feature matrix: features at t use info to t-1; target y_t = r_t ----
rows=[]; ys=[]; dts=[]; grp=[]
for gi,pn in enumerate(names):
    g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); d=g['date'].values; n=len(y)
    if n<400: continue
    ew=np.zeros(n); ew[0]=np.std(y[:60]); lam=0.94
    for i in range(1,n): ew[i]=math.sqrt(max(lam*ew[i-1]**2+(1-lam)*y[i-1]**2,1e-8))
    for t in range(30,n):
        v=max(ew[t],1e-6)
        feat=[math.log(v)]+[y[t-k]/v for k in range(1,6)]+[y[t-5:t].mean()/v, y[t-20:t].std()/v if t>=20 else 0.0]
        rows.append(feat); ys.append(y[t]); dts.append(d[t]); grp.append(gi)
X=np.array(rows,np.float32); Y=np.array(ys,np.float32); DT=np.array(dts); G=np.array(grp)
cut=np.quantile(DT,0.6); tr=DT<cut; te=~tr
mu=X[tr].mean(0); sd=X[tr].std(0)+1e-6; Xn=((X-mu)/sd).astype(np.float32)
lg("rows=%d train=%d test=%d feat=%d %.0fs"%(len(Y),tr.sum(),te.sum(),X.shape[1],time.time()-t0))
def pinball_np(r,q,a): d=r-q; return np.where(d>=0,a*d,(a-1)*d)
res={'note':'Tail-aware neural IQN vs trees vs GARCH-t on conditional VaR. avg pinball at tail taus, lower=better. '
            'iqn_tail = tail-weighted tau sampling + loss weight + monotone output; iqn_unif = uniform tau. gap = iqn_tail - gbm.',
     'n_names':int(len(names)),'n_test':int(te.sum()),'tails':TAILS,'models':{}}
# ---- GARCH-t parametric anchor (per name, pinball at test rows) ----
try:
    from arch import arch_model
    gpin={a:[] for a in TAILS}
    for gi,pn in enumerate(names):
        g=rr[rr.permno==pn].sort_values('date'); y=g['ret'].values.astype(float); n=len(y); sp=int(n*0.6)
        try:
            m=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False); p=m.params
            om,al,be,muu,nu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)),float(p.get('nu',8))
        except Exception: continue
        e=y-muu; s2=np.empty(n); s2[0]=np.var(y[:sp])
        for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
        sig=np.sqrt(s2); scale=math.sqrt(max((nu-2)/nu,1e-6))
        for a in TAILS:
            zq=scale*stats.t.ppf(a,nu)
            for k in range(sp,n): gpin[a].append(pinball_np(y[k],muu+sig[k]*zq,a))
    res['models']['garch_t']={('pinball_%g'%a):round(float(np.mean(gpin[a])),4) for a in TAILS}
except Exception as ex: res['models']['garch_t']={'error':str(ex)}
# ---- GBM trees baseline (quantile) ----
try:
    import lightgbm as lgb; TREES='lightgbm'
    def fit_q(a):
        m=lgb.LGBMRegressor(objective='quantile',alpha=a,n_estimators=300,num_leaves=31,learning_rate=0.05,min_child_samples=50,verbose=-1)
        m.fit(Xn[tr],Y[tr]); return m.predict(Xn[te])
except Exception:
    from sklearn.ensemble import GradientBoostingRegressor; TREES='sklearn'
    sub=np.where(tr)[0]; sub=np.random.default_rng(0).choice(sub,min(120000,len(sub)),replace=False)
    def fit_q(a):
        m=GradientBoostingRegressor(loss='quantile',alpha=a,n_estimators=200,max_depth=3,learning_rate=0.05,subsample=0.7)
        m.fit(Xn[sub],Y[sub]); return m.predict(Xn[te])
gbm={}
for a in TAILS: gbm[a]=float(np.mean(pinball_np(Y[te],fit_q(a),a)))
res['models']['gbm']={('pinball_%g'%a):round(gbm[a],4) for a in TAILS}; res['trees']=TREES
lg("GBM(%s) done %.0fs"%(TREES,time.time()-t0))
# ---- IQN (torch, GPU): uniform vs tail-aware ----
import torch, torch.nn as nn
dev='cuda' if torch.cuda.is_available() else 'cpu'; torch.manual_seed(0)
Xt=torch.tensor(Xn); Yt=torch.tensor(Y); trmask=torch.tensor(tr); temask=torch.tensor(te)
Xtr=Xt[trmask].to(dev); Ytr=Yt[trmask].to(dev); Xte=Xt[temask].to(dev)
class IQN(nn.Module):
    def __init__(s,din,ne=64,h=128):
        super().__init__(); s.psi=nn.Sequential(nn.Linear(din,h),nn.ReLU(),nn.Linear(h,h),nn.ReLU())
        s.phi=nn.Sequential(nn.Linear(ne,h),nn.ReLU()); s.out=nn.Sequential(nn.Linear(h,h),nn.ReLU(),nn.Linear(h,1))
        s.reg=torch.arange(1,ne+1,dtype=torch.float32)
    def forward(s,x,tau): return s.out(s.psi(x)*s.phi(torch.cos(math.pi*s.reg.to(x.device)[None,:]*tau))).squeeze(-1)
def train_iqn(tail_aware):
    net=IQN(Xtr.shape[1]).to(dev); opt=torch.optim.Adam(net.parameters(),1e-3); N=Xtr.shape[0]
    for step in range(8000):
        idx=torch.randint(0,N,(512,),device=dev); x=Xtr[idx]; y=Ytr[idx]
        if tail_aware:
            u=torch.rand(512,1,device=dev); tau=torch.where(u<0.5,torch.rand(512,1,device=dev)*0.10,torch.rand(512,1,device=dev))
            w=(1.0/(tau.squeeze(1)+0.05)); w=w/w.mean()
        else:
            tau=torch.rand(512,1,device=dev); w=torch.ones(512,device=dev)
        q=net(x,tau); d=y-q; pl=torch.maximum(tau.squeeze(1)*d,(tau.squeeze(1)-1)*d)
        loss=(w*pl).mean(); opt.zero_grad(); loss.backward(); opt.step()
    net.eval(); out={}
    with torch.no_grad():
        # monotone: evaluate a sorted tau grid incl tails, then pick each tail level
        allt=sorted(set(TAILS)|{0.005,0.02,0.03,0.075,0.1})
        Qs=np.stack([net(Xte,torch.full((Xte.shape[0],1),float(t),device=dev)).cpu().numpy() for t in allt],1)
        Qs=np.sort(Qs,1); pos={t:i for i,t in enumerate(allt)}
        for a in TAILS: out[a]=float(np.mean(pinball_np(Y[te],Qs[:,pos[a]],a)))
    return out
iu=train_iqn(False); lg("iqn_unif done %.0fs"%(time.time()-t0)); it=train_iqn(True); lg("iqn_tail done %.0fs"%(time.time()-t0))
res['models']['iqn_unif']={('pinball_%g'%a):round(iu[a],4) for a in TAILS}
res['models']['iqn_tail']={('pinball_%g'%a):round(it[a],4) for a in TAILS}
res['gap_iqn_tail_minus_gbm']={('pinball_%g'%a):round(it[a]-gbm[a],4) for a in TAILS}
res['gap_iqn_tail_minus_unif']={('pinball_%g'%a):round(it[a]-iu[a],4) for a in TAILS}
res['dev']=dev
json.dump(res,open(os.path.join(D,"tail_iqn_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(res,indent=2))
