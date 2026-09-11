# r36_garch_evt_edits.py -- fold the same-rows GARCH-EVT comparison (garch_evt_results.json,
# holdout_garch_evt_results.json), the residual-hybrid walk-forward (walkforward_hybrid_results.json) and the
# per-asset rerun with 97.5% conditional coverage (perasset_v2_results.json) into the manuscript and OA.
# Exact unique replacements; ledger appended to docs/CHANGE_LEDGER_R34.md under an R36 heading.
import sys, json
M="paper_A_jfec.tex"; OA="paper_A_jfec_online_appendix.tex"
s=open(M,encoding="utf-8").read(); o=open(OA,encoding="utf-8").read(); led=[]
def ed(doc,tag,old,new,why):
    global s,o
    t=s if doc=="M" else o; n=t.count(old)
    if n!=1: sys.exit(f"ANCHOR {tag}: {n}\n{old[:200]}")
    t=t.replace(old,new); led.append((doc,tag,old,new,why))
    if doc=="M": s=t
    else: o=t
G=json.load(open("garch_evt_results.json")); H=json.load(open("holdout_garch_evt_results.json"))
W=json.load(open("walkforward_hybrid_results.json")); PA=json.load(open("perasset_v2_results.json"))['per_variant']
pb=G['pinball']; F=G['fz0']
ep=pb['engine_vs_evt_pool']; en=pb['engine_vs_evt_name']; vg=pb['vs_garch_t']
assert ep['top_mk63_decile']['DM']>2 and abs(ep['bulk_mk63_d1to9']['edge_pct'])<0.2   # pre-set rule: frontier claim stands
# ---------------- Section 1.2: replace the placeholder
ed("M","1.2-garchevt",
 r"A same-rows comparison against per-name and pooled GARCH-EVT tails, on the frontier sorts and on the FZ0 score, is reported in the Online Appendix once run.",
 r"A same-rows comparison against standalone McNeil--Frey GARCH-EVT, per name and with a pooled tail, is reported in Sections~\ref{sec:frontier} and~\ref{sec:frtb} and in the Online Appendix: the conventional EVT tail carries no frontier of its own, and the estimator beats it by %.2f\%% (DM %.1f) in the top kurtosis decile and on the joint score at both levels."%(ep['top_mk63_decile']['edge_pct'],ep['top_mk63_decile']['DM']),
 "the pending comparison has run")
# ---------------- Section 4.1: GARCH-EVT on the frontier rows, after the Table 1 discussion
ed("M","4.1-garchevt",
 r"\paragraph{The composite score.} Table~\ref{tab:frontier} sorts on each",
 r"\paragraph{GARCH-EVT on the same rows.} The frontier is a statement about a state-conditioned residual shape, so the natural question is whether a conventional unconditional tail captures it. On the rows of Table~\ref{tab:frontier}, a McNeil--Frey GARCH-EVT forecast (the same GARCH-$t$ filter, GPD tails fitted by maximum likelihood to the 10\%% most extreme training residuals per tail, empirical residual quantiles in between) shows no frontier: against GARCH-$t$ its top-decile edge is $%+.2f\%%$ (DM %.1f) per name and $%+.2f\%%$ (DM %.1f) with a pooled tail, and its overall edge is negative in both forms. The estimator beats the pooled GARCH-EVT by $%+.2f\%%$ (DM %.1f) in the top kurtosis decile and by $%+.2f\%%$ (DM %.1f) in deciles one through nine, and the per-name GARCH-EVT by $%+.2f\%%$ (DM %.1f) and $%+.2f\%%$ (DM %.1f). The same-rows table and the GPD threshold diagnostics are in the Online Appendix."%(
   vg['evt_name']['top_mk63_decile']['edge_pct'],vg['evt_name']['top_mk63_decile']['DM'],vg['evt_pool']['top_mk63_decile']['edge_pct'],vg['evt_pool']['top_mk63_decile']['DM'],
   ep['top_mk63_decile']['edge_pct'],ep['top_mk63_decile']['DM'],ep['bulk_mk63_d1to9']['edge_pct'],ep['bulk_mk63_d1to9']['DM'],
   en['top_mk63_decile']['edge_pct'],en['top_mk63_decile']['DM'],en['bulk_mk63_d1to9']['edge_pct'],en['bulk_mk63_d1to9']['DM'])+"\n\n"+r"\paragraph{The composite score.} Table~\ref{tab:frontier} sorts on each",
 "TODO C.2: the missing benchmark on the frontier rows")
