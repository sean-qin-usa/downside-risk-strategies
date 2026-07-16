# Reconcile the weekly Sharpe: (all vs top-10%-VRP) x (weekly vs monthly aggregation). Chart the selected monthly book.
import os, json, math, sys
import numpy as np, pandas as pd
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; sys.path.insert(0,P)
from trade_analysis import analyze
w=pd.read_csv(os.path.join(P,"weekly_trades.csv")); w['date']=pd.to_datetime(w['date']); w['ym']=pd.PeriodIndex(w['ym'],freq='M') if 'ym' in w else w['date'].dt.to_period('M')
w['wk']=w['date'].dt.to_period('W'); w=w.dropna(subset=['vrp','net'])
def sel(g,q): return g[g.vrp>=g.vrp.quantile(q)]
def sr(x,ppy): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*math.sqrt(ppy)),2) if len(x)>6 and x.std()>0 else None
res={'note':'weekly-tenor VRP book: Sharpe under (selection) x (aggregation freq). Explains 3.46 (top10% monthly-agg) vs 1.35 (all weekly-agg).'}
# monthly-aggregated
mo_all=w.groupby('ym')['net'].mean()
mo_top=w.groupby('ym',group_keys=False).apply(lambda g:sel(g,0.90)).groupby('ym')['net'].mean()
# weekly-aggregated
wk_all=w.groupby('wk')['net'].mean()
wk_top=w.groupby('wk',group_keys=False).apply(lambda g:sel(g,0.90)).groupby('wk')['net'].mean()
res['sharpe_grid']={'all_monthly':sr(mo_all,12),'top10_monthly':sr(mo_top,12),'all_weekly':sr(wk_all,52),'top10_weekly':sr(wk_top,52)}
res['avg_bp']={'all_monthly':round(float(mo_all.mean()*1e4),1),'top10_monthly':round(float(mo_top.mean()*1e4),1)}
# chart the selected monthly book + trade counts
mts=w.groupby('ym',group_keys=False).apply(lambda g:sel(g,0.90))
mo_top_ret=mts.groupby('ym')['net'].mean(); mo_top_n=mts.groupby('ym')['net'].count()
idx=mo_top_ret.index.to_timestamp(); s=pd.Series(mo_top_ret.values,index=idx); nser=pd.Series(mo_top_n.values,index=idx)
res['selected_monthly']=analyze(s,"Weekly_tenor_TOP10VRP_monthly",P,ppy=12,trades=nser)
json.dump(res,open(os.path.join(P,"weekly_selected.json"),"w"),indent=2,default=str)
print("SHARPE GRID:",json.dumps(res['sharpe_grid'])); print("DONE")
