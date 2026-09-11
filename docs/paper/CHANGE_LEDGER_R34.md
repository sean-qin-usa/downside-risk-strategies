# Change ledger R34 (text pass on R32 implementing DECISION_REVIEW FIX list, NOTATION_AUDIT, accepted Sep 8 sentences)

Applied by tools/r34_text_edits.py; 77 edits, each an exact unique replacement in paper_A_jfec.tex.

## B4-garch

**Why.** beta collided with the GPD scale, alpha with the quantile level, omega with the Gibbs temperature

**Before.**

```
\sigma_t^2 = \omega + \alpha (r_{t-1}-\mu)^2 + \beta \sigma_{t-1}^2,
```

**After.**

```
\sigma_t^2 = \omega_G + \alpha_G (r_{t-1}-\mu)^2 + \beta_G \sigma_{t-1}^2,
```

## B4-trailing

**Why.** text said trailing window; the evaluated protocol fits once on the estimation window (line 589)

**Before.**

```
by quasi-maximum likelihood on a trailing window, and keep
```

**After.**

```
by Student-$t$ quasi-maximum likelihood on the estimation window of Section~\ref{sec:protocol} (annually refit in ongoing use), and keep
```

## B3-stage3

**Why.** the closed-form ES was retired; the accuracy layer integrates the envelope numerically. GPD expanded at first use

**Before.**

```
conditions \citep{balkema1974, pickands1975, mcneilfrey2000}. The GPD closed form for ES of \citet{mcneilfrey2000}, used below,
requires $\xi<1$, a condition each fitted tail in this paper
satisfies by a wide margin.
```

**After.**

```
conditions \citep{balkema1974, pickands1975, mcneilfrey2000}. The finite tail mean of the generalized Pareto distribution (GPD) requires $\xi<1$, a condition each fitted tail in this paper
satisfies by a wide margin.
```

## B3-gpdfit

**Why.** estimation method was never named; the code is genpareto.fit(exc, floc=0) on pooled training residuals

**Before.**

```
On losses $X=-\widehat{z}$, fix a threshold $u$ at the empirical $(1-p_0)$ loss quantile with $p_0 = 0.025$. Fit the generalized Pareto distribution (GPD) $G_{\xi,\beta}(x) = 1-(1+\xi x/\beta)^{-1/\xi}$ to exceedances $X - u > 0$ strictly on past data. The shape $\xi$ sets how heavy the tail is and the scale $\beta$ how wide. For $\tau \le p_0$, set
```

**After.**

```
On losses $X=-\widehat{z}$, set the threshold $u$ at the empirical $(1-p_0)$ quantile of the pooled training residual losses, with $p_0 = 0.025$. Fit the GPD $G_{\xi,\beta}(y) = 1-(1+\xi y/\beta)^{-1/\xi}$ to the excesses $y = X - u > 0$ by maximum likelihood with location fixed at zero, strictly on past data, giving $(\widehat\xi,\widehat\beta)$; \eqref{eq:evt} is evaluated at these estimates and hats are suppressed below. The shape $\xi$ sets how heavy the tail is and the scale $\beta>0$ how wide; this $\beta$ is the GPD scale, distinct from the GARCH persistence $\beta_G$. One $(\xi,\beta)$ pair is fitted per panel and held fixed across states and levels within a fit. For $\tau \le p_0$, set
```

## B3-support

**Why.** support condition written in the excess

**Before.**

```
The formula requires $\beta>0$ and $1+\xi(x-u)/\beta>0$, and reduces
```

**After.**

```
The formula requires $1+\xi y/\beta>0$, and reduces
```

## B3-splice

**Why.** q-tilde was used before its Stage 4 definition; the coverage-activation rule is not what the CRSP pipeline runs; the minimum was never motivated at Stage 3

**Before.**

```
The threshold $u$ is the \emph{unconditional} empirical loss threshold, while the Stage-2 body quantile at $p_0$ is the state-conditional $\widetilde q(p_0\mid s)$. The splice is therefore exactly continuous only when the threshold is anchored at the body's own $p_0$-quantile, $u = -\widetilde q(p_0\mid s)$. Otherwise a small level shift of size
$|{-}u - \widetilde q(p_0\mid s)|$ remains at the join, absorbed by the
min-envelope and rearrangement in \eqref{eq:hybrid}. The tail is applied where the raw tail under-covers at $p_0$ and omitted where the body already covers, as on some volatility-index series.
```

**After.**

```
The threshold $u$ is unconditional with respect to the state, while the Stage-2 body quantile at $p_0$ is the state-conditional $\widehat q_\phi(p_0\mid s)$, so the two branches need not meet at the join. In the tail the forecast takes the pointwise minimum of the two, the more conservative (more negative) branch: the pooled GPD extrapolation can tighten a thin state-conditioned body on a stressed day but never loosen it. The curve is then made non-crossing by monotone rearrangement, which cannot move it further from the true quantile curve in any $L^p$ norm \citep{cherno2010rearr}. Both steps are written out in \eqref{eq:hybrid}.
```

## B3-stage4

**Why.** the code shifts last (min, sort, then add c_tau); the accuracy layer applies no shift. Error symbol e_i collided with ES

**Before.**

```
\emph{Stage 4 (conformal finish).} On a held-out calibration split of size $n$, compute the signed errors $e_i = \widehat{z}_i - \widehat{q}(\tau \mid s_i)$. Let $c_\tau$ be the $\lceil (n{+}1)\tau \rceil$-th order statistic of $\{e_i\}$. The curve is shifted per level by this empirical correction, $\widetilde{q}(\tau \mid s) = \widehat{q}(\tau \mid s) + c_\tau$ \citep{vovk2005, lei2018}, the one-sided form of conformalized quantile regression \citep{romano2019cqr}.
```

**After.**

```
\emph{Stage 4 (conformal finish).} On a held-out calibration split of size $n$, compute the signed errors $\varepsilon_i = \widehat{z}_i - \widehat{q}_\phi(\tau \mid s_i)$ against the Stage-2 body. Let $c_\tau$ be the $\lceil (n{+}1)\tau \rceil$-th order statistic of $\{\varepsilon_i\}$. The finished curve is shifted per level by this scalar, $\widetilde{Q}^{z}_t(\tau) = Q^{z}_t(\tau) + c_\tau$ with $Q^{z}_t$ the envelope of \eqref{eq:hybrid} \citep{vovk2005, lei2018}, the one-sided form of conformalized quantile regression \citep{romano2019cqr}. The shift is the last operation, after the minimum and the rearrangement. The \emph{accuracy layer} that carries the FZ0 comparisons of Section~\ref{sec:frtb} and Table~\ref{tab:frtb} sets $c_\tau\equiv0$; the \emph{conformal overlay} applies the shift at the 97.5\% level.
```

## B3-prop

**Why.** proposition stated for the shifted body, which is what the errors are computed against

**Before.**

```
\tau \;\le\; \Pr\big(z_{n+1} \le \widetilde{q}(\tau \mid s_{n+1})\big)
```

**After.**

```
\tau \;\le\; \Pr\big(z_{n+1} \le \widehat{q}_\phi(\tau \mid s_{n+1}) + c_\tau\big)
```

## B3-prop2

**Why.** symbol

**Before.**

```
If the calibration and test residuals $e_1,\dots,e_{n+1}$ are
```

**After.**

```
If the calibration and test errors $\varepsilon_1,\dots,\varepsilon_{n+1}$ are
```

## B3-prop3

**Why.** symbol

**Before.**

```
Under exchangeability and no ties the rank of $e_{n+1}$ among
$\{e_1,\dots,e_{n+1}\}$ is uniform on $\{1,\dots,n+1\}$. The event
$z_{n+1}\le\widetilde{q}(\tau\mid s_{n+1})$ equals $\{e_{n+1}\le
e_{(\lceil(n+1)\tau\rceil)}\}=\{\mathrm{rank}\le\lceil(n{+}1)\tau\rceil\}$,
```

**After.**

```
Under exchangeability and no ties the rank of $\varepsilon_{n+1}$ among
$\{\varepsilon_1,\dots,\varepsilon_{n+1}\}$ is uniform on $\{1,\dots,n+1\}$. The event
$z_{n+1}\le\widehat{q}_\phi(\tau\mid s_{n+1})+c_\tau$ equals $\{\varepsilon_{n+1}\le
\varepsilon_{(\lceil(n+1)\tau\rceil)}\}=\{\mathrm{rank}\le\lceil(n{+}1)\tau\rceil\}$,
```

## B3-marginal

