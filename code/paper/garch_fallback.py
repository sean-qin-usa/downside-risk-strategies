# garch_fallback.py -- minimal GARCH(1,1)-t QML used ONLY when the arch package is absent (sandbox self-tests).
# The Windows runs always use arch. exec()-ed into the job namespace; defines arch_model(y, **kw).fit(**kw).params.
import math, numpy as np
from scipy import stats, optimize
class _Res:
    def __init__(s,p): s.params=p
def _garch_t_fit(y):
    y=np.asarray(y,float); n=len(y); v0=np.var(y)
    def nll(th):
        mu,lom,la,lb,lnu=th; om=math.exp(lom); a=1/(1+math.exp(-la)); b=(1-a)/(1+math.exp(-lb)); nu=2.05+math.exp(lnu)
        e=y-mu; s2=np.empty(n); s2[0]=v0
        for k in range(1,n): s2[k]=om+a*e[k-1]**2+b*s2[k-1]
        sc=math.sqrt(nu/(nu-2))                     # standardized-t: unit variance
        zt=e/np.sqrt(s2)*sc
        ll=stats.t.logpdf(zt,nu)+math.log(sc)-0.5*np.log(s2)
        return -float(np.sum(ll)) if np.isfinite(ll).all() else 1e12
    x0=[float(np.mean(y)),math.log(0.05*v0),math.log(0.1/0.9),math.log(0.9/0.1),math.log(6-2.05)]
    r=optimize.minimize(nll,x0,method='Nelder-Mead',options={'maxiter':4000,'xatol':1e-6,'fatol':1e-6})
    mu,lom,la,lb,lnu=r.x; a=1/(1+math.exp(-la)); b=(1-a)/(1+math.exp(-lb))
    return _Res({'mu':mu,'omega':math.exp(lom),'alpha[1]':a,'beta[1]':b,'nu':2.05+math.exp(lnu)})
class _AM:
    def __init__(s,y,**k): s.y=y
    def fit(s,**k): return _garch_t_fit(s.y)
def arch_model(y,**k): return _AM(y)
