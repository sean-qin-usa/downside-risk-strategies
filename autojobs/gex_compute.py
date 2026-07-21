import os, glob, json
import numpy as np, pandas as pd
W=r"C:\GBC_data\data\wrds"; PROJ=r"C:\Users\OWNER\Claude\Projects\GBC Project"
ch=sorted(glob.glob(os.path.join(W,"spx_chain_*.csv.gz")))
if not ch or not os.path.exists(os.path.join(W,"spx_spot.csv")):
    print("GEX pull not complete yet"); raise SystemExit
d=pd.concat([pd.read_csv(f) for f in ch]); d['date']=pd.to_datetime(d['date'])
sp=pd.read_csv(os.path.join(W,"spx_spot.csv")); sp['date']=pd.to_datetime(sp['date']); sp=sp.set_index('date')['close']
d=d[d['gamma'].notna() & d['open_interest'].notna()]
d['sign']=np.where(d.cp_flag.astype(str).str.upper().str.startswith('C'),1.0,-1.0)   # dealers long calls, short puts
d['gxoi']=d['gamma']*d['open_interest']*d['sign']
g=d.groupby('date')['gxoi'].sum()
S=sp.reindex(g.index).ffill()
GEX=(g*S*S*0.01*100)/1e9   # $bn per 1% move (SqueezeMetrics-style)
GEX=GEX.dropna()
GEX.to_csv(os.path.join(PROJ,"spx_gex_daily.csv"))
print("GEX daily: n=%d  range %s..%s  median %.1f  pct_negative %.0f%%"%(len(GEX),GEX.index.min().date(),GEX.index.max().date(),GEX.median(),(GEX<0).mean()*100))
# merge GEX at month-entry with base-leg strategy monthly returns
bt=pd.read_csv(os.path.join(PROJ,"exp_bt_series.csv"),parse_dates=['date']); bt=bt[['date','s0']].dropna()
bt=bt[bt.date.dt.year>=2016].copy()
def gex_at(dt):
    x=GEX[:dt]; return float(x.iloc[-1]) if len(x) else np.nan
bt['gex']=bt['date'].apply(gex_at); bt=bt.dropna(subset=['gex'])
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>3 and x.std()>0 else None
med=bt['gex'].median()
res=dict(n_months=len(bt), gex_median_bn=round(float(med),1), pct_neg_gex=round(float((bt.gex<0).mean()*100),0),
    ALL=dict(SR=sr(bt.s0), mean=round(bt.s0.mean(),2), worst=round(bt.s0.min(),1)),
    GEX_POSITIVE_dealers_long=dict(SR=sr(bt[bt.gex>0].s0), mean=round(bt[bt.gex>0].s0.mean(),2), worst=round(bt[bt.gex>0].s0.min(),1), n=int((bt.gex>0).sum())),
    GEX_NEGATIVE_dealers_short=dict(SR=sr(bt[bt.gex<0].s0), mean=round(bt[bt.gex<0].s0.mean(),2), worst=round(bt[bt.gex<0].s0.min(),1), n=int((bt.gex<0).sum())),
    GEX_above_median=dict(SR=sr(bt[bt.gex>med].s0), mean=round(bt[bt.gex>med].s0.mean(),2), worst=round(bt[bt.gex>med].s0.min(),1)),
    corr_gex_ret=round(float(bt.gex.corr(bt.s0)),3))
# did GEX flag the worst months?
worst=bt.nsmallest(6,'s0')[['date','s0','gex']]; worst['date']=worst.date.dt.strftime('%Y-%m')
res['worst6_months_and_their_GEX']=worst.to_dict('records')
json.dump(res,open(os.path.join(PROJ,"gex_regime_results.json"),"w"),indent=2,default=str)
print(json.dumps(res,indent=2,default=str))
