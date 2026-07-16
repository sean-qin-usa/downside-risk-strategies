import os, glob, json, time, math
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
t0=time.time(); lg=lambda s:print(s,flush=True)
sec=pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']); sec['secid']=sec['secid'].astype(int)
sym={int(r.secid):str(r.ticker) for r in sec.itertuples()}
d23=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"), usecols=['secid','open_interest'])
uni=[int(s) for s in d23.groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:40]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
        t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def pxat(s,dt):
    ser=px.get(s)
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
# CORRECT vix load: exact ticker match
def volser(tick):
    for fn in ['vol_indices.csv','bbg_impvol.csv']:
        p=os.path.join(RAW,fn)
        if not os.path.exists(p): continue
        v=pd.read_csv(p); cl={c.lower():c for c in v.columns}
        tc,dc,fc,vc=cl.get('ticker'),cl.get('date'),cl.get('field'),cl.get('value')
        if not(tc and dc and vc): continue
        m=v[v[tc].astype(str).str.strip().isin([tick, tick+' Index', tick+' INDEX'])]
        if fc is not None: m=m[m[fc].astype(str).str.contains('PX_LAST',case=False,na=False)]
        if len(m)==0: continue
        m=m[[dc,vc]].dropna(); m[dc]=pd.to_datetime(m[dc]); return m.set_index(dc)[vc].sort_index().astype(float)
    return None
vix=volser('VIX'); vix3=volser('VIX3M')
lg("vix max %.1f (should be ~80 not ~150)"%(vix.max() if vix is not None else -1))
def vat(s,dt):
    if s is None: return np.nan
    x=s[:dt]; return float(x.iloc[-1]) if len(x) else np.nan
tr=[]
for f in sorted(glob.glob(os.path.join(W,"spreads_[12]*.csv.gz"))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    d=pd.concat([c[c.secid.isin(uni)] for c in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','impl_volatility','delta'],chunksize=1000000)])
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.impl_volatility>0)&(d.delta<0)]; d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        row=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; dl=float(row.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        Se=K*math.exp(-ppf(-dl)*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,row.date); p1=pxat(s,row.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); net=(row.best_bid-max(K-Sx,0.0))/K
        vx=vat(vix,row.date); v3=vat(vix3,row.date)
        tr.append((s,row.date,net,sig,vx,(vx/v3 if (v3 and v3>0) else np.nan),row.date.month))
T=pd.DataFrame(tr,columns=['secid','date','net','iv','vix','vxr','mo']); T['ym']=T['date'].dt.to_period('M')
# name's own IV elevated: sig above its rolling 6-entry median per secid
T=T.sort_values(['secid','date'])
T['ivmed']=T.groupby('secid')['iv'].transform(lambda s:s.rolling(6,min_periods=3).median())
T['iv_elev']=T['iv']>T['ivmed']
def stat(mask,label):
    x=T[mask]; m=x.groupby('ym')['net'].mean()
    return dict(gate=label, frac_traded=round(len(x)/len(T),2),
                SR=round(float(m.mean()/m.std()*np.sqrt(12)),2) if m.std()>0 else None,
                ann_ret_pctK=round(m.mean()*12*100,2), worst_mo_pctK=round(m.min()*100,1), n=len(x))
res=[stat(T.net==T.net,"BASELINE all"),
     stat(T.iv_elev,"sell only IV-elevated (vs name's own median)"),
     stat(T.vxr<1,"VIX contango (vix<vix3m)"),
     stat(T.vxr>=1,"VIX inverted (vix>=vix3m)"),
     stat(T.vix>T.vix.median(),"VIX above median"),
     stat(T.vix<=T.vix.median(),"VIX below median (complacent)"),
     stat(~T.mo.isin([2]),"skip February"),
     stat(T.iv_elev & (~T.mo.isin([2])),"COMPOSITE: IV-elev & not-Feb"),
     stat(T.iv_elev & (T.vxr<1) & (~T.mo.isin([2])),"COMPOSITE: IV-elev & contango & not-Feb")]
json.dump(res, open(os.path.join(P,"regime_gate_results.json"),"w"), indent=2, default=str)
lg("DONE"); 
for r in res: lg(f"  {r['gate']:52s} SR {str(r['SR']):>5}  ret {r['ann_ret_pctK']:>6}%  trades {int(r['frac_traded']*100):>3}%  worst {r['worst_mo_pctK']}")
