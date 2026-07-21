import os, glob, math, time
import numpy as np, pandas as pd
PROJ=r"C:\Users\OWNER\Claude\Projects\GBC Project"; RAW=r"C:\GBC_data\data\raw"
t0=time.time(); lg=lambda s:print(s,flush=True)
d=pd.read_csv(os.path.join(PROJ,"mh_panel_v2.csv.gz")); d['date']=pd.to_datetime(d.date)
d=d.sort_values(['tk','date']).reset_index(drop=True)
lg("panel %s"%(d.shape,))
# ---- panel-only features ----
mo=d.date.dt.month
d['mo_sin']=np.sin(2*np.pi*mo/12); d['mo_cos']=np.cos(2*np.pi*mo/12); d['febmar']=mo.isin([2,3]).astype(float)
d['vrp']=(d.liv-d.lrv21).fillna(0)
g=d.groupby('tk')
def zroll(col,w=252):
    m=g[col].transform(lambda s:s.rolling(w,min_periods=40).mean()); sd=g[col].transform(lambda s:s.rolling(w,min_periods=40).std())
    return ((d[col]-m)/(sd+1e-6)).fillna(0)
d['ivz']=zroll('liv'); d['skwz']=zroll('skw')
d['skew_chg']=g['skw'].transform(lambda s:s-s.shift(21)).fillna(0)
lg("panel-only feats done %.0fs"%(time.time()-t0))
# ---- market returns for network corr ----
mkt=None
try:
    ff=pd.read_csv(os.path.join(RAW,"ff_factors.csv"),header=None,names=['date','mktrf','smb','hml','rf'])
    ff['date']=pd.to_datetime(ff.date,format='%Y%m%d',errors='coerce'); ff=ff.dropna(subset=['date'])
    mkt=ff.set_index('date')['mktrf'].astype(float)/100.0
    lg("ff mkt %d rows"%len(mkt))
except Exception as e: lg("ff err "+str(e)[:100])
# ---- raw-data features per name ----
for c in ['rv5','rv63','amihud','netcorr','earn_prox']: d[c]=np.nan
names=d.tk.unique()
for i,tk in enumerate(names):
    f=os.path.join(RAW,f"tpx_{tk}.csv")
    if not os.path.exists(f): continue
    t=pd.read_csv(f,usecols=['date','field','value'])
    px=t[t.field=='PX_LAST'].copy(); vol=t[t.field=='PX_VOLUME'].copy()
    px['date']=pd.to_datetime(px.date); vol['date']=pd.to_datetime(vol.date)
    s=px.set_index('date')['value'].sort_index().astype(float); v=vol.set_index('date')['value'].sort_index().astype(float)
    ret=s.pct_change()
    feat=pd.DataFrame(index=s.index)
    feat['rv5']=np.log(np.sqrt(252)*ret.rolling(5).std()+1e-6)
    feat['rv63']=np.log(np.sqrt(252)*ret.rolling(63).std()+1e-6)
    dv=(s*v).replace(0,np.nan)
    feat['amihud']=np.log((ret.abs()/dv).rolling(21).mean()*1e9+1e-9)
    if mkt is not None:
        feat['netcorr']=ret.rolling(63).corr(mkt.reindex(ret.index))
    # earnings proximity
    ef=os.path.join(RAW,f"earn_{tk}.csv")
    if os.path.exists(ef):
        try:
            e=pd.read_csv(ef)
            dc=[c for c in e.columns if 'nnounce' in c or c.lower()=='date']
            if dc:
                ed=pd.to_datetime(e[dc[0]],errors='coerce').dropna().sort_values().values
                idx=s.index.values.astype('datetime64[D]')
                nxt=np.searchsorted(ed.astype('datetime64[D]'),idx)
                days=np.array([ (ed[j]-idx[k])/np.timedelta64(1,'D') if j<len(ed) else 30 for k,j in enumerate(nxt)])
                feat['earn_prox']=np.exp(-np.clip(days,0,30)/7.0)
        except Exception: pass
    # merge onto panel rows for this tk (asof by date)
    m=d.tk==tk
    sub=d.loc[m,['date']].merge(feat.reset_index().rename(columns={'index':'date'}),on='date',how='left')
    for c in ['rv5','rv63','amihud','netcorr','earn_prox']:
        if c in sub: d.loc[m,c]=sub[c].values
    if i%25==0: lg("  %d/%d names %.0fs"%(i,len(names),time.time()-t0))
for c in ['rv5','rv63','amihud','netcorr','earn_prox']:
    d[c]=d[c].fillna(d[c].median()).fillna(0)
NEW=['mo_sin','mo_cos','febmar','vrp','ivz','skwz','skew_chg','rv5','rv63','amihud','netcorr','earn_prox']
lg("NEW feats: "+", ".join(f"{c}(nan{d[c].isna().mean():.0%})" for c in NEW))
d.to_csv(os.path.join(PROJ,"mh_panel_v3.csv.gz"),index=False,compression='gzip')
lg("saved mh_panel_v3 %s  %.0fs"%(d.shape,time.time()-t0))
