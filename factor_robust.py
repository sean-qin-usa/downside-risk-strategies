# (1) FACTOR ATTRIBUTION: is VRP edge alpha or disguised factor risk?  (2) RV-WINDOW ROBUSTNESS.
import os, math, numpy as np, pandas as pd
W=r"C:\GBC_data\data\wrds"; RAW=r"C:\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
df=pd.read_csv(os.path.join(P,"improve_trades.csv")); df['ym']=pd.PeriodIndex(pd.to_datetime(df['date']).dt.to_period('M'),freq='M'); df=df.dropna(subset=['vrp'])
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
liq100=set(int(s) for s in oi.index[:100]); L=df[df.secid.isin(liq100)].copy()
def SR(s): s=s.dropna(); return round(float(s.mean()/s.std()*np.sqrt(12)),2) if len(s)>6 and s.std()>0 else None
def strat(vcol='vrp',q=0.90,derisk=0.5):
    thr=L.groupby('ym')[vcol].transform(lambda s:s.quantile(q)); d=L[L[vcol]>=thr]; m=d.groupby('ym')['net'].mean()
    if derisk is not None: m=m*np.where(m.shift(1)<0,derisk,1.0)
    return m
m=strat()  # final strategy monthly returns
# ---- FF factors monthly (compound daily) ----
ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=['date','mktrf','smb','hml','rf'])
ff['date']=pd.to_datetime(ff.date,format='%Y%m%d',errors='coerce'); ff=ff.dropna(subset=['date'])
ffm=((1+ff.set_index('date')[['mktrf','smb','hml','rf']]/100).resample('ME').prod()-1); ffm.index=ffm.index.to_period('M')
bt=pd.read_csv(os.path.join(P,"exp_bt_series.csv"),parse_dates=['date']); bt['ym']=bt.date.dt.to_period('M'); sv=(bt.set_index('ym')['s0']/100.0).rename('sv')
D=pd.DataFrame({'ret':m}).join(ffm).join(sv).dropna(); D['exc']=D['ret']-D['rf']
def ols(y,cols):
    X=np.column_stack([np.ones(len(D))]+[D[c].values for c in cols]); yv=y.values
    b,_,_,_=np.linalg.lstsq(X,yv,rcond=None); r=yv-X@b; n,k=X.shape; s2=(r@r)/(n-k)
    se=np.sqrt(np.diag(s2*np.linalg.inv(X.T@X))); t=b/se; R2=1-(r@r)/(((yv-yv.mean())**2).sum())
    return b,se,t,R2,['alpha']+cols
print("=== (1) FACTOR ATTRIBUTION: final strategy excess return regressed on factors ===")
print(f"  n_months={len(D)}, mean monthly ret={D['ret'].mean()*100:.2f}%")
for cols,lab in [(['mktrf','smb','hml'],'CAPM+size+value'),(['mktrf','smb','hml','sv'],'+short-vol factor')]:
    b,se,t,R2,nm=ols(D['exc'],cols)
    print(f"\n  Model: {lab}  (R2={R2:.2f})")
    for i,n in enumerate(nm):
        ann=b[i]*12*100 if n=='alpha' else None
        extra=f"  ann alpha={ann:.1f}%/yr" if n=='alpha' else ""
        print(f"    {n:9} beta={b[i]:+.3f}  t={t[i]:+.2f}{extra}")
# ---- (2) RV-WINDOW ROBUSTNESS ----
print("\n=== (2) RV-WINDOW ROBUSTNESS (recompute VRP with different trailing RV) ===")
px={}
for s in liq100:
    f=os.path.join(RAW,f"tpx_{sym.get(s)}.csv")
    if os.path.exists(f):
        t=pd.read_csv(f,usecols=['date','field','value']); t=t[t.field=='PX_LAST'][['date','value']].dropna(); t['date']=pd.to_datetime(t['date']); px[s]=t.set_index('date')['value'].sort_index()
L['dt']=pd.to_datetime(L['date'])
for win in [10,21,42,63]:
    rvmap={}
    for s,ser in px.items(): rvmap[s]=(np.log(ser/ser.shift(1)).rolling(win).std()*math.sqrt(252))
    def rvat(row):
        r=rvmap.get(row.secid); 
        if r is None: return np.nan
        z=r[:row['dt']]; return float(z.iloc[-1]) if len(z) else np.nan
    L['vrp_w']=L['iv']-L.apply(rvat,axis=1)
    print(f"  RV window {win}d: top-10% VRP SR = {SR(strat('vrp_w'))}")
print("FACTORDONE")
