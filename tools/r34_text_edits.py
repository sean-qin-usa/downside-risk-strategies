# r34_text_edits.py -- surgical edits to paper_A_jfec.tex (R32 baseline) implementing the FIX list of
# DECISION_REVIEW.md, the notation audit (NOTATION_AUDIT.md), and the accepted Sep 8 sentences.
# Every edit is an exact, unique string replacement; the script aborts if any anchor is missing or
# ambiguous, and writes a before/after ledger to docs/CHANGE_LEDGER_R34.md.
import sys, re
M="paper_A_jfec.tex"; s=open(M,encoding="utf-8").read(); led=[]
def ed(tag,old,new,why):
    global s
    n=s.count(old)
    if n!=1: sys.exit(f"ANCHOR {tag}: found {n} times:\n{old[:200]}")
    s=s.replace(old,new); led.append((tag,old,new,why))

# ---------------- B.4 / FIX 10: GARCH coefficients subscripted so alpha, beta are free for the level and the GPD
ed("B4-garch",
 r"\sigma_t^2 = \omega + \alpha (r_{t-1}-\mu)^2 + \beta \sigma_{t-1}^2,",
 r"\sigma_t^2 = \omega_G + \alpha_G (r_{t-1}-\mu)^2 + \beta_G \sigma_{t-1}^2,",
 "beta collided with the GPD scale, alpha with the quantile level, omega with the Gibbs temperature")
ed("B4-trailing",
 "by quasi-maximum likelihood on a trailing window, and keep",
 "by Student-$t$ quasi-maximum likelihood on the estimation window of Section~\\ref{sec:protocol} (annually refit in ongoing use), and keep",
 "text said trailing window; the evaluated protocol fits once on the estimation window (line 589)")
# ---------------- B.2/B.3/FIX 1: Stage 3 in the code's order, GPD by ML with hats, minimum motivated, activation rule removed
ed("B3-stage3",
 r"conditions \citep{balkema1974, pickands1975, mcneilfrey2000}. The GPD closed form for ES of \citet{mcneilfrey2000}, used below,"
 "\nrequires $\\xi<1$, a condition each fitted tail in this paper\nsatisfies by a wide margin.",
 r"conditions \citep{balkema1974, pickands1975, mcneilfrey2000}. The finite tail mean of the generalized Pareto distribution (GPD) requires $\xi<1$, a condition each fitted tail in this paper"
 "\nsatisfies by a wide margin.",
 "the closed-form ES was retired; the accuracy layer integrates the envelope numerically. GPD expanded at first use")
ed("B3-gpdfit",
 r"On losses $X=-\widehat{z}$, fix a threshold $u$ at the empirical $(1-p_0)$ loss quantile with $p_0 = 0.025$. Fit the generalized Pareto distribution (GPD) $G_{\xi,\beta}(x) = 1-(1+\xi x/\beta)^{-1/\xi}$ to exceedances $X - u > 0$ strictly on past data. The shape $\xi$ sets how heavy the tail is and the scale $\beta$ how wide. For $\tau \le p_0$, set",
 r"On losses $X=-\widehat{z}$, set the threshold $u$ at the empirical $(1-p_0)$ quantile of the pooled training residual losses, with $p_0 = 0.025$. Fit the GPD $G_{\xi,\beta}(y) = 1-(1+\xi y/\beta)^{-1/\xi}$ to the excesses $y = X - u > 0$ by maximum likelihood with location fixed at zero, strictly on past data, giving $(\widehat\xi,\widehat\beta)$; \eqref{eq:evt} is evaluated at these estimates and hats are suppressed below. The shape $\xi$ sets how heavy the tail is and the scale $\beta>0$ how wide; this $\beta$ is the GPD scale, distinct from the GARCH persistence $\beta_G$. One $(\xi,\beta)$ pair is fitted per panel and held fixed across states and levels within a fit. For $\tau \le p_0$, set",
 "estimation method was never named; the code is genpareto.fit(exc, floc=0) on pooled training residuals")
ed("B3-support",
 r"The formula requires $\beta>0$ and $1+\xi(x-u)/\beta>0$, and reduces",
 r"The formula requires $1+\xi y/\beta>0$, and reduces",
 "support condition written in the excess")
