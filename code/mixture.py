"""
Extracción de la probabilidad de un evento binario desde una cadena de opciones,
con una mezcla de dos lognormales (Melick & Thomas 1997; Bahra 1997).

Bajo la medida forward (Q), al vencimiento T:
    S_T = F_j * exp(-0.5*s_j^2*T + s_j*sqrt(T)*Z),   j = up con prob p, down con prob 1-p
    restricción de martingala:  p*F_up + (1-p)*F_dn = F

Dos especificaciones:
  "binary"  : s_up = s_dn = s (difusión común + salto binario). Parámetros (p, g, s), g = ln(F_up/F_dn).
  "free"    : s_up, s_dn libres. Parámetros (p, g, s_up, s_dn).
Variante "pinned": g fijo desde información externa (event beta), se estima solo (p, s).

Precios en valor forward (sin descontar): C = E[(S_T-K)+], P = E[(K-S_T)+].
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq, least_squares
from scipy.stats import norm


# ---------- Black-76 ----------
def b76(F, K, s, T, cp):
    F, K = np.asarray(F, float), np.asarray(K, float)
    v = np.maximum(s * np.sqrt(T), 1e-12)
    d1 = (np.log(F / K) + 0.5 * v**2) / v
    d2 = d1 - v
    call = F * norm.cdf(d1) - K * norm.cdf(d2)
    put = K * norm.cdf(-d2) - F * norm.cdf(-d1)
    return np.where(np.asarray(cp) == "C", call, put)


def implied_vol(price, F, K, T, cp):
    intrinsic = max(F - K, 0) if cp == "C" else max(K - F, 0)
    if price <= intrinsic + 1e-10:
        return np.nan
    f = lambda s: float(b76(F, K, s, T, cp)) - price
    try:
        return brentq(f, 1e-4, 5.0)
    except ValueError:
        return np.nan


# ---------- mezcla ----------
def _legs(F, p, g):
    Fdn = F / (p * np.exp(g) + (1 - p))
    return Fdn * np.exp(g), Fdn


def mix_price(F, K, T, cp, p, g, s_up, s_dn):
    Fup, Fdn = _legs(F, p, g)
    return p * b76(Fup, K, s_up, T, cp) + (1 - p) * b76(Fdn, K, s_dn, T, cp)


@dataclass
class MixFit:
    spec: str
    p: float          # prob. del escenario "up" (bajo Q)
    g: float          # gap log entre escenarios
    s_up: float
    s_dn: float
    F: float
    T: float
    rmse_rel: float   # error relativo medio ponderado
    n: int
    cost: float

    @property
    def up_move(self):   # movimiento del forward en el escenario up, en %
        Fup, _ = _legs(self.F, self.p, self.g)
        return Fup / self.F - 1

    @property
    def dn_move(self):
        _, Fdn = _legs(self.F, self.p, self.g)
        return Fdn / self.F - 1

    def as_dict(self):
        return dict(spec=self.spec, p_up=self.p, gap=self.g, s_up=self.s_up, s_dn=self.s_dn,
                    up_move=self.up_move, dn_move=self.dn_move, rmse_rel=self.rmse_rel,
                    n=self.n, cost=self.cost)


def fit_mixture(K, price, cp, F, T, weights=None, spec="binary", g_fixed=None,
                n_starts=12, seed=0) -> MixFit:
    """
    Ajusta la mezcla a precios OTM. weights ~ 1/half-spread (o 1/precio si no hay spread).
    spec: 'binary' | 'free' | 'pinned' (requiere g_fixed).
    """
    K, price, cp = np.asarray(K, float), np.asarray(price, float), np.asarray(cp)
    w = np.ones_like(price) if weights is None else np.asarray(weights, float)
    rng = np.random.default_rng(seed)

    # parámetros naturales con cotas: p in [.01,.99], g in [0,.9], s in [.03,1.2]
    if spec == "binary":
        lo, hi = [0.01, 0.0, 0.03], [0.99, 0.9, 1.2]
    elif spec == "free":
        lo, hi = [0.01, 0.0, 0.03, 0.03], [0.99, 0.9, 1.2, 1.2]
    elif spec == "pinned":
        lo, hi = [0.01, 0.03], [0.99, 1.2]
    else:
        raise ValueError(spec)

    def unpack(x):
        if spec == "binary":
            return x[0], x[1], x[2], x[2]
        if spec == "free":
            return x[0], x[1], x[2], x[3]
        return x[0], g_fixed, x[1], x[1]

    def resid(x):
        p, g, su, sd = unpack(x)
        return (mix_price(F, K, T, cp, p, g, su, sd) - price) * w

    best = None
    for _ in range(n_starts):
        p0, g0, s0 = rng.uniform(0.1, 0.9), rng.uniform(0.03, 0.35), rng.uniform(0.10, 0.45)
        if spec == "binary":
            x0 = [p0, g0, s0]
        elif spec == "free":
            x0 = [p0, g0, s0, s0 * rng.uniform(0.7, 1.4)]
        else:
            x0 = [p0, s0]
        r = least_squares(resid, x0, bounds=(lo, hi), method="trf", max_nfev=4000)
        if best is None or r.cost < best.cost:
            best = r
    p, g, su, sd = unpack(best.x)
    model = mix_price(F, K, T, cp, p, g, su, sd)
    rel = np.sqrt(np.average(((model - price) / np.maximum(price, 1e-6)) ** 2))
    return MixFit(spec, p, g, su, sd, F, T, float(rel), len(K), float(best.cost))


def fit_single_lognormal(K, price, cp, F, T, weights=None) -> float:
    """Benchmark: una sola lognormal (vol plana). Devuelve el costo."""
    K, price, cp = np.asarray(K, float), np.asarray(price, float), np.asarray(cp)
    w = np.ones_like(price) if weights is None else np.asarray(weights, float)
    r = least_squares(lambda x: (b76(F, K, np.exp(x[0]), T, cp) - price) * w, [np.log(0.3)])
    return float(r.cost)


def mixture_density(fit: MixFit, x):
    """Densidad Q de S_T implícita en la mezcla."""
    Fup, Fdn = _legs(fit.F, fit.p, fit.g)
    def ln_pdf(F, s):
        v = s * np.sqrt(fit.T)
        mu = np.log(F) - 0.5 * v**2
        return np.exp(-(np.log(x) - mu) ** 2 / (2 * v**2)) / (x * v * np.sqrt(2 * np.pi))
    return fit.p * ln_pdf(Fup, fit.s_up) + (1 - fit.p) * ln_pdf(Fdn, fit.s_dn)


def implied_forward(chain, spot_px, T, r_guess):
    """
    Forward por paridad put-call: C - P = DF*(F - K) en strikes con ambos lados.
    Si no hay pares suficientes, usa spot*exp(r*T).
    """
    c = chain[chain.type == "C"].set_index("K")["mid"]
    p = chain[chain.type == "P"].set_index("K")["mid"]
    common = c.index.intersection(p.index)
    common = [k for k in common if 0.9 * spot_px <= k <= 1.1 * spot_px]
    if len(common) >= 3:
        Kc = np.array(common, float)
        y = (c.loc[common] - p.loc[common]).values
        A = np.vstack([np.ones_like(Kc), -Kc]).T       # y = DF*F - DF*K
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        DF = coef[1]
        if 0.8 < DF < 1.0:
            return coef[0] / DF, DF, "parity"
    DF = np.exp(-r_guess * T)
    return spot_px / DF, DF, "carry"
