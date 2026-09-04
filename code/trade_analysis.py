"""Reusable trading-analysis toolkit. Point it at a date-indexed returns Series -> tables + charts.
Usage:  from trade_analysis import analyze ; analyze(returns_series, "MyStrategy", outdir)
Or run directly: builds the standard GBC strategy charts (yearly/monthly/weekly + equity/Sharpe/DD/heatmap).
"""
import os, math, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

def _sr(r, ppy): r=pd.Series(r).dropna(); return float(r.mean()/r.std()*math.sqrt(ppy)) if len(r)>3 and r.std()>0 else np.nan

def period_stats(r, ppy):
    """Return per-year table: mean, ann_return, ann_Sharpe, %periods>0, worst, n."""
    r=r.dropna(); yr=r.index.year
    rows=[]
    for y,g in r.groupby(yr):
        rows.append(dict(year=int(y), n=len(g), mean=float(g.mean()), ann_ret=float(g.mean()*ppy),
                         ann_SR=_sr(g,ppy), pct_pos=float((g>0).mean()*100), worst=float(g.min())))
    return pd.DataFrame(rows)

def analyze(r, name, outdir, ppy=12, trades=None, compounded=False):
    """r: date-indexed period returns. ppy: periods/yr (12 monthly, 52 weekly, 252 daily). trades: optional per-period trade counts."""
    r=pd.Series(r).dropna().sort_index()
    eq=(1+r).cumprod() if compounded else (1+r.cumsum())
    dd=eq/eq.cummax()-1
    roll=max(ppy, 6); rsr=r.rolling(roll).apply(lambda x: x.mean()/x.std()*math.sqrt(ppy) if x.std()>0 else np.nan)
    yt=period_stats(r,ppy)
    fig,ax=plt.subplots(2,2,figsize=(14,8)); fig.suptitle(f"{name}  —  full-period consistency ({len(r)} periods, {r.index.min().date()}→{r.index.max().date()})",fontsize=13,weight='bold')
    ax[0,0].plot(eq.index,eq.values,color='#1f77b4'); ax[0,0].set_title("Cumulative equity (1 + Σ returns)"); ax[0,0].grid(alpha=.3)
    cols=['#2ca02c' if v>0 else '#d62728' for v in yt['ann_ret']]
    ax[0,1].bar(yt['year'].astype(str),yt['ann_ret']*100,color=cols); ax[0,1].set_title("PnL by YEAR (annualized %)"); ax[0,1].axhline(0,color='k',lw=.6); ax[0,1].tick_params(axis='x',rotation=45); ax[0,1].grid(alpha=.3,axis='y')
    ax[1,0].plot(rsr.index,rsr.values,color='#9467bd'); ax[1,0].axhline(0,color='k',lw=.6); ax[1,0].axhline(1,color='gray',ls='--',lw=.6); ax[1,0].set_title(f"Rolling {roll}-period Sharpe"); ax[1,0].grid(alpha=.3)
    ax[1,1].fill_between(dd.index,dd.values*100,0,color='#d62728',alpha=.5); ax[1,1].set_title("Drawdown (%)"); ax[1,1].grid(alpha=.3)
    plt.tight_layout(rect=[0,0,1,0.96]); f1=os.path.join(outdir,f"{name}_overview.png"); plt.savefig(f1,dpi=110); plt.close()
    # period-of-year heatmap (year x month, or year x week)
    try:
        if ppy>=52: r2=r.copy(); pcol=r2.index.isocalendar().week.astype(int); plabel='ISO week'
        else: r2=r.copy(); pcol=r2.index.month; plabel='month'
        piv=pd.DataFrame({'y':r2.index.year,'p':pcol,'r':r2.values}).pivot_table(index='y',columns='p',values='r',aggfunc='sum')
        fig2,axh=plt.subplots(figsize=(14,max(3,0.4*len(piv)+1)))
        im=axh.imshow(piv.values*100,aspect='auto',cmap='RdYlGn',vmin=-np.nanpercentile(np.abs(piv.values*100),95),vmax=np.nanpercentile(np.abs(piv.values*100),95))
        axh.set_yticks(range(len(piv.index))); axh.set_yticklabels(piv.index); axh.set_xlabel(plabel); axh.set_title(f"{name} — PnL heatmap (year × {plabel}, %)"); fig2.colorbar(im,ax=axh)
        f2=os.path.join(outdir,f"{name}_heatmap.png"); plt.tight_layout(); plt.savefig(f2,dpi=110); plt.close()
    except Exception as e: f2=None
    f3=None
    if trades is not None:
        t=pd.Series(trades).reindex(r.index).fillna(0)
        ty=t.groupby(t.index.year).sum()
        fig3,axt=plt.subplots(2,1,figsize=(14,7)); fig3.suptitle(f"{name} — TRADE VOLUME over time",fontsize=13,weight='bold')
        axt[0].fill_between(t.index,t.values,step='mid',color='#8c564b',alpha=.5); axt[0].plot(t.index,t.values,drawstyle='steps-mid',color='#8c564b',lw=.8)
        axt[0].set_title(f"Trades per period (avg {t.mean():.0f}/period)"); axt[0].grid(alpha=.3)
        axt[1].bar(ty.index.astype(str),ty.values,color='#8c564b'); axt[1].set_title("Trades per YEAR (total activity)"); axt[1].grid(alpha=.3,axis='y'); axt[1].tick_params(axis='x',rotation=45)
        f3=os.path.join(outdir,f"{name}_tradevol.png"); plt.tight_layout(rect=[0,0,1,.96]); plt.savefig(f3,dpi=110); plt.close()
        # COMBINED: cumulative PnL + trades on one plot (twin axis)
        wdt=max(1.0,float(np.median(np.diff(t.index.values).astype('timedelta64[D]').astype(float)))*0.8) if len(t)>2 else 20
        figc,axc=plt.subplots(figsize=(14,5)); axc2=axc.twinx()
        axc2.bar(t.index,t.values,width=wdt,color='#8c564b',alpha=.30,label='trades/period')
        axc.plot(eq.index,eq.values,color='#1f77b4',lw=1.6,label='cumulative PnL')
        axc.set_ylabel('cumulative PnL (1+Σret)',color='#1f77b4'); axc2.set_ylabel('trades / period',color='#8c564b')
        axc.set_title(f"{name}: cumulative PnL + trade volume (per {'week' if ppy>=52 else 'month'})"); axc.grid(alpha=.3)
        axc.set_zorder(2); axc.patch.set_visible(False)
        f4=os.path.join(outdir,f"{name}_pnl_and_trades.png"); plt.tight_layout(); plt.savefig(f4,dpi=110); plt.close()
    summ=dict(name=name,ppy=ppy,n_periods=len(r),full_SR=_sr(r,ppy),full_ann_ret=float(r.mean()*ppy),
              pct_periods_pos=float((r>0).mean()*100),n_losing_years=int((yt['ann_ret']<0).sum()),
              worst_period=float(r.min()),max_drawdown=float(dd.min()),
              yearly=yt.round(4).to_dict('records'),charts=[c for c in [f1,f2,f3,locals().get('f4')] if c])
    if trades is not None:
        t=pd.Series(trades).reindex(r.index); summ['total_trades']=int(t.sum()); summ['avg_trades_per_period']=round(float(t.mean()),1)
    return summ

