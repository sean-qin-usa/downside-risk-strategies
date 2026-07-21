# NEURAL WEIGHT-INPUT IQN for CO-CRASH (ai2, torch) — the elegant co-crash test after direct-GBM was ruled out.
# Learn Q(tau | state_t, w): ONE network prices the tau-quantile of the next-day return of ANY portfolio w on the simplex.
# Weight vector w is sampled each batch (incl. concentrated corners), so tail co-movement must be learned as: concentrated-w
# portfolios have fatter downside than diversification predicts. Compare to CCC-GARCH & DCC-lite on held-out portfolios,
# especially CONCENTRATED ones (where v1/v2 direct-GBM lost). Hypothesis: sharing one net across all w beats per-basket fits.
import os, json, time, math, warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
from arch import arch_model
import torch, torch.nn as nn
D=os.path.expanduser("~/sean_dev/GBC_data"); t0=time.time(); lg=lambda s:print(s,flush=True)
dev='cuda' if torch.cuda.is_available() else 'cpu'; torch.manual_seed(0); np.random.seed(0)
TAUS=np.array([0.01,0.025,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.975,0.99])
rr=pd.read_csv(os.path.join(D,"crsp_panel_returns.csv"),dtype={'permno':'int32'})
rr['date']=pd.to_datetime(rr['date']); rr['ret']=pd.to_numeric(rr['ret'],errors='coerce')*100.0
ch=pd.read_csv(os.path.join(D,"crsp_panel_chars.csv"))
lc=ch[ch['cohort']=='largecap']['permno'].tolist() if 'cohort' in ch else ch['permno'].tolist()
W=rr[rr.permno.isin(lc)].pivot_table(index='date',columns='permno',values='ret')
W=W.dropna(axis=1,thresh=int(0.9*len(W))).dropna()
# order by avg pairwise corr so 'concentrated top-k' is genuinely co-crash-prone
C=np.corrcoef(W.values.T); avgc=(C.sum(1)-1)/(C.shape[1]-1); W=W[W.columns[np.argsort(-avgc)]]
if W.shape[1]>20: W=W.iloc[:,:20]
A=W.values.astype(np.float32); dates=W.index; n,N=A.shape; sp=int(n*0.6)
lg("panel %d days x %d names dev=%s %.0fs"%(n,N,dev,time.time()-t0))
# per-name causal EWMA vol + last return as state
ew=np.zeros_like(A); lam=0.94
for j in range(N):
    v=np.zeros(n); v[0]=A[:sp,j].var()
    for i in range(1,n): v[i]=lam*v[i-1]+(1-lam)*A[i-1,j]**2
    ew[:,j]=np.sqrt(v)
STATE=np.concatenate([ew, np.vstack([np.zeros((1,N),np.float32),A[:-1]])],axis=1).astype(np.float32)  # [vol(N), lastret(N)]
# ---- IQN net ----
class IQN(nn.Module):
    def __init__(s,din,ne=64,h=128):
        super().__init__(); s.ne=ne
        s.psi=nn.Sequential(nn.Linear(din,h),nn.ReLU(),nn.Linear(h,h),nn.ReLU())
        s.phi=nn.Sequential(nn.Linear(ne,h),nn.ReLU())
        s.out=nn.Sequential(nn.Linear(h,h),nn.ReLU(),nn.Linear(h,1))
        s.reg=torch.arange(1,ne+1,dtype=torch.float32)
    def forward(s,x,tau):                       # x:[B,din] tau:[B,1]
        b=x.shape[0]; cos=torch.cos(math.pi*s.reg.to(x.device)[None,:]*tau)  # [B,ne]
        return s.out(s.psi(x)*s.phi(cos)).squeeze(-1)
def simplex(b,N,conc):                            # sample weights; conc small => concentrated corners
    a=np.random.gamma(conc,1.0,size=(b,N)).astype(np.float32); return a/a.sum(1,keepdims=True)
din=2*N+N
net=IQN(din).to(dev); opt=torch.optim.Adam(net.parameters(),1e-3)
St=torch.tensor(STATE[:sp]).to(dev); Rt=torch.tensor(A[:sp]).to(dev)  # states/returns train; target uses next day
idx_all=np.arange(sp-1)
lg("train start %.0fs"%(time.time()-t0))
for step in range(4000):
    bi=np.random.choice(idx_all,256)
    conc=float(np.random.choice([0.2,0.5,1.0,3.0]))               # mix concentrated & diffuse portfolios
    w=torch.tensor(simplex(256,N,conc)).to(dev)
    st=St[bi]; y=(w*Rt[bi+1]).sum(1)                               # next-day portfolio return
    x=torch.cat([st,w],1)
    tau=torch.rand(256,1,device=dev)*0.98+0.01
    q=net(x,tau); d=y-q
    loss=torch.maximum(tau.squeeze(1)*d,(tau.squeeze(1)-1)*d).mean()
    opt.zero_grad(); loss.backward(); opt.step()
    if step%1000==0: lg("  step %d loss %.4f %.0fs"%(step,loss.item(),time.time()-t0))
