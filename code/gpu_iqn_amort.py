# NEURAL IQN amortized on CRSP panel — runs on ai2 GPU. Reads panel from cwd. Saves neural_iqn_ai2.json.
import os, json, time, math
HERE=os.path.dirname(os.path.abspath(__file__)); lg=lambda s:print(s,flush=True); t0=time.time()
import numpy as np, pandas as pd, torch, torch.nn as nn
dev='cuda' if torch.cuda.is_available() else 'cpu'; lg("dev "+dev+" torch "+torch.__version__)
rets=pd.read_csv(os.path.join(HERE,"crsp_panel_returns.csv")); rets['date']=pd.to_datetime(rets['date']); rets['ret']=pd.to_numeric(rets['ret'],errors='coerce')*100
ch=pd.read_csv(os.path.join(HERE,"crsp_panel_chars.csv")); chd={int(r.permno):r for r in ch.itertuples()}
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
Xtr=((tr[Xc].values-mu)/sd).astype('float32'); ytr=tr['y'].values.astype('float32'); Xte=((te[Xc].values-mu)/sd).astype('float32')
class IQN(nn.Module):
    def __init__(s,nf,emb=96,ncos=64,hid=96):
        super().__init__(); s.register_buffer('ipi',torch.arange(ncos).float()*math.pi)
        s.psi=nn.Sequential(nn.Linear(nf,hid),nn.ReLU(),nn.Linear(hid,emb),nn.ReLU()); s.phi=nn.Linear(ncos,emb); s.head=nn.Sequential(nn.Linear(emb,hid),nn.ReLU(),nn.Linear(hid,1))
    def forward(s,x,tau):
        h=s.psi(x)[:,None,:]; c=torch.cos(tau[...,None]*s.ipi); p=torch.relu(s.phi(c)); return s.head(h*p)[...,0]
net=IQN(len(Xc)).to(dev); opt=torch.optim.Adam(net.parameters(),1e-3)
Xt=torch.tensor(Xtr,device=dev); yt=torch.tensor(ytr,device=dev); n=len(Xt); bs=16384; g=torch.Generator(device=dev).manual_seed(0)
lg("training n=%d %.0fs"%(n,time.time()-t0))
for ep in range(80):
    perm=torch.randperm(n,generator=g,device=dev)
    for i in range(0,n,bs):
        idx=perm[i:i+bs]; xb=Xt[idx]; yb=yt[idx]; tau=torch.rand(len(idx),8,generator=g,device=dev).clamp(1e-3,1-1e-3)
        q=net(xb,tau); u=yb[:,None]-q; loss=(u*(tau-(u<0).float())).mean(); opt.zero_grad(); loss.backward(); opt.step()
    if ep%20==0: lg(f"  ep{ep} loss {loss.item():.4f} {time.time()-t0:.0f}s")
net.eval()
with torch.no_grad():
    tg=torch.tensor(np.array(TAUS,dtype='float32'),device=dev).repeat(len(Xte),1); pred=net(torch.tensor(Xte,device=dev),tg).cpu().numpy()
pred=np.sort(pred,axis=1); te=te.copy()
for j,tau in enumerate(TAUS): te[f'n{tau}']=pred[:,j]
def pin(y,q,tau): d=y-q; return np.where(d>=0,tau*d,(tau-1)*d)
# NOTE: ai2 lacks 'arch' -> report IQN pinball per cohort (all + hist>=250 subset). Compare to amort_v2 GARCH numbers locally (same panel/split seed=3): IPO 0.919, small 0.6791, large 0.3523.
rows=[]
for pn,gg in te.groupby('permno'):
    y=gg['y'].values; coh=gg['cohort'].iloc[0]; hist=len(gg)
    ln=float(np.nanmean([np.nanmean(pin(y,gg[f'n{tau}'].values,tau)) for tau in TAUS]))
    rows.append((coh,hist,ln))
df=pd.DataFrame(rows,columns=['cohort','hist','iqn']); out={'dev':dev,'torch':torch.__version__,'by_cohort':{}}
GARCH_REF={'recent_ipo':0.919,'smallcap':0.6791,'largecap':0.3523}  # from amort_v2 (same split), for the >=250d subset
for c in ['recent_ipo','smallcap','largecap']:
    a=df[df.cohort==c]; fit=a[a.hist>=250]
    out['by_cohort'][c]=dict(n=int(len(a)),iqn_all=round(float(a.iqn.mean()),4),
        iqn_fittable_subset=round(float(fit.iqn.mean()),4) if len(fit) else None,
        garch_ref_amort_v2=GARCH_REF.get(c),
        ratio_iqn_over_garch=round(float(fit.iqn.mean()/GARCH_REF[c]),3) if len(fit) else None)
out['note']='NEURAL IQN (GPU) amortized. iqn_fittable_subset vs garch_ref (from amort_v2, same panel/split). Compare ratio to GBM stand-in (amort_v2: IPO 0.998, small 0.995, large 0.99).'
json.dump(out,open(os.path.join(HERE,"neural_iqn_ai2.json"),"w"),indent=2,default=str)
lg("NEURAL_AI2\n"+json.dumps(out['by_cohort'],indent=2,default=str)); lg("DONE %.0fs"%(time.time()-t0))