ed("B3-splice",
 r"The threshold $u$ is the \emph{unconditional} empirical loss threshold, while the Stage-2 body quantile at $p_0$ is the state-conditional $\widetilde q(p_0\mid s)$. The splice is therefore exactly continuous only when the threshold is anchored at the body's own $p_0$-quantile, $u = -\widetilde q(p_0\mid s)$. Otherwise a small level shift of size"
 "\n$|{-}u - \\widetilde q(p_0\\mid s)|$ remains at the join, absorbed by the\nmin-envelope and rearrangement in \\eqref{eq:hybrid}. The tail is applied where the raw tail under-covers at $p_0$ and omitted where the body already covers, as on some volatility-index series.",
 r"The threshold $u$ is unconditional with respect to the state, while the Stage-2 body quantile at $p_0$ is the state-conditional $\widehat q_\phi(p_0\mid s)$, so the two branches need not meet at the join. In the tail the forecast takes the pointwise minimum of the two, the more conservative (more negative) branch: the pooled GPD extrapolation can tighten a thin state-conditioned body on a stressed day but never loosen it. The curve is then made non-crossing by monotone rearrangement, which cannot move it further from the true quantile curve in any $L^p$ norm \citep{cherno2010rearr}. Both steps are written out in \eqref{eq:hybrid}.",
 "q-tilde was used before its Stage 4 definition; the coverage-activation rule is not what the CRSP pipeline runs; the minimum was never motivated at Stage 3")
ed("B3-stage4",
 r"\emph{Stage 4 (conformal finish).} On a held-out calibration split of size $n$, compute the signed errors $e_i = \widehat{z}_i - \widehat{q}(\tau \mid s_i)$. Let $c_\tau$ be the $\lceil (n{+}1)\tau \rceil$-th order statistic of $\{e_i\}$. The curve is shifted per level by this empirical correction, $\widetilde{q}(\tau \mid s) = \widehat{q}(\tau \mid s) + c_\tau$ \citep{vovk2005, lei2018}, the one-sided form of conformalized quantile regression \citep{romano2019cqr}.",
 r"\emph{Stage 4 (conformal finish).} On a held-out calibration split of size $n$, compute the signed errors $\varepsilon_i = \widehat{z}_i - \widehat{q}_\phi(\tau \mid s_i)$ against the Stage-2 body. Let $c_\tau$ be the $\lceil (n{+}1)\tau \rceil$-th order statistic of $\{\varepsilon_i\}$. The finished curve is shifted per level by this scalar, $\widetilde{Q}^{z}_t(\tau) = Q^{z}_t(\tau) + c_\tau$ with $Q^{z}_t$ the envelope of \eqref{eq:hybrid} \citep{vovk2005, lei2018}, the one-sided form of conformalized quantile regression \citep{romano2019cqr}. The shift is the last operation, after the minimum and the rearrangement. The \emph{accuracy layer} that carries the FZ0 comparisons of Section~\ref{sec:frtb} and Table~\ref{tab:frtb} sets $c_\tau\equiv0$; the \emph{conformal overlay} applies the shift at the 97.5\% level.",
 "the code shifts last (min, sort, then add c_tau); the accuracy layer applies no shift. Error symbol e_i collided with ES")
ed("B3-prop",
 r"\tau \;\le\; \Pr\big(z_{n+1} \le \widetilde{q}(\tau \mid s_{n+1})\big)",
 r"\tau \;\le\; \Pr\big(z_{n+1} \le \widehat{q}_\phi(\tau \mid s_{n+1}) + c_\tau\big)",
 "proposition stated for the shifted body, which is what the errors are computed against")
ed("B3-prop2",
 r"If the calibration and test residuals $e_1,\dots,e_{n+1}$ are",
 r"If the calibration and test errors $\varepsilon_1,\dots,\varepsilon_{n+1}$ are",
 "symbol")
ed("B3-prop3",
 r"Under exchangeability and no ties the rank of $e_{n+1}$ among"+"\n"+r"$\{e_1,\dots,e_{n+1}\}$ is uniform on $\{1,\dots,n+1\}$. The event"+"\n"+r"$z_{n+1}\le\widetilde{q}(\tau\mid s_{n+1})$ equals $\{e_{n+1}\le"+"\n"+r"e_{(\lceil(n+1)\tau\rceil)}\}=\{\mathrm{rank}\le\lceil(n{+}1)\tau\rceil\}$,",
 r"Under exchangeability and no ties the rank of $\varepsilon_{n+1}$ among"+"\n"+r"$\{\varepsilon_1,\dots,\varepsilon_{n+1}\}$ is uniform on $\{1,\dots,n+1\}$. The event"+"\n"+r"$z_{n+1}\le\widehat{q}_\phi(\tau\mid s_{n+1})+c_\tau$ equals $\{\varepsilon_{n+1}\le"+"\n"+r"\varepsilon_{(\lceil(n+1)\tau\rceil)}\}=\{\mathrm{rank}\le\lceil(n{+}1)\tau\rceil\}$,",
 "symbol")
ed("B3-marginal",
 "The guarantee is marginal, not conditional\non $s_{n+1}$.",
 "The guarantee is marginal over the state $s_{n+1}$, not state-conditional.",
 "avoid the clash with Christoffersen conditional coverage")
ed("B3-scope",
 r"The guarantee also attaches to the shifted quantile alone, not to the full curve of \eqref{eq:hybrid}, whose tail branch takes the more conservative of the shifted and EVT values and is then monotone-rearranged.",
 r"The guarantee also attaches to the shifted body quantile alone. The finished forecast adds the same scalar to the envelope of \eqref{eq:hybrid}, whose tail nodes take the minimum of body and EVT branches before rearrangement, so the shifted envelope sits weakly below the shifted body in the tail.",
 "order of operations as coded")
