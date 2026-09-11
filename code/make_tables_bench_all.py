# make_tables_bench_all.py -- LaTeX tables from bench_all_results.json (job_bench_all.py).
# tables/tab_bench_pinball.tex : eleven-level pinball edge over GARCH-t by region, engine head-to-head, MCS membership
# tables/tab_bench_fz0.tex     : FZ0 at 1% and 2.5%, breach, DM vs the accuracy layer, MCS membership
# tables/tab_bench_tests.tex   : CPA Wald and slope t, DQ pass rates, Murphy fraction, per-date win rate
# Usage: python make_tables_bench_all.py [results.json] [outdir]
import os, sys, json
P=os.environ.get("GBC_PROJ",r"C:\Users\OWNER\Claude\Projects\GBC Project")
src=sys.argv[1] if len(sys.argv)>1 else os.path.join(P,"bench_all_results.json")
outdir=sys.argv[2] if len(sys.argv)>2 else os.path.join(P,"paper","jfec","tables"); os.makedirs(outdir,exist_ok=True)
R=json.load(open(src))
NAMES={'engine':'Engine (accuracy layer)','engine_overlay':'Engine $+$ conformal overlay','body':'GARCH $+$ pooled body (no EVT)',
 'garch_t':'GARCH(1,1)-$t$','gjr_skewt':'GJR-GARCH-skew-$t$','ewma':'EWMA (RiskMetrics)','hs500':'Historical simulation (500d)',
 'fhs_pool':'GARCH-FHS (pooled)','fhs_name':'GARCH-FHS (per name)','fhs_roll500':'GARCH-FHS (rolling 500d)',
 'sav_caviar':'SAV-CAViaR','evt_pool':'GARCH-EVT (pooled tail)','evt_name':'GARCH-EVT (per name)','gas_pzc':'GAS-FZ (PZC)','taylor':'ES-CAViaR (Taylor)'}
ORDER=['engine','engine_overlay','body','garch_t','gjr_skewt','fhs_pool','fhs_name','fhs_roll500','evt_pool','evt_name','sav_caviar','gas_pzc','taylor','ewma','hs500']
def f(x,d=2,sign=True):
    if x is None: return '---'
    return ('%+.'+str(d)+'f')%x if sign else ('%.'+str(d)+'f')%x
def cell(e):
    if e is None: return '---'
    return '$%s$ (%s)'%(f(e['edge_pct']),f(e['DM'],2,False))
def tick(m,key): return r'$\checkmark$' if m in R['mcs'][key]['in_90pct_MCS'] else ''
pb=R['pinball']; regs=[('top_mk63_decile','Top $\\mathrm{mk}_{63}$ decile'),('bulk_mk63_d1to9','Deciles 1--9'),('overall','Overall')]
L=['\\begin{tabular}{l'+'c'*len(regs)+'cc}','\\toprule',
   'Model & '+' & '.join(n for _,n in regs)+' & Engine vs model (top) & MCS \\\\','\\midrule']
for m in ORDER:
    if m not in pb['mean_pinball']: continue
    row=[NAMES[m]]
    if m=='garch_t': row+=['(reference)']*len(regs)
    else: row+=[cell(pb['vs_garch_t'][m][r]) for r,_ in regs]
    row.append('---' if m=='engine' else cell(pb['engine_vs'][m]['top_mk63_decile'])); row.append(tick(m,'pinball_11tau'))
    L.append(' & '.join(row)+' \\\\')
L+=['\\bottomrule','\\end{tabular}','\\begin{tablenotes}\\footnotesize',
    '\\item %d names, %s test rows, the rows of Table~1 of the paper. Edge $=$ (GARCH-$t$ pinball $-$ model pinball)/GARCH-$t$ pinball over the eleven-level grid, per-date Newey--West(10) DM in parentheses. The last column is the 90\\%% Model Confidence Set on the per-date eleven-level pinball series (T$_{\\max}$, stationary bootstrap over dates, mean block 10, $B=1{,}000$)%s.'%(
        R['n_names'],'{:,}'.format(R['n_test']),'' if not R['mcs']['pinball_11tau'].get('models_with_missing_rows_excluded') else '; excluded for missing rows: '+', '.join(NAMES[m] for m in R['mcs']['pinball_11tau']['models_with_missing_rows_excluded'])),
    '\\end{tablenotes}']
if R.get('synthetic'): L.insert(-1,'\\item SYNTHETIC PANEL (self-test output); not for the paper.')
open(os.path.join(outdir,'tab_bench_pinball.tex'),'w').write('\n'.join(L)+'\n')

