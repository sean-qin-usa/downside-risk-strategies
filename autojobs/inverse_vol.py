import os, json, numpy as np, pandas as pd
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
f=os.path.join(P,"improve_trades.csv")
if not os.path.exists(f): print("needs improve_trades.csv (run improve_sharpe first)"); raise SystemExit
df=pd.read_csv(f); df['ym']=pd.PeriodIndex(pd.to_datetime(df['date']).dt.to_period('M'),freq='M')
df=df.dropna(subset=['rv_trail']); df=df[df.rv_trail>0]
def sr(x): x=x.dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
# equal weight
eq=df.groupby('ym')['net'].mean()
# inverse trailing-vol weight (lagged -> clean): w_i ∝ 1/rv_trail_i, normalized within month
def ivw(g):
    w=1.0/g.rv_trail; w=w/w.sum(); return float((w*g.net).sum())
iv=df.groupby('ym',group_keys=False).apply(ivw)
out=dict(n=len(df), equal_weight_SR=sr(eq), equal_avg_bp=round(float(df.net.mean()*1e4),1),
         inverse_vol_SR=sr(iv), inverse_vol_worst=round(float(iv.min()*100),2), equal_worst=round(float(eq.min()*100),2))
json.dump(out,open(os.path.join(P,"inverse_vol_results.json"),"w"),indent=2,default=str)
print(json.dumps(out,indent=2,default=str)); print("INVVOLDONE")
