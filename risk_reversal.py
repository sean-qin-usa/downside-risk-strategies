# Risk reversal (skew harvest) + strangle/straddle, using puts + the new calls pull.
# STAGED: runs once calls_{yr}.csv.gz exist (2016+). Sell d-0.12 put, buy d+0.12 call = pure skew harvest.
import os, glob, time, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
ppf=NormalDist().inv_cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
if not glob.glob(os.path.join(W,'calls_2016.csv.gz')):
    print("calls pull not complete yet (need calls_2016.csv.gz)"); raise SystemExit
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
uni=[int(s) for s in pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False).index[:18]]
px={}
for s in uni:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
def pxat(s,dt):
    ser=px.get(s)
    if ser is None: return np.nan
    z=ser[:dt]; return float(z.iloc[-1]) if len(z) else np.nan
def rd(f):
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    return pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
def nr(df,tgt): return df.iloc[(df.delta-tgt).abs().values.argmin()] if len(df) else None
rows=[]
for yr in range(2016,2027):
    fp=os.path.join(W,f'spreads_{yr}.csv.gz'); fc=os.path.join(W,f'calls_{yr}.csv.gz')
    if not (os.path.exists(fp) and os.path.exists(fc)): continue
    dp=rd(fp); dc=rd(fc)
    fa=os.path.join(W,f'atmputs_{yr}.csv.gz')
    if os.path.exists(fa): dp=pd.concat([dp,rd(fa)],ignore_index=True)
    for D in (dp,dc):
        D['date']=pd.to_datetime(D['date']); D['exdate']=pd.to_datetime(D['exdate']); D['dte']=(D['exdate']-D['date']).dt.days
    dp=dp[(dp.dte>=20)&(dp.dte<=40)&(dp.best_bid>0)&(dp.best_offer>0)&(dp.impl_volatility>0)]
    dc=dc[(dc.dte>=20)&(dc.dte<=40)&(dc.best_bid>0)&(dc.best_offer>0)&(dc.impl_volatility>0)]
    for D in (dp,dc): D['K']=D.strike_price/1000.0; D['mid']=(D.best_bid+D.best_offer)/2; D['cyc']=D['date'].dt.to_period('M')
    pk={(s,c):g for (s,c),g in dp.groupby(['secid','cyc'])}
    ck={(s,c):g for (s,c),g in dc.groupby(['secid','cyc'])}
    for key in set(pk)&set(ck):
        s,c=key; gp=pk[key]; gc=ck[key]
        gp=gp[gp.date==gp.date.min()]; gc=gc[gc.date==gc.date.min()]
        if len(gp)<2 or len(gc)<2: continue
        P12=nr(gp,-0.12); C12=nr(gc,0.12); Patm=nr(gp,-0.5); Catm=nr(gc,0.5)
        if any(x is None for x in [P12,C12,Patm,Catm]): continue
        K=P12.K; sig=float(P12.impl_volatility); T=P12.dte/365.0; dl=float(P12.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        d1=-ppf(-dl); Se=K*math.exp(d1*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,P12.date); p1=pxat(s,P12.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0)
        def sp(r): return (float(r.mid)-max(r.K-Sx,0.0))/Se     # short put
        def lp(r): return (max(r.K-Sx,0.0)-float(r.mid))/Se
        def sc(r): return (float(r.mid)-max(Sx-r.K,0.0))/Se     # short call
        def lc(r): return (max(Sx-r.K,0.0)-float(r.mid))/Se
        rows.append(dict(date=P12.date,
            naked_put=sp(P12),
            risk_reversal=sp(P12)+lc(C12),        # sell put, buy call (harvest skew)
            short_strangle=sp(P12)+sc(C12),       # sell put + sell call
            short_straddle=sp(Patm)+sc(Catm),
            long_straddle=lp(Patm)+lc(Catm)))
    lg("  %d %d %.0fs"%(yr,len(rows),time.time()-t0))
df=pd.DataFrame(rows); df['ym']=df['date'].dt.to_period('M')
df.to_csv(os.path.join(P,"risk_reversal_trades.csv"),index=False)
def sr(x): x=x.dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if x.std()>0 else None
out={'n':len(df)}
for k in ['naked_put','risk_reversal','short_strangle','short_straddle','long_straddle']:
    m=df.groupby('ym')[k].mean()
    out[k]=dict(avg_bp=round(float(df[k].mean()*1e4),1), SR=sr(m), worst_mo_pct=round(float(m.min()*100),2),
                mar2020_bp=round(float(df[df.ym==pd.Period('2020-03')][k].mean()*1e4),1) if (df.ym==pd.Period('2020-03')).any() else None)
json.dump(out,open(os.path.join(P,"risk_reversal_results.json"),"w"),indent=2,default=str)
lg(json.dumps(out,indent=2,default=str)); lg("RRDONE")
