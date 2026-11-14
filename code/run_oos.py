"""
Corrida FUERA DE MUESTRA (12/11/2026) con el código congelado (framework.py 221320a15437, sin cambios) y las mismas
tres reglas y el mismo loop que run_events.py. Solo agrega eventos y activos nuevos; no toca los 11 casos del
pre-registro (esos se vuelven a correr con run_events.py, que necesita los COTAHIST y los ZIP de iVolatility del 11/11).

Casos:
  - EWZ (iVolatility) para el resto de Brasil, que BOVA11 no cubre (antes de 2020 sin opciones; 2026-1T paridad rota):
    BR-2014-1T, BR-2014-2T, BR-2018-2T, BR-2022-1T, BR-2026-1T.
  - Argentina (ARGT, GGAL, YPF como activos propios), los 11 eventos principales elegibles con datos (AR-2019-1T sin datos).
Uso: python run_oos.py <dir_ivol> <event_inputs.csv> <dir_salida>

Tasa (T-bill a 4 semanas, aproximada por año; el efecto con 1-3 semanas a vencimiento es despreciable):
  2014 0,02%; 2015 0,1%; 2017 1,0%; 2018 2,2%; 2019 2,0%; 2021 0,05%; 2022 3,9% (= run_events.py); 2023 5,3%;
  2025 4,0%; 2026 3,95% (= run_events.py). Valores de 2014-2025 aproximados (sin verificar subasta por subasta).
"""
import contextlib
import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import framework as fw
from event_inputs import load_events
from ivol_adapter import load_ivol

D = Path(sys.argv[1])
CSV = sys.argv[2]
OUT = Path(sys.argv[3])
OUT.mkdir(exist_ok=True)

R_US = {"2014": 0.0002, "2015": 0.001, "2017": 0.010, "2018": 0.022, "2019": 0.020, "2021": 0.0005,
        "2022": 0.039, "2023": 0.053, "2025": 0.040, "2026": 0.0395}
EV_US = load_events(CSV, only_eligible=True, us_dates=True)
for v in EV_US.values():
    v["r"] = R_US.get(v["fecha_evento"][:4], 0.04)

RULES = {
    "principal": dict(ROBUST_MODE="recargo", THETA=0.25, SEV_DECISION="promedio", CALL_FLOOR="auto", KEEP_UP=0.0,
                      MAX_CALLS=1, COST_MAX=0.0025),
    "piso50": dict(ROBUST_MODE="recargo", THETA=0.25, SEV_DECISION="promedio", CALL_FLOOR=False, KEEP_UP=0.5,
                   MAX_CALLS=1, COST_MAX=0.0025),
    "v1": dict(ROBUST_MODE="ve_fijo", SEV_DECISION="primario", CALL_FLOOR=False, KEEP_UP=0.0, MAX_CALLS=1,
               COST_MAX=0.0025),
}
EWZ = dict(root="EWZ", tk="EWZ")
AR_EV = ["AR-2015-1T", "AR-2015-2T", "AR-2017-LEG", "AR-2019-PASO", "AR-2021-PASO", "AR-2021-LEG", "AR-2023-PASO",
         "AR-2023-1T", "AR-2023-2T", "AR-2025-PBA", "AR-2025-LEG"]
RUNS = ([("oos-BR", ek, EWZ) for ek in ["BR-2014-1T", "BR-2014-2T", "BR-2018-2T", "BR-2022-1T", "BR-2026-1T"]]
        + [("oos-AR", ek, dict(root=tk, tk=tk)) for ek in AR_EV for tk in ("ARGT", "GGAL", "YPF")])

IVOL_FILES = sorted(p for p in D.iterdir() if p.suffix.lower() in (".csv", ".zip"))
# Ventana de datos por evento: [t0 - 45 días corridos, t1]. framework.py no acota hacia atrás la búsqueda de la vol
# base en eventos sin 1ª vuelta previa (lower = 1900) ni la RV20 (toma los últimos 21 cierres que haya). Con varios
# eventos del mismo ticker en la misma base, eso mezclaba días de otros años (AR-2017-LEG tomaba la vol base del
# 23/11/2015). La ventana contiene la 1ª vuelta de toda 2ª vuelta de la muestra (<= 28 días antes de t0) y deja lugar
# para 21 cierres previos a la medición de la vol base. No cambia framework.py.
WINDOW_DAYS = 45
cache = {}
reg, txt, results = [], [], {}
for grp, ek, asset in RUNS:
    if asset["tk"] not in cache:
        cache[asset["tk"]] = load_ivol(IVOL_FILES, symbols=[asset["tk"]])
    A = cache[asset["tk"]]
    t0, t1 = pd.Timestamp(EV_US[ek]["pre"]), pd.Timestamp(EV_US[ek]["post"])
    fw.DF_ALL = A[(A.DATA >= t0 - pd.Timedelta(days=WINDOW_DAYS)) & (A.DATA <= t1)].reset_index(drop=True)
    for rn, cfg in RULES.items():
        for k, v in cfg.items():
            setattr(fw, k, v)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                o = fw.run(EV_US[ek], asset)
            g = dict(o["registro"], regla=rn, grupo=grp)
            ch = o["decision"]["elegida"]
            g["P_alza_estres"] = ch["P_alza_estres"] if ch is not None else 1.5 * g["u"]
            results[(ek, asset["tk"], rn)] = o
        except Exception as e:   # criterio 3: sin cadena utilizable
            g = dict(evento=ek, activo=asset["tk"], regla=rn, grupo=grp, decision="NO EVALUABLE", motivo=str(e))
            buf.write(f"\n{ek} · {asset['tk']}: NO EVALUABLE ({e})\n")
        reg.append(g)
        if rn == "principal":
            txt.append(buf.getvalue())

R = pd.DataFrame(reg)
cols = ["grupo", "evento", "activo", "regla", "resultado", "p_central", "u", "d", "decision", "patas", "costo",
        "P_malo_protocolo", "P_bueno_protocolo", "retorno_real", "P_real_protocolo", "P_real_ingenuo"]
R.to_csv(OUT / "registro_eventos_oos.csv", index=False)
pd.set_option("display.width", 260)
pd.set_option("display.max_colwidth", 40)
summary = R[[c for c in cols if c in R]].round(4).to_string(index=False)
(OUT / "framework_output_oos.txt").write_text(
    "FUERA DE MUESTRA (12/11/2026), framework.py 221320a15437\n"
    "REGLA PRINCIPAL: recargo 25%, severidad promedio, no topear la suba si u > |d|, caja <= 0,25%\n"
    + "".join(txt) + "\n\nRESUMEN, TRES REGLAS (principal / piso50 / v1)\n" + summary + "\n")
pd.to_pickle(results, OUT / "framework_results_oos.pkl")
print(summary)