# ---------------- Section 4.1 holdout paragraph
hp=H['engine_vs_evt_pool']; hg=H['vs_garch_t']['evt_pool']
ed("M","4.1-holdout-garchevt",
 r"This is the same threshold nonlinearity, attenuated in a larger-cap, pre-2014 universe.",
 r"This is the same threshold nonlinearity, attenuated in a larger-cap, pre-2014 universe. On the same holdout rows the pooled GARCH-EVT again shows no frontier ($%+.2f\%%$ against GARCH-$t$ in the top decile, DM %.1f), and the frozen learner beats it there by $%+.2f\%%$ (DM %.1f), within noise elsewhere."%(
   hg['top_decile_qcut']['edge_pct'],hg['top_decile_qcut']['DM'],hp['top_decile_qcut']['edge_pct'],hp['top_decile_qcut']['DM']),
 "TODO C.4")
# ---------------- Section 3: residual-hybrid refit numbers now have a committed file
ed("M","3-refit",
 r"which the top decile still carries $+2.47\%$ at DM 6.05 while the average"+"\n"+r"edge compresses to $+0.32\%$ (DM 0.8), within noise; this check uses the returns-space learner of the frozen holdout specification.",
 r"which the top decile still carries $%+.2f\%%$ at DM %.2f while the average"%(W['top_decile_edge_pct'],W['top_decile_DM'])+"\n"+r"edge washes out ($%+.2f\%%$, DM $%.2f$); the returns-space learner of the frozen holdout specification gives $+2.47\%%$ (DM 6.05) and $+0.32\%%$ (DM 0.8) under the same schedule."%(W['overall_edge_pct'],W['overall_DM']),
 "walkforward_hybrid_results.json (residual-hybrid learner) replaces the file-less +2.09/4.43")
ed("OA","OA-refit-row",
 r"4.43 (annual-refit residual-hybrid walk-forward, $+2.09\%$)",
 r"%.2f (annual-refit residual-hybrid walk-forward, $%+.2f\%%$)"%(W['top_decile_DM'],W['top_decile_edge_pct']),
 "same file")
# ---------------- Section 5.1: FZ0 against GARCH-EVT; Figure 2 bars and caption
fp1=F['0.01']['evt_pool']['vs_engine']; fp2=F['0.025']['evt_pool']['vs_engine']; fn1=F['0.01']['evt_name']['vs_engine']; fn2=F['0.025']['evt_name']['vs_engine']
ed("M","5.1-garchevt",
 r"At 2.5\% it again wins over GARCH-$t$ (DM 5.1). The two closest dynamic",
 r"At 2.5\%% it again wins over GARCH-$t$ (DM 5.1). On the same rows it also beats standalone GARCH-EVT, whose ES is the McNeil--Frey closed form: with a pooled tail by DM %.1f at 1\%% and %.1f at 2.5\%%, and per name by DM %.1f and %.1f, so the gain over the conventional EVT construction is not confined to the pinball frontier. The two closest dynamic"%(fp1['DM_t'],fp2['DM_t'],fn1['DM_t'],fn2['DM_t']),
 "TODO C.2: FZ0 head-to-head")
ed("M","fig2-bars",
 r"symbolic x coords={GARCH-$t$,Taylor,FHS,GAS}, xtick=data,",
 r"symbolic x coords={GARCH-$t$,GARCH-EVT,Taylor,FHS,GAS}, xtick=data,","GARCH-EVT enters Figure 2")
