"""
Corrida final (13/11/2026) con el código congelado (framework.py 221320a15437, sin cambios), mismas tres reglas y
mismo loop que run_events.py. Junta en un solo registro el pre-registro (6 principales + 5 exploratorios de BOVA11),
Chile 2021-2T (ECH) y el fuera de muestra (EWZ 2014-2026, Argentina con ARGT/GGAL/YPF).

Insumos nuevos respecto del 11/11 (todos cambian datos de entrada, no el framework):
  1. Cadenas del día ideal de vol base (iVolatility del 12/11) y COTAHIST de octubre 2026 (M102026).
  2. Cierres diarios (Stooq, ajustados por dividendos y splits) para la RV20 del paso 4 y para el r_previo del event
     beta (EWZ 5/10 y 8/10/2018). Se reescalan al nivel no ajustado de iVolatility, por evento, con la mediana del
     cociente en los días que están en las dos fuentes; se agregan solo los días que iVolatility no tiene.
  3. Tasa de los ETF y ADRs = T-bill a 4 semanas (FRED DTB4WK) del último dato <= t0 (antes: valores a mano).
  4. r_previo de EWZ 2026-2T sale de los datos (antes: prensa, 38,19 -> 42,98).
  5. Ventana de datos por evento [t0 - 45 días, t1] (VENTANA=1). Con VENTANA=0 se pasa toda la base del ticker
     (como run_events.py) más los cierres del evento: sirve para mostrar el efecto de la ventana.
Uso: python run_final.py <dir_datos> <event_inputs.csv> <dir_cierres> <DTB4WK.csv> <dir_salida> [VENTANA=1] [reglas|robustez]
     <dir_datos>/cotahist_bova_petr.pkl y <dir_datos>/ivol/ (todos los ZIP de iVolatility, 11/11 y 12/11)
     <dir_cierres>/*<ticker en minúscula>_us_d.csv (formato Stooq: Date,Open,High,Low,Close,Volume)
"""
import contextlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import framework as fw
from event_inputs import load_events
from ivol_adapter import load_ivol

D, CSV, CL, TB, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5])
VENTANA = int(sys.argv[6]) if len(sys.argv) > 6 else 1
OUT.mkdir(exist_ok=True)
WINDOW_DAYS = 45

tb = pd.read_csv(TB, parse_dates=["observation_date"]).dropna()
tb = tb.set_index("observation_date").iloc[:, 0].astype(float) / 100


def tbill(t0):
    return float(tb[tb.index <= pd.Timestamp(t0)].iloc[-1])


EV_LOC = load_events(CSV, only_eligible=True)
EV_US = load_events(CSV, only_eligible=True, us_dates=True)
for v in EV_US.values():
    v["r"] = tbill(v["pre"])

RULES = {
    "principal": dict(ROBUST_MODE="recargo", THETA=0.25, SEV_DECISION="promedio", CALL_FLOOR="auto", KEEP_UP=0.0,
                      MAX_CALLS=1, COST_MAX=0.0025),
    "piso50": dict(ROBUST_MODE="recargo", THETA=0.25, SEV_DECISION="promedio", CALL_FLOOR=False, KEEP_UP=0.5,
                   MAX_CALLS=1, COST_MAX=0.0025),
    "v1": dict(ROBUST_MODE="ve_fijo", SEV_DECISION="primario", CALL_FLOOR=False, KEEP_UP=0.0, MAX_CALLS=1,
               COST_MAX=0.0025),
}
# 13/11: modo "robustez" (7º argumento): regla principal con recargo θ = 10% y 50% (robustez del protocolo).
MODO = sys.argv[7] if len(sys.argv) > 7 else "reglas"
if MODO == "robustez":
    RULES = {f"theta{int(t * 100)}": dict(RULES["principal"], THETA=t) for t in (0.10, 0.50)}
BOVA = dict(root="BOVA", tk="BOVA11")
EWZ = dict(root="EWZ", tk="EWZ")
AR_EV = ["AR-2015-1T", "AR-2015-2T", "AR-2017-LEG", "AR-2019-PASO", "AR-2021-PASO", "AR-2021-LEG", "AR-2023-PASO",
         "AR-2023-1T", "AR-2023-2T", "AR-2025-PBA", "AR-2025-LEG"]
RUNS = ([("main", "cotahist", "BR-2022-2T", BOVA, EV_LOC), ("main", "cotahist", "BR-2026-2T", BOVA, EV_LOC),
         ("main", "ivol", "BR-2022-2T", EWZ, EV_US), ("main", "ivol", "BR-2026-2T", EWZ, EV_US),
         ("main", "ivol", "MX-2024", dict(root="EWW", tk="EWW"), EV_US),
         ("main", "ivol", "IN-2024", dict(root="INDA", tk="INDA"), EV_US)]
        + [("expl", "cotahist", ek, BOVA, EV_LOC) for ek in ["BR-2014-1T", "BR-2014-2T", "BR-2018-2T", "BR-2022-1T", "BR-2026-1T"]]
        + [("oos-CL", "ivol", "CL-2021-2T", dict(root="ECH", tk="ECH"), EV_US)]
        + [("oos-BR", "ivol", ek, EWZ, EV_US) for ek in ["BR-2014-1T", "BR-2014-2T", "BR-2018-2T", "BR-2022-1T", "BR-2026-1T"]]
        + [("oos-AR", "ivol", ek, dict(root=tk, tk=tk), EV_US) for ek in AR_EV for tk in ("ARGT", "GGAL", "YPF")])

