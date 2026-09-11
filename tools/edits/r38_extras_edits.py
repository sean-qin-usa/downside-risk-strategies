# r38_extras_edits.py -- fold the evaluation extras (CPA, Murphy, DQ, dispersion) from garch_evt_results.json into the text.
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
X=json.load(open("garch_evt_results.json"))['extras']; C=X['cpa']; MU=X['murphy']; DQ=X['dq']; DS=X['loss_diff_dispersion']
c1=C['garch_t_vs_engine']; c2=C['garch_t_vs_engine_mk63pct']; c3=C['evt_pool_vs_engine']
# ---- Section 4.1: CPA regression and win rates, appended to the paragraph after Table 1
ed("M","4.1-cpa",
 r"The edge is concentrated in the top decile: the top $\mathrm{mk}_{63}$ decile"+"\n"+r"carries $+2.98\%$ at per-date DM $10.5$, the overall edge is $+0.35\%$ at"+"\n"+r"DM $5.35$, and the lower deciles are statistically indistinguishable"+"\n"+r"from zero.",
 r"The edge is concentrated in the top decile: the top $\mathrm{mk}_{63}$ decile"+"\n"+r"carries $+2.98\%$ at per-date DM $10.5$, the overall edge is $+0.35\%$ at"+"\n"+r"DM $5.35$, and the lower deciles are statistically indistinguishable"+"\n"+r"from zero. The sort has a regression form. Taking the asset-day loss differential (GARCH-$t$ pinball minus engine pinball) and the lagged score as the conditioning variable, the conditional-predictive-ability test of \citet{giacominiwhite2006} with instruments (1, score) rejects equal conditional accuracy (Wald $\chi^2_2=%.1f$ on the composite percentile, %.1f on the kurtosis percentile), and the slope of the differential on the score is positive with a date-clustered $t$ of %.1f (composite) and %.1f (kurtosis). On a date-by-date reading the engine has the lower loss on %d\%% of dates in the top decile and %d\%% in deciles one through nine."%(
   c1['GW_wald_chi2_2'],c2['GW_wald_chi2_2'],c1['slope_t'],c2['slope_t'],round(100*DS['top_mk63_decile']['garch_t']['win_rate_dates']),round(100*DS['bulk_mk63_d1to9']['garch_t']['win_rate_dates'])),
 "Giacomini-White CPA as the regression form of the frontier; per-date win rates")
# ---- Section 5.1: DQ and Murphy after the GARCH-EVT FZ0 sentence
dq1=DQ['0.01']; dq2=DQ['0.025']; m1=MU['0.01']; m2=MU['0.025']
ed("M","5.1-dq-murphy",
 r"so the gain over the conventional EVT construction is not confined to the pinball frontier. The two closest dynamic",
 r"so the gain over the conventional EVT construction is not confined to the pinball frontier. The dynamic quantile test of \citet{engle2004caviar} (four hit lags and the VaR) passes at the 5\%% level for %d\%% of names at 1\%% and %d\%% at 2.5\%% for the accuracy layer, against %d\%% and %d\%% for GARCH-$t$ and %d\%% and %d\%% for the pooled GARCH-EVT; the overlay lifts the 2.5\%% rate to %d\%%. Because a ranking under one consistent score need not hold under another \citep{patton2020}, the Online Appendix reports Murphy diagrams \citep{ehm2016} for the VaR forecasts: the accuracy layer has the lower elementary score against GARCH-$t$ on %d\%% of the threshold grid at 1\%% and %d\%% at 2.5\%%, and against the pooled GARCH-EVT on %d\%% at both levels, losing in a band of thresholds near the typical VaR level. The two closest dynamic"%(
   round(100*dq1['engine']['dq_passrate_5pct']),round(100*dq2['engine']['dq_passrate_5pct']),round(100*dq1['garch_t']['dq_passrate_5pct']),round(100*dq2['garch_t']['dq_passrate_5pct']),
   round(100*dq1['evt_pool']['dq_passrate_5pct']),round(100*dq2['evt_pool']['dq_passrate_5pct']),round(100*dq2['engine_overlay']['dq_passrate_5pct']),
   round(100*m1['garch_t']['frac_theta_engine_better']),round(100*m2['garch_t']['frac_theta_engine_better']),round(100*m1['evt_pool']['frac_theta_engine_better'])),
 "DQ test and Murphy-diagram summary")
