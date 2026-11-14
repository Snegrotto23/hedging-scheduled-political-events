"""
Cargador de inputs por evento para framework.py.

Lee datos/event_inputs.csv (una fila por evento) y devuelve diccionarios con el mismo formato que EVENTS en
framework.py: name, pre, post, r, p_pm_good, poll_margin_good, poll_miss_1T, prior_pre, prior_post, prior_dp.
p_pm_good = todas las fuentes no-encuesta que entran a la grilla (mercados, casas sin margen por Shin, consultoras, modelos);
framework.run arma la grilla con ellas más las dos p de encuestas, igual que en event_inputs.csv (p_grid_min/med/max).

Uso:
    from event_inputs import load_events
    EVENTS = load_events("datos/event_inputs.csv", only_eligible=True)
    run(EVENTS["BR-2026-2T"], ASSETS["BOVA11"])
Para activos listados en EE.UU. (EWZ, ECH, EC, CIB, GXG, TUR, EWW, INDA) pasar us_dates=True: usa pre_us/post_us.

11/11/2026: se agregan event_id y fecha_evento al diccionario (la regla de vol base del paso 4 necesita la fecha
del evento para saber qué vencimientos vencen antes). Con us_dates=True, prior_pre/prior_post quedan iguales
(las fechas de la 1ª vuelta en EE.UU. coinciden con las locales en todos los eventos con event beta).
"""
from __future__ import annotations

import csv


def _num(x):
    return float(x) if x not in ("", None) else None


def load_events(path="datos/event_inputs.csv", only_eligible=False, only_main=True, us_dates=False, r_default=None):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if only_eligible and row["elegible_prob"] != "si":
                continue
            if only_main and row["principal"] != "1":
                continue
            pre, post = (row["pre_us"], row["post_us"]) if us_dates else (row["pre"], row["post"])
            r = _num(row["r"])
            ev = dict(
                event_id=row["event_id"], fecha_evento=row["fecha_evento"],
                name=f"{row['pais']} {row['fecha_evento'][:4]} · {row['ronda']} (bueno = {row['bueno']})",
                pre=pre, post=post, r=r if r is not None else r_default,
                p_pm_good=[float(x) for x in row["p_fuentes_good"].split(";") if x],
                poll_margin_good=_num(row["poll_margin_good"]),
                poll_miss_1T=_num(row["poll_miss_1T"]) or 4.0,
                p_grid=[_num(row["p_grid_min"]), _num(row["p_grid_med"]), _num(row["p_grid_max"])],
                binario=row["binario"], bueno=row["bueno"], malo=row["malo"], activos=row["activos"].split(";"),
                resultado_bueno=int(row["resultado_bueno"]),
            )
            if row["prior_pre"]:
                ev.update(prior_pre=row["prior_pre"], prior_post=row["prior_post"], prior_dp=_num(row["prior_dp"]))
            out[row["event_id"]] = ev
    return out


if __name__ == "__main__":
    import sys
    E = load_events(sys.argv[1] if len(sys.argv) > 1 else "datos/event_inputs.csv")
    for k, v in E.items():
        g = v["p_grid"]
        print(f"{k:12s} pre {v['pre']} post {v['post']} margen {v['poll_margin_good']} miss {v['poll_miss_1T']} "
              f"fuentes {len(v['p_pm_good'])} grilla {g} r {v['r']}")