**Why.** avoid the clash with Christoffersen conditional coverage

**Before.**

```
The guarantee is marginal, not conditional
on $s_{n+1}$.
```

**After.**

```
The guarantee is marginal over the state $s_{n+1}$, not state-conditional.
```

## B3-scope

**Why.** order of operations as coded

**Before.**

```
The guarantee also attaches to the shifted quantile alone, not to the full curve of \eqref{eq:hybrid}, whose tail branch takes the more conservative of the shifted and EVT values and is then monotone-rearranged.
```

**After.**

```
The guarantee also attaches to the shifted body quantile alone. The finished forecast adds the same scalar to the envelope of \eqref{eq:hybrid}, whose tail nodes take the minimum of body and EVT branches before rearrangement, so the shifted envelope sits weakly below the shifted body in the tail.
```

## B3-eq5

**Why.** equation (5) in the code's order: unshifted body, minimum, rearrangement, scalar shift last (c_tau = 0 in the accuracy layer)

**Before.**

```
\widehat{Q}_t(\tau) \;=\; \widehat{\mu} + \widehat{\sigma}_t \cdot
\mathrm{R}\Big[\, \min\{\widetilde{q}_\phi(\tau \mid s_t),\,
\widehat{q}^{\,\mathrm{EVT}}(\tau)\}\,\mathbb{I}\{\tau \le p_0\}
\;+\; \widetilde{q}_\phi(\tau \mid s_t)\,\mathbb{I}\{\tau > p_0\}
\Big],
```

**After.**

```
Q^{z}_t(\tau) \;=\;
\mathrm{R}\Big[\, \min\{\widehat{q}_\phi(\tau \mid s_t),\,
\widehat{q}^{\,\mathrm{EVT}}(\tau)\}\,\mathbb{I}\{\tau \le p_0\}
\;+\; \widehat{q}_\phi(\tau \mid s_t)\,\mathbb{I}\{\tau > p_0\}
\Big],\qquad
\widehat{Q}_t(\tau) \;=\; \widehat{\mu} + \widehat{\sigma}_t \big(Q^{z}_t(\tau) + c_\tau\big),
```

## B3-eq5text

**Why.** one name for the envelope (Q^z_t; Q-hat-z and Q* dropped); VaR/ES in return space use q, e as at line 231; integration dummy v since u is the threshold

**Before.**

```
where $\mathrm{R}[\cdot]$ is the monotone rearrangement across
levels \citep{cherno2010rearr}. The conditional scale $\widehat{\sigma}_t$ carries the day's volatility from the GARCH stage, and the bracketed curve carries the shape from the nonparametric and EVT stages. A forecast is therefore the conditional mean plus scale times the modeled residual quantile: $\widehat{\VaR}_{\tau,t}=\widehat{\mu}+\widehat{\sigma}_t\widehat{Q}^{z}_t(\tau)$
and $\widehat{\ES}_{\tau,t}=\widehat{\mu}+\widehat{\sigma}_t\,\tau^{-1}\!\int_0^\tau \widehat{Q}^{z}_t(u)\,du$,
with $\widehat{Q}^{z}_t$ the bracketed standardized-residual curve.
The tail forecast is the pointwise more conservative branch (the body branch is the minimum on 38\% of tail
nodes), and both risk measures come from this one curve.
```

**After.**

```
where $\mathrm{R}[\cdot]$ is the monotone rearrangement across
levels \citep{cherno2010rearr} and $c_\tau\equiv0$ in the accuracy layer. $Q^{z}_t$ is the standardized-residual quantile curve, the single object from which both risk measures are read; the conditional scale $\widehat{\sigma}_t$ carries the day's volatility from the GARCH stage. The return-space forecasts are $\widehat{q}_{\tau,t}=\widehat{Q}_t(\tau)$
and $\widehat{e}_{\tau,t}=\widehat{\mu}+\widehat{\sigma}_t\,\big(\tau^{-1}\!\int_0^\tau Q^{z}_t(v)\,dv + c_\tau\big)$, the latter a numerical integral of the same curve.
The body branch is the minimum on 38\% of tail nodes.
```

## B3-Qstar1

**Why.** single name for the envelope

**Before.**

```
one monotonized min-envelope curve $Q^{*}=\min\{$body$,$EVT$\}$.
```

**After.**

```
one monotonized min-envelope curve $Q^{z}_t$ of \eqref{eq:hybrid}.
```

## B3-Qstar2

**Why.** single name for the envelope

**Before.**

```
VaR and ES are read from the coherent min-envelope curve $Q^{*}$ and
```

**After.**

```
VaR and ES are read from the coherent min-envelope curve $Q^{z}_t$ of \eqref{eq:hybrid} and
```

## B3-rearr

**Why.** closed form is retired, not used below

**Before.**

```
Recomputing ES$_\alpha$ as the numerical integral of \eqref{eq:hybrid} rather than the GPD closed form leaves each comparison in place.
```

**After.**

```
Computing ES$_\alpha$ as the numerical integral of \eqref{eq:hybrid} rather than by the GPD closed form of \citet{mcneilfrey2000}, an earlier convention, leaves each comparison in place.
```

## B3-algo

**Why.** consistent with the protocol

**Before.**

```
(i)~Fit \eqref{eq:garch} per asset on a trailing window. Store
```

**After.**

```
(i)~Fit \eqref{eq:garch} per asset on the estimation window. Store
```

## B3-algo2

**Why.** algorithm box in the code's order

**Before.**

```
(iii)~Fit the GPD tail \eqref{eq:evt} on past exceedances. Splice at
$p_0$.
```

**After.**

```
(iii)~Fit the GPD tail \eqref{eq:evt} by maximum likelihood on the pooled training excesses. Take the minimum with the body at $\tau\le p_0$ and rearrange.
```

## B3-algo3

**Why.** which layer carries which results

**Before.**

```
(iv)~Learn the conformal shifts $c_\tau$ on a calibration split
disjoint from the training data.
```

**After.**

```
(iv)~Learn the conformal shifts $c_\tau$ on a calibration split
disjoint from the training data (overlay only; $c_\tau\equiv0$ in the accuracy layer).
```

## B3-lem

**Why.** envelope name

**Before.**

```
If $\tau \mapsto \widetilde{q}(\tau \mid s)$ is nondecreasing and
```

**After.**

```
If $\tau \mapsto Q^{z}_t(\tau)+c_\tau$ is nondecreasing and
```

## B3-activation2

**Why.** no coverage-based activation rule exists in the pipeline (line 323 companion)

**Before.**

```
The GPD tail is left off for some
volatility indices, where the raw body already covers, by the coverage-based activation rule of
Section~\ref{sec:hybrid}. Instrument-level
```

**After.**

```
Instrument-level
```

## B3-pooledres

**Why.** FIX 2: the shape learner and the tail never see the calibration split

**Before.**

```
model is fitted on pooled estimation-window residuals, the GPD tail on
```

**After.**

```
model is fitted on the pooled training-window residuals (the estimation window less the calibration split), the GPD tail on
```

## B2-tau

**Why.** two letters for the level were never reconciled

**Before.**

```
the number the return falls below with probability $\tau$. One sign convention is used throughout.
```

**After.**

```
the number the return falls below with probability $\tau$. Throughout, $\tau\in(0,1)$ is a generic quantile level and $\alpha\in\{0.01,0.025\}$ denotes the reported regulatory levels; both index the same object. One sign convention is used throughout.
```

## B2-caviar

**Why.** beta freed; tau pointed to its definition at first use

**Before.**

```
$q_t(\tau) = \beta_0 + \beta_1\, q_{t-1}(\tau) + \beta_2\,|r_{t-1}|$, the
```

**After.**

```
$q_t(\tau) = b_0 + b_1\, q_{t-1}(\tau) + b_2\,|r_{t-1}|$ for a quantile level $\tau$ (defined in Section~\ref{sec:notation}), the
```

## B2-theta1

**Why.** theta and x_t were the same objects as phi and s_t

**Before.**

```
The nonparametric family estimates $Q_\theta(\tau \mid x_t)$ directly
```

**After.**

```
The nonparametric family estimates $Q_\phi(\tau \mid s_t)$ directly
```

## B2-theta2

**Why.** same

**Before.**

```
U(0,1)$, output $Q_\theta(\tau \mid x)$) is a capability
```

**After.**

```
U(0,1)$, output $Q_\phi(\tau \mid s)$) is a capability
```

## B2-es

**Why.** u reserved for the threshold

**Before.**

```
$e_t^\alpha=\alpha^{-1}\!\int_0^\alpha F_t^{-1}(u)\,du$, the
```

