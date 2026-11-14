"""
Corrida del 11/11/2026 (tarde) con tres reglas de decisión del paso 6, inputs de datos/event_inputs.csv:
  principal : recargo 25%, severidad promedio, no topear la suba si u > |d|, caja <= 0,25%
  piso50    : alternativa del texto; igual que la principal pero sin la condición u > |d| y con piso P_bueno >= 50% de u
  v1        : regla del 11/11 a la mañana (VE_min >= -0,25 pp, severidad primaria, calls donde caigan), por protocolo
Casos: BOVA11 (COTAHIST) y EWZ (iVolatility) Brasil 2022 y 2026, 2ª vuelta; EWW (México 2024); INDA (India 2024);
y, exploratorio, el resto de Brasil sobre BOVA11 (1ª vuelta 2014, 2ª 2014, 2ª 2018, 1ª 2022, 1ª 2026).
Uso: python run_events.py <dir_datos> <event_inputs.csv> <dir_salida>
     <dir_datos>/cotahist_bova_petr.pkl  (sale de build_cotahist_pkl.py)
     <dir_datos>/ivol/                   (los archivos de iVolatility tal como se bajan: data_download*.zip o .csv;
                                          se leen todos y se filtra por ticker, el nombre del archivo no importa)

Tasas para ETFs en EE.UU. (el CSV solo trae la local de Brasil): T-bill a 4 semanas, subasta más cercana a t0.
  oct-2022 3,9% (aprox.); may-2024 5,37%; oct-2026 3,95%. Con 1-3 semanas a vencimiento el efecto es despreciable.
r_previo de EWZ en la 1ª vuelta 2026 (no hay cadenas de iVolatility del 2/10 y 5/10): 38,19 -> 42,98 = +12,54%
  (Rio Times vía UA.News, 11/10/2026; Kalkine: +12,5% a 42,98).
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

D = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/data")
CSV = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/datos/event_inputs.csv"
OUT = Path(sys.argv[3] if len(sys.argv) > 3 else "/home/claude/out")
OUT.mkdir(exist_ok=True)

EV_LOC = load_events(CSV, only_eligible=True)
R_US = {"2022": 0.039, "2024": 0.0537, "2026": 0.0395}
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
EWZ_PRIOR = {"BR-2026-2T": dict(ret=42.98 / 38.19 - 1, fuente="EWZ 38,19 -> 42,98 (Rio Times vía UA.News; Kalkine)")}
BOVA = dict(root="BOVA", tk="BOVA11")
RUNS = [
    ("main", "cotahist", "BR-2022-2T", BOVA, EV_LOC),
    ("main", "cotahist", "BR-2026-2T", BOVA, EV_LOC),
    ("main", "ivol", "BR-2022-2T", dict(root="EWZ", tk="EWZ"), EV_US),
    ("main", "ivol", "BR-2026-2T", dict(root="EWZ", tk="EWZ", prior_ret=EWZ_PRIOR), EV_US),
    ("main", "ivol", "MX-2024", dict(root="EWW", tk="EWW"), EV_US),
    ("main", "ivol", "IN-2024", dict(root="INDA", tk="INDA"), EV_US),
] + [("expl", "cotahist", ek, BOVA, EV_LOC) for ek in ["BR-2014-1T", "BR-2014-2T", "BR-2018-2T", "BR-2022-1T", "BR-2026-1T"]]

COT = pd.read_pickle(D / "cotahist_bova_petr.pkl")
IVOL_FILES = sorted(p for p in (D / "ivol").iterdir() if p.suffix.lower() in (".csv", ".zip"))
reg, txt_main, txt_expl, results = [], [], [], {}
for grp, src, ek, asset, E in RUNS:
    fw.DF_ALL = COT if src == "cotahist" else load_ivol(IVOL_FILES, symbols=[asset["tk"]])
    for rn, cfg in RULES.items():
        for k, v in cfg.items():
            setattr(fw, k, v)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                o = fw.run(E[ek], asset)
            g = dict(o["registro"], regla=rn, grupo=grp)
            ch = o["decision"]["elegida"]
            g["P_alza_estres"] = ch["P_alza_estres"] if ch is not None else 1.5 * g["u"]
            results[(ek, asset["tk"], rn)] = o
        except Exception as e:   # criterio 3: sin cadena utilizable
            g = dict(evento=ek, activo=asset["tk"], regla=rn, grupo=grp, decision="NO EVALUABLE", motivo=str(e))
            buf.write(f"\n{ek} · {asset['tk']}: NO EVALUABLE ({e})\n")
        reg.append(g)
        if rn == "principal":
            (txt_main if grp == "main" else txt_expl).append(buf.getvalue())

R = pd.DataFrame(reg)
cols = ["grupo", "evento", "activo", "regla", "resultado", "p_central", "u", "d", "decision", "patas", "costo",
        "P_malo_protocolo", "P_bueno_protocolo", "retorno_real", "P_real_protocolo", "P_real_ingenuo"]
R.to_csv(OUT / "registro_eventos.csv", index=False)
pd.set_option("display.width", 260)
pd.set_option("display.max_colwidth", 40)
summary = R[cols].round(4).to_string(index=False)
(OUT / "framework_output.txt").write_text(
    "REGLA PRINCIPAL: recargo 25%, severidad promedio, no topear la suba si u > |d|, caja <= 0,25%\n"
    + "".join(txt_main) + "\n\nRESUMEN, TRES REGLAS (principal / piso50 / v1)\n" + summary + "\n")
(OUT / "framework_output_bova_otros.txt").write_text("REGLA PRINCIPAL, exploratorio BOVA11\n" + "".join(txt_expl))
pd.to_pickle(results, OUT / "framework_results.pkl")
print(summary)