ed("M","fig2-bar1",
 r"\addplot[fill=npblue,draw=npblue] coordinates {(GARCH-$t$,0.00848)(Taylor,0.01748)(FHS,0.02517)(GAS,0.08514)};",
 r"\addplot[fill=npblue,draw=npblue] coordinates {(GARCH-$t$,0.00848)(GARCH-EVT,%.5f)(Taylor,0.01748)(FHS,0.02517)(GAS,0.08514)};"%fp1['mean_diff'],"same-rows job, pooled tail")
ed("M","fig2-bar2",
 r"\addplot[fill=npmid,draw=npmid] coordinates {(GARCH-$t$,0.00545)(Taylor,0.00024)(FHS,0.01370)(GAS,0.05030)};",
 r"\addplot[fill=npmid,draw=npmid] coordinates {(GARCH-$t$,0.00545)(GARCH-EVT,%.5f)(Taylor,0.00024)(FHS,0.01370)(GAS,0.05030)};"%fp2['mean_diff'],"same")
ed("M","fig2-caption",
 r"$1\%$, $5.1$ at $2.5\%$) and FHS (DM $4.9$), together with the two",
 r"$1\%%$, $5.1$ at $2.5\%%$), pooled-tail GARCH-EVT (DM $%.1f$ and $%.1f$, same-rows run) and FHS (DM $4.9$), together with the two"%(fp1['DM_t'],fp2['DM_t']),"caption")
ed("M","fig2-enlarge", r"enlarge x limits=0.28, ymajorgrids,", r"enlarge x limits=0.22, ymajorgrids,","five bars")
# ---------------- Per-asset pass rates from the committed rerun (perasset_v2_results.json, 200 names), with 97.5% CC
e=PA['hybrid_EVT']; c=PA['hybrid_EVT_conf']
ed("M","5.1-passrates",
 r"EVT-tailed residual-hybrid passes Kupiec at 99\% for $84\%$ of names and"+"\n"+r"Christoffersen conditional coverage for $86\%$, and the date-clustered test passes at 99\% ($t=1.01$) and marginally at 97.5\% ($t=1.86$)",
 r"EVT-tailed residual-hybrid passes Kupiec at 99\%% for $%d\%%$ of names and"%round(100*e['kupiec99_passrate'])+"\n"+r"Christoffersen conditional coverage for $%d\%%$ (at 97.5\%%, $%d\%%$ and $%d\%%$), and the date-clustered test passes at 99\%% ($t=%.2f$) and marginally at 97.5\%% ($t=%.2f$)"%(round(100*e['christoffersen99_passrate']),round(100*e['kupiec975_passrate']),round(100*e['christoffersen975_passrate']),e['dateclustered99_NW_t'],e['dateclustered975_NW_t']),
 "B.6/E.8: conditional coverage at both levels; numbers from the committed rerun of job_perasset_v2.py")
ed("M","5.1-passrates2",
 r"Per-name diagnostics show residual cross-sectional calibration heterogeneity (84\% and 86\% pass rates at 99\%, Online Appendix Figure~OA.2).",
 r"Per-name diagnostics show residual cross-sectional calibration heterogeneity (%d\%% and %d\%% pass rates at 99\%%, Online Appendix Figure~OA.2)."%(round(100*e['kupiec99_passrate']),round(100*e['christoffersen99_passrate'])),"same file")
ed("M","5.1-passrates3",
 r"(Kupiec$_{97.5}$ pass rate 47\%, against 72\% unshifted and 69\% adaptive)",
 r"(Kupiec$_{97.5}$ pass rate %d\%%, against %d\%% unshifted and 69\%% adaptive)"%(round(100*c['kupiec975_passrate']),round(100*e['kupiec975_passrate'])),"same file")
