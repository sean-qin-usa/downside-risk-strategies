# r40_bench_edits.py -- fold the all-benchmark same-rows evaluation (bench_all_results.json, tables/tab_bench_*.tex)
# into the manuscript and OA. Exact unique replacements; ledger appended to docs/CHANGE_LEDGER_R34.md under R40.
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
R=json.load(open("bench_all_results.json")); pb=R['pinball']; F=R['fz0']; MC=R['mcs']; C=R['cpa']
NAMES={'engine':'the accuracy layer','engine_overlay':'the conformal overlay','body':'the pooled body','garch_t':'GARCH-$t$','gjr_skewt':'GJR-GARCH-skew-$t$','ewma':'EWMA','hs500':'historical simulation',
 'fhs_pool':'pooled FHS','fhs_name':'per-name FHS','fhs_roll500':'rolling FHS','sav_caviar':'SAV-CAViaR','evt_pool':'pooled-tail GARCH-EVT','evt_name':'per-name GARCH-EVT','gas_pzc':'the GAS model','taylor':'the Taylor model'}
def lst(ms):
    ms=[NAMES[m] for m in ms]
    return ms[0] if len(ms)==1 else ", ".join(ms[:-1])+" and "+ms[-1]
m1=MC['fz0_0.01']['in_90pct_MCS']; m2=MC['fz0_0.025']['in_90pct_MCS']; mp=MC['pinball_11tau']['in_90pct_MCS']
g1=F['0.01']['gjr_skewt']['vs_engine']['DM_t']; g2=F['0.025']['gjr_skewt']['vs_engine']['DM_t']; t2=F['0.025']['taylor']['vs_engine']['DM_t']
cav=pb['vs_garch_t']['sav_caviar']; ev=pb['engine_vs']['sav_caviar']
# competitors with a top-decile edge over GARCH-t above 1% (other than body/engine)
big=[m for m in pb['vs_garch_t'] if m not in ('body','engine') and pb['vs_garch_t'][m]['top_mk63_decile'] and pb['vs_garch_t'][m]['top_mk63_decile']['edge_pct']>1.0]
pos=[m for m in C if m in NAMES and m not in ('body',) and C[m] and C[m]['slope_t']>2]
nonpos=[m for m in C if m in NAMES and m not in ('body',) and C[m] and C[m]['slope_t']<=2]
# ---- abstract: scope the FZ0 claim to what holds on the full set
ed("M","abstract-fz0",
 "and it attains the lowest joint (VaR, ES) loss against standard benchmarks.",
 "and it attains the lowest joint (VaR, ES) loss against GARCH-$t$ and FHS.",
 "on the full comparison set GJR-GARCH-skew-t (both levels) and the Taylor model (2.5%) are within noise of the accuracy layer; the unscoped claim no longer holds")
# ---- Section 5.1: full-set joint score and MCS, after the DQ/Murphy sentences
ed("M","5.1-fullset",
 r"losing in a band of thresholds near the typical VaR level. The two closest dynamic",
 r"losing in a band of thresholds near the typical VaR level. Extending the joint score to the whole comparison set on the same rows (Online Appendix Table~OA.11), the accuracy layer has the lowest mean FZ0 at 1\%% and is within noise of GJR-GARCH-skew-$t$ at both levels (DM %.1f and %.1f) and of the Taylor model at 2.5\%% (DM %.1f); the 90\%% Model Confidence Set on the per-date FZ0 series contains %s at 1\%% and %s at 2.5\%%, and excludes GARCH-$t$, every FHS variant, both GARCH-EVT forms, the GAS model, EWMA and historical simulation at both levels. On the eleven-level pinball the set contains only %s: the EVT branch costs pinball, as Table~\ref{tab:frtb} reports for the twelve-level battery, and is kept for the exception tests it passes. The two closest dynamic"%(g1,g2,t2,lst(m1),lst(m2),lst(mp)),
 "full-set FZ0 and MCS on the same rows")
