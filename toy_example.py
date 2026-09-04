"""Synthetic end-to-end check for gbc_downside_main (Sec. theory/toy).
Truth known by construction. Seed fixed. Runtime ~20s.

DGP: z_t ~ unit-variance Student-t with regime-switching nu:
  calm nu=12, fat nu=4; persistent Markov chain. sigma_t from GARCH(1,1).
Forecasters of the residual tau-quantile (scale known => isolates shape):
  FIXED : single t_nu MLE fit on train residuals (fixed shape)
  BINNED: empirical quantile within trailing-kurtosis-decile bin
          (state-conditioned shape; the amortized model's toy analogue)
  ORACLE: true regime quantile.
Checks: (C1) Lemma-1 identity numerics; (C2) regret concentrates in top
score decile; (C3) 1% coverage before/after split-conformal shift.
"""
import numpy as np, pandas as pd
from scipy import stats, optimize

rng = np.random.default_rng(20260728)
T, BURN = 80_000, 1000
NU_CALM, NU_FAT, P_STAY_CALM, P_STAY_FAT = 12.0, 3.0, 0.997, 0.99

# regimes
reg = np.zeros(T + BURN, dtype=int)
for t in range(1, T + BURN):
    stay = P_STAY_CALM if reg[t-1] == 0 else P_STAY_FAT
    reg[t] = reg[t-1] if rng.random() < stay else 1 - reg[t-1]

def tq(nu, tau):     # unit-variance t quantile
    return stats.t.ppf(tau, nu) * np.sqrt((nu - 2) / nu)
def trvs(nu, size):
    return stats.t.rvs(nu, size=size, random_state=rng) * np.sqrt((nu - 2) / nu)

z = np.where(reg == 0, trvs(NU_CALM, T + BURN), trvs(NU_FAT, T + BURN))
z = z[BURN:]; reg = reg[BURN:]

# trailing 63d excess kurtosis score (the meter)
zs = pd.Series(z)
mk = zs.rolling(63).kurt().shift(1)  # causal, pandas C impl (excess kurtosis)
valid = ~mk.isna()
z_v, reg_v, mk_v = z[valid], reg[valid.values], mk[valid].values
n = len(z_v)
itr, ical, itst = np.arange(n) < n//2, (np.arange(n) >= n//2) & (np.arange(n) < 3*n//4), np.arange(n) >= 3*n//4

# FIXED shape: MLE nu on train
def negll(nu):
    s = np.sqrt((nu - 2) / nu)
    return -stats.t.logpdf(z_v[itr] / s, nu).sum() + itr.sum() * np.log(s)
nu_hat = optimize.minimize_scalar(negll, bounds=(2.2, 60), method='bounded').x

TAUS = [0.01, 0.025]
score_dec = np.digitize(mk_v, np.quantile(mk_v[itr], np.linspace(.1, .9, 9)))  # deciles from train

rows, cov = [], {}
pin = lambda u, tau: u * (tau - (u < 0))
for tau in TAUS:
    qF = tq(nu_hat, tau) * np.ones(n)
    # BINNED: empirical tau-quantile of train residuals per score decile
    qB = np.full(n, np.nan)
    for d in range(10):
        m_tr = itr & (score_dec == d)
        qB[score_dec == d] = np.quantile(z_v[m_tr], tau) if m_tr.sum() > 200 else np.quantile(z_v[itr], tau)
    qO = np.where(reg_v == 0, tq(NU_CALM, tau), tq(NU_FAT, tau))
    # conformal shift for BINNED on calibration split
    err_rate = (z_v[ical] < qB[ical]).mean()
    shift = np.quantile(z_v[ical] - qB[ical], tau)   # per-level additive shift
    qBc = qB + shift
    for name, q in [("FIXED", qF), ("BINNED", qB), ("ORACLE", qO)]:
        L = pin(z_v[itst] - q[itst], tau).mean()
        rows.append((tau, name, L))
    cov[tau] = dict(
        fixed=(z_v[itst] < qF[itst]).mean(),
        binned=(z_v[itst] < qB[itst]).mean(),
        binned_conf=(z_v[itst] < qBc[itst]).mean())

res = pd.DataFrame(rows, columns=["tau", "model", "pinball"]).pivot(index="tau", columns="model", values="pinball")
res["regret_FIXED_%"] = 100 * (res.FIXED - res.ORACLE) / res.ORACLE
res["regret_BINNED_%"] = 100 * (res.BINNED - res.ORACLE) / res.ORACLE
print("nu_hat (single fixed shape fitted):", round(nu_hat, 2))
print(res.round(5).to_string(), "\n")

# C2: FIXED-minus-BINNED edge by score decile (tau=0.01), test set
tau = 0.01
qF = tq(nu_hat, tau); edge_by_dec = []
for d in range(10):
    m = itst & (score_dec == d)
    qBd = np.quantile(z_v[itr & (score_dec == d)], tau)
    e = 100 * (pin(z_v[m] - qF, tau).mean() - pin(z_v[m] - qBd, tau).mean()) / pin(z_v[m] - qF, tau).mean()
    edge_by_dec.append((d + 1, round(e, 2), int(m.sum())))
print("edge of BINNED over FIXED by score decile (tau=1%): (decile, %edge, n)")
print(edge_by_dec, "\n")

# C1: Lemma-1 identity check, fat regime, tau=0.01
tau = 0.01; nu_true = NU_FAT
qtrue, qmis = tq(nu_true, tau), tq(nu_hat, tau)
s = np.sqrt((nu_true - 2) / nu_true)
F = lambda u: stats.t.cdf(u / s, nu_true)
from scipy.integrate import quad
identity = quad(lambda u: F(u) - tau, qtrue, qmis)[0]
zf = trvs(nu_true, 2_000_000)
emp_regret = pin(zf - qmis, tau).mean() - pin(zf - qtrue, tau).mean()
print(f"C1 Lemma-1 identity: integral={identity:.6f}  MC regret={emp_regret:.6f}")

print("\nC3 coverage at stated levels (test):")
for tau in TAUS:
    print(f" tau={tau}: fixed={cov[tau]['fixed']:.4f} binned={cov[tau]['binned']:.4f} binned+conformal={cov[tau]['binned_conf']:.4f}")