COT = pd.read_pickle(D / "cotahist_bova_petr.pkl")
IVOL_FILES = sorted(p for p in (D / "ivol").iterdir() if p.suffix.lower() in (".csv", ".zip"))
cache, closes, escalas = {}, {}, []


def stooq(tk):
    if tk not in closes:
        f = sorted(CL.glob(f"*{tk.lower()}_us_d.csv"))
        closes[tk] = (pd.read_csv(f[0], parse_dates=["Date"]).set_index("Date")["Close"].astype(float)
                      if f else pd.Series(dtype=float))
    return closes[tk]


def with_closes(A, tk, lo, hi, ek):
    """Agrega a A (formato framework) los cierres de Stooq de [lo, hi] que iVolatility no tiene, reescalados."""
    s = stooq(tk)
    s = s[(s.index >= lo) & (s.index <= hi)]
    if s.empty:
        return A
    sp = A[(A.TPMERC == "010") & (A.CODNEG == tk)].drop_duplicates("DATA").set_index("DATA").PREULT
    common = s.index.intersection(sp[(sp.index >= lo) & (sp.index <= hi)].index)
    if len(common) == 0:
        return A
    q = (sp.loc[common] / s.loc[common])
    k = float(q.median())
    escalas.append(dict(evento=ek, activo=tk, dias_comunes=len(common), escala=k,
                        dispersion=float(q.max() / q.min() - 1)))
    new = s[~s.index.isin(sp.index)] * k
    rows = pd.DataFrame({"DATA": new.index, "TPMERC": "010", "CODNEG": tk, "NOMRES": tk, "PREEXE": 0.0, "PREOFC": 0.0,
                         "PREOFV": 0.0, "PREULT": new.values, "TOTNEG": 0, "VOLTOT": 0.0, "OI": 0, "DATVEN": pd.NaT})
    return pd.concat([A, rows], ignore_index=True)


reg, txt, results = [], [], {}
for grp, src, ek, asset, E in RUNS:
    ev = E[ek]
    t0, t1 = pd.Timestamp(ev["pre"]), pd.Timestamp(ev["post"])
    lo = t0 - pd.Timedelta(days=WINDOW_DAYS)
    if src == "cotahist":
        A = COT
    else:
        if asset["tk"] not in cache:
            cache[asset["tk"]] = load_ivol(IVOL_FILES, symbols=[asset["tk"]])
        A = with_closes(cache[asset["tk"]], asset["tk"], lo, t1, ek)
    fw.DF_ALL = (A[(A.DATA >= lo) & (A.DATA <= t1)].reset_index(drop=True) if VENTANA else A)
    for rn, cfg in RULES.items():
        for k, v in cfg.items():
            setattr(fw, k, v)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                o = fw.run(ev, asset)
            g = dict(o["registro"], regla=rn, grupo=grp, r=ev["r"], vol_base=o["curva"]["vol_base"],
                     vol_base_fuente=o["curva"]["vol_base_fuente"], iv_evento=o["curva"]["iv_evento"],
                     salto=o["curva"]["salto_implicito"])
            ch = o["decision"]["elegida"]
            g["P_alza_estres"] = ch["P_alza_estres"] if ch is not None else 1.5 * g["u"]
            results[(grp, ek, asset["tk"], rn)] = o
        except Exception as e:   # criterio 3: sin cadena utilizable
            g = dict(evento=ek, activo=asset["tk"], regla=rn, grupo=grp, decision="NO EVALUABLE", motivo=str(e))
            buf.write(f"\n{ek} · {asset['tk']}: NO EVALUABLE ({e})\n")
        reg.append(g)
        if rn == "principal":
            txt.append(buf.getvalue())

R = pd.DataFrame(reg)
R.to_csv(OUT / "registro_final.csv", index=False)
pd.DataFrame(escalas).drop_duplicates(["evento", "activo"]).to_csv(OUT / "escalas_cierres.csv", index=False)
cols = ["grupo", "evento", "activo", "regla", "resultado", "p_central", "u", "d", "decision", "patas", "costo",
        "P_malo_protocolo", "P_bueno_protocolo", "retorno_real", "P_real_protocolo", "P_real_ingenuo"]
pd.set_option("display.width", 260)
pd.set_option("display.max_colwidth", 40)
summary = R[[c for c in cols if c in R]].round(4).to_string(index=False)
(OUT / "framework_output_final.txt").write_text(
    f"CORRIDA FINAL (13/11/2026), framework.py 221320a15437, ventana {'[t0-45, t1]' if VENTANA else 'sin ventana'}\n"
    "REGLA PRINCIPAL: recargo 25%, severidad promedio, no topear la suba si u > |d|, caja <= 0,25%\n"
    + "".join(txt) + "\n\nRESUMEN, TRES REGLAS (principal / piso50 / v1)\n" + summary + "\n")
pd.to_pickle(results, OUT / "framework_results_final.pkl")
print(summary)