# ---------------- OA: new section with the two tables (inlined)
tf=open("tables/tab_garch_evt_frontier.tex").read(); tz=open("tables/tab_garch_evt_fz0.tex").read()
tf=tf.replace("Figure~\\ref{fig:fz}","Figure~2 of the paper").replace("Table~\\ref{tab:frontier}","Table~1 of the paper")
tz=tz.replace("Figure~\\ref{fig:fz}","Figure~2 of the paper")
sec=r"""\section{Standalone GARCH-EVT on the canonical rows}\label{sec:garchevt-oa}
The manuscript's comparison set omits standalone GARCH-EVT \citep{mcneilfrey2000}, which \citet{kuester2006} rank first among classical methods. This section reports it on exactly the rows, filter and splits of the frontier sorts (Table~1 of the paper) and of the full-panel FZ0 run (Figure~2 of the paper), from \texttt{job\_garch\_evt.py} (result file \texttt{garch\_evt\_results.json}). Two forms are run: per name, with the GPD tails fitted to each name's own training residuals, and pooled, with one threshold and one $(\xi,\beta)$ per tail across names. The pooled body row is the frontier engine of Table~1 (no EVT branch); the engine row adds the body/EVT minimum and rearrangement of equation~(5). Table~\ref{tab:garchevt-frontier} gives the eleven-level pinball comparison and Table~\ref{tab:garchevt-fz0} the joint score.

\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{GARCH-EVT on the frontier rows: pinball edge by score region and head-to-head comparisons.}
\label{tab:garchevt-frontier}
\small
%s\end{threeparttable}
\end{table}

\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{GARCH-EVT on the full-panel FZ0 rows.}
\label{tab:garchevt-fz0}
\small
%s\end{threeparttable}
\end{table}

\noindent\emph{Threshold diagnostics.} Over a threshold grid $p_0\in\{0.025,0.05,0.10,0.15\}$ the pooled lower-tail fit gives $\hat\xi=%s$ on %s exceedances; per name at $p_0=0.10$ the interquartile range of $\hat\xi$ is %s to %s (median %s) with a median of %d exceedances, and no name has $\hat\xi\ge1$. The EVT branch is the tighter of the two inside the engine's minimum on %s\%% of test rows at the 1\%% node and %s\%% at the 2.5\%% node. On the 2000--2013 holdout rows (\texttt{job\_holdout\_garch\_evt.py}) the frozen learner beats the pooled GARCH-EVT by $%+.2f\%%$ (DM %.2f) in the top holdout decile and by $%+.2f\%%$ (DM %.2f) in the frozen design-era bucket, and by $%+.2f\%%$ (DM %.2f) in deciles one through nine.

"""
D=G['gpd_diagnostics']; pg=D['pooled_grid']; pn=D['per_name_grid']['0.1']
xis=", ".join("%.3f"%pg[k]['xi'] for k in ['0.025','0.05','0.1','0.15']); nex=", ".join("{:,}".format(pg[k]['n_exc']) for k in ['0.025','0.05','0.1','0.15'])
sec=sec%(tf,tz,xis,nex,"%.3f"%pn['xi_q25_50_75'][0],"%.3f"%pn['xi_q25_50_75'][2],"%.3f"%pn['xi_q25_50_75'][1],pn['n_exc_median'],
        "%.1f"%(100*D['evt_branch_binds_frac']['0.01']),"%.1f"%(100*D['evt_branch_binds_frac']['0.025']),
        hp['top_decile_qcut']['edge_pct'],hp['top_decile_qcut']['DM'],hp['top_bucket_frozen']['edge_pct'],hp['top_bucket_frozen']['DM'],hp['bulk_qcut_1to9']['edge_pct'],hp['bulk_qcut_1to9']['DM'])
ed("OA","OA-garchevt-section", "\\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}", sec+"\\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}","new OA section")
open(M,"w",encoding="utf-8").write(s); open(OA,"w",encoding="utf-8").write(o)
with open("docs/CHANGE_LEDGER_R34.md","a",encoding="utf-8") as f:
    f.write("\n# R36: GARCH-EVT same-rows results, residual-hybrid refit provenance, per-asset rerun\n\n")
    for doc,tag,old,new,why in led: f.write("## %s (%s)\n\n**Why.** %s\n\n**Before.**\n\n```\n%s\n```\n\n**After.**\n\n```\n%s\n```\n\n"%(tag,doc,why,old[:1200],new[:3000]))
print("applied",len(led))
