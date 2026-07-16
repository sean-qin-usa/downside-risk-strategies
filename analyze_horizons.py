import os, glob, json, time
import numpy as np, pandas as pd
W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
DB=[-0.5,-0.3,-0.2,-0.15,-0.10,-0.05,0.0]
NROWS=400000   # cap per file: medians are stable, keeps runtime sane on slow disk
bands={'short_5_15':('spreads_dte05_15_*.csv.gz',10,26),
       'monthly_20_40':('spreads_[12]*.csv.gz',30,12),
       'long_45_70':('spreads_dte45_70_*.csv.gz',57,6)}
def load(f):
    d=pd.read_csv(f,usecols=['best_bid','best_offer','delta'],nrows=NROWS)
    d=d[(d.best_offer>0)&(d.best_bid>=0)]
    d['mid']=(d.best_bid+d.best_offer)/2
    d=d[d['mid']>=0.05]
    d['relhalf']=((d.best_offer-d.best_bid)/(2*d['mid'])).clip(0,1)
    d['db']=pd.cut(d.delta,DB)
    return d
res={}; t0=time.time()
for name,(pat,dte,rolls) in bands.items():
    files=sorted(glob.glob(os.path.join(W,pat)))
    if not files: res[name]={'status':'NO FILES (%s)'%pat}; continue
    parts=[]; by_year={}
    for f in files:
        yr=os.path.basename(f).split('_')[-1][:4]
        try: d=load(f)
        except Exception as e:
            by_year[yr]='err'; continue
        parts.append(d.groupby('db',observed=True)['relhalf'].median())
        tb=d[(d.delta<=-0.15)&(d.delta>=-0.25)]['relhalf']
        by_year[yr]=round(float(tb.median()),3) if len(tb)>50 else None
    surf=pd.concat(parts,axis=1)
    by_delta={str(k):round(float(v),3) for k,v in surf.median(axis=1).items()}
    vals=[v for v in by_year.values() if isinstance(v,float)]
    tb_all=float(np.median(vals)) if vals else float('nan')
    res[name]=dict(dte_mid=dte, rolls_per_year=rolls, n_years=len(files),
                   halfspread_by_delta=by_delta,
                   tau25_halfspread_median=round(tb_all,3),
                   annual_spread_paid_x_premium=round(tb_all*rolls,2),
                   by_year=by_year)
    print(name,"done",round(time.time()-t0,1),"s",flush=True)
# ---- net-by-strike + cost-aware new strategy (uses monthly measured surface) ----
m=res.get('monthly_20_40',{}).get('halfspread_by_delta',{})
def hs_at(delta):
    b=str(pd.cut([delta],DB)[0]); return m.get(b, np.nan)
gross={'tau05':(-0.07,1.59),'tau10':(-0.12,1.59),'tau25':(-0.20,1.02),'tau50':(-0.42,0.85)}
net={}
for k,(dl,sr) in gross.items():
    h=hs_at(dl); drag=0.39*(h/0.10) if h==h else float('nan')  # scale paper's 10%-cost drag
    net[k]=dict(delta=dl, one_way_halfspread=round(h,3) if h==h else None,
                gross_SR=sr, est_net_SR=round(sr-drag,2) if drag==drag else None)
res['net_by_strike']=net
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"horizon_results.json"),"w"), indent=2)
print("ALL DONE"); print(json.dumps(res,indent=2))