**After.**

```
$e_t^\alpha=\alpha^{-1}\!\int_0^\alpha F_t^{-1}(v)\,dv$, the
```

## B2-es2

**Why.** same

**Before.**

```
$e_\tau = \tau^{-1}\int_0^{\tau} Q_t(u)\,du \le q_\tau$
```

**After.**

```
$e_\tau = \tau^{-1}\int_0^{\tau} Q_t(v)\,dv \le q_\tau$
```

## B2-pin

**Why.** same

**Before.**

```
\rho_\tau(u) \;=\; u\,(\tau - \mathbb{I}\{u<0\}),
\qquad u = z - q,
```

**After.**

```
\rho_\tau(x) \;=\; x\,(\tau - \mathbb{I}\{x<0\}),
\qquad x = z - q,
```

## B2-regret

**Why.** same

**Before.**

```
S(q) - S(q_F) \;=\; \int_{q_F}^{q} \big(F(u) - \tau\big)\,du \;\ge\; 0,
```

**After.**

```
S(q) - S(q_F) \;=\; \int_{q_F}^{q} \big(F(v) - \tau\big)\,dv \;\ge\; 0,
```

## B2-frtbint

**Why.** same

**Before.**

```
$\alpha^{-1}\!\int_0^\alpha Q(u)\,du$: closed forms for the $t$ and
```

**After.**

```
$\alpha^{-1}\!\int_0^\alpha Q(v)\,dv$: closed forms for the $t$ and
```

## B2-composite

**Why.** the headline +2.79% ranks against the full pooled panel (job_composite.py); the trailing version is the +2.72% figure

**Before.**

```
where $\widehat{F}_t$ is each signal's percentile in the trailing panel available before $t$. The composite is itself deciled.
```

**After.**

```
where $\widehat{F}_t$ is each signal's percentile in the pooled test panel for the sorts of Table~\ref{tab:frontier} and Figure~\ref{fig:holdout}, and in the trailing panel available before $t$ for the expanding-cutoff check reported beside them. The composite is itself deciled.
```

## B9-gibbs

**Why.** the Gibbs posterior feeds no table or figure; the 'Gibbs update' in 2.3 is an affine shrinkage

**Before.**

```
Generalized Bayes supplies the frame for this estimator without being a component of it. Pinball ERM is the flat-prior mode, and the large-$\omega$ limit, of the Gibbs posterior $\pi_n(\theta) \propto \exp\{-\omega \sum_t \ell_\theta(z_t)\}\pi(\theta)$, which is built from a loss in place of a likelihood and targets the risk minimizer directly \citep{jiang2008gibbs, bissiri2016general}. We use the posterior itself only as a hierarchical shrinkage check in Section~\ref{sec:gbcmethod}.
```

**After.**

```
Pinball ERM can be read as the mode of a Gibbs posterior built from the loss in place of a likelihood \citep{jiang2008gibbs, bissiri2016general}; no result below uses that posterior.
```

## B9-shrink

**Why.** what code/amort_gibbs_fast.py computes

**Before.**

```
Two explicit hierarchical corrections, a naive quantile blend toward
own-history and an amortized-as-prior affine Gibbs update \citep{jiang2008gibbs, bissiri2016general}, both
```

**After.**

```
Two explicit hierarchical corrections, a naive quantile blend toward
own-history and an affine own-history shrinkage of the amortized quantile toward the name's trailing location and scale, with weight age$/$(age$+80$), both
```

## B9-data

**Why.** routines that feed no result

**Before.**

```
the FRTB comparison, the generative-posterior and SBC
routines, and the walk-forward
```

**After.**

```
the FRTB comparison, and the walk-forward
```

## B6-label

**Why.** the code computes the joint CC likelihood ratio, not the independence component

**Before.**

```
together with unconditional \citep{kupiec1995} and independence \citep{christoffersen1998} exception tests at both levels.
```

**After.**

```
together with the unconditional-coverage test of \citet{kupiec1995} and the conditional-coverage test of \citet{christoffersen1998}, the joint likelihood-ratio test of correct coverage and breach independence, at both levels.
```

## B6-label2

**Why.** label

**Before.**

```
Exception behavior is tested by Kupiec, Christoffersen, and date-clustered breach tests at the two regulatory levels.
```

**After.**

```
Exception behavior is tested by the Kupiec unconditional-coverage, Christoffersen conditional-coverage, and date-clustered breach tests at the two regulatory levels.
```

## B6-label3

**Why.** label

**Before.**

```
EVT-tailed residual-hybrid passes Kupiec at 99\% for $84\%$ of names and
Christoffersen for $86\%$, and the date-clustered
```

**After.**

```
EVT-tailed residual-hybrid passes Kupiec at 99\% for $84\%$ of names and
Christoffersen conditional coverage for $86\%$, and the date-clustered
```

## B7-iqn1

**Why.** it is the architecture GBC uses, run without the Bayesian part

**Before.**

```
\emph{The neural implicit quantile network (IQN), the GBC estimator.} A
```

**After.**

```
\emph{The neural implicit quantile network (IQN), the network at the core of GBC.} A
```

## B7-iqn2

**Why.** cosine index starts at 1 in the code (n_c = 64); varphi looked like phi

**Before.**

```
\varphi_j(\tau) = \mathrm{ReLU}\Big(\textstyle\sum_{i=0}^{n_c-1}
```

**After.**

```
c_j(\tau) = \mathrm{ReLU}\Big(\textstyle\sum_{i=1}^{n_c}
```

## B7-iqn3

**Why.** same

**Before.**

```
H_\phi(s,\tau) \;=\; g\big(\psi(s)\circ\varphi(\tau)\big),
```

**After.**

```
H_\phi(s,\tau) \;=\; g\big(\psi(s)\circ c(\tau)\big),
```

## B7-iqn4

**Why.** B.8: Beta(0.3,0.3) stated as pre-set with its reason; widths as coded

**Before.**

```
where $\circ$ is elementwise multiplication and $g,\psi$ are
feed-forward nets. It uses tail-aware $\tau$-sampling, monotone rearrangement of the $\tau$-curve, and the conformal layer of Section~\ref{sec:hybrid}. The tail-aware sampling, $\lambda = \tfrac12\,U(0,1) + \tfrac12\,\mathrm{Beta}(0.3,0.3)$, oversamples the extremes that uniform sampling starves (the raw net's 99\% breach rate was 3.2\%).
```

**After.**

```
where $\circ$ is elementwise multiplication, $c(\tau)$ is a cosine embedding of the level with $n_c=64$ features, and $g,\psi$ are two-layer ReLU feed-forward nets of width 192 (128 in the untuned run) acting on the level embedding and on the standardized state respectively. The tuned variant uses tail-aware $\tau$-sampling, monotone rearrangement of the $\tau$-curve, and a conformal shift. The tail-aware sampling, $\lambda = \tfrac12\,U(0,1) + \tfrac12\,\mathrm{Beta}(0.3,0.3)$, was set once, before the tuned run, so that about a tenth of the training levels fall below 2.5\% against 2.5\% under uniform sampling; the mixture and the Beta parameters were not tuned on any test data. It answers the untuned run, whose 99\% breach rate was 3.2\% under uniform sampling, and the tuned IQN row of Table~\ref{tab:noncore} is a design revision made after that run and evaluated on a later sub-window.
```

## B7-train

**Why.** text said early stopping; the code uses a fixed Adam step budget

**Before.**

```
weights carries the entire quantile curve. Early stopping is on
held-out pinball loss. Monotone rearrangement
```

**After.**

```
weights carries the entire quantile curve. Training runs for a fixed budget of 12{,}000 minibatch steps (Adam, batch 512, rate $10^{-3}$; 6{,}000 in the untuned run) with no early stopping. Monotone rearrangement
```

## B7-noncore-note

**Why.** the tuned IQN's shift is calibrated on the first half of the test window, not the Proposition 1 split

**Before.**

```
\item[a] Tail-aware $\tau$-sampling, monotone rearrangement, and the conformal overlay of Section~\ref{sec:hybrid}.
```

**After.**

```
\item[a] Tail-aware $\tau$-sampling, monotone rearrangement, and a per-level conformal shift calibrated on the first half of the test window and scored on the second half; the residual-hybrid in this row is recalibrated the same way, so the loss levels are not comparable with Table~\ref{tab:frtb}.
```

## B6-eta

**Why.** eta was undefined and the GBM hyperparameters were given nowhere

**Before.**

```
is grown stagewise by gradient boosting \citep{friedman2001}.
```

