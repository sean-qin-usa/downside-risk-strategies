# Anatomy of wins & losses for the tau.10 short-put book + seasonality/regime gates.
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
# VIX term structure
def loadvol(tick):
    for fn in ['vol_indices.csv','bbg_impvol.csv']:
        p=os.path.join(RAW,fn)
        if not os.path.exists(p): continue
        v=pd.read_csv(p)
        cols={c.lower():c for c in v.columns}
        tc=cols.get('ticker'); dc=cols.get('date'); fc=cols.get('field'); vc=cols.get('value')
        if not(tc and dc and vc): continue
        m=v[v[tc].astype(str).str.contains(tick,case=False,na=False)]
        if fc: m=m[m[fc].astype(str).str.contains('PX_LAST',case=False,na=False)]
        if len(m)==0: continue
        m=m[[dc,vc]].dropna(); m[dc]=pd.to_datetime(m[dc])
        return m.set_index(dc)[vc].sort_index()
    return None
vix=loadvol('VIX '); vix3=loadvol('VIX3M')
lg("vix %s vix3m %s"%(vix is not None, vix3 is not None))
def vat(ser,dt):
    if ser is None: return np.nan
    s2=ser[:dt]; return float(s2.iloc[-1]) if len(s2) else np.nan
# build tau.10 trades w/ context
tr=[]
for f in sorted(glob.glob(os.path.join(W,"spreads_[12]*.csv.gz"))):
    yr=int(os.path.basename(f).split('_')[-1][:4])
    if yr<2016: continue
    parts=[]
    for ch in pd.read_csv(f,usecols=['secid','date','exdate','strike_price','best_bid','best_offer','impl_volatility','delta'],chunksize=1000000):
        parts.append(ch[ch.secid.isin(uni)])
    d=pd.concat(parts); d['date']=pd.to_datetime(d['date']); d['exdate']=pd.to_datetime(d['exdate']); d['dte']=(d['exdate']-d['date']).dt.days
    d=d[(d.dte>=20)&(d.dte<=40)&(d.best_bid>0)&(d.impl_volatility>0)&(d.delta<0)]
    d['cyc']=d['date'].dt.to_period('M')
    for (s,c),g in d.groupby(['secid','cyc']):
        g=g[g.date==g.date.min()]
        if not len(g): continue
        row=g.iloc[(g.delta+0.12).abs().values.argmin()]
        K=row.strike_price/1000.0; sig=float(row.impl_volatility); T=row.dte/365.0; dl=float(row.delta)
        if K<=0 or sig<=0 or T<=0 or -dl<=0 or -dl>=1: continue
        Se=K*math.exp(-ppf(-dl)*sig*math.sqrt(T)-0.5*sig*sig*T); p0=pxat(s,row.date); p1=pxat(s,row.exdate)
        if not(np.isfinite(p0) and np.isfinite(p1) and p0>0): continue
        Sx=Se*(p1/p0); payoff=max(K-Sx,0.0); net=(row.best_bid-payoff)/K
        vx=vat(vix,row.date); v3=vat(vix3,row.date)
        tr.append((sym.get(s),row.date,net,sig,row.best_bid/K, p1/p0-1.0, vx, (vx/v3 if (v3 and v3>0) else np.nan)))
T=pd.DataFrame(tr,columns=['name','date','net','iv','premK','uret','vix','vixratio'])
T['mo']=T['date'].dt.month; T['ym']=T['date'].dt.to_period('M'); T['win']=T.net>0
lg("trades %d  %.0fs"%(len(T),time.time()-t0))
def sr(x): return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>2 and x.std()>0 else None
res={}
# 1) win/loss anatomy
wins=T[T.win]; loss=T[~T.win]
tot_loss=loss.net.sum(); worst5=T.net.nsmallest(max(1,int(0.05*len(T)))).sum()
res['winloss']=dict(n=len(T), pct_win=round(len(wins)/len(T),3),
    avg_win_bp=round(wins.net.mean()*1e4,1), avg_loss_bp=round(loss.net.mean()*1e4,1),
    win_loss_ratio=round(abs(wins.net.mean()/loss.net.mean()),2),
    worst_bp=round(T.net.min()*1e4,0), best_bp=round(T.net.max()*1e4,0), skew=round(float(T.net.skew()),2),
    share_of_all_losses_from_worst5pct=round(float(worst5/tot_loss),2) if tot_loss<0 else None)
# 2) conditioning terciles
def by_tercile(col):
    q=T[col].quantile([1/3,2/3]).values; out={}
    for lab,m in [('low',T[col]<=q[0]),('mid',(T[col]>q[0])&(T[col]<=q[1])),('high',T[col]>q[1])]:
        out[lab]=dict(net_bp=round(T[m].net.mean()*1e4,1), SR=sr(T[m].groupby('ym')['net'].mean()), n=int(m.sum()))
    return out
res['by_entry_IV']=by_tercile('iv')
res['by_vix_level']=by_tercile('vix')
# 3) VIX term structure gate (contango vs backwardation)
bt=T.dropna(subset=['vixratio'])
res['by_term_structure']=dict(
    contango_vix_lt_vix3m=dict(net_bp=round(bt[bt.vixratio<1].net.mean()*1e4,1), SR=sr(bt[bt.vixratio<1].groupby('ym')['net'].mean()), n=int((bt.vixratio<1).sum())),
    inverted_vix_ge_vix3m=dict(net_bp=round(bt[bt.vixratio>=1].net.mean()*1e4,1), SR=sr(bt[bt.vixratio>=1].groupby('ym')['net'].mean()), n=int((bt.vixratio>=1).sum())))
# 4) worst 12 trades
w=T.nsmallest(12,'net')[['name','date','net','iv','uret','vix']].copy(); w['date']=w.date.dt.strftime('%Y-%m-%d'); w['net_pctK']=(w.net*100).round(1); w['uret_pct']=(w.uret*100).round(1); w['iv']=w.iv.round(2)
res['worst_trades']=w[['name','date','net_pctK','uret_pct','iv','vix']].to_dict('records')
# 5) monthly return clustering (autocorr) + recovery after loss month
mon=T.groupby('ym')['net'].mean()
res['monthly_autocorr_lag1']=round(float(mon.autocorr(1)),2)
neg=mon<0; res['after_loss_month_mean_bp']=round(float(mon[neg.shift(1,fill_value=False)].mean()*1e4),1)
# 6) GATE STRATEGIES
def gsr(mask): return sr(T[mask].groupby('ym')['net'].mean())
res['gates']=dict(
    baseline=sr(mon),
    ex_feb_mar=gsr(~T.mo.isin([2,3])),
    ex_inverted_TS=gsr(~(T.vixratio>=1)),
    ex_feb_mar_and_inverted=gsr(~(T.mo.isin([2,3])|(T.vixratio>=1))),
    ex_lowIV_entry=gsr(T.iv>T.iv.quantile(1/3)))   # skip calmest-IV entries (ambush guard)
res['runtime_sec']=round(time.time()-t0,1)
json.dump(res, open(os.path.join(P,"bt_anatomy_results.json"),"w"), indent=2, default=str)
lg("ALL DONE"); lg(json.dumps(res['winloss'])); lg(json.dumps(res['gates']))
