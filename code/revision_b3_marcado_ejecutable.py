"""
Revisión (20/11/2026), pedido B.3: marcado ejecutable en t1 de las estructuras elegidas (reglas principal, piso50,
v1 y theta 10/50%), con el filtro de liquidez codificado y con el estricto. No cambia ningún resultado del registro.

framework.py 221320a15437 (paso 7): P_real = ret + h · Σ lado · (mid_t1 − entrada) / S0, entrada al ask (comprada) o
al bid (vendida); mid_t1 = (bid + ask)/2 si la opción cotiza en t1, y si no PREULT (B3: último negocio del día;
iVolatility: (bid + ask)/2 con alguna punta en cero). Este script recalcula:
  P_real_mid          control: tiene que reproducir el registro.
  P_real_ejecutable   salida al bid (comprada) o al ask (vendida) en t1; NaN si a alguna pata le falta esa punta
                      (bid = 0 para una comprada, ask = 0 para una vendida).
  P_real_ejec_o_intr  igual, pero la pata sin esa punta se valúa a su valor intrínseco con el spot de t1.
  P_real_intrinseco   todas las patas a su valor intrínseco con el spot de t1 (pago al vencimiento si el spot
                      se queda en S1), la medida principal de la revisión.
Uso: python revision_b3_marcado_ejecutable.py <dir_datos> <salida_dir> <etiqueta>=<dir_registro> ...
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from ivol_adapter import load_ivol

D, OUT = Path(sys.argv[1]), Path(sys.argv[2])
RUNS = [a.split("=", 1) for a in sys.argv[3:]]
OUT.mkdir(exist_ok=True, parents=True)

IV = load_ivol(sorted(p for p in (D / "ivol").iterdir() if p.suffix.lower() in (".csv", ".zip")))
B3 = pd.read_pickle(D / "cotahist_bova_petr.pkl")


def chain(tk, day, expiry):
    src = B3 if tk == "BOVA11" else IV
    root = "BOVA" if tk == "BOVA11" else tk
    o = src[(src.DATA == day) & src.TPMERC.isin(["070", "080"]) & src.CODNEG.str.startswith(root)
            & (src.DATVEN == expiry)].copy()
    o["type"] = o.TPMERC.map({"070": "C", "080": "P"})
    o["K"] = o.PREEXE.astype(float)
    o["quoted"] = (o.PREOFC > 0) & (o.PREOFV > 0) & (o.PREOFV >= o.PREOFC)
    o["mid"] = np.where(o.quoted, (o.PREOFC + o.PREOFV) / 2, o.PREULT)
    o = o.sort_values("TOTNEG", ascending=False).drop_duplicates(["type", "K"])  # igual que framework.chain
    return o.set_index(["type", "K"])


def intrinsic(t, K, S):
    return max(S - K, 0.0) if t == "C" else max(K - S, 0.0)


legs_out, struct_out = [], []
for etiqueta, base in RUNS:
    base = Path(base)
    for regfile in ["registro_final.csv"]:
        REG = pd.read_csv(base / regfile)
        RS = pd.read_pickle(base / "framework_results_final.pkl")
        for _, r in REG.iterrows():
            if not isinstance(r.patas, str) or r.patas == "—":
                continue
            o = RS[(r.grupo, r.evento, r.activo, r.regla)]
            x1 = pd.Timestamp(o["curva"]["venc_evento"])
            S0, S1 = o["curva"]["spot"], o["real"]["spot_post"]
            ret = S1 / S0 - 1
            c0, c1 = chain(r.activo, pd.Timestamp(r.t0), x1), chain(r.activo, pd.Timestamp(r.t1), x1)
            h = float(r.patas.split(" x ")[0])
            lg = [(1 if s == "+" else -1, t, float(k)) for s, t, k in re.findall(r"([+-])([PC])([\d.]+)", r.patas)]
            acc = dict(mid=0.0, ejec=0.0, ejec_o_intr=0.0, intr=0.0)
            sin_cot, notas = 0, []
            for side, t, K in lg:
                a = c0.loc[(t, K)]
                entry = float(a.PREOFV) if side > 0 else float(a.PREOFC)
                q = c1.loc[(t, K)] if (t, K) in c1.index else None
                intr = intrinsic(t, K, S1)
                if q is None:
                    mid, bid, ask, quoted, last, ntr = np.nan, np.nan, np.nan, False, np.nan, np.nan
                else:
                    mid, bid, ask, quoted = float(q.mid), float(q.PREOFC), float(q.PREOFV), bool(q.quoted)
                    last, ntr = float(q.PREULT), float(q.TOTNEG if r.activo == "BOVA11" else q.VOLTOT)
                lado = bid if side > 0 else ask           # punta contra la que se cierra la pata
                lado_ok = bool(np.isfinite(lado) and lado > 0)
                exitp = lado if lado_ok else np.nan
                if not quoted:
                    notas.append(f"{'+' if side > 0 else '-'}{t}{K:g} sin doble punta en t1 (bid {bid:g}, ask {ask:g}): "
                                 f"el registro la marca a {'último negocio' if r.activo == 'BOVA11' else '(bid+ask)/2'}"
                                 f" {mid:.4g}; intrínseco {intr:.4g}")
                if not lado_ok:
                    sin_cot += 1
                f = h * side / S0
                acc["mid"] += f * (mid - entry)
                acc["ejec"] += f * (exitp - entry)
                acc["ejec_o_intr"] += f * ((exitp if lado_ok else intr) - entry)
                acc["intr"] += f * (intr - entry)
                legs_out.append(dict(filtro=etiqueta, regla=r.regla, evento=r.evento, activo=r.activo, patas=r.patas,
                                     pata=f"{'+' if side > 0 else '-'}{t}{K:g}", h=h, t0=r.t0, t1=r.t1,
                                     vencimiento=x1.date(), S0=S0, S1=S1, entrada=entry, bid_t1=bid, ask_t1=ask,
                                     cotiza_t1=quoted, spread_rel_t1=(ask - bid) / mid if quoted else np.nan,
                                     punta_salida_t1=lado_ok, mid_t1_usado=mid, ultimo_negocio_t1=last,
                                     negocios_o_volumen_t1=ntr, intrinseco_t1=intr,
                                     mid_menos_intrinseco=mid - intr, salida_ejecutable=exitp))
            struct_out.append(dict(filtro=etiqueta, grupo=r.grupo, evento=r.evento, activo=r.activo, regla=r.regla,
                                   patas=r.patas, resultado=r.resultado, retorno_real=ret,
                                   P_real_registro=r.P_real_protocolo, P_real_mid=ret + acc["mid"],
                                   control_ok=bool(np.isclose(ret + acc["mid"], r.P_real_protocolo, atol=1e-9)),
                                   P_real_ejecutable=ret + acc["ejec"], P_real_ejec_o_intr=ret + acc["ejec_o_intr"],
                                   P_real_intrinseco=ret + acc["intr"], patas_sin_punta_salida_t1=sin_cot,
                                   patas_sin_doble_punta_t1=sum(1 for n in notas),
                                   nota="; ".join(notas)))

L, S = pd.DataFrame(legs_out), pd.DataFrame(struct_out)
L.to_csv(OUT / "revision_b3_patas_t1.csv", index=False)
S.to_csv(OUT / "revision_b3_marcado_ejecutable.csv", index=False)
pd.set_option("display.width", 260)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 500)
pd.set_option("display.max_colwidth", 120)
print(f"control (P_real_mid = registro): {S.control_ok.sum()} de {len(S)}")
v = S.copy()
for c in ["retorno_real", "P_real_mid", "P_real_ejecutable", "P_real_ejec_o_intr", "P_real_intrinseco"]:
    v[c] = (100 * v[c]).round(2)
print(v.drop(columns=["grupo", "P_real_registro", "control_ok"]).to_string(index=False))
