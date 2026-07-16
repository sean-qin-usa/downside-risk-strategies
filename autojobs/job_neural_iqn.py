# NEURAL IQN (the real architecture) amortized on CRSP panel — does it match the gradient-boosting stand-in? Try local torch; else flag for ai2.
import os, json, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
out={}
try:
    import torch, torch.nn as nn
    out['torch']=torch.__version__; lg("torch "+torch.__version__)
except Exception as e:
    json.dump({'torch':False,'note':'torch not in this env -> run neural IQN on ai2 (has torch+cuda). GBM stand-in result stands.','err':str(e)[:120]},open(os.path.join(P,"neural_iqn.json"),"w"),indent=2)
    lg("NO TORCH -> ai2 needed"); raise SystemExit
import numpy as np, pandas as pd
from arch import arch_model
from scipy import stats as sps
rets=pd.read_csv(os.path.join(P,"crsp_panel_returns.csv")); rets['date']=pd.to_datetime(rets['date']); rets['ret']=pd.to_numeric(rets['ret'],errors='coerce')*100
ch=pd.read_csv(os.path.join(P,"crsp_panel_chars.csv")); chd={int(r.permno):r for r in ch.itertuples()}
def build(g):
    g=g.sort_values('date'); r=g['ret']; d=pd.DataFrame({'permno':g['permno'].values,'y':r.values})
    d['lag1']=r.shift(1).values; d['abs1']=r.abs().shift(1).values; d['rv5']=r.rolling(5).std().shift(1).values
    d['rv21']=r.rolling(21).std().shift(1).values; d['mean21']=r.rolling(21).mean().shift(1).values; d['dn']=(r.shift(1)<0).astype(float).values; d['age']=np.arange(len(g))
    return d
D=pd.concat([build(g) for _,g in rets.groupby('permno')],ignore_index=True).dropna(subset=['lag1','rv21'])
D['cohort']=D.permno.map(lambda p:getattr(chd.get(int(p)),'cohort',None))
D['logmcap']=D.permno.map(lambda p:math.log(max(getattr(chd.get(int(p)),'mcap_mm',100) or 100,1)))
D['beta']=pd.to_numeric(D.permno.map(lambda p:getattr(chd.get(int(p)),'beta',None)),errors='coerce').fillna(1.0)
D['sector']=D.permno.map(lambda p:getattr(chd.get(int(p)),'sector',0) or 0); D['logage']=np.log(D['age']+1)
rng=np.random.default_rng(3); hold=set()
for c in ['recent_ipo','smallcap','largecap']:
    cn=ch[ch.cohort==c]['permno'].astype(int).values; rng.shuffle(cn); hold|=set(cn[:int(len(cn)*0.4)])
D['held']=D.permno.isin(hold); Xc=['lag1','abs1','rv5','rv21','mean21','dn','logmcap','beta','sector','logage']
tr=D[~D.held]; te=D[D.held]; TAUS=[0.05,0.10,0.25,0.50,0.75,0.90,0.95]
mu=tr[Xc].mean().values; sd=tr[Xc].std().values+1e-8
Xtr=((tr[Xc].values-mu)/sd).astype('float32'); ytr=tr['y'].values.astype('float32')
Xte=((te[Xc].values-mu)/sd).astype('float32')
class IQN(nn.Module):
    def __init__(s,nf,emb=64,ncos=48,hid=64):
        super().__init__(); s.register_buffer('ipi',torch.arange(ncos).float()*math.pi)
        s.psi=nn.Sequential(nn.Linear(nf,hid),nn.ReLU(),nn.Linear(hid,emb),nn.ReLU())
        s.phi=nn.Linear(ncos,emb); s.head=nn.Sequential(nn.Linear(emb,hid),nn.ReLU(),nn.Linear(hid,1))
    def forward(s,x,tau):
        h=s.psi(x)[:,None,:]; c=torch.cos(tau[...,None]*s.ipi); p=torch.relu(s.phi(c)); return s.head(h*p)[...,0]
dev='cpu'; net=IQN(len(Xc)).to(dev); opt=torch.optim.Adam(net.parameters(),1e-3)
Xt=torch.tensor(Xtr); yt=torch.tensor(ytr); n=len(Xt); bs=8192; g=torch.Generator().manual_seed(0)
lg("training IQN n=%d %.0fs"%(n,time.time()-t0))
for ep in range(45):
    perm=torch.randperm(n,generator=g)
    for i in range(0,n,bs):
        idx=perm[i:i+bs]; xb=Xt[idx]; yb=yt[idx]
        tau=torch.rand(len(idx),8,generator=g).clamp(1e-3,1-1e-3)
        q=net(xb,tau); u=yb[:,None]-q; loss=(u*(tau-(u<0).float())).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    if ep%10==0: lg(f"  ep{ep} loss {loss.item():.4f} {time.time()-t0:.0f}s")
net.eval()
with torch.no_grad():
    tg=torch.tensor(np.array(TAUS,dtype='float32')).repeat(len(Xte),1); pred=net(torch.tensor(Xte),tg).numpy()
pred=np.sort(pred,axis=1)
te=te.copy()
for j,tau in enumerate(TAUS): te[f'n{tau}']=pred[:,j]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
def garch_q(y):
    y=np.asarray(y,float)
    if len(y)<250: return None
    try:
        am=arch_model(y-y.mean(),mean='Zero',vol='GARCH',p=1,o=1,q=1,dist='t').fit(disp='off'); nu=float(am.params.get('nu',8)); sig=am.conditional_volatility; m=float(y.mean()); std=math.sqrt(nu/(nu-2)) if nu>2.05 else 1.0
        return {tau:m+sig*(sps.t.ppf(tau,nu)/std) for tau in TAUS}
    except Exception: return None
rows=[]
for pn,gg in te.groupby('permno'):
    gg=gg.sort_values('date'); y=gg['y'].values; coh=gg['cohort'].iloc[0]
    ln=float(np.nanmean([np.nanmean(pin(y,gg[f'n{tau}'].values,tau)) for tau in TAUS]))
    gq=garch_q(y); lgv=float(np.nanmean([np.nanmean(pin(y,gq[tau],tau)) for tau in TAUS])) if gq else None
    rows.append((coh,ln,lgv))
df=pd.DataFrame(rows,columns=['cohort','iqn','garch'])
out['by_cohort']={}
for c in ['recent_ipo','smallcap','largecap']:
    a=df[(df.cohort==c)]; g2=a.dropna(subset=['garch'])
    out['by_cohort'][c]=dict(n=int(len(a)),iqn_pinball=round(float(a.iqn.mean()),4),garch_pinball=round(float(g2.garch.mean()),4) if len(g2) else None,ratio_iqn_over_garch=round(float(g2.iqn.mean()/g2.garch.mean()),3) if len(g2) else None)
out['note']='NEURAL IQN (cosine-embedding, amortized on characteristics) vs per-name GARCH on held-out unseen names. Compare ratios to GBM stand-in (amort_v2).'
json.dump(out,open(os.path.join(P,"neural_iqn.json"),"w"),indent=2,default=str)
lg("NEURAL_IQN\n"+json.dumps(out['by_cohort'],indent=2,default=str)); lg("DONE %.0fs"%(time.time()-t0))