# ---- Section 4.1: every benchmark through the frontier and the CPA regression
eo=pb['engine_vs']['sav_caviar']['overall']
ed("M","4.1-fullset",
 r"The same-rows table and the GPD threshold diagnostics are in the Online Appendix.",
 r"The same-rows table and the GPD threshold diagnostics are in the Online Appendix, together with the rest of the comparison set on the same rows (Table~OA.10). Of the standard benchmarks, only SAV-CAViaR shows a top-decile edge over GARCH-$t$ above one percent ($%+.2f\%%$, DM %.1f): it models the quantile directly and reacts to $|r_{t-1}|$, so it carries the same frontier the engine does, and the two tie in every region (top decile $%+.2f\%%$, DM $%.1f$; overall $%+.2f\%%$, DM $%.1f$, engine over CAViaR), the tie Section~\ref{sec:frtb} reports on the FRTB battery. The conditional-predictive-ability slope of each benchmark's loss differential against the engine on the lagged score is positive with $t>2$ for %s, so the engine's advantage over each of them grows with the score; it is flat for %s."%(
   cav['top_mk63_decile']['edge_pct'],cav['top_mk63_decile']['DM'],ev['top_mk63_decile']['edge_pct'],ev['top_mk63_decile']['DM'],eo['edge_pct'],eo['DM'],lst(pos),lst(nonpos) if nonpos else "none"),
 "every benchmark on the frontier rows; CPA against every model; CAViaR shares the frontier")
assert set(big)<= {'sav_caviar'}, big
# ---- OA subsection with the three tables
tp=open("tables/tab_bench_pinball.tex").read(); tf=open("tables/tab_bench_fz0.tex").read(); tt=open("tables/tab_bench_tests.tex").read()
tp=tp.replace("Table~1 of the paper","Table~1 of the paper")
sec=r"""\subsection*{All benchmarks on the canonical rows}
The GARCH-EVT comparison above is one row of a larger exercise (\texttt{job\_bench\_all.py}, result file \texttt{bench\_all\_results.json}): every model in the paper's comparison set is scored on the identical 221,600 test rows of the 200-name panel, through every statistic. GARCH-$t$, GJR-GARCH-skew-$t$, the two GARCH-EVT forms, the GAS and Taylor models and SAV-CAViaR are estimated per name on the estimation window; the FHS variants take the empirical quantiles of the GARCH-$t$ residuals (pooled across names, per name on the training window, or over a rolling 500-day window); EWMA is the RiskMetrics recursion with Gaussian quantiles; historical simulation is the rolling 500-day empirical return quantile. GAS and Taylor exist only at the two regulatory levels and enter the joint-score, dynamic-quantile and Murphy statistics. Table~\ref{tab:bench-pinball} gives the eleven-level pinball frontier, Table~\ref{tab:bench-fz0} the joint score, and Table~\ref{tab:bench-tests} the conditional-predictive-ability, dynamic-quantile, Murphy and win-rate statistics.

\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{Every benchmark on the frontier rows: eleven-level pinball edge over GARCH-$t$ by score region, engine head-to-head, and Model Confidence Set membership.}
\label{tab:bench-pinball}
\footnotesize
%s\end{threeparttable}
\end{table}

\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{Every benchmark on the full-panel FZ0 rows.}
\label{tab:bench-fz0}
\footnotesize
%s\end{threeparttable}
\end{table}

\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{Conditional predictive ability, dynamic quantile test, Murphy diagrams and win rates for every benchmark against the accuracy layer.}
\label{tab:bench-tests}
\footnotesize
%s\end{threeparttable}
\end{table}

"""%(tp,tf,tt)
ed("OA","OA-bench", "\\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}", sec+"\\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}","OA subsection with the three all-benchmark tables")
open(M,"w",encoding="utf-8").write(s); open(OA,"w",encoding="utf-8").write(o)
with open("docs/CHANGE_LEDGER_R34.md","a",encoding="utf-8") as f:
    f.write("\n# R40: every standard benchmark on the canonical rows\n\n")
    for doc,tag,old,new,why in led: f.write("## %s (%s)\n\n**Why.** %s\n\n**Before.**\n\n```\n%s\n```\n\n**After.**\n\n```\n%s\n```\n\n"%(tag,doc,why,old[:1200],new[:2500]))
print("applied",len(led))