net.eval()
# ---- GARCH CCC/DCC baselines (per fixed w, as in joint_tail) ----
vol=np.zeros((n,N)); nus=[]
for j in range(N):
    y=A[:,j]
    try:
        p=arch_model(y[:sp],vol='Garch',p=1,q=1,dist='t',rescale=False).fit(disp='off',show_warning=False).params
        om,al,be,mu=float(p['omega']),float(p['alpha[1]']),float(p['beta[1]']),float(p.get('mu',0)); nus.append(float(p.get('nu',8)))
    except Exception: om,al,be,mu=0.1,0.05,0.9,0.0; nus.append(8)
    e=y-mu; s2=np.empty(n); s2[0]=np.var(y[:sp])
    for k in range(1,n): s2[k]=max(om+al*e[k-1]**2+be*s2[k-1],1e-8)
    vol[:,j]=np.sqrt(s2)
nu_p=float(np.mean(nus)); Z=A/np.maximum(vol,1e-6); Rccc=np.corrcoef(Z[:sp].T); tsc=math.sqrt(nu_p/(nu_p-2))
Qt=Rccc.copy(); lam2=0.97; DCCr=[None]*n
for i in range(n):
    if i>0:
        z=Z[i-1]; Qt=(1-lam2)*np.outer(z,z)+lam2*Qt; dd=np.sqrt(np.clip(np.diag(Qt),1e-8,None)); DCCr[i]=Qt/np.outer(dd,dd)
    else: DCCr[i]=Rccc
def psig(Vt,Rt,w): return math.sqrt(max(w@(np.outer(Vt,Vt)*Rt)@w,1e-10))
def pinball(y,q,t): d=y-q; return np.where(d>=0,t*d,(t-1)*d)
teidx=np.arange(sp,n-1)
def eval_w(w):
    w=w.astype(np.float32); yv=(A[teidx+1]*w).sum(1)
    xs=np.concatenate([STATE[teidx], np.tile(w,(len(teidx),1))],1).astype(np.float32)
    xt=torch.tensor(xs).to(dev)
    pln=0.0
    with torch.no_grad():
        for t in TAUS:
            tau=torch.full((len(teidx),1),float(t),device=dev); q=net(xt,tau).cpu().numpy()
            pln+=pinball(yv,q,t).mean()
    pln/=len(TAUS)
    # CCC/DCC parametric quantiles
    def par(sig_i): return {t:sig_i*stats.t.ppf(t,nu_p)/tsc for t in TAUS}
    plc=0.0; pld=0.0
    for jj,i in enumerate(teidx):
        yi=yv[jj]; sc=psig(vol[i],Rccc,w); sd=psig(vol[i],DCCr[i],w)
        qc=par(sc); qd=par(sd)
        plc+=np.mean([pinball(yi,qc[t],t) for t in TAUS]); pld+=np.mean([pinball(yi,qd[t],t) for t in TAUS])
    return dict(wiqn=round(float(pln),4),ccc=round(plc/len(teidx),4),dcc=round(pld/len(teidx),4))
schemes={}
schemes['equal']=np.ones(N)/N
for k in (1,3,5):
    w=np.zeros(N); w[:k]=1.0/k; schemes['top%d'%k]=w
rng=np.random.default_rng(1); randres=[eval_w(rng.dirichlet(np.ones(N))) for _ in range(15)]
res={k:eval_w(w) for k,w in schemes.items()}
res['random_mean']={m:round(float(np.mean([r[m] for r in randres])),4) for m in ['wiqn','ccc','dcc']}
def win(d): return 'wiqn' if d['wiqn']<=min(d['ccc'],d['dcc']) else ('dcc' if d['dcc']<=d['ccc'] else 'ccc')
out={'note':'Neural weight-input IQN Q(tau|state,w) vs CCC-GARCH & DCC-lite on held-out portfolios. One net trained with w '
            'sampled from the simplex (incl. concentrated corners) prices every portfolio. Names ordered by pairwise corr so '
            'top-k are co-crash-prone. Lower pinball=better. Tests if amortizing across w beats per-basket multivariate GARCH, '
            'esp. concentrated. dev=%s'%dev,
     'n_days':int(n),'n_names':int(N),'nu_p':round(nu_p,1),'results':res,
     'winner_by_scheme':{k:win(v) for k,v in res.items()}}
json.dump(out,open(os.path.join(D,"neural_wiqn_results.json"),"w"),indent=2)
lg("DONE %.0fs"%(time.time()-t0)); lg(json.dumps(out,indent=2))
