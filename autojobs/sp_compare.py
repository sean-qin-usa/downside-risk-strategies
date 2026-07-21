import os, numpy as np, pandas as pd
PROJ=r"C:\Users\OWNER\Claude\Projects\GBC Project"; RAW=r"C:\GBC_data\data\raw"
bt=pd.read_csv(os.path.join(PROJ,"exp_bt_series.csv"),parse_dates=['date'])[['date','s0']].dropna().sort_values('date')
bt['ym']=bt.date.dt.to_period('M')
ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=['date','mktrf','smb','hml','rf'])
ff['date']=pd.to_datetime(ff.date,format='%Y%m%d',errors='coerce'); ff=ff.dropna(subset=['date'])
ff['mkt']=(ff.mktrf+ff.rf)/100.0   # daily total mkt return
mm=(1+ff.set_index('date')['mkt']).resample('M').prod()-1   # monthly S&P total return
mm.index=mm.index.to_period('M')
def ann(x): return (1+x).prod()**(12/len(x))-1
def sr(x): return x.mean()/x.std()*np.sqrt(12)
def mdd(x):
    w=(1+x).cumprod(); return (w/w.cummax()-1).min()
for lab,yr0 in [("1995-2026",1995),("2016-2026 (last 10y)",2016)]:
    b=bt[bt.date.dt.year>=yr0].set_index('ym')['s0']/100.0   # base leg monthly, % of strike -> decimal
    m=mm[mm.index.year>=yr0]; idx=b.index.intersection(m.index); b=b[idx]; m=m[idx]
    # vol-match strategy to the S&P's realized vol (so leverage is comparable)
    k=m.std()/b.std(); bs=b*k
    print(f"\n=== {lab}  (n={len(idx)} months) ===")
    print(f"  S&P (total return):   CAGR {ann(m)*100:5.1f}%   Sharpe {sr(m):.2f}   maxDD {mdd(m)*100:5.1f}%")
    print(f"  Strategy vol-matched: CAGR {ann(bs)*100:5.1f}%   Sharpe {sr(bs):.2f}   maxDD {mdd(bs)*100:5.1f}%   (levered {k:.1f}x to match S&P vol)")
    print(f"  terminal wealth ratio strat/S&P: {((1+bs).prod()/(1+m).prod()):.2f}x")
    print(f"  corr(strategy, S&P monthly): {b.corr(m):.2f}")
