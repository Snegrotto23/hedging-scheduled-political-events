"""Construye los CSV de inputs por evento y las fichas en markdown a partir de data_*.py."""
import csv
import math
import sys

import numpy as np
from scipy.stats import norm

from data_events import EVENTS, POLLS, UMBRAL_SIGNO, MISS_1T
from data_probs import P
from data_scen import S
from devig import proportional, shin

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
SIGMA = 4.0


def f(x, d=4):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return ""
    return f"{x:.{d}f}"


EV = {e["id"]: e for e in EVENTS}

# ------------------------------------------------------------ encuestas
poll_rows, margins = [], {}
for (ev, who, campo, pub, n, b, m, base, inc, ver, nota) in POLLS:
    modo = EV[ev]["modo"]
    if modo == "dos_vias":
        mg = (b - m) / (b + m) * 100
    elif modo == "diferencia":
        mg = b - m
    elif modo == "umbral":
        mg = UMBRAL_SIGNO[ev] * (b - m)
    else:
        raise ValueError(ev)
    poll_rows.append(dict(event_id=ev, encuestadora=who, campo=campo, publicada=pub, n=n or "", bueno=b, malo=m,
                          base=base, modo=modo, margen_bueno_pp=f(mg, 2), incluida=inc, verificacion=ver, nota=nota))
    if inc:
        margins.setdefault(ev, []).append(mg)
poll_margin = {ev: float(np.mean(v)) for ev, v in margins.items()}
poll_n = {ev: len(v) for ev, v in margins.items()}

# ------------------------------------------------------------ error de 1ª vuelta
miss_rows, miss = [], {}
for ev, src, pm, real in MISS_1T:
    if isinstance(pm, str):
        pm = poll_margin[pm[1:]]
    err = abs(pm - real)
    miss.setdefault(ev, []).append(err)
    miss_rows.append(dict(event_id=ev, fuente=src, margen_encuestas=f(pm, 2), margen_real=f(real, 2), error_pp=f(err, 2)))
poll_miss = {ev: float(np.mean(v)) for ev, v in miss.items()}

# ------------------------------------------------------------ probabilidades
prob_rows, src_p = [], {}
for r in P:
    k, v, gi = r["kind"], r["vals"], r["good_idx"]
    over = pprop = pshin = z = None
    if k in ("odds", "price"):
        pi = np.array([1 / o for o in v]) if k == "odds" else np.array(v, float)
        over = pi.sum() - 1
        pp = proportional(pi)
        ps, z = shin(pi)
        pprop, pshin = float(pp[gi]), float(ps[gi])
        praw = float(pi[gi])
        pused = pshin
    elif k == "price1":
        praw = pused = float(v[0])
    elif k == "prob":
        praw = pused = float(v[0])
    elif k == "prob_range":
        praw = pused = float(np.mean(v))
    reason = []
    if not r["ex_ante"]:
        reason.append("posterior al corte")
    if r["binario"] != "exacto":
        reason.append(f"binario {r['binario']}")
    if not r["latest"]:
        reason.append("superada por cotización posterior de la misma fuente")
    if r["pre1T"]:
        reason.append("anterior a la 1ª vuelta")
    if r["verif"] not in ("si", "pdf"):
        reason.append(f"verificación: {r['verif']}")
    if not math.isfinite(pused):
        reason.append("sin precio")
    if "partidario" in r["tipo"] or "lectura del mercado" in r["contrato"]:
        reason.append("no es pronóstico independiente")
    en = int(not reason)
    if en:
        src_p.setdefault(r["ev"], []).append(pused)
    prob_rows.append(dict(
        event_id=r["ev"], fuente=r["fuente"], tipo=r["tipo"], contrato=r["contrato"], binario=r["binario"],
        fecha=r["fecha"], forma=k, valores=";".join(f"{x:g}" for x in v), resultados=";".join(r["labels"]),
        overround=f(over), p_bueno_bruto=f(praw), p_bueno_proporcional=f(pprop), p_bueno_shin=f(pshin),
        z_shin=f(z), p_bueno_usado=f(pused), ex_ante=r["ex_ante"], en_grilla=en, motivo_exclusion="; ".join(reason),
        verificacion=r["verif"], url=r["url"], nota=r["nota"]))