if __name__=="__main__":
    P=os.path.dirname(os.path.abspath(__file__)); out={}
    # 1) Cross-asset ETF book (monthly)
    try:
        d=pd.read_csv(os.path.join(P,"xasset_combined_curve.csv")); d.index=pd.PeriodIndex(d['ym'],freq='M').to_timestamp()
        out['CrossAsset_ETF']=analyze(d['combined_ret'],"CrossAsset_ETF_monthly",P,ppy=12)
    except Exception as e: out['CrossAsset_ETF']={'err':str(e)[:120]}
    # 2) Refined single-name VRP (monthly, mid)
    try:
        d=pd.read_csv(os.path.join(P,"paper_sim_series.csv")); d.index=pd.PeriodIndex(d['ym'],freq='M').to_timestamp()
        out['SingleName_refined']=analyze(d['mid'],"SingleName_VRP_monthly",P,ppy=12)
    except Exception as e: out['SingleName_refined']={'err':str(e)[:120]}
    # 2b) Monthly single-name (tau10_monthly_series has trade counts n)
    try:
        d=pd.read_csv(os.path.join(P,"tau10_monthly_series.csv")); d.index=pd.PeriodIndex(d['ym'],freq='M').to_timestamp()
        out['SingleName_monthly_tau10']=analyze(d['net_pctK'],"SingleName_VRP_monthly_tau10",P,ppy=12,trades=d['n'])
    except Exception as e: out['SingleName_monthly_tau10']={'err':str(e)[:120]}
    # 3) WEEKLY single-name VRP (from weekly_trades.csv -> weekly mean net at mid)
    try:
        w=pd.read_csv(os.path.join(P,"weekly_trades.csv")); w['date']=pd.to_datetime(w['date'])
        wk=w.groupby(pd.Grouper(key='date',freq='W'))['net'].mean().dropna()
        cnt=w.groupby(pd.Grouper(key='date',freq='W'))['net'].count()
        out['Weekly_singlename']=analyze(wk,"SingleName_VRP_WEEKLY",P,ppy=52,trades=cnt)
    except Exception as e: out['Weekly_singlename']={'err':str(e)[:120]}
    json.dump(out,open(os.path.join(P,"trade_analysis_summary.json"),"w"),indent=2,default=str)
    for k,v in out.items():
        if 'err' in v: print(k,'ERR',v['err']); continue
        print(f"{k}: full_SR={v['full_SR']:.2f} ann={v['full_ann_ret']*100:.1f}% pos={v['pct_periods_pos']:.0f}% losing_yrs={v['n_losing_years']} maxDD={v['max_drawdown']*100:.1f}%")
    print("DONE trade_analysis")