**After.**

```
is grown stagewise by gradient boosting \citep{friedman2001}, where $\eta=0.06$ is a fixed shrinkage rate, $M=250$ trees of depth three are grown, and $h_m$ is the $m$-th regression tree, fitted by least squares to the pinball pseudo-residuals.
```

## B4-hansen

**Why.** eta and lambda were both taken

**Before.**

```
$\eta,\lambda$ (median $4.2$, $-0.015$), validated against the
```

**After.**

```
degrees of freedom and skewness (median $4.2$ and $-0.015$), validated against the
```

## B4-decay

**Why.** lambda is the tau-sampling law

**Before.**

```
EWMA with the RiskMetrics decay $\lambda=0.94$
```

**After.**

```
EWMA with the RiskMetrics decay $0.94$
```

## B5-garch

**Why.** GARCH never expanded

**Before.**

```
\citep{kuester2006, nietoruiz2016}. Fully parametric filters, GARCH and
```

**After.**

```
\citep{kuester2006, nietoruiz2016}. Fully parametric filters, generalized autoregressive conditional heteroskedasticity (GARCH) and
```

## B5-fhs

**Why.** FHS

**Before.**

```
and its GARCH-filtered variant (FHS) \citep{baroneadesi1999fhs}.
```

**After.**

```
and its GARCH-filtered variant, filtered historical simulation (FHS) \citep{baroneadesi1999fhs}.
```

## B5-evt

**Why.** EVT

**Before.**

```
the two-step logic of filtered historical simulation and GARCH-EVT \citep{baroneadesi1999fhs, mcneilfrey2000}. It keeps
```

**After.**

```
the two-step logic of filtered historical simulation and GARCH with an extreme-value-theory (EVT) tail \citep{baroneadesi1999fhs, mcneilfrey2000}. It keeps
```

## B5-mcs

**Why.** MCS

**Before.**

```
both remain in the $90\%$ Model Confidence Set \citep{hansen2011mcs}, and it improves
```

**After.**

```
both remain in the $90\%$ Model Confidence Set (MCS) \citep{hansen2011mcs}, and it improves
```

## B5-ewma

**Why.** EWMA

**Before.**

```
It includes historical simulation, EWMA with
```

**After.**

```
It includes historical simulation, exponentially weighted moving average (EWMA) variance with
```

## B5-gjr

**Why.** GJR

**Before.**

```
and GJR-GARCH-skew-$t$ \citep{glosten1993, hansen1994ARCD}, which adds
```

**After.**

```
and the GJR (Glosten--Jagannathan--Runkle) GARCH-skew-$t$ \citep{glosten1993, hansen1994ARCD}, which adds
```

## B5-caviar

**Why.** CAViaR

**Before.**

```
The strongest non-nested semiparametric rival in the set is SAV-CAViaR \citep{engle2004caviar}
```

**After.**

```
The strongest non-nested semiparametric rival in the set is SAV-CAViaR (conditional autoregressive value-at-risk) \citep{engle2004caviar}
```

## B5-gas

**Why.** GAS

**Before.**

```
minimization, the GAS of \citet{patton2019} (DM $9.5$ and $8.6$) and the
```

**After.**

```
minimization, the generalized autoregressive score (GAS) model of \citet{patton2019} (DM $9.5$ and $8.6$) and the
```

## B5-spa

**Why.** SPA

**Before.**

```
A superior-predictive-ability test \citep{hansen2005spa}
```

**After.**

```
A superior-predictive-ability (SPA) test \citep{hansen2005spa}
```

## B5-fz0

**Why.** FZ0

**Before.**

```
the zero-homogeneous FZ0 loss of \citet{fissler2016} and \citet{patton2019}, against
```

**After.**

```
the Fissler--Ziegler zero-homogeneous (FZ0) loss of \citet{fissler2016} and \citet{patton2019}, against
```

## B5-glossary

**Why.** glossary written as OA Section 1

**Before.**

```
algorithm boxes given. A glossary of acronyms is in the Online
Appendix.
```

**After.**

```
algorithm boxes given. A glossary of acronyms opens the Online
Appendix.
```

## B10-loss

**Why.** B.10

**Before.**

```
would silently exclude them.
```

**After.**

```
would silently exclude them. Each benchmark is estimated by its own conventional criterion: Student-$t$ or skew-$t$ likelihood for the GARCH family, empirical residual quantiles for HS and FHS, FZ0 for the two dynamic-ES models of Section~\ref{sec:frtb}, and pinball for CAViaR and for the shape learners. All are then scored out of sample by the same pinball and FZ0 losses, so a model fitted on the evaluation loss carries an in-sample advantage that the out-of-sample comparison tests.
```

## B10-levels

**Why.** eleven levels in the frontier jobs; not a proper scoring rule for the distribution

**Before.**

```
Distributional accuracy is scored by mean pinball loss across twelve quantile levels, a quantile-weighted proper score \citep{gneitingranjan2011}, and joint
```

**After.**

```
Distributional accuracy is scored by mean pinball loss across a fixed grid of quantile levels, twelve in the FRTB comparison of Table~\ref{tab:frtb} and eleven in the frontier sorts, a consistent scoring function for the quantile vector that is the point-mass case of the quantile-weighted CRPS \citep{gneitingranjan2011}, and joint
```

## F2-floor

**Why.** no floor is guaranteed; the bulk is a statistical tie

**Before.**

```
model throughout; the residual-hybrid is the choice where a guaranteed
$\ge$GARCH floor is wanted, with the score as a monitor
```

**After.**

```
model throughout; the residual-hybrid is the choice where forecast accuracy no worse than GARCH-$t$ in the bulk is wanted, with the score as a monitor
```

## F2-oracle1

**Why.** unreachable/unpredictable overstated

**Before.**

```
and the per-day oracle gap ($4.4\%$) is
unreachable because which day the tail event lands is unpredictable from
prior-day state.
```

**After.**

```
and the per-day oracle gap ($4.4\%$) is largely unforecastable from prior-day state.
```

## F2-oracle2

**Why.** same

**Before.**

```
day by day, because the per-day oracle gap is not forecastable from
prior-day state and a learned gate
```

**After.**

```
day by day, because the per-day oracle gap ($4.4\%$) is largely unforecastable from
prior-day state and a learned gate
```

## F2-holds

**Why.** 'holds well' is not what was tested; a tie was

**Before.**

```
A fixed-shape parametric filter is hard to beat where its shape assumption holds, and for most assets on most days it holds well.
```

**After.**

```
A fixed-shape parametric filter is hard to beat where its shape assumption holds, and for most assets on most days the flexible model cannot improve on it.
```

## F2-referee

**Why.** imagined-referee voice

**Before.**

```
The two FZ-estimated dynamic $(\VaR,\ES)$ models a referee would turn to next are the one-factor
```

**After.**

```
The two closest dynamic $(\VaR,\ES)$ benchmarks are the one-factor
```

## F4-refit

**Why.** walkforward_results.json; the residual-hybrid refit figure has no committed file (job_walkforward_hybrid.py queued)

**Before.**

```
which the top decile still carries $+2.09\%$ at DM 4.43 while the average
edge washes out ($-0.18\%$).
```

**After.**

```
which the top decile still carries $+2.47\%$ at DM 6.05 while the average
edge compresses to $+0.32\%$ (DM 0.8), within noise; this check uses the returns-space learner of the frozen holdout specification.
```

## F5-cross

**Why.** 0.018 is the t3-versus-normal value; Prop. 2's pair gives 0.023

**Before.**

```
with the crossover near $\tau_c \approx 0.018$, so $1\%$ sits below it and $2.5\%$ just above \citep{patton2020}.
```

**After.**

```
with a pair-dependent crossover $\tau^*$ ($0.018$ for $t_3$ against the normal, $0.023$ for $t_5$ against $t_8$), so $1\%$ sits below it and $2.5\%$ just above \citep{patton2020}.
```

## F7-dm

**Why.** fz_fullpanel_results.json: garch_t vs engine at 2.5%, DM -1.80

**Before.**

```
loses to GARCH-$t$ on the 2.5\% joint score (DM $-2.0$), and
```

**After.**

```
loses to GARCH-$t$ on the 2.5\% joint score (DM $-1.8$), and
```

## F11-korea

**Why.** R32 used both labels; 'negative control' is the one Section 4 uses

**Before.**

```
provides a falsification case that sharpens the claim: a price crash is not residual misspecification, and GARCH-$t$ wins there, as the frontier predicts.
```

**After.**

