"""Genera claude/fichas-eventos.md a partir de los CSV de datos/."""
import csv
import sys
from collections import defaultdict

D = sys.argv[1]
rd = lambda n: list(csv.DictReader(open(f"{D}/{n}", encoding="utf-8")))
EV, PR, PO, MI, SC = (rd("event_inputs.csv"), rd("event_probabilities.csv"), rd("event_polls.csv"),
                      rd("event_poll_miss_1T.csv"), rd("event_scenarios.csv"))
by = lambda rows: (lambda d: [d[r["event_id"]].append(r) for r in rows] and d)(defaultdict(list))
PRb, POb, MIb, SCb = by(PR), by(PO), by(MI), by(SC)
pct = lambda x: f"{float(x):.1%}" if x not in ("", None) else "—"

L = ["# Fichas por evento: inputs ex ante (paso 0 y paso 2)", "",
     "Generado el 2026-11-12 (Argentina agregada; resto sin cambios desde el 11/11) desde `datos/event_*.csv` (fuente de verdad: los CSV; esto es la vista legible).",
     "Probabilidades = del escenario **bueno** (pro-mercado). Margen de cuotas: proporcional y Shin; la grilla usa Shin.",
     "Grilla = min / mediana / max de {p encuestas con σ=4, p encuestas con σ=max(4, error 1ª vuelta)} ∪ fuentes en grilla "
     "(misma regla que `framework.py`).",
     "Verificación: **si** = confirmado contra la fuente en esta sesión; **pdf** = como lo reporta Perplexity, fuente no accesible; "
     "**no/conflicto** = fuera de la grilla.", "",
     "**Regla del binario (pre-registro, 11/11/2026).** Para todos: información al corte, resoluble con información pública el día "
     "del marcado, bueno/malo fijado por las notas ex ante sobre el activo cubierto (en la moneda del inversor) y nunca revisado, "
     "alguna fuente en 5-95%. 2ª vuelta y plebiscito: quién gana. Legislativa: el umbral al que las notas asocian el movimiento y que "
     "se resuelve al día siguiente. 1ª vuelta: del menú {gana en 1ª, quién termina primero, cupo disputado de la 2ª}, el binario al que "
     "las notas ex ante asocian el mayor movimiento con cifras entre los que tienen fuente en 5-95%; sin cifras, el de mayor p(1-p); "
     "empate, el que define el par de la 2ª. Los binarios descartados quedan con sufijo -ROB (robustez, principal = 0).", "",
     "**Argentina (AR-*, agregada el 12/11/2026, fuera de muestra) con tres extensiones a confirmar:** (a) la PASO o el evento "
     "previo del ciclo hace de 1ª vuelta para el error de encuestas (σ de la 1ª vuelta y de la legislativa); (b) PASO y provincial "
     "se tratan como legislativa: umbral de votos que citan las notas, el de mayor movimiento con cifras entre los que tienen fuente "
     "en 5-95%; (c) un binario del menú al que las notas no le fijan signo sale del menú.", "",
     "## Resumen", "",
     "| Evento | Binario (bueno) | Margen enc. (pp) | Error 1ª v. | Grilla min / med / max | Fuentes | Elegible | Resultado |",
     "|---|---|---|---|---|---|---|---|"]
for e in EV:
    L.append(f"| {e['event_id']} | {e['bueno']} | {e['poll_margin_good'] or '—'} | {e['poll_miss_1T'] or '—'} | "
             f"{pct(e['p_grid_min'])} / {pct(e['p_grid_med'])} / {pct(e['p_grid_max'])} | {e['n_fuentes_grilla']} | "
             f"{e['elegible_prob']} | {'bueno' if e['resultado_bueno'] == '1' else 'malo'} |")
