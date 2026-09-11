# make_tables_garch_evt.py -- LaTeX tables from garch_evt_results.json (job_garch_evt.py).
# Emits tables/tab_garch_evt_frontier.tex (11-tau pinball edge vs GARCH-t by score region, plus the
# engine-vs-EVT head-to-head rows) and tables/tab_garch_evt_fz0.tex (FZ0 at 1% and 2.5%, breach, DM
# vs engine). Usage: python make_tables_garch_evt.py [results.json] [outdir]. Defaults: the project
# path's garch_evt_results.json and tables/. Both files are threeparttable bodies meant for \input.
import os, sys, json
P=os.environ.get("GBC_PROJ",r"C:\Users\OWNER\Claude\Projects\GBC Project")
src=sys.argv[1] if len(sys.argv)>1 else os.path.join(P,"garch_evt_results.json")
outdir=sys.argv[2] if len(sys.argv)>2 else os.path.join(P,"paper","jfec","tables"); os.makedirs(outdir,exist_ok=True)
R=json.load(open(src))
NAMES={'garch_t':'GARCH(1,1)-$t$','evt_name':'GARCH-EVT, per name','evt_pool':'GARCH-EVT, pooled tail',
       'body':'GARCH $+$ pooled body (no EVT)','engine':'Engine (body/EVT minimum)','engine_overlay':'Engine $+$ conformal overlay (97.5\\%)'}
def f(x,d=2,sign=True):
    if x is None: return '---'
    return ('%+.'+str(d)+'f')%x if sign else ('%.'+str(d)+'f')%x
def cell(e):
    if e is None: return '---'
    return '$%s$ (%s)'%(f(e['edge_pct']),f(e['DM'],2,False))
pb=R['pinball']; regs=[('top_mk63_decile','Top $\\mathrm{mk}_{63}$ decile'),('bulk_mk63_d1to9','Deciles 1--9'),
      ('top_composite_decile','Top composite decile'),('overall','Overall')]
L=[]
L.append('\\begin{tabular}{l'+'c'*len(regs)+'}'); L.append('\\toprule')
L.append('Model & '+' & '.join(n for _,n in regs)+' \\\\'); L.append('\\midrule')
L.append('\\multicolumn{%d}{l}{\\emph{Edge over GARCH-$t$, \\%% (per-date DM)}} \\\\'%(len(regs)+1))
for m in ['evt_name','evt_pool','body','engine']:
    L.append(NAMES[m]+' & '+' & '.join(cell(pb['vs_garch_t'][m][r]) for r,_ in regs)+' \\\\')
L.append('\\midrule'); L.append('\\multicolumn{%d}{l}{\\emph{Head-to-head, \\%% (per-date DM)}} \\\\'%(len(regs)+1))
for k,lab in [('engine_vs_evt_pool','Engine over GARCH-EVT pooled'),('engine_vs_evt_name','Engine over GARCH-EVT per name'),
              ('body_vs_evt_pool','Pooled body over GARCH-EVT pooled'),('engine_vs_body','Engine over pooled body')]:
    L.append(lab+' & '+' & '.join(cell(pb[k][r]) for r,_ in regs)+' \\\\')
L.append('\\bottomrule'); L.append('\\end{tabular}')
d=R['gpd_diagnostics']
L.append('\\begin{tablenotes}\\footnotesize')
L.append('\\item %d names, %s test rows, same rows and splits as Table~\\ref{tab:frontier} and Figure~\\ref{fig:fz}. '
         'Edge $=$ (reference pinball $-$ model pinball)/reference pinball over the eleven-level grid; DM is the per-date Newey--West(10) '
         'Diebold--Mariano statistic. GARCH-EVT is McNeil--Frey: GARCH(1,1)-$t$ filter, GPD tails fitted by maximum likelihood to the '
         '10\\%% most extreme training residuals per tail (per name, or pooled across names), empirical residual quantiles between the thresholds. '
         'The engine\'s pooled GPD at $p_0=0.025$ has $\\hat\\xi=%s$, $\\hat\\beta=%s$ on %d exceedances; the EVT branch is the tighter of the two at the 1\\%% node on %s\\%% of test rows and at the 2.5\\%% node on %s\\%%.'
         %(R['n_names'],'{:,}'.format(R['n_test']),f(d['engine_pooled_p0_0.025']['xi'],3,False),f(d['engine_pooled_p0_0.025']['beta'],3,False),
           d['engine_pooled_p0_0.025']['n_exc'],f(100*d['evt_branch_binds_frac']['0.01'],1,False),f(100*d['evt_branch_binds_frac']['0.025'],1,False)))
if R.get('synthetic'): L.append('\\item SYNTHETIC PANEL (self-test output); not for the paper.')
L.append('\\end{tablenotes}')
open(os.path.join(outdir,'tab_garch_evt_frontier.tex'),'w').write('\n'.join(L)+'\n')

F=R['fz0']; L=[]
L.append('\\begin{tabular}{lcccccc}'); L.append('\\toprule')
L.append('& \\multicolumn{3}{c}{$\\alpha=1\\%$} & \\multicolumn{3}{c}{$\\alpha=2.5\\%$} \\\\')
L.append('\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}')
L.append('Model & FZ0 & Breach & DM vs engine & FZ0 & Breach & DM vs engine \\\\'); L.append('\\midrule')
for m in ['engine','engine_overlay','body','evt_pool','evt_name','garch_t']:
    row=[NAMES[m]]
    for a in ['0.01','0.025']:
        r=F[a][m]; row+= [f(r['meanFZ0'],4,False),f(100*r['breach'],2,False)+'\\%',
                          '---' if 'vs_engine' not in r else f(r['vs_engine']['DM_t'],2,False)]
    L.append(' & '.join(row)+' \\\\')
L.append('\\bottomrule'); L.append('\\end{tabular}')
L.append('\\begin{tablenotes}\\footnotesize')
L.append('\\item FZ0 is the zero-homogeneous Fissler--Ziegel joint (VaR, ES) loss, lower is better; DM $>0$ means the row model scores worse than the engine '
         '(per-date Newey--West(10)). The engine row is the accuracy layer (no conformal shift) at both levels and is the reference of every DM; the overlay row adds the split-conformal shift at 97.5\\%% and coincides with the engine at 1\\%%. '
         'GARCH-EVT ES is the McNeil--Frey closed form; the engine and body ES are the 20-node integral of the monotonized quantile curve. '
         'Top-$\\mathrm{mk}_{63}$-decile DM of pooled GARCH-EVT versus the engine: %s at 1\\%% and %s at 2.5\\%%.'
         %(f(F['0.01']['engine_vs_evt_pool_top_mk63']['DM_t'],2,False),f(F['0.025']['engine_vs_evt_pool_top_mk63']['DM_t'],2,False)))
if R.get('synthetic'): L.append('\\item SYNTHETIC PANEL (self-test output); not for the paper.')
L.append('\\end{tablenotes}')
open(os.path.join(outdir,'tab_garch_evt_fz0.tex'),'w').write('\n'.join(L)+'\n')
print("wrote",outdir)