```
is the negative control that sharpens the claim: a price crash is not residual misspecification, and GARCH-$t$ wins there, as the frontier predicts.
```

## S8-rv

**Why.** R32 intro overclaimed relative to its own Section 5

**Before.**

```
An independently estimated realized-volatility scale reproduces the same split.
```

**After.**

```
On large caps with intraday data, re-estimation on realized-volatility residuals leaves the score within noise.
```

## S8-transfer

**Why.** amort_agecurve.json 6.4%, amort_full_results.json 9.7%

**Before.**

```
In its characteristics-only form it forecasts VaR and ES for assets with no return history at all, the day-one regime in which no per-asset model exists.
```

**After.**

```
Its gains over own-history benchmarks are largest in the first trading month, at roughly 6--10\% of pinball loss. In its characteristics-only form it forecasts VaR and ES for assets with no return history at all, the day-one regime in which no per-asset model exists.
```

## S8-strawman

**Why.** X-not-Y verdict

**Before.**

```
The comparison in this paper is therefore against the methods in standard use across the industry, not a regulatory strawman.
```

**After.**

```
The comparison in this paper is therefore against the methods in standard use across the industry.
```

## S8-conclusion

**Why.** X-not-Y; Sep 8 credit/freight sentence kept

**Before.**

```
And the score is a monitor, not a day-to-day switching rule, since the day-ahead oracle gap is largely unforecastable (Section~\ref{sec:gate}).
```

**After.**

```
And the score serves as a monitor rather than a day-to-day switching rule, since the day-ahead oracle gap is largely unforecastable (Section~\ref{sec:gate}). Credit and freight retain accuracy gains but fail breach-independence tests, which makes dependence-aware calibration a priority for those applications.
```

## S8-conc2

**Why.** wording

**Before.**

```
The score is predictive, not a necessary or sufficient condition: high residual kurtosis coincides with ties in some markets, and in credit and freight the accuracy edges sit alongside open calibration.
```

**After.**

```
The score is predictive rather than a necessary or sufficient condition: high residual kurtosis coincides with ties in some markets, and in credit and freight the accuracy edges sit alongside failed breach-independence tests.
```

## GE-disclaim

**Why.** GARCH-EVT is the top-ranked referee risk; a same-rows job (job_garch_evt.py) is queued. Delete 'once run' after the numbers land

**Before.**

```
The comparison set does not include GARCH-EVT \citep{mcneilfrey2000}, which
\citet{kuester2006} rank first among classical methods. Its
filter-then-tail logic is instead absorbed into the estimator's own EVT
stage (Section~\ref{sec:methods}), so the EVT-tailed layer is its
analogue within the comparison set.
```

**After.**

```
The comparison set of Table~\ref{tab:frtb} does not include standalone GARCH-EVT \citep{mcneilfrey2000}, which
\citet{kuester2006} rank first among classical methods. Its
filter-then-tail logic is absorbed into the estimator's own EVT
stage (Section~\ref{sec:methods}), so the EVT-tailed layer is its
analogue within the comparison set. A same-rows comparison against per-name and pooled GARCH-EVT tails, on the frontier sorts and on the FZ0 score, is reported in the Online Appendix once run.
```

## JEL

**Why.** forecasting and financial-forecasting codes fit the paper; C14/C52 kept

**Before.**

```
\noindent\textbf{JEL classification:} C14; C52; C58.
```

**After.**

```
\noindent\textbf{JEL classification:} C14; C52; C53; C58; G17.
```

## B3-lemma

**Why.** envelope name in the sampler lemma; unused \Q macro deleted

**Before.**

```
If $\tau \mapsto Q^{z}_t(\tau)+c_\tau$ is nondecreasing and
left-continuous (guaranteed by the rearrangement step) and
$\tau \sim U(0,1)$, then $Z^* = \widetilde{q}(\tau \mid s)$ has
quantile function exactly $\widetilde{q}(\cdot \mid s)$.
```

**After.**

```
If $\tau \mapsto \widetilde{Q}^{z}_t(\tau) = Q^{z}_t(\tau)+c_\tau$ is nondecreasing and
left-continuous (guaranteed by the rearrangement step) and
$\tau \sim U(0,1)$, then $Z^* = \widetilde{Q}^{z}_t(\tau)$ has
quantile function exactly $\widetilde{Q}^{z}_t(\cdot)$.
```


# Online appendix edits

## OA-glossary

**Why.** the manuscript promises a glossary the OA did not contain

**Before.**

```
\section{Algorithms}
```

**After.**

```
\section{Glossary of acronyms}
\begin{tabular}{ll}
\toprule
ARCD & autoregressive conditional density model \citep{hansen1994ARCD} \\
CAViaR & conditional autoregressive value-at-risk \citep{engle2004caviar}; SAV, its symmetric absolute value form \\
CC, UC & conditional coverage \citep{christoffersen1998} and unconditional coverage \citep{kupiec1995} exception tests \\
CRPS & continuous ranked probability score \\
CRSP, WRDS & Center for Research in Security Prices; Wharton Research Data Services \\
DM & Diebold--Mariano test \citep{dieboldmariano1995} \\
EM, IG, OAS & emerging markets; investment grade; option-adjusted spread \\
ERM & empirical risk minimization \\
ES, VaR & Expected Shortfall; Value-at-Risk \\
EVT, GPD & extreme-value theory; generalized Pareto distribution \\
EWMA & exponentially weighted moving average variance \citep{riskmetrics1996} \\
FHS, HS & filtered historical simulation \citep{baroneadesi1999fhs}; historical simulation \\
FRTB & Fundamental Review of the Trading Book \citep{bcbs2019frtb} \\
FWER & family-wise error rate \\
FZ0 & the zero-homogeneous Fissler--Ziegel joint (VaR, ES) scoring function \citep{fissler2016, patton2019} \\
GARCH, GJR & generalized autoregressive conditional heteroskedasticity \citep{bollerslev1986}; the Glosten--Jagannathan--Runkle leverage form \citep{glosten1993} \\
GAS & generalized autoregressive score model \citep{patton2019} \\
GBC & generative Bayesian computation \citep{polson2023gbc} \\
GBM & gradient boosting machine (gradient-boosted regression trees) \\
GFC & the 2008 global financial crisis \\
IQN & implicit quantile network \citep{dabney2018iqn} \\
MCS & Model Confidence Set \citep{hansen2011mcs} \\
PIT & probability integral transform \\
PZC & Patton, Ziegel and Chen \citep{patton2019} \\
QML & quasi-maximum likelihood \\
RV & realized variance \\
SPA & superior predictive ability test \citep{hansen2005spa} \\
TAQ & NYSE Trade and Quote database \\
\bottomrule
\end{tabular}

\section{Algorithms}
```

## OA-pipeline

**Why.** OA dropped mu-hat; envelope named as in the paper

**Before.**

```
$\widehat Q_{t+1}(\tau) = \widehat\sigma_{t+1}\,\widetilde q(\tau\mid s_t)$
at the desk's levels, with VaR and ES$_{97.5}$ both read from the coherent
min-envelope curve $Q^{*}=\min\{$body$,$EVT$\}$ (VaR at the $\alpha$
```

**After.**

```
$\widehat Q_{t+1}(\tau) = \widehat\mu+\widehat\sigma_{t+1}\,\big(Q^{z}_{t+1}(\tau)+c_\tau\big)$
at the desk's levels, with VaR and ES$_{97.5}$ both read from the coherent
min-envelope curve $Q^{z}$ of equation~(5) of the paper (VaR at the $\alpha$
```

## OA-Qstar2

**Why.** name

**Before.**

```
coherent min-envelope curve $Q^{*}$ --- the exact forecasts
```

**After.**

```
coherent min-envelope curve $Q^{z}$ of equation~(5) of the paper --- the exact forecasts
```

## OA-schem1

**Why.** schematic label matches the code's order (E.12)

**Before.**

```
\draw[arr] (shape) -- node[lab, above] {splice at $p_0$} (evt);
```

**After.**

```
\draw[arr] (shape) -- node[lab, above] {minimum at $\tau\le p_0$, rearrange} (evt);
```

## OA-schem2

**Why.** same

**Before.**

```
\draw[arr] (conf) -- node[lab, above] {calibrated curve $\widetilde q$} (out);
```

**After.**

```
\draw[arr] (conf) -- node[lab, above] {shifted curve $Q^{z}+c_\tau$ (overlay)} (out);
```

## OA-rgarch

**Why.** Realized GARCH reused omega, beta, xi, phi, tau with unrelated meanings

**Before.**

