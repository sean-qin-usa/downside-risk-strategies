import os, json
import numpy as np, pandas as pd
PROJ=r"C:\Users\OWNER\Claude\Projects\GBC Project"; RES=r"C:\GBC_data\results\pq_trade"
seas_f=os.path.join(PROJ,"mh_quantiles_seas.csv"); base_f=os.path.join(RES,"mh_quantiles_gpu_v2.csv")
if not os.path.exists(seas_f):
    print("SEAS OUTPUT NOT READY yet - training still running; re-drop this job when train_seas.log ends with DONE."); raise SystemExit
TAUS=[.05,.10,.50,.90,.95]
def bymonth(f):
    d=pd.read_csv(f); d=d[d.h==21].copy(); d['date']=pd.to_datetime(d.date); d['mo']=d.date.dt.month; d=d[d.y.notna()]
    om={}
    for m in range(1,13):
        s=d[d.mo==m]
        om[m]={f"{int(t*100):02d}": round(float((s.y<s[f'p{int(t*100):02d}']).mean()),3) for t in TAUS}; om[m]['n']=int(len(s))
    ov={f"{int(t*100):02d}": round(float((d.y<d[f'p{int(t*100):02d}']).mean()),3) for t in TAUS}
    return om, ov
sm,sov=bymonth(seas_f); bm,bov=bymonth(base_f)
res=dict(seas_overall=sov, raw9_overall=bov, seas_bymonth=sm, raw9_bymonth=bm,
         Q1_p05=dict(nominal=0.05, raw9_feb=bm[2]['05'], seas_feb=sm[2]['05'], raw9_mar=bm[3]['05'], seas_mar=sm[3]['05']),
         Q1_p10=dict(nominal=0.10, raw9_feb=bm[2]['10'], seas_feb=sm[2]['10'], raw9_mar=bm[3]['10'], seas_mar=sm[3]['10']))
json.dump(res, open(os.path.join(PROJ,"seas_bymonth_eval.json"),"w"), indent=2)
# figure: p05 & p10 downside-tail breach rate by month, seas vs raw9
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
mos=list(range(1,13)); L=['J','F','M','A','M','J','J','A','S','O','N','D']
fig,ax=plt.subplots(1,2,figsize=(14,4.6)); fig.suptitle("Does adding calendar features fix the model's Q1 tail? (h=21, downside breach rate by month)",fontsize=12,fontweight='bold')
for k,(tau,nom) in enumerate([('05',0.05),('10',0.10)]):
    A=ax[k]
    A.plot(mos,[bm[m][tau] for m in mos],'-o',color='#c0504d',label='raw-9 (baseline)')
    A.plot(mos,[sm[m][tau] for m in mos],'-o',color='#3a7a3a',label='raw-9 + seasonality')
    A.axhline(nom,ls='--',color='k',lw=1); A.text(0.5,nom+0.005,f'nominal {int(tau)}%',fontsize=8)
    A.set_xticks(mos); A.set_xticklabels(L); A.set_ylabel(f'breach rate of {int(tau)}% quantile')
    A.set_title(f"{int(tau)}% downside quantile — closer to nominal = better\n(Feb-Mar is where baseline under-covers)",fontsize=10); A.legend(fontsize=9)
plt.tight_layout(rect=[0,0,1,0.93]); plt.savefig(os.path.join(PROJ,"seas_bymonth_calibration.png"),dpi=110)
print("EVAL DONE"); print("Q1 p05:",json.dumps(res['Q1_p05'])); print("overall seas",sov,"raw9",bov)