ed("B3-eq5",
 r"\widehat{Q}_t(\tau) \;=\; \widehat{\mu} + \widehat{\sigma}_t \cdot"+"\n"+r"\mathrm{R}\Big[\, \min\{\widetilde{q}_\phi(\tau \mid s_t),\,"+"\n"+r"\widehat{q}^{\,\mathrm{EVT}}(\tau)\}\,\mathbb{I}\{\tau \le p_0\}"+"\n"+r"\;+\; \widetilde{q}_\phi(\tau \mid s_t)\,\mathbb{I}\{\tau > p_0\}"+"\n"+r"\Big],",
 r"Q^{z}_t(\tau) \;=\;"+"\n"+r"\mathrm{R}\Big[\, \min\{\widehat{q}_\phi(\tau \mid s_t),\,"+"\n"+r"\widehat{q}^{\,\mathrm{EVT}}(\tau)\}\,\mathbb{I}\{\tau \le p_0\}"+"\n"+r"\;+\; \widehat{q}_\phi(\tau \mid s_t)\,\mathbb{I}\{\tau > p_0\}"+"\n"+r"\Big],\qquad"+"\n"+r"\widehat{Q}_t(\tau) \;=\; \widehat{\mu} + \widehat{\sigma}_t \big(Q^{z}_t(\tau) + c_\tau\big),",
 "equation (5) in the code's order: unshifted body, minimum, rearrangement, scalar shift last (c_tau = 0 in the accuracy layer)")
ed("B3-eq5text",
 r"where $\mathrm{R}[\cdot]$ is the monotone rearrangement across"+"\n"+r"levels \citep{cherno2010rearr}. The conditional scale $\widehat{\sigma}_t$ carries the day's volatility from the GARCH stage, and the bracketed curve carries the shape from the nonparametric and EVT stages. A forecast is therefore the conditional mean plus scale times the modeled residual quantile: $\widehat{\VaR}_{\tau,t}=\widehat{\mu}+\widehat{\sigma}_t\widehat{Q}^{z}_t(\tau)$"+"\n"+r"and $\widehat{\ES}_{\tau,t}=\widehat{\mu}+\widehat{\sigma}_t\,\tau^{-1}\!\int_0^\tau \widehat{Q}^{z}_t(u)\,du$,"+"\n"+r"with $\widehat{Q}^{z}_t$ the bracketed standardized-residual curve."+"\n"+r"The tail forecast is the pointwise more conservative branch (the body branch is the minimum on 38\% of tail"+"\n"+r"nodes), and both risk measures come from this one curve.",
 r"where $\mathrm{R}[\cdot]$ is the monotone rearrangement across"+"\n"+r"levels \citep{cherno2010rearr} and $c_\tau\equiv0$ in the accuracy layer. $Q^{z}_t$ is the standardized-residual quantile curve, the single object from which both risk measures are read; the conditional scale $\widehat{\sigma}_t$ carries the day's volatility from the GARCH stage. The return-space forecasts are $\widehat{q}_{\tau,t}=\widehat{Q}_t(\tau)$"+"\n"+r"and $\widehat{e}_{\tau,t}=\widehat{\mu}+\widehat{\sigma}_t\,\big(\tau^{-1}\!\int_0^\tau Q^{z}_t(v)\,dv + c_\tau\big)$, the latter a numerical integral of the same curve."+"\n"+r"The body branch is the minimum on 38\% of tail nodes.",
 "one name for the envelope (Q^z_t; Q-hat-z and Q* dropped); VaR/ES in return space use q, e as at line 231; integration dummy v since u is the threshold")
ed("B3-Qstar1",
 r"one monotonized min-envelope curve $Q^{*}=\min\{$body$,$EVT$\}$.",
 r"one monotonized min-envelope curve $Q^{z}_t$ of \eqref{eq:hybrid}.",
 "single name for the envelope")
ed("B3-Qstar2",
 r"VaR and ES are read from the coherent min-envelope curve $Q^{*}$ and",
 r"VaR and ES are read from the coherent min-envelope curve $Q^{z}_t$ of \eqref{eq:hybrid} and",
 "single name for the envelope")
ed("B3-rearr",
 r"Recomputing ES$_\alpha$ as the numerical integral of \eqref{eq:hybrid} rather than the GPD closed form leaves each comparison in place.",
 r"Computing ES$_\alpha$ as the numerical integral of \eqref{eq:hybrid} rather than by the GPD closed form of \citet{mcneilfrey2000}, an earlier convention, leaves each comparison in place.",
 "closed form is retired, not used below")
