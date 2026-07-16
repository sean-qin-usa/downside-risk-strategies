# YOUNG-NAME / IPO put-writing study (Phase 1): does a young-name VRP book work, does selection help, does it survive cost?
# Age = trading days since first PX_LAST (listing-age proxy). Cohorts by age. VRP = IV - trailing RV. Settle via BS-inversion.
import os, glob, time, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
px={}; rv={}; first_date={}; agecount={}
for s,tk in sym.items():
    f=os.path.join(RAW,f"tpx_{tk}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna()
    if len(t)<15: continue
    t['date']=pd.to_datetime(t['date']); ser=t.set_index('date')['value'].sort_index()
    px[s]=ser; first_date[s]=ser.index[0]
    lr=np.log(ser/ser.shift(1)); rv[s]=(lr.rolling(21,min_periods=10).std()*math.sqrt(252))
    agecount[s]=pd.Series(range(len(ser)),index=ser.index)  # trading-day age at each date
uset=set(px); lg("names=%d %.0fs"%(len(uset),time.time()-t0))
def pxat(s,dt):
    z=px[s][:dt]; return float(z.iloc[-1]) if len(z) else np.nan
def rvat(s,dt):
    z=rv[s][:dt].dropna(); return float(z.iloc[-1]) if len(z) else np.nan
def ageat(s,dt):
    z=agecount[s][:dt]; return int(z.iloc[-1]) if len(z) else np.nan
rows=[]
for f in sorted(glob.glob(os.path.join(W,'spreads_[12]*.csv.gz'))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uset)])
    d=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
    if not len(d): continue
    d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.best_offer>0)&(d.impl_volatility>0)&(d.delta<0)]
    d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        r=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=r.strike_price/1000.0; sig=float(r.impl_volatility); T=r.dte/365.0; dl=float(r.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T)
        p0=pxat(s,r.date); p1=pxat(s,r.exdate); rvt=rvat(s,r.date); age=ageat(s,r.date)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); payoff=max(K-Sx,0.0); bid=float(r.best_bid); off=float(r.best_offer); mid=(bid+off)/2
        spr=(off-bid)/mid if mid>0 else np.nan
        rows.append((s,r.date,(mid-payoff)/K,(bid-payoff)/K,sig,rvt,age,spr))
    lg("  %d rows=%d %.0fs"%(yr,len(rows),time.time()-t0))
df=pd.DataFrame(rows,columns=['secid','date','net_mid','net_bid','iv','rv_trail','age','spread'])
df['ym']=df['date'].dt.to_period('M'); df['vrp']=df['iv']-df['rv_trail']
df.to_csv(os.path.join(P,"young_trades.csv"),index=False)
def sr(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
def stats(sub,col):
    if not len(sub): return dict(SR=None,avg_bp=None,worst_mo=None,n=0)
    m=sub.groupby('ym')[col].mean()
    return dict(SR=sr(m), avg_bp=round(float(sub[col].mean()*1e4),1), worst_mo=round(float(m.min()*100),2), n=int(len(sub)))
COH=[('young1_<=252',0,252),('young2_253-504',253,504),('mid_505-1512',505,1512),('mature_>1512',1513,10**9)]
out={'n_trades':len(df),'note':'age=trading days since first PX_LAST. VRP-select = top-25% by VRP within cohort (needs valid trailing RV).'}
out['cohorts']={}
for lbl,lo,hi in COH:
    c=df[(df.age>=lo)&(df.age<=hi)]
    cell={'n':int(len(c)), 'n_names':int(c.secid.nunique()),
          'avg_spread_pct':round(float(c.spread.median()*100),1),
          'NAIVE_mid':stats(c,'net_mid'), 'NAIVE_bid':stats(c,'net_bid')}
    cv=c.dropna(subset=['vrp'])
    if len(cv)>30:
        top=cv.groupby('ym',group_keys=False).apply(lambda g:g[g.vrp>=g.vrp.quantile(0.75)])
        cell['VRPsel_mid']=stats(top,'net_mid'); cell['VRPsel_bid']=stats(top,'net_bid')
        cell['avg_vrp']=round(float(cv.vrp.mean()),3)
    out['cohorts'][lbl]=cell
    lg(f"{lbl}: n={cell['n']} names={cell['n_names']} spread%={cell['avg_spread_pct']} naive_mid_SR={cell['NAIVE_mid']['SR']} naive_bid_SR={cell['NAIVE_bid']['SR']}")
json.dump(out,open(os.path.join(P,"young_vrp_results.json"),"w"),indent=2,default=str)
lg("YOUNG_RESULTS\n"+json.dumps(out,indent=2,default=str)); lg("JOBYOUNGDONE %.0fs"%(time.time()-t0))