```
$\log h_t=\omega+\beta\log h_{t-1}+\gamma\log \mathrm{RV}_{t-1}$ with a measurement
equation $\log\mathrm{RV}_t=\xi+\phi\log h_t+\tau(z_t)+u_t$ linking the realized
```

**After.**

```
$\log h_t=\omega_R+\beta_R\log h_{t-1}+\gamma_R\log \mathrm{RV}_{t-1}$ with a measurement
equation $\log\mathrm{RV}_t=\xi_R+\phi_R\log h_t+\tau_R(z_t)+u_{R,t}$ linking the realized
```

## OA-title

**Why.** A.6: X-not-Y title

**Before.**

```
\subsection*{On the score-ordering: why it is an empirical regularity, not a theorem}
```

**After.**

```
\subsection*{Remark on the score ordering}
```

## OA-tab2

**Why.** A.6: claim-in-title neutralized

**Before.**

```
\caption{Double sort: the edge needs both a shape break and an active
regime. Cells are
```

**After.**

```
\caption{Double sort on the misspecification score and trailing volatility. Cells are
```

## B3-colon

**Why.** colon-setup sentence

**Before.**

```
the more conservative (more negative) branch: the pooled GPD extrapolation can tighten a thin state-conditioned body on a stressed day but never loosen it.
```

**After.**

```
the more conservative (more negative) branch, so the pooled GPD extrapolation can tighten a thin state-conditioned body on a stressed day but never loosen it.
```

## B3-range

**Why.** the body is fitted at the sub-alpha nodes too; the GPD does not only extrapolate (Sep 8 M12, kept)

**Before.**

```
\emph{Stage 3 (EVT tail).} Beyond the estimation range of
\eqref{eq:shapeERM}, extrapolate with the generalized Pareto
```

**After.**

```
\emph{Stage 3 (EVT tail).} In the sparsely observed lower tail, where
\eqref{eq:shapeERM} is fitted on few exceedances, use the generalized Pareto
```

## B3-scope-b

**Why.** 'weakly below' is not guaranteed nodewise after rearrangement; state only what holds

**Before.**

```
whose tail nodes take the minimum of body and EVT branches before rearrangement, so the shifted envelope sits weakly below the shifted body in the tail.
```

**After.**

```
whose tail nodes take the minimum of body and EVT branches before rearrangement, so the proposition covers the shifted body while the reported curve is the shifted envelope.
```


# R36: GARCH-EVT same-rows results, residual-hybrid refit provenance, per-asset rerun

## 1.2-garchevt (M)

**Why.** the pending comparison has run

**Before.**

```
A same-rows comparison against per-name and pooled GARCH-EVT tails, on the frontier sorts and on the FZ0 score, is reported in the Online Appendix once run.
```

**After.**

```
A same-rows comparison against standalone McNeil--Frey GARCH-EVT, per name and with a pooled tail, is reported in Sections~\ref{sec:frontier} and~\ref{sec:frtb} and in the Online Appendix: the conventional EVT tail carries no frontier of its own, and the estimator beats it by 2.64\% (DM 8.9) in the top kurtosis decile and on the joint score at both levels.
```

## 4.1-garchevt (M)

**Why.** TODO C.2: the missing benchmark on the frontier rows

**Before.**

```
\paragraph{The composite score.} Table~\ref{tab:frontier} sorts on each
```

**After.**

```
\paragraph{GARCH-EVT on the same rows.} The frontier is a statement about a state-conditioned residual shape, so the natural question is whether a conventional unconditional tail captures it. On the rows of Table~\ref{tab:frontier}, a McNeil--Frey GARCH-EVT forecast (the same GARCH-$t$ filter, GPD tails fitted by maximum likelihood to the 10\% most extreme training residuals per tail, empirical residual quantiles in between) shows no frontier: against GARCH-$t$ its top-decile edge is $+0.31\%$ (DM 3.6) per name and $-0.16\%$ (DM -2.7) with a pooled tail, and its overall edge is negative in both forms. The estimator beats the pooled GARCH-EVT by $+2.64\%$ (DM 8.9) in the top kurtosis decile and by $+0.10\%$ (DM 2.5) in deciles one through nine, and the per-name GARCH-EVT by $+2.18\%$ (DM 9.6) and $+0.21\%$ (DM 4.6). The same-rows table and the GPD threshold diagnostics are in the Online Appendix.

\paragraph{The composite score.} Table~\ref{tab:frontier} sorts on each
```

## 4.1-holdout-garchevt (M)

**Why.** TODO C.4

**Before.**

```
This is the same threshold nonlinearity, attenuated in a larger-cap, pre-2014 universe.
```

**After.**

```
This is the same threshold nonlinearity, attenuated in a larger-cap, pre-2014 universe. On the same holdout rows the pooled GARCH-EVT again shows no frontier ($-0.15\%$ against GARCH-$t$ in the top decile, DM -2.8), and the frozen learner beats it there by $+1.16\%$ (DM 2.5), within noise elsewhere.
```

## 3-refit (M)

**Why.** walkforward_hybrid_results.json (residual-hybrid learner) replaces the file-less +2.09/4.43

**Before.**

```
which the top decile still carries $+2.47\%$ at DM 6.05 while the average
edge compresses to $+0.32\%$ (DM 0.8), within noise; this check uses the returns-space learner of the frozen holdout specification.
```

**After.**

```
which the top decile still carries $+2.12\%$ at DM 4.41 while the average
edge washes out ($-0.22\%$, DM $-0.59$); the returns-space learner of the frozen holdout specification gives $+2.47\%$ (DM 6.05) and $+0.32\%$ (DM 0.8) under the same schedule.
```

## OA-refit-row (OA)

**Why.** same file

**Before.**

```
4.43 (annual-refit residual-hybrid walk-forward, $+2.09\%$)
```

**After.**

```
4.41 (annual-refit residual-hybrid walk-forward, $+2.12\%$)
```

## 5.1-garchevt (M)

**Why.** TODO C.2: FZ0 head-to-head

**Before.**

```
At 2.5\% it again wins over GARCH-$t$ (DM 5.1). The two closest dynamic
```

**After.**

```
At 2.5\% it again wins over GARCH-$t$ (DM 5.1). On the same rows it also beats standalone GARCH-EVT, whose ES is the McNeil--Frey closed form: with a pooled tail by DM 4.8 at 1\% and 6.8 at 2.5\%, and per name by DM 5.2 and 5.4, so the gain over the conventional EVT construction is not confined to the pinball frontier. The two closest dynamic
```

## fig2-bars (M)

**Why.** GARCH-EVT enters Figure 2

**Before.**

```
symbolic x coords={GARCH-$t$,Taylor,FHS,GAS}, xtick=data,
```

**After.**

```
symbolic x coords={GARCH-$t$,GARCH-EVT,Taylor,FHS,GAS}, xtick=data,
```

## fig2-bar1 (M)

**Why.** same-rows job, pooled tail

**Before.**

```
\addplot[fill=npblue,draw=npblue] coordinates {(GARCH-$t$,0.00848)(Taylor,0.01748)(FHS,0.02517)(GAS,0.08514)};
```

**After.**

```
\addplot[fill=npblue,draw=npblue] coordinates {(GARCH-$t$,0.00848)(GARCH-EVT,0.00784)(Taylor,0.01748)(FHS,0.02517)(GAS,0.08514)};
```

## fig2-bar2 (M)

**Why.** same

**Before.**

```
\addplot[fill=npmid,draw=npmid] coordinates {(GARCH-$t$,0.00545)(Taylor,0.00024)(FHS,0.01370)(GAS,0.05030)};
```

**After.**

```
\addplot[fill=npmid,draw=npmid] coordinates {(GARCH-$t$,0.00545)(GARCH-EVT,0.00888)(Taylor,0.00024)(FHS,0.01370)(GAS,0.05030)};
```

## fig2-caption (M)

**Why.** caption

**Before.**

```
$1\%$, $5.1$ at $2.5\%$) and FHS (DM $4.9$), together with the two
```

**After.**

```
$1\%$, $5.1$ at $2.5\%$), pooled-tail GARCH-EVT (DM $4.8$ and $6.8$, same-rows run) and FHS (DM $4.9$), together with the two
```

## fig2-enlarge (M)

**Why.** five bars

**Before.**

```
enlarge x limits=0.28, ymajorgrids,
```

**After.**

```
enlarge x limits=0.22, ymajorgrids,
```

## 5.1-passrates (M)

**Why.** B.6/E.8: conditional coverage at both levels; numbers from the committed rerun of job_perasset_v2.py