# ------------------------------------------------------------ eventos
ev_rows = []
for e in EVENTS:
    i = e["id"]
    pm = poll_margin.get(i)
    ms = poll_miss.get(i)
    pm = round(pm, 4) if pm is not None else None   # se guarda con 4 decimales: la grilla sale del valor guardado
    ms = round(ms, 4) if ms is not None else None
    pp = []
    if pm is not None:
        pp = [float(norm.cdf(pm / SIGMA)), float(norm.cdf(pm / max(SIGMA, ms if ms else SIGMA)))]
    ps = src_p.get(i, [])
    ps = [round(x, 6) for x in ps]
    allp = sorted(pp + ps)
    gmin = gmed = gmax = None
    if allp:
        gmin, gmed, gmax = allp[0], float(np.median(allp)), allp[-1]
    eleg = "si" if any(0.05 <= x <= 0.95 for x in allp) else "no"
    vs = [r["verificacion"] for r in prob_rows if r["event_id"] == i and r["en_grilla"]]
    ver = f"{sum(v == 'si' for v in vs)} de {len(vs)} fuentes de la grilla verificadas en la fuente original"
    ev_rows.append(dict(
        event_id=i, pais=e["pais"], ronda=e["ronda"], fecha_evento=e["fecha"], pre=e["pre"], post=e["post"],
        pre_us=e["pre_us"], post_us=e["post_us"], binario=e["binario"], bueno=e["bueno"], malo=e["malo"],
        modo_margen=e["modo"], poll_margin_good=f(pm, 4), n_encuestas=poll_n.get(i, 0), poll_miss_1T=f(ms, 4),
        p_poll_s4=f(pp[0]) if pp else "", p_poll_smiss=f(pp[1]) if pp else "",
        p_fuentes_good=";".join(f"{x:.6f}" for x in ps), n_fuentes_grilla=len(allp),
        p_grid_min=f(gmin), p_grid_med=f(gmed), p_grid_max=f(gmax), elegible_prob=eleg,
        prior_pre=e.get("prior_pre", ""), prior_post=e.get("prior_post", ""),
        prior_dp=f(e.get("prior_dp"), 2), prior_dp_fuente=e.get("prior_dp_fuente", ""), r=f(e.get("r"), 4),
        activos=e["activos"], resultado_bueno=e["resultado_bueno"], resultado=e["resultado"], mov_real=e["mov_real"],
        principal=e.get("principal", 1), verificacion=ver, notas=e["notas"]))


def write(name, rows):
    with open(f"{OUT}/{name}", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


write("event_inputs.csv", ev_rows)
write("event_probabilities.csv", prob_rows)
write("event_polls.csv", poll_rows)
write("event_poll_miss_1T.csv", miss_rows)
write("event_scenarios.csv", [dict(event_id=a, institucion=b, fecha=c, activo=d, escenario=e_, descripcion=g,
                                   mov_esperado_pct=f(h, 1), ex_ante=k, verificacion=l)
                              for (a, b, c, d, e_, g, h, k, l) in S])
print(f"{len(ev_rows)} eventos, {len(prob_rows)} fuentes, {len(poll_rows)} encuestas, {len(S)} escenarios")
for r in ev_rows:
    print(f"{r['event_id']:15s} margen {r['poll_margin_good']:>7s} miss {r['poll_miss_1T']:>6s} "
          f"grilla {r['p_grid_min']:>6s} {r['p_grid_med']:>6s} {r['p_grid_max']:>6s} n={r['n_fuentes_grilla']} eleg={r['elegible_prob']}")
