# Misspecification confirmation: does GARCH-t break on the wildest domains? Fit GARCH-t, measure tail-VaR breach + residual kurtosis.
import json, os, time, math
P=r"C:\Users\OWNER\Claude\Projects\GBC Project"; lg=lambda s:print(s,flush=True); t0=time.time()
from xbbg import blp
import numpy as np, pandas as pd, datetime as dt
from arch import arch_model
from scipy import stats as sps
def to_pd(d):
    for m in ('to_pandas','to_native'):
        if hasattr(d,m):
            try:
                x=getattr(d,m)()
                if hasattr(x,'to_pandas') and not isinstance(x,pd.DataFrame): x=x.to_pandas()
                if isinstance(x,pd.DataFrame): return x
            except Exception: pass
    return d if isinstance(d,pd.DataFrame) else None
def extract(pdf):
    if pdf is None or not len(pdf): return np.array([])
    cols=[str(c).lower() for c in pdf.columns]
    if 'value' in cols:
        vcol=pdf.columns[cols.index('value')]; dcol=[pdf.columns[i] for i,c in enumerate(cols) if 'date' in c]
        if dcol: pdf=pdf.sort_values(dcol[0])
        return pd.to_numeric(pdf[vcol],errors='coerce').dropna().values.astype(float)
    num=pdf.select_dtypes('number'); return num.iloc[:,-1].dropna().values.astype(float) if num.shape[1] else np.array([])
SER={'USDARS':'USDARS Curncy','USDTRY':'USDTRY Curncy','USDRUB':'USDRUB Curncy','NATGAS':'NG1 Comdty','COPPER':'HG1 Comdty','SPY_ctrl':'SPY US Equity'}
end=dt.date.today(); start=end-dt.timedelta(days=365*10)
out={}
for nm,tk in SER.items():
    try:
        vals=extract(to_pd(blp.bdh(tk,'px_last',start,end)))
        s=pd.Series(vals).astype(float); r=np.log(s/s.shift(1)).replace([np.inf,-np.inf],np.nan).dropna()*100  # pct
        if len(r)<300: out[nm]={'err':'short'}; continue
        # GARCH-t (leverage GJR, Student-t) in-sample filter
        am=arch_model(r-r.mean(),mean='Zero',vol='GARCH',p=1,o=1,q=1,dist='t').fit(disp='off')
        nu=float(am.params.get('nu',8)); cv=am.conditional_volatility
        z=(r-r.mean()).values/cv.values  # standardized resid
        # model 1% and 5% one-sided VaR breach (both tails) using Student-t quantile of standardized innovations
        tq=lambda a: sps.t.ppf(a,nu)*math.sqrt((nu-2)/nu)  # standardized t quantile
        br1=float((z< tq(0.01)).mean()*100); br5=float((z< tq(0.05)).mean()*100)
        bru1=float((z> -tq(0.01)).mean()*100)
        out[nm]={'ticker':tk,'n':int(len(r)),'garch_t_nu':round(nu,2),
                 'resid_kurtosis_after_GARCH':round(float(sps.kurtosis(z,fisher=True)),1),
                 'left_breach_1pct_nominal1':round(br1,2),'left_breach_5pct_nominal5':round(br5,2),
                 'right_breach_1pct_nominal1':round(bru1,2),
                 'raw_return_kurtosis':round(float(sps.kurtosis(r,fisher=True)),1)}
        lg(f"{nm}: rawKurt={out[nm]['raw_return_kurtosis']} -> residKurt(afterGARCH)={out[nm]['resid_kurtosis_after_GARCH']} | 1%VaR breach={br1} (want~1) 5%={br5} (want~5)")
    except Exception as e:
        out[nm]={'ticker':tk,'err':str(e)[:120]}; lg(f"{nm} ERR {str(e)[:100]}")
out['_note']='resid kurtosis AFTER GARCH-t filtering >> 0 and breach rates >> nominal ==> GARCH-t misspecified (jumps/regime remain). SPY_ctrl is the well-specified baseline.'
json.dump(out,open(os.path.join(P,"misspec_pilot.json"),"w"),indent=2,default=str)
lg("MISSPEC_PILOT_DONE %.0fs"%(time.time()-t0))