**Before.**

```
EVT-tailed residual-hybrid passes Kupiec at 99\% for $84\%$ of names and
Christoffersen conditional coverage for $86\%$, and the date-clustered test passes at 99\% ($t=1.01$) and marginally at 97.5\% ($t=1.86$)
```

**After.**

```
EVT-tailed residual-hybrid passes Kupiec at 99\% for $82\%$ of names and
Christoffersen conditional coverage for $89\%$ (at 97.5\%, $71\%$ and $79\%$), and the date-clustered test passes at 99\% ($t=0.93$) and marginally at 97.5\% ($t=1.85$)
```

## 5.1-passrates2 (M)

**Why.** same file

**Before.**

```
Per-name diagnostics show residual cross-sectional calibration heterogeneity (84\% and 86\% pass rates at 99\%, Online Appendix Figure~OA.2).
```

**After.**

```
Per-name diagnostics show residual cross-sectional calibration heterogeneity (82\% and 89\% pass rates at 99\%, Online Appendix Figure~OA.2).
```

## 5.1-passrates3 (M)

**Why.** same file

**Before.**

```
(Kupiec$_{97.5}$ pass rate 47\%, against 72\% unshifted and 69\% adaptive)
```

**After.**

```
(Kupiec$_{97.5}$ pass rate 48\%, against 71\% unshifted and 69\% adaptive)
```

## OA-garchevt-section (OA)

**Why.** new OA section

**Before.**

```
\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}
```

**After.**

```
\section{Standalone GARCH-EVT on the canonical rows}\label{sec:garchevt-oa}
The manuscript's comparison set omits standalone GARCH-EVT \citep{mcneilfrey2000}, which \citet{kuester2006} rank first among classical methods. This section reports it on exactly the rows, filter and splits of the frontier sorts (Table~1 of the paper) and of the full-panel FZ0 run (Figure~2 of the paper), from \texttt{job\_garch\_evt.py} (result file \texttt{garch\_evt\_results.json}). Two forms are run: per name, with the GPD tails fitted to each name's own training residuals, and pooled, with one threshold and one $(\xi,\beta)$ per tail across names. The pooled body row is the frontier engine of Table~1 (no EVT branch); the engine row adds the body/EVT minimum and rearrangement of equation~(5). Table~\ref{tab:garchevt-frontier} gives the eleven-level pinball comparison and Table~\ref{tab:garchevt-fz0} the joint score.

\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{GARCH-EVT on the frontier rows: pinball edge by score region and head-to-head comparisons.}
\label{tab:garchevt-frontier}
\small
\begin{tabular}{lcccc}
\toprule
Model & Top $\mathrm{mk}_{63}$ decile & Deciles 1--9 & Top composite decile & Overall \\
\midrule
\multicolumn{5}{l}{\emph{Edge over GARCH-$t$, \% (per-date DM)}} \\
GARCH-EVT, per name & $+0.31$ (3.62) & $-0.22$ (-6.61) & $+0.37$ (5.35) & $-0.16$ (-5.00) \\
GARCH-EVT, pooled tail & $-0.16$ (-2.69) & $-0.12$ (-4.55) & $-0.06$ (-1.40) & $-0.12$ (-4.89) \\
GARCH $+$ pooled body (no EVT) & $+2.98$ (10.48) & $+0.02$ (0.43) & $+2.79$ (8.91) & $+0.35$ (5.35) \\
Engine (body/EVT minimum) & $+2.48$ (10.08) & $-0.01$ (-0.25) & $+2.19$ (8.00) & $+0.27$ (4.62) \\
\midrule
\multicolumn{5}{l}{\emph{Head-to-head, \% (per-date DM)}} \\
Engine over GARCH-EVT pooled & $+2.64$ (8.91) & $+0.10$ (2.47) & $+2.24$ (7.51) & $+0.39$ (7.66) \\
Engine over GARCH-EVT per name & $+2.18$ (9.63) & $+0.21$ (4.63) & $+1.82$ (7.39) & $+0.43$ (8.22) \\
Pooled body over GARCH-EVT pooled & $+3.14$ (9.39) & $+0.14$ (2.84) & $+2.84$ (8.37) & $+0.47$ (7.96) \\
Engine over pooled body & $-0.51$ (-9.04) & $-0.04$ (-2.28) & $-0.62$ (-9.64) & $-0.09$ (-5.25) \\
\bottomrule
\end{tabular}
\begin{tablenotes}\footnotesize
\item 200 names, 221,600 test rows, same rows and splits as Table~1 of the paper and Figure~2 of the paper. Edge $=$ (reference pinball $-$ model pinball)/reference pinball over the eleven-level grid; DM is the per-date Newey--West(10) Diebold--Mariano statistic. GARCH-EVT is McNeil--Frey: GARCH(1,1)-$t$ filter, GPD tails fitted by maximum likelihood to the 10\% most extreme training residuals per tail (per name, or pooled across names), empirical residual quantiles between the thresholds. The engine's pooled GPD at $p_0=0.025$ has $\hat\xi=0.298$, $\hat\beta=0.639$ on 6075 exceedances; the EVT branch is the tighter of the two at the 1\% node on 60.1\% of test rows and at the 2.5\% node on 59.5\%.
\end{tablenotes}
\end{threeparttable}
\end{table}

\begin{table}[h
```


# R38: evaluation extras (CPA regression, Murphy diagrams, DQ test, dispersion)

## 4.1-cpa (M)

**Why.** Giacomini-White CPA as the regression form of the frontier; per-date win rates

**Before.**

```
The edge is concentrated in the top decile: the top $\mathrm{mk}_{63}$ decile
carries $+2.98\%$ at per-date DM $10.5$, the overall edge is $+0.35\%$ at
DM $5.35$, and the lower deciles are statistically indistinguishable
from zero.
```

**After.**

```
The edge is concentrated in the top decile: the top $\mathrm{mk}_{63}$ decile
carries $+2.98\%$ at per-date DM $10.5$, the overall edge is $+0.35\%$ at
DM $5.35$, and the lower deciles are statistically indistinguishable
from zero. The sort has a regression form. Taking the asset-day loss differential (GARCH-$t$ pinball minus engine pinball) and the lagged score as the conditioning variable, the conditional-predictive-ability test of \citet{giacominiwhite2006} with instruments (1, score) rejects equal conditional accuracy (Wald $\chi^2_2=73.6$ on the composite percentile, 90.0 on the kurtosis percentile), and the slope of the differential on the score is positive with a date-clustered $t$ of 8.6 (composite) and 9.8 (kurtosis). On a date-by-date reading the engine has the lower loss on 74\% of dates in the top decile and 55\% in deciles one through nine.
```

## 5.1-dq-murphy (M)

**Why.** DQ test and Murphy-diagram summary

**Before.**

```
so the gain over the conventional EVT construction is not confined to the pinball frontier. The two closest dynamic
```

**After.**

```
so the gain over the conventional EVT construction is not confined to the pinball frontier. The dynamic quantile test of \citet{engle2004caviar} (four hit lags and the VaR) passes at the 5\% level for 86\% of names at 1\% and 70\% at 2.5\% for the accuracy layer, against 84\% and 68\% for GARCH-$t$ and 83\% and 62\% for the pooled GARCH-EVT; the overlay lifts the 2.5\% rate to 84\%. Because a ranking under one consistent score need not hold under another \citep{patton2020}, the Online Appendix reports Murphy diagrams \citep{ehm2016} for the VaR forecasts: the accuracy layer has the lower elementary score against GARCH-$t$ on 70\% of the threshold grid at 1\% and 65\% at 2.5\%, and against the pooled GARCH-EVT on 85\% at both levels, losing in a band of thresholds near the typical VaR level. The two closest dynamic
```

## OA-extras (OA)

**Why.** OA subsection with CPA/DQ/dispersion table and Murphy figure

**Before.**

```
\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}
```

**After.**

