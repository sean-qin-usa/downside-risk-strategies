# EARNINGS-VRP robustness FIX: use per-ticker earn_*.csv ('Earnings Announcement Date') = the source that works.
import os, time, json, math
import numpy as np, pandas as pd
RAW=r"C:\Users\OWNER\Desktop\GBC_data\data\raw"; W=r"C:\Users\OWNER\Desktop\GBC_data\data\wrds"; P=r"C:\Users\OWNER\Claude\Projects\GBC Project"
lg=lambda s:print(s,flush=True); t0=time.time()
sym={int(r.secid):str(r.ticker) for r in pd.read_csv(os.path.join(W,"secids.csv")).dropna(subset=['secid']).astype({'secid':int}).itertuples()}
oi=pd.read_csv(os.path.join(W,"spreads_2023.csv.gz"),usecols=['secid','open_interest']).groupby('secid')['open_interest'].sum().sort_values(ascending=False)
oi_rank={int(s):i for i,s in enumerate(oi.index)}
mo=pd.read_csv(os.path.join(P,"improve_trades.csv")); mo['date']=pd.to_datetime(mo['date']); mo['ym']=pd.PeriodIndex(mo['ym'],freq='M')
mo['rank']=mo.secid.astype(int).map(oi_rank); mo['tk']=mo.secid.astype(int).map(sym)
# per-ticker earnings dates
ann={}
for tk in mo['tk'].dropna().unique():
    f=os.path.join(RAW,f"earn_{tk}.csv")
    if not os.path.exists(f): continue
    try:
        e=pd.read_csv(f); dc=[c for c in e.columns if 'nnounce' in c]
        if dc:
            d=pd.to_datetime(e[dc[0]],errors='coerce').dropna().sort_values().values
            if len(d): ann[tk]=d.astype('datetime64[D]')
    except Exception: pass
lg("earn tickers=%d %.0fs"%(len(ann),time.time()-t0))
def spans(row):
    a=ann.get(row['tk'])
    if a is None: return False
    lo=np.datetime64(pd.Timestamp(row['date']).date()); hi=lo+np.timedelta64(35,'D')
    return bool(((a>=lo)&(a<=hi)).any())
mo['earn']=mo.apply(spans,axis=1)
def sr(x): x=pd.Series(x).dropna(); return round(float(x.mean()/x.std()*np.sqrt(12)),2) if len(x)>6 and x.std()>0 else None
d=mo[mo['rank']<100].dropna(subset=['vrp'])
top=d.groupby('ym',group_keys=False).apply(lambda g:g[g.vrp>=g.vrp.quantile(0.90)])
def bookSR(fr):
    if not len(fr): return None,None,0
    m=fr.groupby('ym')['net'].mean(); return sr(m), round(float(fr.net.mean()*1e4),1), int(len(fr))
E={}
E['pct_all_trades_earn']=round(float(d['earn'].mean()*100),1)
E['pct_selected_earn']=round(float(top['earn'].mean()*100),1)
E['avg_vrp_earn']=round(float(d[d.earn].vrp.mean()),3); E['avg_vrp_noearn']=round(float(d[~d.earn].vrp.mean()),3)
E['avg_iv_earn']=round(float(d[d.earn].iv.mean()),3); E['avg_iv_noearn']=round(float(d[~d.earn].iv.mean()),3)
for lbl,fr in [('top10_ALL',top),('top10_earn_only',top[top.earn]),('top10_NO_earn',top[~top.earn])]:
    s,bp,n=bookSR(fr); E[lbl]=dict(SR=s,avg_bp=bp,n=n)
def sizedown(g):
    g=g.copy(); g['w']=np.where(g['earn'],0.5,1.0); g['w']/=g['w'].sum(); return (g['net']*g['w']).sum()
m_base=top.groupby('ym')['net'].mean(); m_sd=top.groupby('ym').apply(sizedown)
E['book_equalwt_SR']=sr(m_base); E['book_earnHALF_SR']=sr(m_sd)
E['book_equal_ann_bp']=round(float(m_base.mean()*1e4),1); E['book_earnHALF_ann_bp']=round(float(m_sd.mean()*1e4),1)
# worst months earn vs noearn selected
E['worst_mo_earn_bp']=round(float(top[top.earn].net.min()*1e4),1) if len(top[top.earn]) else None
E['worst_mo_noearn_bp']=round(float(top[~top.earn].net.min()*1e4),1) if len(top[~top.earn]) else None
json.dump(E,open(os.path.join(P,"earnings_deep_results.json"),"w"),indent=2,default=str)
lg("EARN_FIXED\n"+json.dumps(E,indent=2,default=str)); lg("JOB5DONE %.0fs"%(time.time()-t0))