F=R['fz0']; L=['\\begin{tabular}{lcccccccc}','\\toprule','& \\multicolumn{4}{c}{$\\alpha=1\\%$} & \\multicolumn{4}{c}{$\\alpha=2.5\\%$} \\\\','\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}',
   'Model & FZ0 & Breach & DM & MCS & FZ0 & Breach & DM & MCS \\\\','\\midrule']
for m in ORDER:
    if m not in F['0.01'] or F['0.01'][m].get('meanFZ0') is None: continue
    row=[NAMES[m]]
    for a in ['0.01','0.025']:
        r=F[a][m]; row+=[f(r['meanFZ0'],4,False),f(100*r['breach'],2,False)+'\\%','---' if not r.get('vs_engine') else f(r['vs_engine']['DM_t'],2,False),tick(m,'fz0_%g'%float(a))]
    L.append(' & '.join(row)+' \\\\')
L+=['\\bottomrule','\\end{tabular}','\\begin{tablenotes}\\footnotesize',
    '\\item FZ0 is the zero-homogeneous Fissler--Ziegel joint (VaR, ES) loss, lower is better; DM $>0$ means the row model scores worse than the accuracy layer (per-date Newey--West(10)). ES: closed forms for the $t$, skew-$t$ and Gaussian entrants; empirical tail means for HS and FHS; McNeil--Frey closed form for GARCH-EVT; the FZ0-estimated dynamic pair for GAS and Taylor; the 20-node integral of the monotonized curve for the engine and body. SAV-CAViaR produces no ES and is absent here. MCS: 90\\% Model Confidence Set on the per-date FZ0 series.',
    '\\end{tablenotes}']
if R.get('synthetic'): L.insert(-1,'\\item SYNTHETIC PANEL (self-test output); not for the paper.')
open(os.path.join(outdir,'tab_bench_fz0.tex'),'w').write('\n'.join(L)+'\n')

C=R['cpa']; DQ=R['dq']; MU=R['murphy']; DS=R['loss_diff_dispersion']
L=['\\begin{tabular}{lcccccccc}','\\toprule','& \\multicolumn{2}{c}{CPA vs engine} & \\multicolumn{2}{c}{DQ pass rate} & \\multicolumn{2}{c}{Murphy: engine better} & \\multicolumn{2}{c}{Engine win rate} \\\\',
   '\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}',
   'Model & Wald $\\chi^2_2$ & slope $t$ & 1\\% & 2.5\\% & 1\\% & 2.5\\% & top decile & overall \\\\','\\midrule']
def pc(x): return '---' if x is None else '%d\\%%'%round(100*x)
for m in ORDER:
    if m=='engine': continue
    c=C.get(m); d1=DQ['0.01'].get(m); d2=DQ['0.025'].get(m); m1=MU['0.01'].get(m); m2=MU['0.025'].get(m)
    ds=DS['top_mk63_decile'].get(m); do=DS['overall'].get(m)
    row=[NAMES[m],'---' if not c else f(c['GW_wald_chi2_2'],1,False),'---' if not c else f(c['slope_t'],1,False),
         pc(d1['dq_passrate_5pct'] if d1 else None),pc(d2['dq_passrate_5pct'] if d2 else None),
         pc(m1['frac_theta_engine_better'] if m1 else None),pc(m2['frac_theta_engine_better'] if m2 else None),
         pc(ds['win_rate_dates'] if ds else None),pc(do['win_rate_dates'] if do else None)]
    L.append(' & '.join(row)+' \\\\')
e1=DQ['0.01']['engine']['dq_passrate_5pct']; e2=DQ['0.025']['engine']['dq_passrate_5pct']
L+=['\\midrule','Engine (accuracy layer) & --- & --- & %s & %s & --- & --- & --- & --- \\\\'%(pc(e1),pc(e2)),'\\bottomrule','\\end{tabular}','\\begin{tablenotes}\\footnotesize',
    '\\item CPA: Giacomini--White Wald test of equal conditional accuracy of the model and the engine with instruments (1, lagged composite score percentile), Newey--West(10) over per-date sums, and the date-clustered $t$ of the slope of the loss differential (model minus engine) on the score; a positive slope means the engine\'s advantage grows with the score. DQ: Engle--Manganelli dynamic quantile test with four hit lags and the VaR, share of names passing at 5\\%. Murphy: share of a forty-point return-space threshold grid on which the engine has the lower elementary quantile score. Win rate: share of test dates on which the date-averaged engine pinball is below the model\'s. Models with an entry only at the regulatory levels (GAS, Taylor) have no pinball-based columns.',
    '\\end{tablenotes}']
if R.get('synthetic'): L.insert(-1,'\\item SYNTHETIC PANEL (self-test output); not for the paper.')
open(os.path.join(outdir,'tab_bench_tests.tex'),'w').write('\n'.join(L)+'\n')
print("wrote",outdir)