ed("B3-algo",
 r"(i)~Fit \eqref{eq:garch} per asset on a trailing window. Store",
 r"(i)~Fit \eqref{eq:garch} per asset on the estimation window. Store",
 "consistent with the protocol")
ed("B3-algo2",
 r"(iii)~Fit the GPD tail \eqref{eq:evt} on past exceedances. Splice at"+"\n"+r"$p_0$.",
 r"(iii)~Fit the GPD tail \eqref{eq:evt} by maximum likelihood on the pooled training excesses. Take the minimum with the body at $\tau\le p_0$ and rearrange.",
 "algorithm box in the code's order")
ed("B3-algo3",
 r"(iv)~Learn the conformal shifts $c_\tau$ on a calibration split"+"\n"+r"disjoint from the training data.",
 r"(iv)~Learn the conformal shifts $c_\tau$ on a calibration split"+"\n"+r"disjoint from the training data (overlay only; $c_\tau\equiv0$ in the accuracy layer).",
 "which layer carries which results")
ed("B3-lem",
 r"If $\tau \mapsto \widetilde{q}(\tau \mid s)$ is nondecreasing and",
 r"If $\tau \mapsto Q^{z}_t(\tau)+c_\tau$ is nondecreasing and",
 "envelope name")
ed("B3-activation2",
 "The GPD tail is left off for some\nvolatility indices, where the raw body already covers, by the coverage-based activation rule of\nSection~\\ref{sec:hybrid}. Instrument-level",
 "Instrument-level",
 "no coverage-based activation rule exists in the pipeline (line 323 companion)")
ed("B3-pooledres",
 "model is fitted on pooled estimation-window residuals, the GPD tail on",
 "model is fitted on the pooled training-window residuals (the estimation window less the calibration split), the GPD tail on",
 "FIX 2: the shape learner and the tail never see the calibration split")
# ---------------- B.2: tau and alpha defined at first use; state symbol
ed("B2-tau",
 r"the number the return falls below with probability $\tau$. One sign convention is used throughout.",
 r"the number the return falls below with probability $\tau$. Throughout, $\tau\in(0,1)$ is a generic quantile level and $\alpha\in\{0.01,0.025\}$ denotes the reported regulatory levels; both index the same object. One sign convention is used throughout.",
 "two letters for the level were never reconciled")
ed("B2-caviar",
 r"$q_t(\tau) = \beta_0 + \beta_1\, q_{t-1}(\tau) + \beta_2\,|r_{t-1}|$, the",
 r"$q_t(\tau) = b_0 + b_1\, q_{t-1}(\tau) + b_2\,|r_{t-1}|$ for a quantile level $\tau$ (defined in Section~\ref{sec:notation}), the",
 "beta freed; tau pointed to its definition at first use")
ed("B2-theta1", r"The nonparametric family estimates $Q_\theta(\tau \mid x_t)$ directly", r"The nonparametric family estimates $Q_\phi(\tau \mid s_t)$ directly", "theta and x_t were the same objects as phi and s_t")
ed("B2-theta2", r"U(0,1)$, output $Q_\theta(\tau \mid x)$) is a capability", r"U(0,1)$, output $Q_\phi(\tau \mid s)$) is a capability", "same")
ed("B2-es", r"$e_t^\alpha=\alpha^{-1}\!\int_0^\alpha F_t^{-1}(u)\,du$, the", r"$e_t^\alpha=\alpha^{-1}\!\int_0^\alpha F_t^{-1}(v)\,dv$, the", "u reserved for the threshold")
ed("B2-es2", r"$e_\tau = \tau^{-1}\int_0^{\tau} Q_t(u)\,du \le q_\tau$", r"$e_\tau = \tau^{-1}\int_0^{\tau} Q_t(v)\,dv \le q_\tau$", "same")
ed("B2-pin", r"\rho_\tau(u) \;=\; u\,(\tau - \mathbb{I}\{u<0\}),"+"\n"+r"\qquad u = z - q,", r"\rho_\tau(x) \;=\; x\,(\tau - \mathbb{I}\{x<0\}),"+"\n"+r"\qquad x = z - q,", "same")
ed("B2-regret", r"S(q) - S(q_F) \;=\; \int_{q_F}^{q} \big(F(u) - \tau\big)\,du \;\ge\; 0,", r"S(q) - S(q_F) \;=\; \int_{q_F}^{q} \big(F(v) - \tau\big)\,dv \;\ge\; 0,", "same")
ed("B2-frtbint", r"$\alpha^{-1}\!\int_0^\alpha Q(u)\,du$: closed forms for the $t$ and", r"$\alpha^{-1}\!\int_0^\alpha Q(v)\,dv$: closed forms for the $t$ and", "same")
ed("B2-composite",
 r"where $\widehat{F}_t$ is each signal's percentile in the trailing panel available before $t$. The composite is itself deciled.",
 r"where $\widehat{F}_t$ is each signal's percentile in the pooled test panel for the sorts of Table~\ref{tab:frontier} and Figure~\ref{fig:holdout}, and in the trailing panel available before $t$ for the expanding-cutoff check reported beside them. The composite is itself deciled.",
 "the headline +2.79% ranks against the full pooled panel (job_composite.py); the trailing version is the +2.72% figure")
