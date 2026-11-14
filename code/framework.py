"""
Framework de cobertura de eventos binarios (elecciones en mercados emergentes) — versión 11/11/2026.
Una sola función, parametrizada por evento y activo. Solo usa información de la víspera (t0),
salvo el bloque de P&L real (marcado el día hábil siguiente al evento, t1).

REGLA PRINCIPAL (11/11/2026, tarde; decidida con Santiago después de ver EWZ 2026 = -19,8% sin cubrir con la regla v1):
 - Robustez = recargo de seguro: -VE_min (peor punto de la grilla p x método) <= 25% de la pérdida esperada evitada,
   (1 - p) x (P_malo con cobertura - d). Reemplaza VE_min >= -0,25 pp, que era un filtro de alfa en puntos fijos y se
   volvía obligatorio justo en los eventos grandes (EWZ 2026: rechazaba un collar con crédito que dejaba -4,0%).
 - Severidad de decisión = promedio de event beta y term structure cuando existen los dos (la robustez mira los dos).
 - Si u > |d| (el resultado malo es el favorito, p_bueno < 50%): los calls vendidos van >= S0 (1 + u), no se topea
   la suba; si con eso no hay estructura que pase, no se hace nada. Si u <= |d|: máxima protección, calls donde caigan.
 - Tope de caja 0,25% del nocional en todos los casos. Sin 1x2 (máximo una opción por unidad).
 - Alternativa reportada: piso de suba (P_bueno >= 50% de u) en todos los casos. Regla v1 reportada por protocolo.
 - Limitación conocida: si el malo es favorito pero severo (p. ej. p_bueno 45%, d -12%), la regla puede terminar en
   "no hacer nada" por el tope de caja. No ocurre en la muestra al 11/11.

CAMBIOS RESPECTO DE LA VERSIÓN DEL PILOTO (hash f210a4fd4e68)
 - Paso 4, vol base (regla del protocolo, "con semanales"): IV ATM de un vencimiento que vence ANTES del evento,
   medida el último día con >= 3 días hábiles a ese vencimiento (en una 2ª vuelta: después de la 1ª vuelta).
   Filtro: si esa IV > 1,5 x la vol realizada de los 20 días previos, se usa la realizada. Sin vencimiento previo:
   vol realizada de 20 días. Si tampoco hay historia de precios (ETFs con solo los días comprados), respaldo FUERA
   DE REGLA: vol forward entre el primer par de vencimientos posteriores al evento con varianza forward positiva
   (se marca en el registro). Si el día ideal de medición no está en los datos, se usa el último disponible y se marca.
 - Paso 6, regla de decisión (actualizada el 10/11/2026; mira la SEVERIDAD, no la probabilidad):
     a) Si |d| < 5% con p central y en toda la grilla: no hacer nada.
     b) Si no: entre put, put spread, collar y put spread collar (patas del paso 1, puts >= 0,8 S0, calls <= 1,25 S0,
        h en {0,5; 0,75; 1}), las que pasan dos filtros: costo neto de entrada <= 0,25% del nocional y valor esperado
        >= -0,25 pp en toda la grilla (p x método de severidad), y que reducen la pérdida del escenario malo frente
        a no cubrir. Entre esas, la que deja la menor pérdida en el escenario malo (pérdida = -min(P&L, 0), p central,
        severidad primaria, pago al vencimiento; redondeo a 0,1 pp); desempate: menor pérdida en estrés (1,5 d),
        después mayor resultado en el escenario bueno.
     c) Si ninguna pasa: no hacer nada y registrar "sin cobertura barata". Si no hay ningún put líquido en el rango:
        "sin opciones líquidas (criterio 3)".
   Achicar NO es opción: queda como comparación ("achicar equivalente" = la fracción de la posición que deja la
   misma pérdida en el escenario malo que la estructura elegida). Se descarta el límite duro de pérdida.
 - Se agrega el hedge de evento ingenuo (put comprado al ask con strike más cercano a 0,95 S0, h = 1) como benchmark.
 - Lado short: no se corre (robustez pendiente).

PASOS (protocolo)
 1. Datos: cadena de los vencimientos que cruzan el evento; spot por paridad; filtros de liquidez.
 2. Probabilidad del escenario bueno: grilla min / mediana / max de encuestas (Phi(margen / sigma), sigma en
    {4, max(4, error 1ª vuelta)}) y fuentes (mercados sin margen por Shin, consultoras, modelos).
 3. Severidad: event beta si |Δp| >= 0,15 (u - d = r_previo / Δp); si no, term structure
    (sigma_ev^2 = IV1^2 T1 - base^2 (T1 - 1/252); |d| = sigma_ev sqrt(p/(1-p)), u = sigma_ev sqrt((1-p)/p)).
 4. Vol base: ver arriba.
 5. Curva: spreads verticales y zonas robustas (comprado al ask, vendido al bid, toda la grilla).
 6. Decisión: ver arriba.
 7. Marcado en t1 con el mid de cada pata y spot por paridad.

INPUTS POR EVENTO: datos/event_inputs.csv, leído con codigo/event_inputs.py (load_events). Para ETFs y ADRs en
EE.UU.: us_dates=True y r = T-bill a 4 semanas (el CSV solo trae la tasa local de Brasil).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from mixture import b76, implied_vol

DF_ALL: pd.DataFrame | None = None      # lo fija el script que corre (COTAHIST o iVolatility adaptado)

# ---------------------------------------------------------------- parámetros congelados (tabla del protocolo)
STRESS_MULT = 1.5          # m
DP_MIN = 0.15              # umbral de Δp para event beta
D_MIN = 0.05               # |d| mínimo para cubrir (paso 6, regla del 10/11)
COST_MAX = 0.0025          # costo neto de entrada máximo (0,25% del nocional, valor del protocolo)
EV_TOL = 0.0025            # tolerancia de valor esperado (0,25 pp)
H = (0.5, 0.75, 1.0)       # cantidades por unidad de posición
PUT_MIN, CALL_MAX = 0.80, 1.25
ZONE_LO, ZONE_HI = 0.70, 1.30
VB_MIN_BD = 3              # días hábiles mínimos al vencimiento para medir la vol base
RV_CAP = 1.5               # filtro de calidad de la vol base
RV_N = 20
NAIVE_MNY = 0.95           # hedge ingenuo: put 5% fuera del dinero
P_MIN_GRID = 0.01          # la grilla de p se acota a [0,01; 0,99]
# Regla del 11/11/2026 (tarde), decidida con Santiago después de la corrida de EWZ 2026:
ROBUST_MODE = "recargo"    # "recargo": -VE_min <= THETA x pérdida esperada evitada; "ve_fijo": VE_min >= -EV_TOL (regla anterior)
THETA = 0.25               # recargo máximo del seguro (robustez: 0,10 y 0,50)
SEV_DECISION = "promedio"  # con event beta y term structure: escenarios = promedio de los dos; "primario" = regla anterior
CALL_FLOOR = "auto"        # "auto": si u > |d| (malo favorito) los calls vendidos van >= S0 (1 + u) y no se topea la suba;
                           # True: siempre; False: nunca (calls donde caigan)
KEEP_UP = 0.0              # piso al escenario bueno: P_bueno >= KEEP_UP x u central (0 = sin piso)
MAX_CALLS = 1              # calls vendidos por unidad de posición (2 = collar 1x2, deja un call descubierto)


# ---------------------------------------------------------------- datos
def bd(d0, d1):
    return int(np.busday_count(pd.Timestamp(d0).date(), pd.Timestamp(d1).date()))


def bdT(d0, d1):
    return bd(d0, d1) / 252


def _opts(d, root):
    return DF_ALL[(DF_ALL.DATA == pd.Timestamp(d)) & DF_ALL.TPMERC.isin(["070", "080"]) & DF_ALL.CODNEG.str.startswith(root)]


def chain(d, root, expiry):
    o = _opts(d, root)
    o = o[o.DATVEN == pd.Timestamp(expiry)].copy()
    o["type"] = o.TPMERC.map({"070": "C", "080": "P"})
    o["K"] = o.PREEXE
    o["quoted"] = (o.PREOFC > 0) & (o.PREOFV > 0) & (o.PREOFV >= o.PREOFC)
    o["bid"] = np.where(o.quoted, o.PREOFC, np.nan)
    o["ask"] = np.where(o.quoted, o.PREOFV, np.nan)
    o["mid"] = np.where(o.quoted, (o.PREOFC + o.PREOFV) / 2, o.PREULT)
    o = o.sort_values("TOTNEG", ascending=False).drop_duplicates(["type", "K"])
    return o[["type", "K", "bid", "ask", "mid", "quoted", "TOTNEG"]].sort_values(["type", "K"]).reset_index(drop=True)


def last_px(d, tk):
    s = DF_ALL[(DF_ALL.DATA == pd.Timestamp(d)) & (DF_ALL.TPMERC == "010") & (DF_ALL.CODNEG == tk)]
    return float(s.PREULT.iloc[0]) if len(s) else np.nan


def parity_spot(d, root, expiry, tk, r):
    """Spot por paridad: mediana de K + (C-P)/DF en pares cotizados a ±5% del último negocio; si hay < 2 pares,
    último negocio (marcado)."""
    ch = chain(d, root, expiry)
    S_hint = last_px(d, tk)
    c = ch[(ch.type == "C") & ch.quoted].set_index("K")
    p = ch[(ch.type == "P") & ch.quoted].set_index("K")
    j = c.join(p, lsuffix="_c", rsuffix="_p", how="inner")
    j = j[(j.index > 0.95 * S_hint) & (j.index < 1.05 * S_hint)]
    T = bdT(d, expiry)
    DF = np.exp(-r * T)
    # Con mids de cotizaciones muy anchas la paridad puede romperse (BOVA11 2/10/2026: 196,6 contra 190,0 de último
    # negocio y ~189,8 implícito por el Ibovespa). No se corrige (regla congelada): run() marca el caso si la paridad
    # difiere más de 2% del último negocio.
    if len(j) >= 2:
        F = float(np.median(j.index + (j.mid_c - j.mid_p) / DF))
        return F * DF, "paridad", S_hint
    return S_hint, "último negocio", S_hint


def atm_iv(d, root, expiry, S, r):
    ch = chain(d, root, expiry)
    T = bdT(d, expiry)
    if T <= 0:
        return np.nan
    F = S * np.exp(r * T)
    ivs = []
    for t in ["C", "P"]:
        x = ch[(ch.type == t) & ((ch.quoted) | (ch.TOTNEG >= 5))]
        if x.empty:
            continue
        row = x.iloc[(x.K - F).abs().argsort()[:1]].iloc[0]
        if abs(row.K / F - 1) > 0.05:
            continue
        ivs.append(implied_vol(row.mid * np.exp(r * T), F, row.K, T, t))
    ivs = [v for v in ivs if np.isfinite(v)]
    return float(np.mean(ivs)) if ivs else np.nan


def realized_vol(tk, before, n=RV_N):
    """Vol realizada anualizada de los n retornos diarios que terminan en el último cierre ANTERIOR a `before`.
    Huecos de datos (días hábiles faltantes) se normalizan por sqrt(días hábiles del retorno). Necesita >= 15."""
    s = DF_ALL[(DF_ALL.TPMERC == "010") & (DF_ALL.CODNEG == tk) & (DF_ALL.DATA < pd.Timestamp(before))]
    s = s.drop_duplicates("DATA").sort_values("DATA").tail(n + 1)
    if len(s) < 16:
        return np.nan, len(s) - 1 if len(s) else 0
    lr = np.log(s.PREULT.values[1:] / s.PREULT.values[:-1])
    gaps = np.array([max(bd(a, b), 1) for a, b in zip(s.DATA.values[:-1], s.DATA.values[1:])])
    z = lr / np.sqrt(gaps)
    return float(np.std(z, ddof=1) * np.sqrt(252)), len(z)


def vol_base(ev, root, tk, r, pre, ivs_post):
    """Regla del paso 4 (ver docstring). Devuelve (sigma_base, fuente, marcas)."""
    flags = []
    t_ev = pd.Timestamp(ev["fecha_evento"])
    lower = pd.Timestamp(ev["prior_post"]) if ev.get("prior_post") else pd.Timestamp("1900-01-01")
    prior_ev = pd.Timestamp(ev["prior_pre"]) + pd.Timedelta(days=2) if ev.get("prior_pre") else pd.Timestamp("1900-01-01")
    days = sorted(DF_ALL[(DF_ALL.DATA >= lower) & (DF_ALL.DATA <= pre) & DF_ALL.TPMERC.isin(["070", "080"])
                         & DF_ALL.CODNEG.str.startswith(root)].DATA.unique())
    cands = []
    all_x = set()
    for d in days:
        xs = sorted(pd.Timestamp(x) for x in _opts(d, root).DATVEN.dropna().unique())
        xs = [x for x in xs if prior_ev < x < t_ev]
        all_x.update(xs)
        for x in xs:
            if bd(d, x) >= VB_MIN_BD:
                cands.append((pd.Timestamp(d), x))
    # día ideal: el último día hábil con >= 3 días hábiles a algún vencimiento previo al evento (y <= t0)
    ideal = None
    for x in all_x:
        dd = pd.Timestamp(np.busday_offset(x.date(), -VB_MIN_BD, roll="backward"))
        dd = min(dd, pre)
        if dd >= lower and (ideal is None or dd > ideal):
            ideal = dd
    sig, src = np.nan, ""
    for d, x in sorted(cands, key=lambda z: (z[0], -z[1].value), reverse=True):
        Sd = parity_spot(d, root, x, tk, r)[0]
        v = atm_iv(d, root, x, Sd, r)
        if np.isfinite(v):
            sig, src = v, f"IV {x.date()} medida {d.date()}"
            if ideal is not None and d < ideal:
                flags.append(f"vol base medida {d.date()}; día ideal {ideal.date()} sin datos")
            rv, n = realized_vol(tk, d)
            if np.isfinite(rv) and sig > RV_CAP * rv:
                flags.append(f"IV {sig:.1%} > 1,5 x RV20 {rv:.1%}: se usa la realizada")
                sig, src = rv, f"vol realizada 20d antes de {d.date()} (filtro 1,5x)"
            elif not np.isfinite(rv):
                flags.append(f"sin RV20 para el filtro 1,5x ({n} retornos)")
            else:
                src += f"; RV20 {rv:.1%}"
            return sig, src, flags
    rv, n = realized_vol(tk, pre)
    if np.isfinite(rv):
        return rv, "vol realizada 20d (sin vencimiento previo cotizado)", flags + ["sin vencimiento previo al evento"]
    # respaldo fuera de regla: vol forward entre el primer par de vencimientos posteriores al evento con varianza
    # forward positiva (los dos vencimientos cruzan el evento; la forward entre ellos no lo contiene)
    for (xa, va), (xb, vb) in zip(ivs_post[:-1], ivs_post[1:]):
        Ta, Tb = bdT(pre, xa), bdT(pre, xb)
        fwd_var = (vb**2 * Tb - va**2 * Ta) / (Tb - Ta)
        if fwd_var > 0:
            flags.append("FUERA DE REGLA: sin vencimiento previo ni historia de precios; vol forward entre vencimientos")
            return np.sqrt(fwd_var), f"vol forward {xa.date()}-{xb.date()} (fuera de regla)", flags
    if len(ivs_post) > 1:
        flags.append("FUERA DE REGLA: sin vol base; se usa la IV del 2º vencimiento")
        return ivs_post[1][1], "IV del 2º vencimiento (fuera de regla)", flags
    raise ValueError("sin vol base: ni vencimiento previo, ni historia de precios, ni 2º vencimiento")


# ---------------------------------------------------------------- modelo
def scen_from_rule(p, sev):
    """(u, d) para un p dado según la severidad elegida por la regla."""
    if sev["method"].startswith("promedio"):
        a, b = (scen_from_rule(p, x) for x in sev["parts"])
        return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if sev["method"] == "event beta":
        spread = sev["spread"]
        return (1 - p) * spread, -p * spread
    s = sev["sigma_ev"]
    return s * np.sqrt((1 - p) / p), -s * np.sqrt(p / (1 - p))


def mix_value(S0, K, cp, T, p, u, d, sig, r):
    """Valor descontado bajo la mezcla de escenarios (forward = S0 e^{rT}, saltos con media cero)."""
    F = S0 * np.exp(r * T)
    return np.exp(-r * T) * (p * b76(F * (1 + u), K, sig, T, cp) + (1 - p) * b76(F * (1 + d), K, sig, T, cp))


def mix_prob_below(S0, K, T, p, u, d, sig, r):
    F = S0 * np.exp(r * T)

    def cdf(Fj):
        v = sig * np.sqrt(T)
        return norm.cdf((np.log(K / Fj) + 0.5 * v * v) / v)
    return p * cdf(F * (1 + u)) + (1 - p) * cdf(F * (1 + d))


def payoff(t, K, ST):
    return np.maximum(ST - K, 0) if t == "C" else np.maximum(K - ST, 0)


# ---------------------------------------------------------------- framework
def run(ev: dict, asset: dict, verbose=True):
    out = dict(flags=[])
    pre, post, r = pd.Timestamp(ev["pre"]), pd.Timestamp(ev["post"]), ev["r"]
    root, tk = asset["root"], asset["tk"]

    # PASO 1: vencimientos que cruzan el evento (primero con >= 2 días hábiles después de t1, y el siguiente)
    exps = sorted(pd.Timestamp(x) for x in _opts(pre, root).DATVEN.dropna().unique())
    exps = [x for x in exps if bd(post, x) >= 2]
    S0, s0src, S0_last = parity_spot(pre, root, exps[0], tk, r)
    if s0src != "paridad":
        out["flags"].append(f"spot t0: {s0src}")
    if abs(S0 / S0_last - 1) > 0.02:
        out["flags"].append(f"spot t0 por paridad difiere {S0 / S0_last - 1:+.1%} del último negocio")
    ivs = []
    for x in exps:
        iv = atm_iv(pre, root, x, S0, r)
        if np.isfinite(iv):
            ivs.append((x, iv))
        if len(ivs) == 5:
            break
    if not ivs:
        raise ValueError("sin IV ATM en los vencimientos que cruzan el evento (criterio 3)")
    (x1, iv1), (x2, iv2) = ivs[0], (ivs[1] if len(ivs) > 1 else (pd.NaT, np.nan))
    T1 = bdT(pre, x1)

    # PASO 4 (se necesita antes): vol base
    sig_base, base_src, vb_flags = vol_base(ev, root, tk, r, pre, ivs)
    if asset.get("vol_base_override") is not None:      # solo para sensibilidad, nunca en la corrida principal
        sig_base, base_src = asset["vol_base_override"], "SENSIBILIDAD (vol base fijada a mano)"
        vb_flags = vb_flags + ["SENSIBILIDAD: vol base fijada a mano"]
    out["flags"] += vb_flags
    sig_ev = np.sqrt(max(iv1**2 * T1 - sig_base**2 * (T1 - 1 / 252), 0.0))
    out["curva"] = dict(spot=S0, spot_fuente=s0src, ultimo_negocio=S0_last, venc_evento=x1.date(), iv_evento=iv1,
                        venc_siguiente=x2.date(), iv_siguiente=iv2, vol_base=sig_base, vol_base_fuente=base_src,
                        salto_implicito=sig_ev)

    # PASO 2: probabilidad del escenario bueno
    p_poll = ([norm.cdf(ev["poll_margin_good"] / s) for s in (4.0, max(4.0, ev.get("poll_miss_1T", 4.0)))]
              if ev.get("poll_margin_good") is not None else [])
    p_pm = list(ev.get("p_pm_good", []))
    p_all = sorted([x for x in p_poll + p_pm if np.isfinite(x)])
    p_grid = sorted(set([round(min(p_all), 3), round(float(np.median(p_all)), 3), round(max(p_all), 3)]))
    # p acotada a [0,01; 0,99] (11/11/2026): con p = 0,999 el term structure daba |d| > 100% (Brasil 2018-2T)
    p_grid = sorted(set(float(min(max(p, P_MIN_GRID), 1 - P_MIN_GRID)) for p in p_grid))
    out["probabilidad"] = dict(encuestas=p_poll, fuentes=p_pm, grilla=p_grid)

    # PASO 3: severidad (regla fija)
    sev_ts = dict(method="term structure", sigma_ev=sig_ev)
    sev_eb = None
    if ev.get("prior_dp") is not None and abs(ev["prior_dp"]) >= DP_MIN:
        ext = asset.get("prior_ret", {}).get(ev.get("event_id"))
        if ext is not None:
            r_prior, src_prior = ext["ret"], ext["fuente"]
            out["flags"].append(f"r_previo externo: {src_prior}")
        else:
            r_prior = last_px(ev["prior_post"], tk) / last_px(ev["prior_pre"], tk) - 1
            src_prior = "datos"
        if np.isfinite(r_prior):
            sev_eb = dict(method="event beta", spread=r_prior / ev["prior_dp"], r_prior=r_prior, fuente=src_prior)
        else:
            out["flags"].append("event beta aplicable pero sin precios de la 1ª vuelta: se usa term structure")
    if sev_eb and SEV_DECISION == "promedio":
        sev = dict(method="promedio (event beta y term structure)", parts=[sev_eb, sev_ts])
        sevs = [sev_eb, sev_ts]          # la robustez se mide en los dos extremos
    else:
        sev = sev_eb if sev_eb else sev_ts
        sevs = [sev] + ([sev_ts] if sev_eb else [])
    out["severidad"] = dict(primaria=sev["method"],
                            event_beta=None if not sev_eb else dict(r_previo=sev_eb["r_prior"], dp=ev["prior_dp"],
                                                                     distancia=sev_eb["spread"], fuente=sev_eb["fuente"]),
                            term_structure=dict(salto_sd=sig_ev),
                            escenarios={p: scen_from_rule(p, sev) for p in p_grid},
                            escenarios_alt={p: scen_from_rule(p, sev_ts) for p in p_grid} if sev_eb else None,
                            escenarios_eb={p: scen_from_rule(p, sev_eb) for p in p_grid} if sev_eb else None)
    p_c = p_grid[len(p_grid) // 2]
    u_c, d_c = scen_from_rule(p_c, sev)

    # PASO 5a: spreads verticales (probabilidad que cobra el mercado) vs escenarios
    ch = chain(pre, root, x1)
    ch_q = ch[ch.quoted]
    rows = []
    tight = ch_q[((ch_q.ask - ch_q.bid) <= 0.20 * ch_q.mid + 0.02) & (ch_q.TOTNEG >= 5)]
    DFe = np.exp(-r * T1)
    for t, level in [("P", S0 * (1 + d_c)), ("P", S0 * (1 + d_c / 2)), ("C", S0 * (1 + u_c))]:
        x = tight[tight.type == t].sort_values("K")
        lo, hi = x[x.K <= level - 0.01 * S0], x[x.K >= level + 0.01 * S0]
        if lo.empty or hi.empty:
            continue
        k1, k2 = float(lo.K.iloc[-1]), float(hi.K.iloc[0])
        v1, v2 = float(x[x.K == k1].mid.iloc[0]), float(x[x.K == k2].mid.iloc[0])
        kbar = (k1 + k2) / 2
        pb = float(mix_prob_below(S0, kbar, T1, p_c, u_c, d_c, sig_base, r))
        if t == "P":
            rows.append(dict(rango=f"< {kbar:.2f} ({kbar / S0 - 1:+.1%})", mercado=(v2 - v1) / (k2 - k1) / DFe, escenarios=pb))
        else:
            rows.append(dict(rango=f"> {kbar:.2f} ({kbar / S0 - 1:+.1%})", mercado=(v1 - v2) / (k2 - k1) / DFe, escenarios=1 - pb))
    out["spreads"] = pd.DataFrame(rows)

    # PASO 5c: zonas robustas (opciones líquidas del paso 1, OTM, 0,7-1,3 S0)
    liq = ch_q[(ch_q.TOTNEG >= 20) & ((ch_q.ask - ch_q.bid) <= 0.15 * ch_q.mid + 0.03)]
    liq = liq[((liq.type == "P") & (liq.K < S0) & (liq.K >= ZONE_LO * S0)) |
              ((liq.type == "C") & (liq.K > S0) & (liq.K <= ZONE_HI * S0))].reset_index(drop=True)
    out["n_liquidas"] = dict(puts=int((liq.type == "P").sum()), calls=int((liq.type == "C").sum()),
                             cotizadas=int(len(ch_q)))
    combos = [(p, s_) for s_ in sevs for p in p_grid]
    zr = []
    for _, o in liq.iterrows():
        vals = [float(mix_value(S0, o.K, o.type, T1, p, *scen_from_rule(p, s_), sig_base, r)) for p, s_ in combos]
        buy = [o.ask / v if v > 1e-6 else np.inf for v in vals]
        sell = [o.bid / v if v > 1e-6 else np.inf for v in vals]
        verdict = "BARATO" if max(buy) < 1 else ("CARO" if min(sell) > 1 else "depende")
        zr.append(dict(tipo=o.type, K=o.K, mny=o.K / S0 - 1, bid=o.bid, ask=o.ask, compra_min=min(buy),
                       compra_max=max(buy), venta_min=min(sell), venta_max=max(sell), veredicto=verdict))
    out["zonas"] = pd.DataFrame(zr, columns=["tipo", "K", "mny", "bid", "ask", "compra_min", "compra_max",
                                             "venta_min", "venta_max", "veredicto"]).sort_values(["tipo", "K"])

    # PASO 7 (datos de t1): spot y mids del día después
    post_ch = chain(post, root, x1).set_index(["type", "K"])
    S1, s1src, S1_last = parity_spot(post, root, x1, tk, r)
    if s1src != "paridad":
        out["flags"].append(f"spot t1: {s1src}")
    if abs(S1 / S1_last - 1) > 0.02:
        out["flags"].append(f"spot t1 por paridad difiere {S1 / S1_last - 1:+.1%} del último negocio")
    ret = S1 / S0 - 1
    out["real"] = dict(spot_post=S1, fuente=s1src, ultimo_negocio_post=S1_last, retorno=ret)
    growth = np.exp(r * T1)

    # PASO 6: decisión
    d_grid = [scen_from_rule(p, sev)[1] for p in p_grid]
    small = all(abs(d) < D_MIN for d in d_grid)
    bad, stress, good = S0 * (1 + d_c), S0 * (1 + STRESS_MULT * d_c), S0 * (1 + u_c)
    stress_up = S0 * (1 + STRESS_MULT * u_c)

    legs = liq[((liq.type == "P") & (liq.K >= PUT_MIN * S0)) | ((liq.type == "C") & (liq.K <= CALL_MAX * S0))].copy()
    legs = legs.reset_index(drop=True)

    def leg_stats(t, K, side, px):
        """Métricas por unidad de una pata (en fracción de S0), side = +1 comprada (al ask), -1 vendida (al bid)."""
        e = [float(mix_value(S0, K, t, T1, p, *scen_from_rule(p, s_), sig_base, r)) * growth for p, s_ in combos]
        e_c = float(mix_value(S0, K, t, T1, p_c, u_c, d_c, sig_base, r)) * growth
        try:
            m = float(post_ch.loc[(t, K), "mid"])
        except KeyError:
            m = np.nan
        f = side / S0
        return dict(cost=f * px, ev_grid=np.array([f * (x - px * growth) for x in e]), ev_c=f * (e_c - px * growth),
                    bad=f * (payoff(t, K, bad) - px * growth), stress=f * (payoff(t, K, stress) - px * growth),
                    good=f * (payoff(t, K, good) - px * growth), up=f * (payoff(t, K, stress_up) - px * growth),
                    real=f * (m - px))

    stats = {}
    for i, o in legs.iterrows():
        stats[(i, +1)] = leg_stats(o.type, o.K, +1, o.ask)
        stats[(i, -1)] = leg_stats(o.type, o.K, -1, o.bid)
    P_idx = [i for i in legs.index if legs.type[i] == "P"]
    floor_on = CALL_FLOOR is True or (CALL_FLOOR == "auto" and u_c > abs(d_c))
    out["call_floor"] = floor_on
    C_idx = [i for i in legs.index if legs.type[i] == "C" and (not floor_on or legs.K[i] >= good - 1e-9)]

    structs = []
    for i in P_idx:
        structs.append(("put", [(i, +1)]))
        for j in P_idx:
            if legs.K[j] < legs.K[i]:
                structs.append(("put spread", [(i, +1), (j, -1)]))
        for k in C_idx:
            if legs.K[k] > legs.K[i]:
                for nc in range(1, MAX_CALLS + 1):
                    tag = "" if nc == 1 else f" 1x{nc}"
                    structs.append(("collar" + tag, [(i, +1)] + [(k, -1)] * nc))
                    for j in P_idx:
                        if legs.K[j] < legs.K[i]:
                            structs.append(("put spread collar" + tag, [(i, +1), (j, -1)] + [(k, -1)] * nc))

    def describe(fam, lg, h):
        from collections import Counter
        cnt = Counter(lg)
        return f"{h:g} x (" + ", ".join(f"{'+' if s > 0 else '-'}{'' if n == 1 else str(n)}{legs.type[i]}{legs.K[i]:g}"
                                        for (i, s), n in cnt.items()) + ")"

    cand = []
    for fam, lg in structs:
        agg = {k: sum(stats[x][k] for x in lg) for k in ["cost", "ev_c", "bad", "stress", "good", "up", "real"]}
        evg = sum(stats[x]["ev_grid"] for x in lg)
        for h in H:
            cand.append(dict(familia=fam, patas=describe(fam, lg, h), h=h, costo=h * agg["cost"],
                             ve=h * agg["ev_c"], ve_min=h * float(evg.min()), P_malo=d_c + h * agg["bad"],
                             P_estres=STRESS_MULT * d_c + h * agg["stress"], P_bueno=u_c + h * agg["good"],
                             P_alza_estres=STRESS_MULT * u_c + h * agg["up"],
                             P_real=ret + h * agg["real"]))
    C = pd.DataFrame(cand)
    if len(C):
        C["pasa_costo"] = C.costo <= COST_MAX + 1e-12
        if ROBUST_MODE == "recargo":
            # seguro: el costo esperado en el peor punto de la grilla no supera THETA x la pérdida esperada evitada
            C["perdida_evitada_esp"] = (1 - p_c) * (C.P_malo - d_c)
            C["pasa_robustez"] = -C.ve_min <= THETA * C.perdida_evitada_esp + 1e-12
        else:
            C["pasa_robustez"] = C.ve_min >= -EV_TOL - 1e-12
        C["pasa"] = C.pasa_costo & C.pasa_robustez
        # pérdida = -min(P, 0): una estructura no "reduce la pérdida" por debajo de cero
        C["_k1"], C["_k2"], C["_k3"] = C.P_malo.clip(upper=0).round(3), C.P_estres.clip(upper=0).round(3), C.P_bueno.round(4)
    out["candidatos"] = C

    def best(df):
        if df is None or not len(df):
            return None
        return df.sort_values(["_k1", "_k2", "_k3"], ascending=False).iloc[0].to_dict()

    # además, la estructura tiene que reducir la pérdida del escenario malo (P_malo > sin cubrir)
    if len(C):
        C["reduce"] = (C.P_malo > d_c + 1e-9) & (C.P_bueno >= KEEP_UP * u_c - 1e-9)
    ok = C[C.pasa & C.reduce] if len(C) else C
    chosen = best(ok)
    if small:
        decision, motivo = "no hacer nada", f"|d| < {D_MIN:.0%} en toda la grilla"
    elif not (legs.type == "P").any():
        decision, motivo = "no hacer nada", "sin opciones líquidas (criterio 3 del paso 0)"
    elif chosen is None:
        decision, motivo = "no hacer nada", "sin cobertura barata"
    else:
        decision, motivo = chosen["familia"], "menor pérdida en el escenario malo entre las que pasan costo y recargo"
    if decision == "no hacer nada":
        chosen = None
    out["decision"] = dict(decision=decision, motivo=motivo, elegida=chosen,
                           d_grilla=d_grid)

    # comparaciones
    comp = [dict(alternativa="sin cubrir", patas="—", costo=0.0, ve=0.0, ve_min=0.0, P_malo=d_c,
                 P_estres=STRESS_MULT * d_c, P_bueno=u_c, P_alza_estres=STRESS_MULT * u_c, P_real=ret)]
    puts_any = ch_q[(ch_q.type == "P")]
    pool = legs[legs.type == "P"] if (legs.type == "P").any() else puts_any
    if len(pool):
        o = pool.iloc[(pool.K - NAIVE_MNY * S0).abs().argsort()[:1]].iloc[0]
        s_ = leg_stats("P", o.K, +1, o.ask)
        comp.append(dict(alternativa="hedge ingenuo (put ~5% OTM)", patas=f"1 x (+P{o.K:g})" + ("" if len(legs) and (legs.type == "P").any() else " [no líquido]"),
                         costo=s_["cost"], ve=s_["ev_c"], ve_min=float(s_["ev_grid"].min()), P_malo=d_c + s_["bad"],
                         P_estres=STRESS_MULT * d_c + s_["stress"], P_bueno=u_c + s_["good"],
                         P_alza_estres=STRESS_MULT * u_c + s_["up"], P_real=ret + s_["real"]))
    fams = ["put", "put spread", "collar", "put spread collar"] + (
        [f"collar 1x{n}" for n in range(2, MAX_CALLS + 1)] + [f"put spread collar 1x{n}" for n in range(2, MAX_CALLS + 1)])
    for fam in fams:
        b = best(ok[ok.familia == fam]) if len(C) else None
        comp.append(dict(alternativa=f"mejor {fam}", patas=b["patas"] if b else "ninguna pasa costo y robustez",
                         **({k: b[k] for k in ["costo", "ve", "ve_min", "P_malo", "P_estres", "P_bueno", "P_alza_estres", "P_real"]} if b else {})))
    ref = chosen if chosen is not None else None
    if ref is not None:
        hA = min(max(ref["P_malo"] / d_c, 0.0), 1.0) if d_c < 0 else 1.0
        comp.append(dict(alternativa="achicar equivalente (comparación)", patas=f"queda {hA:.0%} de la posición",
                         costo=0.0, ve=0.0, ve_min=0.0, P_malo=ref["P_malo"], P_estres=hA * STRESS_MULT * d_c,
                         P_bueno=hA * u_c, P_alza_estres=hA * STRESS_MULT * u_c, P_real=hA * ret))
    out["comparacion"] = pd.DataFrame(comp)
    prot = chosen["P_real"] if (decision not in ("no hacer nada",)) else ret
    out["registro"] = dict(evento=ev.get("event_id"), activo=tk, t0=pre.date(), t1=post.date(), p_central=p_c, u=u_c,
                           d=d_c, metodo=sev["method"], decision=decision, motivo=motivo,
                           patas=chosen["patas"] if decision != "no hacer nada" else "—",
                           costo=chosen["costo"] if decision != "no hacer nada" else 0.0,
                           P_malo_protocolo=chosen["P_malo"] if decision != "no hacer nada" else d_c,
                           P_bueno_protocolo=chosen["P_bueno"] if decision != "no hacer nada" else u_c,
                           retorno_real=ret, P_real_protocolo=prot,
                           P_real_ingenuo=comp[1]["P_real"] if len(comp) > 1 and comp[1]["alternativa"].startswith("hedge") else np.nan,
                           resultado="bueno" if ev.get("resultado_bueno") == 1 else "malo",
                           cubrio=decision != "no hacer nada", marcas="; ".join(out["flags"]))
    if verbose:
        report(ev, asset, out)
    return out


def report(ev, asset, o):
    pd.set_option("display.width", 240)
    pd.set_option("display.max_colwidth", 60)
    pct = lambda x: f"{x:+.1%}"
    print(f"\n{'=' * 110}\n{ev['name']} · {asset['tk']}  (víspera {ev['pre']}, marcado {ev['post']})\n{'=' * 110}")
    c = o["curva"]
    print(f"Spot {c['spot']:.2f} ({c['spot_fuente']}; último {c['ultimo_negocio']:.2f}) | IV {c['venc_evento']} "
          f"{c['iv_evento']:.1%} | IV {c['venc_siguiente']} {c['iv_siguiente']:.1%} | vol base {c['vol_base']:.1%} "
          f"({c['vol_base_fuente']}) | salto implícito (1 sd) {c['salto_implicito']:.1%}")
    n = o["n_liquidas"]
    print(f"Opciones del vencimiento del evento: {n['cotizadas']} cotizadas; líquidas OTM 0,7-1,3 S0: {n['puts']} puts, {n['calls']} calls")
    pr = o["probabilidad"]
    print(f"P(bueno): encuestas {', '.join(f'{x:.0%}' for x in pr['encuestas']) or 'sin dato'} | fuentes "
          f"{', '.join(f'{x:.0%}' for x in pr['fuentes']) or 'sin dato'} | grilla {[round(x, 3) for x in pr['grilla']]}")
    s = o["severidad"]
    if s["event_beta"]:
        eb = s["event_beta"]
        print(f"Event beta: r_previo {eb['r_previo']:+.1%} ({eb['fuente']}) / Δp {eb['dp']:.2f} = u - d {eb['distancia']:.1%}")
    print(f"Severidad primaria: {s['primaria']}")
    for p, (u, d) in s["escenarios"].items():
        alt = (f" | event beta: u {pct(s['escenarios_eb'][p][0])}, d {pct(s['escenarios_eb'][p][1])}"
               f" | term structure: u {pct(s['escenarios_alt'][p][0])}, d {pct(s['escenarios_alt'][p][1])}") if s["escenarios_alt"] else ""
        print(f"   p={p:.3f}: u {pct(u)}, d {pct(d)}{alt}")
    if len(o["spreads"]):
        print("\nPaso 5a · spreads verticales: mercado vs escenarios (p central)")
        print(o["spreads"].round(3).to_string(index=False))
    Z = o["zonas"]
    print("\nPaso 5c · zonas (comprado al ask / vendido al bid, toda la grilla):")
    for t in ["P", "C"]:
        z = Z[Z.tipo == t]
        print(f"   {t}: BARATO {z[z.veredicto == 'BARATO'].K.tolist()} | CARO {z[z.veredicto == 'CARO'].K.tolist()} | "
              f"depende {len(z[z.veredicto == 'depende'])}")
    dd = o["decision"]
    C = o["candidatos"]
    npass = int(C.pasa.sum()) if len(C) else 0
    print(f"\nPaso 6 · |d| en la grilla {[f'{x:+.1%}' for x in dd['d_grilla']]}; candidatos {len(C)}, pasan costo y recargo {npass}"
          f" (robustez {ROBUST_MODE}{' ' + format(THETA, '.0%') if ROBUST_MODE == 'recargo' else ''}; severidad {SEV_DECISION};"
          f" suba sin topear {o.get('call_floor')}; piso de suba {KEEP_UP:.0%})")
    print(f"   DECISIÓN: {dd['decision'].upper()} ({dd['motivo']})")
    print(f"   real: {pct(o['real']['retorno'])} (spot t1 {o['real']['spot_post']:.2f}, {o['real']['fuente']})")
    cols = ["alternativa", "patas", "costo", "ve", "ve_min", "P_malo", "P_estres", "P_bueno", "P_alza_estres", "P_real"]
    print(o["comparacion"][cols].round(4).to_string(index=False))
    if o["flags"]:
        print("   Marcas: " + " | ".join(o["flags"]))