assert m1['evt_pool']['frac_theta_engine_better']==m2['evt_pool']['frac_theta_engine_better']
# ---- OA: subsection with the Murphy figure and the CPA/DQ table, appended to the GARCH-EVT section
th=MU['theta_grid_return_space']
def coords(arr): return " ".join("(%.3f,%.3f)"%(t,1e4*v) for t,v in zip(th,arr))
fig=r"""
\subsection*{Additional evaluation statistics on the same rows}
The same run adds four statistics that go beyond mean loss. (i)~The conditional-predictive-ability test of \citet{giacominiwhite2006}, with the asset-day loss differential $d_{it}=L^{\mathrm{GARCH}\text{-}t}_{it}-L^{\mathrm{engine}}_{it}$ (eleven-level pinball) and instruments $(1,\mathrm{score}_{i,t-1})$; the Wald statistic uses a Newey--West(10) covariance of the per-date sums. (ii)~Murphy diagrams \citep{ehm2016}: the mean elementary quantile score $S_\theta(q,y)=(\mathbb{I}\{y<q\}-\alpha)(\mathbb{I}\{\theta<q\}-\mathbb{I}\{\theta<y\})$ of the accuracy layer minus that of a competitor, on a grid of forty return-space thresholds $\theta$ (the 0.1\%% to 15\%% quantiles of test returns); a negative value means the accuracy layer is better at that $\theta$, and a curve that is negative everywhere would mean dominance under every consistent scoring function for the $\alpha$-quantile. (iii)~The dynamic quantile test of \citet{engle2004caviar} per name with four hit lags and the VaR. (iv)~The dispersion of the per-date loss differential.

\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{Conditional predictive ability, dynamic quantile test, and loss-differential dispersion on the frontier rows.}
\label{tab:extras}
\small
\begin{tabular}{lcccc}
\toprule
\multicolumn{5}{l}{\emph{Giacomini--White CPA of $d_{it}$ on $(1,\mathrm{score}_{i,t-1})$}} \\
Comparison & Score & Wald $\chi^2_2$ & Slope of $d$ on score & Slope $t$ \\
\midrule
GARCH-$t$ minus engine & composite pct. & %.1f & %.4f & %.1f \\
GARCH-$t$ minus engine & $\mathrm{mk}_{63}$ pct. & %.1f & %.4f & %.1f \\
Pooled GARCH-EVT minus engine & composite pct. & %.1f & %.4f & %.1f \\
GARCH-$t$ minus pooled body & composite pct. & %.1f & %.4f & %.1f \\
\midrule
\multicolumn{5}{l}{\emph{Dynamic quantile test, per-name pass rate at 5\%% (200 names)}} \\
Model & \multicolumn{2}{c}{$\alpha=1\%%$} & \multicolumn{2}{c}{$\alpha=2.5\%%$} \\
\midrule
Engine (accuracy layer) & \multicolumn{2}{c}{%d\%%} & \multicolumn{2}{c}{%d\%%} \\
Engine $+$ conformal overlay & \multicolumn{2}{c}{%d\%%} & \multicolumn{2}{c}{%d\%%} \\
GARCH(1,1)-$t$ & \multicolumn{2}{c}{%d\%%} & \multicolumn{2}{c}{%d\%%} \\
GARCH-EVT, pooled tail & \multicolumn{2}{c}{%d\%%} & \multicolumn{2}{c}{%d\%%} \\
GARCH-EVT, per name & \multicolumn{2}{c}{%d\%%} & \multicolumn{2}{c}{%d\%%} \\
GARCH $+$ pooled body (no EVT) & \multicolumn{2}{c}{%d\%%} & \multicolumn{2}{c}{%d\%%} \\
\midrule
\multicolumn{5}{l}{\emph{Per-date loss differential, GARCH-$t$ minus engine (pinball units)}} \\
Region & Win rate & Median & 5th--95th pct. & SD \\
\midrule
Top $\mathrm{mk}_{63}$ decile & %d\%% & %.4f & %.4f to %.4f & %.4f \\
Deciles 1--9 & %d\%% & %.4f & %.4f to %.4f & %.4f \\
Overall & %d\%% & %.4f & %.4f to %.4f & %.4f \\
\bottomrule
\end{tabular}
\begin{tablenotes}\footnotesize
\item Same 200 names and 221,600 rows as Table~\ref{tab:garchevt-frontier}. Win rate is the share of the 1,108 test dates on which the date-averaged engine loss is below the reference. The pooled dynamic quantile test rejects for every model at both levels, as pooled asset-day tests do at this sample size (Section~5.1 of the paper).
\end{tablenotes}
\end{threeparttable}
\end{table}

\begin{figure}[htbp]
\centering
\begin{tikzpicture}
\begin{axis}[width=0.48\linewidth,height=5cm, xlabel={threshold $\theta$ (daily return, \%%)}, ylabel={elementary score difference ($\times10^{-4}$)},
  title={$\alpha=1\%%$}, xmin=-9, xmax=-1.5, ymajorgrids, legend style={font=\scriptsize,draw=none,at={(0.03,0.03)},anchor=south west},
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, title style={font=\footnotesize}]
\addplot[npblue,thick] coordinates {%s};
\addplot[npmid,thick,dashed] coordinates {%s};
\addplot[black,thin] coordinates {(-9,0)(-1.5,0)};
\legend{engine minus GARCH-$t$, engine minus pooled GARCH-EVT}
\end{axis}
\end{tikzpicture}
\begin{tikzpicture}
\begin{axis}[width=0.48\linewidth,height=5cm, xlabel={threshold $\theta$ (daily return, \%%)},
  title={$\alpha=2.5\%%$}, xmin=-9, xmax=-1.5, ymajorgrids,
  tick label style={font=\scriptsize}, label style={font=\scriptsize}, title style={font=\footnotesize}]
\addplot[npblue,thick] coordinates {%s};
\addplot[npmid,thick,dashed] coordinates {%s};
\addplot[black,thin] coordinates {(-9,0)(-1.5,0)};
\end{axis}
\end{tikzpicture}
\caption{Murphy diagrams for the VaR forecasts on the frontier rows: mean elementary quantile score of the accuracy layer minus that of GARCH-$t$ (solid) and of the pooled GARCH-EVT (dashed), against the threshold $\theta$. Negative values favor the accuracy layer. It is better on %d\%% (GARCH-$t$) and %d\%% (GARCH-EVT) of the grid at $\alpha=1\%%$ and on %d\%% and %d\%% at $\alpha=2.5\%%$; the competitors win in a band of thresholds near the typical VaR level, so the ranking is not uniform over all consistent quantile scores.}
\label{fig:murphy}
\end{figure}

"""%(c1['GW_wald_chi2_2'],c1['slope_d_on_score'],c1['slope_t'],c2['GW_wald_chi2_2'],c2['slope_d_on_score'],c2['slope_t'],
     c3['GW_wald_chi2_2'],c3['slope_d_on_score'],c3['slope_t'],C['garch_t_vs_body']['GW_wald_chi2_2'],C['garch_t_vs_body']['slope_d_on_score'],C['garch_t_vs_body']['slope_t'],
     *[round(100*DQ[a][m]['dq_passrate_5pct']) for m in ['engine','engine_overlay','garch_t','evt_pool','evt_name','body'] for a in ['0.01','0.025']],
     *[v for r in ['top_mk63_decile','bulk_mk63_d1to9','overall'] for v in (round(100*DS[r]['garch_t']['win_rate_dates']),DS[r]['garch_t']['q05_q25_q50_q75_q95'][2],DS[r]['garch_t']['q05_q25_q50_q75_q95'][0],DS[r]['garch_t']['q05_q25_q50_q75_q95'][4],DS[r]['garch_t']['sd'])],
     coords(m1['garch_t']['engine_minus_garch_t']),coords(m1['evt_pool']['engine_minus_evt_pool']),coords(m2['garch_t']['engine_minus_garch_t']),coords(m2['evt_pool']['engine_minus_evt_pool']),
     round(100*m1['garch_t']['frac_theta_engine_better']),round(100*m1['evt_pool']['frac_theta_engine_better']),round(100*m2['garch_t']['frac_theta_engine_better']),round(100*m2['evt_pool']['frac_theta_engine_better']))
ed("OA","OA-extras", "\\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}", fig+"\\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}","OA subsection with CPA/DQ/dispersion table and Murphy figure")
open(M,"w",encoding="utf-8").write(s); open(OA,"w",encoding="utf-8").write(o)
with open("docs/CHANGE_LEDGER_R34.md","a",encoding="utf-8") as f:
    f.write("\n# R38: evaluation extras (CPA regression, Murphy diagrams, DQ test, dispersion)\n\n")
    for doc,tag,old,new,why in led: f.write("## %s (%s)\n\n**Why.** %s\n\n**Before.**\n\n```\n%s\n```\n\n**After.**\n\n```\n%s\n```\n\n"%(tag,doc,why,old[:1200],new[:2500]))
print("applied",len(led))