# ---------------- B.9 / FIX 10: Gibbs remark; omega freed; own-history shrinkage named
ed("B9-gibbs",
 r"Generalized Bayes supplies the frame for this estimator without being a component of it. Pinball ERM is the flat-prior mode, and the large-$\omega$ limit, of the Gibbs posterior $\pi_n(\theta) \propto \exp\{-\omega \sum_t \ell_\theta(z_t)\}\pi(\theta)$, which is built from a loss in place of a likelihood and targets the risk minimizer directly \citep{jiang2008gibbs, bissiri2016general}. We use the posterior itself only as a hierarchical shrinkage check in Section~\ref{sec:gbcmethod}.",
 r"Pinball ERM can be read as the mode of a Gibbs posterior built from the loss in place of a likelihood \citep{jiang2008gibbs, bissiri2016general}; no result below uses that posterior.",
 "the Gibbs posterior feeds no table or figure; the 'Gibbs update' in 2.3 is an affine shrinkage")
ed("B9-shrink",
 r"Two explicit hierarchical corrections, a naive quantile blend toward"+"\n"+r"own-history and an amortized-as-prior affine Gibbs update \citep{jiang2008gibbs, bissiri2016general}, both",
 r"Two explicit hierarchical corrections, a naive quantile blend toward"+"\n"+r"own-history and an affine own-history shrinkage of the amortized quantile toward the name's trailing location and scale, with weight age$/$(age$+80$), both",
 "what code/amort_gibbs_fast.py computes")
ed("B9-data", "the FRTB comparison, the generative-posterior and SBC\nroutines, and the walk-forward", "the FRTB comparison, and the walk-forward", "routines that feed no result")
# ---------------- B.6 / FIX 8: Christoffersen label
ed("B6-label",
 r"together with unconditional \citep{kupiec1995} and independence \citep{christoffersen1998} exception tests at both levels.",
 r"together with the unconditional-coverage test of \citet{kupiec1995} and the conditional-coverage test of \citet{christoffersen1998}, the joint likelihood-ratio test of correct coverage and breach independence, at both levels.",
 "the code computes the joint CC likelihood ratio, not the independence component")
ed("B6-label2",
 "Exception behavior is tested by Kupiec, Christoffersen, and date-clustered breach tests at the two regulatory levels.",
 "Exception behavior is tested by the Kupiec unconditional-coverage, Christoffersen conditional-coverage, and date-clustered breach tests at the two regulatory levels.",
 "label")
ed("B6-label3",
 r"EVT-tailed residual-hybrid passes Kupiec at 99\% for $84\%$ of names and"+"\n"+r"Christoffersen for $86\%$, and the date-clustered",
 r"EVT-tailed residual-hybrid passes Kupiec at 99\% for $84\%$ of names and"+"\n"+r"Christoffersen conditional coverage for $86\%$, and the date-clustered",
 "label")
# ---------------- B.7 / FIX 10: neural benchmark as coded
ed("B7-iqn1", r"\emph{The neural implicit quantile network (IQN), the GBC estimator.} A", r"\emph{The neural implicit quantile network (IQN), the network at the core of GBC.} A", "it is the architecture GBC uses, run without the Bayesian part")
ed("B7-iqn2", r"\varphi_j(\tau) = \mathrm{ReLU}\Big(\textstyle\sum_{i=0}^{n_c-1}", r"c_j(\tau) = \mathrm{ReLU}\Big(\textstyle\sum_{i=1}^{n_c}", "cosine index starts at 1 in the code (n_c = 64); varphi looked like phi")
ed("B7-iqn3", r"H_\phi(s,\tau) \;=\; g\big(\psi(s)\circ\varphi(\tau)\big),", r"H_\phi(s,\tau) \;=\; g\big(\psi(s)\circ c(\tau)\big),", "same")
ed("B7-iqn4",
 r"where $\circ$ is elementwise multiplication and $g,\psi$ are"+"\n"+r"feed-forward nets. It uses tail-aware $\tau$-sampling, monotone rearrangement of the $\tau$-curve, and the conformal layer of Section~\ref{sec:hybrid}. The tail-aware sampling, $\lambda = \tfrac12\,U(0,1) + \tfrac12\,\mathrm{Beta}(0.3,0.3)$, oversamples the extremes that uniform sampling starves (the raw net's 99\% breach rate was 3.2\%).",
 r"where $\circ$ is elementwise multiplication, $c(\tau)$ is a cosine embedding of the level with $n_c=64$ features, and $g,\psi$ are two-layer ReLU feed-forward nets of width 192 (128 in the untuned run) acting on the level embedding and on the standardized state respectively. The tuned variant uses tail-aware $\tau$-sampling, monotone rearrangement of the $\tau$-curve, and a conformal shift. The tail-aware sampling, $\lambda = \tfrac12\,U(0,1) + \tfrac12\,\mathrm{Beta}(0.3,0.3)$, was set once, before the tuned run, so that about a tenth of the training levels fall below 2.5\% against 2.5\% under uniform sampling; the mixture and the Beta parameters were not tuned on any test data. It answers the untuned run, whose 99\% breach rate was 3.2\% under uniform sampling, and the tuned IQN row of Table~\ref{tab:noncore} is a design revision made after that run and evaluated on a later sub-window.",
 "B.8: Beta(0.3,0.3) stated as pre-set with its reason; widths as coded")
