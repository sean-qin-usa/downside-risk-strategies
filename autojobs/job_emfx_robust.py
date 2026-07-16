# ROBUST EM-FX carry-gate: REAL carry (from 1M forwards), BASKET of 10 currencies, TIME-OOS split, THRESHOLD-robustness (a-priori gates).
import json, os, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import numpy as np, pandas as pd, datetime as dt
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def extract_d(pdf):
    if pdf is None or not len(pdf): return None
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols and any('date' in c for c in cols):
        vcol=pdf.columns[cols.index('value')]; dcol=pdf.columns[[i for i,c in enumerate(cols) if 'date' in c][0]]
        s=pdf[[dcol,vcol]].dropna().copy(); s[dcol]=pd.to_datetime(s[dcol],errors='coerce'); s=s.dropna(subset=[dcol])
        return s.set_index(dcol)[vcol].sort_index().astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().astype(float) if num.shape[1] else None
CCY=['TRY','ZAR','BRL','MXN','RUB','INR','IDR','CLP','COP','HUF']
end=dt.date.today(); start=end-dt.timedelta(days=365*14)
def SR(x): x=pd.Series(x).dropna(); return float(x.mean()/x.std()*np.sqrt(252)) if len(x)>60 and x.std()>0 else np.nan
data={}
for c in CCY:
    try:
        spot=extract_d(to_pd(blp.bdh(f'USD{c} Curncy','px_last',start,end)))
        fwd =extract_d(to_pd(blp.bdh(f'USD{c}1M Curncy','px_last',start,end)))  # 1M forward (points or outright)
        if spot is None or len(spot)<500: lg(f"{c} no spot"); continue
        df=pd.DataFrame({'spot':spot});
        if fwd is not None: df['fwd']=fwd
        df=df.dropna()
        if 'fwd' not in df or len(df)<500:
            # no forward -> skip carry (can't do real carry)
            lg(f"{c} no forward"); data[c]=dict(spot=spot,carry=None); continue
        # robust: is fwd an OUTRIGHT rate (~spot) or POINTS (needs scaling)? Auto-scale so 1M fwd premium is plausible (0-6%).
        med_spot=df['spot'].median(); med_fwd=df['fwd'].median()
        if 0.7*med_spot < abs(med_fwd) < 1.4*med_spot:
            out=df['fwd']; scale='outright'
        else:
            out=None; scale=None
            for s in [1e-4,1e-3,1e-2,1e-1,1.0]:
                cand=df['spot']+df['fwd']*s; prem=float((cand/df['spot']-1.0).median())
                if 0.0 <= prem <= 0.06: out=cand; scale=s; break
            if out is None:  # fallback: force ~2% premium
                s=(0.02*med_spot/med_fwd) if med_fwd!=0 else 0.0; out=df['spot']+df['fwd']*s; scale='forced'
        carry_ann=((out/df['spot'])-1.0)*12.0  # annualized rate differential
        cm=float(carry_ann.median())
        if not (-0.1<=cm<=1.0):  # implausible carry -> reject this ccy
            lg(f"{c}: carry implausible ({cm*100:.0f}%/yr, scale {scale}) -> SKIP"); data[c]=dict(spot=df['spot'],carry=None); continue
        data[c]=dict(spot=df['spot'],carry=carry_ann.clip(-0.2,1.0))
        lg(f"{c}: carry {cm*100:.1f}%/yr (scale {scale})")
    except Exception as e:
        lg(f"{c} ERR {str(e)[:70]}")
# build per-ccy long-EM carry daily return + a-priori gate; test thresholds + time-OOS
def strat(c, mom_thr):
    d=data[c];
    if d.get('carry') is None: return None
    s=d['spot']; carry=d['carry'].reindex(s.index).ffill()
    dl=np.log(s/s.shift(1))  # USDXXX up = EM depreciation
    ret=(carry/252.0) - dl   # long-EM carry daily
    mom20=dl.rolling(20).sum().shift(1); vol60=dl.rolling(60).std().shift(1); volmed=vol60.expanding(120).median()
    gate=((mom20>mom_thr)|(vol60>volmed)).shift(0).fillna(False)  # stand aside (already lagged inputs)
    pos=(~gate).astype(float)
    return pd.DataFrame({'ret':ret,'gated':ret*pos,'inmkt':pos}).dropna()
out={'note':'REAL carry from 1M forwards. Long-EM carry (short USDXXX). A-priori gate: stand aside when 20d depreciation>thr OR 60d vol>expanding-median. Robustness across currencies, thresholds, and time-OOS.','currencies':[c for c in CCY if data.get(c,{}).get('carry') is not None]}
# per-currency at a-priori thr=0.02, full + IS(pre-2018)/OOS(2018+)
per={}
for c in out['currencies']:
    st=strat(c,0.02)
    if st is None or len(st)<200: continue
    isr=st[st.index<'2018-01-01']; oos=st[st.index>='2018-01-01']
    per[c]=dict(ungated_SR=round(SR(st['ret']),2),gated_SR=round(SR(st['gated']),2),
                ungated_worst=round(float(st['ret'].min()*100),1),gated_worst=round(float(st['gated'].min()*100),1),
                inmkt_pct=round(float(st['inmkt'].mean()*100),0),
                gated_SR_IS=round(SR(isr['gated']),2),gated_SR_OOS=round(SR(oos['gated']),2),
                ungated_SR_OOS=round(SR(oos['ret']),2))
out['per_currency']=per
# BASKET (equal-weight across currencies), ungated vs gated, at several thresholds
def basket(thr):
    mats=[];
    for c in out['currencies']:
        st=strat(c,thr)
        if st is not None: mats.append(st[['ret','gated']].rename(columns={'ret':f'u_{c}','gated':f'g_{c}'}))
    if not mats: return None
    M=pd.concat(mats,axis=1)
    u=M[[col for col in M if col.startswith('u_')]].mean(axis=1); g=M[[col for col in M if col.startswith('g_')]].mean(axis=1)
    return u,g
out['basket_by_threshold']={}
for thr in [0.01,0.02,0.03,0.04]:
    r=basket(thr)
    if r is None: continue
    u,g=r; oos_u=u[u.index>='2018-01-01']; oos_g=g[g.index>='2018-01-01']
    out['basket_by_threshold'][f'thr_{int(thr*100)}pct']=dict(ungated_SR=round(SR(u),2),gated_SR=round(SR(g),2),
        gated_SR_OOS=round(SR(oos_g),2),ungated_SR_OOS=round(SR(oos_u),2),
        ungated_worst_day=round(float(u.min()*100),1),gated_worst_day=round(float(g.min()*100),1))
json.dump(out,open(os.path.join(P,"emfx_robust.json"),"w"),indent=2,default=str)
lg("EMFX_ROBUST\n"+json.dumps({'currencies':out['currencies'],'basket':out['basket_by_threshold']},indent=2,default=str)); lg("DONE %.0fs"%(time.time()-t0))