L.append("")
for e in EV:
    i = e["event_id"]
    L += [f"## {i} · {e['pais']} {e['ronda']} ({e['fecha_evento']})", "",
          f"- **Binario:** {e['binario']}. Bueno = {e['bueno']}; malo = {e['malo']}.",
          f"- **Fechas:** víspera {e['pre']} (EE.UU. {e['pre_us']}); día después {e['post']} (EE.UU. {e['post_us']}). "
          f"Activos: {e['activos']}.",
          f"- **Grilla p(bueno):** {pct(e['p_grid_min'])} / {pct(e['p_grid_med'])} / {pct(e['p_grid_max'])} "
          f"({e['n_fuentes_grilla']} valores; {e['verificacion']}). Elegible por probabilidad (alguna fuente en 5-95%): {e['elegible_prob']}."]
    if e["prior_pre"]:
        L.append(f"- **1ª vuelta para event beta:** {e['prior_pre']} → {e['prior_post']}; Δp = {e['prior_dp'] or 's/d'} "
                 f"({e['prior_dp_fuente']}).")
    L += [f"- **Resultado (solo validación):** {e['resultado']}. Mercado: {e['mov_real']}.",
          f"- **Notas:** {e['notas']}", "", "**Probabilidades por fuente**", "",
          "| Fuente | Contrato | Fecha | Cuotas / precios | Overround | Prop. | Shin | Usada | Grilla | Verif. |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in PRb.get(i, []):
        g = "sí" if r["en_grilla"] == "1" else f"no ({r['motivo_exclusion']})"
        L.append(f"| {r['fuente']} | {r['contrato']} ({r['binario']}) | {r['fecha']} | {r['valores']} | "
                 f"{pct(r['overround']) if r['overround'] else '—'} | {pct(r['p_bueno_proporcional'])} | "
                 f"{pct(r['p_bueno_shin'])} | {pct(r['p_bueno_usado'])} | {g} | {r['verificacion']} |")
    if not PRb.get(i):
        L.append("| — | sin fuentes de probabilidad numérica | | | | | | | | |")
    L += ["", f"**Encuestas** (margen bueno − malo, modo {e['modo_margen']}; promedio de las incluidas = "
              f"{e['poll_margin_good'] or '—'} pp, n = {e['n_encuestas']}; p(σ=4) = {pct(e['p_poll_s4'])}, "
              f"p(σ=error 1ª v.) = {pct(e['p_poll_smiss'])})", ""]
    if POb.get(i):
        L += ["| Encuestadora | Campo | Publicada | Bueno | Malo | Base | Margen | Incluida |", "|---|---|---|---|---|---|---|---|"]
        for p in POb[i]:
            L.append(f"| {p['encuestadora']} | {p['campo']} | {p['publicada']} | {p['bueno']} | {p['malo']} | {p['base']} | "
                     f"{p['margen_bueno_pp']} | {'sí' if p['incluida'] == '1' else 'no: ' + p['nota']} |")
    else:
        L.append("Sin margen de encuestas aplicable al binario (ver notas).")
    if MIb.get(i):
        L += ["", f"**Error de encuestas en la 1ª vuelta** (margen entre los dos candidatos de la 2ª): promedio {e['poll_miss_1T']} pp", "",
              "| Fuente | Margen encuestas | Margen real | Error |", "|---|---|---|---|"]
        for m in MIb[i]:
            L.append(f"| {m['fuente']} | {m['margen_encuestas']} | {m['margen_real']} | {m['error_pp']} |")
    L += ["", "**Escenarios de analistas**", ""]
    if SCb.get(i):
        L += ["| Institución | Fecha | Activo | Escenario | Movimiento | Mov. % | Ex ante | Verif. |", "|---|---|---|---|---|---|---|---|"]
        for s in SCb[i]:
            L.append(f"| {s['institucion']} | {s['fecha']} | {s['activo']} | {s['escenario']} | {s['descripcion']} | "
                     f"{s['mov_esperado_pct'] or '—'} | {'sí' if s['ex_ante'] == '1' else 'no'} | {s['verificacion']} |")
    else:
        L.append("Ninguna nota ex ante con cifras por escenario.")
    L.append("")
open(f"{D}/fichas-eventos.md", "w", encoding="utf-8").write("\n".join(L))
print(len(L), "líneas")