ed("B7-train",
 r"weights carries the entire quantile curve. Early stopping is on"+"\n"+r"held-out pinball loss. Monotone rearrangement",
 r"weights carries the entire quantile curve. Training runs for a fixed budget of 12{,}000 minibatch steps (Adam, batch 512, rate $10^{-3}$; 6{,}000 in the untuned run) with no early stopping. Monotone rearrangement",
 "text said early stopping; the code uses a fixed Adam step budget")
ed("B7-noncore-note",
 r"\item[a] Tail-aware $\tau$-sampling, monotone rearrangement, and the conformal overlay of Section~\ref{sec:hybrid}.",
 r"\item[a] Tail-aware $\tau$-sampling, monotone rearrangement, and a per-level conformal shift calibrated on the first half of the test window and scored on the second half; the residual-hybrid in this row is recalibrated the same way, so the loss levels are not comparable with Table~\ref{tab:frtb}.",
 "the tuned IQN's shift is calibrated on the first half of the test window, not the Proposition 1 split")
# ---------------- B.6 (eta) / hyperparameters
ed("B6-eta",
 r"is grown stagewise by gradient boosting \citep{friedman2001}.",
 r"is grown stagewise by gradient boosting \citep{friedman2001}, where $\eta=0.06$ is a fixed shrinkage rate, $M=250$ trees of depth three are grown, and $h_m$ is the $m$-th regression tree, fitted by least squares to the pinball pseudo-residuals.",
 "eta was undefined and the GBM hyperparameters were given nowhere")
# ---------------- B.4: Hansen skew-t parameters, RiskMetrics decay
ed("B4-hansen", r"$\eta,\lambda$ (median $4.2$, $-0.015$), validated against the", r"degrees of freedom and skewness (median $4.2$ and $-0.015$), validated against the", "eta and lambda were both taken")
ed("B4-decay", r"EWMA with the RiskMetrics decay $\lambda=0.94$", r"EWMA with the RiskMetrics decay $0.94$", "lambda is the tau-sampling law")
# ---------------- B.5: acronyms at first use; glossary promise kept (OA glossary written)
ed("B5-garch", r"\citep{kuester2006, nietoruiz2016}. Fully parametric filters, GARCH and", r"\citep{kuester2006, nietoruiz2016}. Fully parametric filters, generalized autoregressive conditional heteroskedasticity (GARCH) and", "GARCH never expanded")
ed("B5-fhs", r"and its GARCH-filtered variant (FHS) \citep{baroneadesi1999fhs}.", r"and its GARCH-filtered variant, filtered historical simulation (FHS) \citep{baroneadesi1999fhs}.", "FHS")
ed("B5-evt", r"the two-step logic of filtered historical simulation and GARCH-EVT \citep{baroneadesi1999fhs, mcneilfrey2000}. It keeps", r"the two-step logic of filtered historical simulation and GARCH with an extreme-value-theory (EVT) tail \citep{baroneadesi1999fhs, mcneilfrey2000}. It keeps", "EVT")
ed("B5-mcs", r"both remain in the $90\%$ Model Confidence Set \citep{hansen2011mcs}, and it improves", r"both remain in the $90\%$ Model Confidence Set (MCS) \citep{hansen2011mcs}, and it improves", "MCS")
ed("B5-ewma", r"It includes historical simulation, EWMA with", r"It includes historical simulation, exponentially weighted moving average (EWMA) variance with", "EWMA")
ed("B5-gjr", r"and GJR-GARCH-skew-$t$ \citep{glosten1993, hansen1994ARCD}, which adds", r"and the GJR (Glosten--Jagannathan--Runkle) GARCH-skew-$t$ \citep{glosten1993, hansen1994ARCD}, which adds", "GJR")
ed("B5-caviar", r"The strongest non-nested semiparametric rival in the set is SAV-CAViaR \citep{engle2004caviar}", r"The strongest non-nested semiparametric rival in the set is SAV-CAViaR (conditional autoregressive value-at-risk) \citep{engle2004caviar}", "CAViaR")
ed("B5-gas", r"minimization, the GAS of \citet{patton2019} (DM $9.5$ and $8.6$) and the", r"minimization, the generalized autoregressive score (GAS) model of \citet{patton2019} (DM $9.5$ and $8.6$) and the", "GAS")
ed("B5-spa", r"A superior-predictive-ability test \citep{hansen2005spa}", r"A superior-predictive-ability (SPA) test \citep{hansen2005spa}", "SPA")
ed("B5-fz0", r"the zero-homogeneous FZ0 loss of \citet{fissler2016} and \citet{patton2019}, against", r"the Fissler--Ziegler zero-homogeneous (FZ0) loss of \citet{fissler2016} and \citet{patton2019}, against", "FZ0")
ed("B5-glossary", "algorithm boxes given. A glossary of acronyms is in the Online\nAppendix.", "algorithm boxes given. A glossary of acronyms opens the Online\nAppendix.", "glossary written as OA Section 1")
# ---------------- B.10: which loss fits which competitor; twelve vs eleven levels; not a proper score
ed("B10-loss",
 r"would silently exclude them.",
 r"would silently exclude them. Each benchmark is estimated by its own conventional criterion: Student-$t$ or skew-$t$ likelihood for the GARCH family, empirical residual quantiles for HS and FHS, FZ0 for the two dynamic-ES models of Section~\ref{sec:frtb}, and pinball for CAViaR and for the shape learners. All are then scored out of sample by the same pinball and FZ0 losses, so a model fitted on the evaluation loss carries an in-sample advantage that the out-of-sample comparison tests.",
 "B.10")