```

\subsection*{Additional evaluation statistics on the same rows}
The same run adds four statistics that go beyond mean loss. (i)~The conditional-predictive-ability test of \citet{giacominiwhite2006}, with the asset-day loss differential $d_{it}=L^{\mathrm{GARCH}\text{-}t}_{it}-L^{\mathrm{engine}}_{it}$ (eleven-level pinball) and instruments $(1,\mathrm{score}_{i,t-1})$; the Wald statistic uses a Newey--West(10) covariance of the per-date sums. (ii)~Murphy diagrams \citep{ehm2016}: the mean elementary quantile score $S_\theta(q,y)=(\mathbb{I}\{y<q\}-\alpha)(\mathbb{I}\{\theta<q\}-\mathbb{I}\{\theta<y\})$ of the accuracy layer minus that of a competitor, on a grid of forty return-space thresholds $\theta$ (the 0.1\% to 15\% quantiles of test returns); a negative value means the accuracy layer is better at that $\theta$, and a curve that is negative everywhere would mean dominance under every consistent scoring function for the $\alpha$-quantile. (iii)~The dynamic quantile test of \citet{engle2004caviar} per name with four hit lags and the VaR. (iv)~The dispersion of the per-date loss differential.

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
GARCH-$t$ minus engine & composite pct. & 73.6 & 0.0081 & 8.6 \\
GARCH-$t$ minus engine & $\mathrm{mk}_{63}$ pct. & 90.0 & 0.0068 & 9.8 \\
Pooled GARCH-EVT minus engine & composite pct. & 64.5 & 0.0072 & 7.5 \\
GARCH-$t$ minus pooled body & composite pct. & 91.4 & 0.0105 & 9.8 \\
\midrule
\multicolumn{5}{l}{\emph{Dynamic quantile test, per-name pass rate at 5\% (200 names)}} \\
Model & \multicolumn{2}{c}{$\alpha=1\%$} & \multicolumn{2}{c}{$\alpha=2.5\%$} \\
\midrule
Engine (accuracy layer) & \multicolumn{2}{c}{86\%} & \multicolumn{2}{c}{70\%} \\
Engine $+$ conformal overlay & \multicolumn{2}{c}{86\%} & \multicolumn{2}{c}{84\%} \\
GARCH(1,1)-$t$ & \multicolumn{2}{c}{84\%} & \multicolumn{2}{c}{68\%} \\
GARCH-EVT, pooled tail & \multicolumn{2}{c}{83\%} & \multicolumn{2}{c}{62\%} \\
GARCH-EVT, per name & \multicolumn{2}{c}{82\%} & \multicolumn{2}{c}{60\%} \\
GARCH $+$ pooled body (no EVT) & \multicolumn{2}{c}{69\%} & \multicolumn{2}{c}{54\%} \\
\midrule
\multicolu
```


# R40: every standard benchmark on the canonical rows

## abstract-fz0 (M)

**Why.** on the full comparison set GJR-GARCH-skew-t (both levels) and the Taylor model (2.5%) are within noise of the accuracy layer; the unscoped claim no longer holds

**Before.**

```
and it attains the lowest joint (VaR, ES) loss against standard benchmarks.
```

**After.**

```
and it attains the lowest joint (VaR, ES) loss against GARCH-$t$ and FHS.
```

## 5.1-fullset (M)

**Why.** full-set FZ0 and MCS on the same rows

**Before.**

```
losing in a band of thresholds near the typical VaR level. The two closest dynamic
```

**After.**

```
losing in a band of thresholds near the typical VaR level. Extending the joint score to the whole comparison set on the same rows (Online Appendix Table~OA.11), the accuracy layer has the lowest mean FZ0 at 1\% and is within noise of GJR-GARCH-skew-$t$ at both levels (DM 1.1 and -0.3) and of the Taylor model at 2.5\% (DM -0.1); the 90\% Model Confidence Set on the per-date FZ0 series contains the accuracy layer, the conformal overlay, the pooled body and GJR-GARCH-skew-$t$ at 1\% and the accuracy layer, the pooled body, GJR-GARCH-skew-$t$ and the Taylor model at 2.5\%, and excludes GARCH-$t$, every FHS variant, both GARCH-EVT forms, the GAS model, EWMA and historical simulation at both levels. On the eleven-level pinball the set contains only the pooled body and SAV-CAViaR: the EVT branch costs pinball, as Table~\ref{tab:frtb} reports for the twelve-level battery, and is kept for the exception tests it passes. The two closest dynamic
```

## 4.1-fullset (M)

**Why.** every benchmark on the frontier rows; CPA against every model; CAViaR shares the frontier

**Before.**

```
The same-rows table and the GPD threshold diagnostics are in the Online Appendix.
```

**After.**

```
The same-rows table and the GPD threshold diagnostics are in the Online Appendix, together with the rest of the comparison set on the same rows (Table~OA.10). Of the standard benchmarks, only SAV-CAViaR shows a top-decile edge over GARCH-$t$ above one percent ($+2.81\%$, DM 8.2): it models the quantile directly and reacts to $|r_{t-1}|$, so it carries the same frontier the engine does, and the two tie in every region (top decile $-0.33\%$, DM $-1.8$; overall $-0.12\%$, DM $-1.6$, engine over CAViaR), the tie Section~\ref{sec:frtb} reports on the FRTB battery. The conditional-predictive-ability slope of each benchmark's loss differential against the engine on the lagged score is positive with $t>2$ for GARCH-$t$, per-name GARCH-EVT, pooled-tail GARCH-EVT, pooled FHS, per-name FHS, rolling FHS, EWMA and GJR-GARCH-skew-$t$, so the engine's advantage over each of them grows with the score; it is flat for historical simulation and SAV-CAViaR.
```

## OA-bench (OA)

**Why.** OA subsection with the three all-benchmark tables

**Before.**

```
\section{Frontier robustness: calendar overlap, family-wise error, and the universe rule}
```

**After.**

```
\subsection*{All benchmarks on the canonical rows}
The GARCH-EVT comparison above is one row of a larger exercise (\texttt{job\_bench\_all.py}, result file \texttt{bench\_all\_results.json}): every model in the paper's comparison set is scored on the identical 221,600 test rows of the 200-name panel, through every statistic. GARCH-$t$, GJR-GARCH-skew-$t$, the two GARCH-EVT forms, the GAS and Taylor models and SAV-CAViaR are estimated per name on the estimation window; the FHS variants take the empirical quantiles of the GARCH-$t$ residuals (pooled across names, per name on the training window, or over a rolling 500-day window); EWMA is the RiskMetrics recursion with Gaussian quantiles; historical simulation is the rolling 500-day empirical return quantile. GAS and Taylor exist only at the two regulatory levels and enter the joint-score, dynamic-quantile and Murphy statistics. Table~\ref{tab:bench-pinball} gives the eleven-level pinball frontier, Table~\ref{tab:bench-fz0} the joint score, and Table~\ref{tab:bench-tests} the conditional-predictive-ability, dynamic-quantile, Murphy and win-rate statistics.

\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{Every benchmark on the frontier rows: eleven-level pinball edge over GARCH-$t$ by score region, engine head-to-head, and Model Confidence Set membership.}
\label{tab:bench-pinball}
\footnotesize
\begin{tabular}{lccccc}
\toprule
Model & Top $\mathrm{mk}_{63}$ decile & Deciles 1--9 & Overall & Engine vs model (top) & MCS \\
\midrule
Engine (accuracy layer) & $+2.48$ (10.08) & $-0.01$ (-0.25) & $+0.27$ (4.62) & --- &  \\
GARCH $+$ pooled body (no EVT) & $+2.98$ (10.48) & $+0.02$ (0.43) & $+0.35$ (5.35) & $-0.51$ (-9.04) & $\checkmark$ \\
GARCH(1,1)-$t$ & (reference) & (reference) & (reference) & $+2.48$ (10.08) &  \\
GJR-GARCH-skew-$t$ & $+0.16$ (0.60) & $-0.01$ (-0.13) & $+0.01$ (0.35) & $+2.32$ (9.70) &  \\
GARCH-FHS (pooled) & $-0.14$ (-2.45) & $-0.12$ (-4.39) & $-0.13$ (-4.62) & $+2.62$ (8.86) &  \\
GARCH-FHS (per name) & $+0.34$ (3.87) & $-0.27$ (-6.86) & $-0.20$ (-5.33) & $+2.15$ (9.67) &  \\
GARCH-FHS (rolling 500d) & $-0.75$ (-6.68) & $-0.03$ (-0.55) & $-0.11$ (-2.19) & $+3.21$ (10.22) &  \\
GARCH-EVT (pooled tail) & $-0.16$ (-2.69) & $-0.12$ (-4.55) & $-0.12$ (-4.89) & $+2.64$ (8.91) &  \\
GARCH-EVT (per name) & $+0.31$ (3.62) & $-0.22$ (-6.61) & $-0.16$ (-5.00) & $+2.18$ (9.63) &  \\
SAV-CAViaR & $+2.81$ (8.16) & $+0.08$ (1.60) & $+0.39$ (6.29) & $-0.33$ (-1.82) & $\checkmark$ \\
EWMA (R
```

