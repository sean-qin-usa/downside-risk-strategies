import os, math, json
import numpy as np, pandas as pd
from statistics import NormalDist
cdf=NormalDist().cdf
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
def bs_put(S,K,T,sig):
    if T<=0 or sig<=0: return max(K-S,0.0)
    d1=(math.log(S/K)+0.5*sig*sig*T)/(sig*math.sqrt(T)); d2=d1-sig*math.sqrt(T)
    return K*cdf(-d2)-S*cdf(-d1)
spot=pd.read_csv(os.path.join(W,"spx_spot.csv")); spot['date']=pd.to_datetime(spot.date); spot=spot.set_index('date')['close'].sort_index()
# VIX
def volser(t):
    for fn in ['vol_indices.csv','bbg_impvol.csv']:
        p=os.path.join(RAW,fn)
        if not os.path.exists(p): continue
        v=pd.read_csv(p); cl={c.lower():c for c in v.columns}; tc,dc,fc,vc=cl.get('ticker'),cl.get('date'),cl.get('field'),cl.get('value')
        if not(tc and dc and vc): continue
        m=v[v[tc].astype(str).str.strip().isin([t,t+' Index',t+' INDEX'])]
        if fc: m=m[m[fc].astype(str).str.contains('PX_LAST',case=False,na=False)]
        if len(m): m=m[[dc,vc]].dropna(); m[dc]=pd.to_datetime(m[dc]); return m.set_index(dc)[vc].astype(float).sort_index()
    return None
vix=volser('VIX')
mspot=spot.resample('ME').last()
def vat(dt): 
    x=vix[:dt]; return float(x.iloc[-1])/100 if len(x) else 0.2
# monthly hedge: buy 5%-OTM 30d SPX put, held to month-end; net return as % of index (minus 3% option spread on cost)
he=[]
for i in range(len(mspot)-1):
    dt=mspot.index[i]; S0=mspot.iloc[i]; S1=mspot.iloc[i+1]; v=vat(dt); K=0.95*S0
    cost=bs_put(S0,K,30/365,v)*1.03; payoff=max(K-S1,0.0)
    he.append((mspot.index[i+1].to_period('M'),(payoff-cost)/S0))
H=pd.DataFrame(he,columns=['ym','hedge']).set_index('ym')['hedge']
bt=pd.read_csv(os.path.join(P,"exp_bt_series.csv"),parse_dates=['date']); bt['ym']=bt.date.dt.to_period('M')
s=bt[bt.date.dt.year>=2016].set_index('ym')['s0']/100.0
idx=s.index.intersection(H.index); s=s[idx]; h_=H[idx]
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2)
def mdd(x): w=(1+x).cumprod(); return round(float((w/w.cummax()-1).min())*100,1)
res={'hedge_carry_pctmo':round(float(h_[h_<0].mean())*100,2),'hedge_best_month_pct':round(float(h_.max())*100,1),'n':len(idx)}
tab=[]
for hr in [0,0.25,0.5,1.0,1.5,2.0,3.0]:
    net=s + hr*h_
    tab.append(dict(hedge_ratio=hr, SR=sr(net), ann_ret_pct=round(float(net.mean()*12*100),2), maxDD=mdd(net),
                    worst_mo_pct=round(float(net.min()*100),2), mar2020=round(float((s+hr*h_).get(pd.Period('2020-03'),np.nan))*100,2)))
res['overlay']=tab
json.dump(res,open(os.path.join(P,"cushion_v1_results.json"),"w"),indent=2,default=str)
print(json.dumps(res,indent=2,default=str))