ed("B10-levels",
 r"Distributional accuracy is scored by mean pinball loss across twelve quantile levels, a quantile-weighted proper score \citep{gneitingranjan2011}, and joint",
 r"Distributional accuracy is scored by mean pinball loss across a fixed grid of quantile levels, twelve in the FRTB comparison of Table~\ref{tab:frtb} and eleven in the frontier sorts, a consistent scoring function for the quantile vector that is the point-mass case of the quantile-weighted CRPS \citep{gneitingranjan2011}, and joint",
 "eleven levels in the frontier jobs; not a proper scoring rule for the distribution")
# ---------------- FIX 2: R32 defects
ed("F2-floor",
 "model throughout; the residual-hybrid is the choice where a guaranteed\n$\\ge$GARCH floor is wanted, with the score as a monitor",
 "model throughout; the residual-hybrid is the choice where forecast accuracy no worse than GARCH-$t$ in the bulk is wanted, with the score as a monitor",
 "no floor is guaranteed; the bulk is a statistical tie")
ed("F2-oracle1",
 "and the per-day oracle gap ($4.4\\%$) is\nunreachable because which day the tail event lands is unpredictable from\nprior-day state.",
 "and the per-day oracle gap ($4.4\\%$) is largely unforecastable from prior-day state.",
 "unreachable/unpredictable overstated")
ed("F2-oracle2",
 "day by day, because the per-day oracle gap is not forecastable from\nprior-day state and a learned gate",
 "day by day, because the per-day oracle gap ($4.4\\%$) is largely unforecastable from\nprior-day state and a learned gate",
 "same")
ed("F2-holds",
 "A fixed-shape parametric filter is hard to beat where its shape assumption holds, and for most assets on most days it holds well.",
 "A fixed-shape parametric filter is hard to beat where its shape assumption holds, and for most assets on most days the flexible model cannot improve on it.",
 "'holds well' is not what was tested; a tie was")
ed("F2-referee",
 r"The two FZ-estimated dynamic $(\VaR,\ES)$ models a referee would turn to next are the one-factor",
 r"The two closest dynamic $(\VaR,\ES)$ benchmarks are the one-factor",
 "imagined-referee voice")
# ---------------- FIX 4: annual-refit figure with a committed file
ed("F4-refit",
 r"which the top decile still carries $+2.09\%$ at DM 4.43 while the average"+"\n"+r"edge washes out ($-0.18\%$).",
 r"which the top decile still carries $+2.47\%$ at DM 6.05 while the average"+"\n"+r"edge compresses to $+0.32\%$ (DM 0.8), within noise; this check uses the returns-space learner of the frozen holdout specification.",
 "walkforward_results.json; the residual-hybrid refit figure has no committed file (job_walkforward_hybrid.py queued)")
# ---------------- FIX 5: crossover pair-dependent
ed("F5-cross",
 r"with the crossover near $\tau_c \approx 0.018$, so $1\%$ sits below it and $2.5\%$ just above \citep{patton2020}.",
 r"with a pair-dependent crossover $\tau^*$ ($0.018$ for $t_3$ against the normal, $0.023$ for $t_5$ against $t_8$), so $1\%$ sits below it and $2.5\%$ just above \citep{patton2020}.",
 "0.018 is the t3-versus-normal value; Prop. 2's pair gives 0.023")
# ---------------- FIX 7: static overlay DM
ed("F7-dm", r"loses to GARCH-$t$ on the 2.5\% joint score (DM $-2.0$), and", r"loses to GARCH-$t$ on the 2.5\% joint score (DM $-1.8$), and", "fz_fullpanel_results.json: garch_t vs engine at 2.5%, DM -1.80")
# ---------------- FIX 11: Korea label
ed("F11-korea",
 "provides a falsification case that sharpens the claim: a price crash is not residual misspecification, and GARCH-$t$ wins there, as the frontier predicts.",
 "is the negative control that sharpens the claim: a price crash is not residual misspecification, and GARCH-$t$ wins there, as the frontier predicts.",
 "R32 used both labels; 'negative control' is the one Section 4 uses")
# ---------------- Accepted Sep 8 sentences
ed("S8-rv", "An independently estimated realized-volatility scale reproduces the same split.", "On large caps with intraday data, re-estimation on realized-volatility residuals leaves the score within noise.", "R32 intro overclaimed relative to its own Section 5")
ed("S8-transfer",
 "In its characteristics-only form it forecasts VaR and ES for assets with no return history at all, the day-one regime in which no per-asset model exists.",
 "Its gains over own-history benchmarks are largest in the first trading month, at roughly 6--10\\% of pinball loss. In its characteristics-only form it forecasts VaR and ES for assets with no return history at all, the day-one regime in which no per-asset model exists.",
 "amort_agecurve.json 6.4%, amort_full_results.json 9.7%")
ed("S8-strawman",
 "The comparison in this paper is therefore against the methods in standard use across the industry, not a regulatory strawman.",
 "The comparison in this paper is therefore against the methods in standard use across the industry.",
 "X-not-Y verdict")
ed("S8-conclusion",
 "And the score is a monitor, not a day-to-day switching rule, since the day-ahead oracle gap is largely unforecastable (Section~\\ref{sec:gate}).",
 "And the score serves as a monitor rather than a day-to-day switching rule, since the day-ahead oracle gap is largely unforecastable (Section~\\ref{sec:gate}). Credit and freight retain accuracy gains but fail breach-independence tests, which makes dependence-aware calibration a priority for those applications.",
 "X-not-Y; Sep 8 credit/freight sentence kept")
ed("S8-conc2",
 "The score is predictive, not a necessary or sufficient condition: high residual kurtosis coincides with ties in some markets, and in credit and freight the accuracy edges sit alongside open calibration.",
 "The score is predictive rather than a necessary or sufficient condition: high residual kurtosis coincides with ties in some markets, and in credit and freight the accuracy edges sit alongside failed breach-independence tests.",
 "wording")
# ---------------- GARCH-EVT disclaimer: point to the pending same-rows comparison
ed("GE-disclaim",
 r"The comparison set does not include GARCH-EVT \citep{mcneilfrey2000}, which"+"\n"+r"\citet{kuester2006} rank first among classical methods. Its"+"\n"+r"filter-then-tail logic is instead absorbed into the estimator's own EVT"+"\n"+r"stage (Section~\ref{sec:methods}), so the EVT-tailed layer is its"+"\n"+r"analogue within the comparison set.",
 r"The comparison set of Table~\ref{tab:frtb} does not include standalone GARCH-EVT \citep{mcneilfrey2000}, which"+"\n"+r"\citet{kuester2006} rank first among classical methods. Its"+"\n"+r"filter-then-tail logic is absorbed into the estimator's own EVT"+"\n"+r"stage (Section~\ref{sec:methods}), so the EVT-tailed layer is its"+"\n"+r"analogue within the comparison set. A same-rows comparison against per-name and pooled GARCH-EVT tails, on the frontier sorts and on the FZ0 score, is reported in the Online Appendix once run.",
 "GARCH-EVT is the top-ranked referee risk; a same-rows job (job_garch_evt.py) is queued. Delete 'once run' after the numbers land")
# ---------------- JEL (A.3 decision): keep R32 codes plus C53, G17
ed("JEL", r"\noindent\textbf{JEL classification:} C14; C52; C58.", r"\noindent\textbf{JEL classification:} C14; C52; C53; C58; G17.", "forecasting and financial-forecasting codes fit the paper; C14/C52 kept")

open(M,"w",encoding="utf-8").write(s)
with open("docs/CHANGE_LEDGER_R34.md","w",encoding="utf-8") as f:
    f.write("# Change ledger R34 (text pass on R32 implementing DECISION_REVIEW FIX list, NOTATION_AUDIT, accepted Sep 8 sentences)\n\n")
    f.write("Applied by tools/r34_text_edits.py; %d edits, each an exact unique replacement in paper_A_jfec.tex.\n\n"%len(led))
    for tag,old,new,why in led:
        f.write("## %s\n\n**Why.** %s\n\n**Before.**\n\n```\n%s\n```\n\n**After.**\n\n```\n%s\n```\n\n"%(tag,why,old,new))
print("applied",len(led))
