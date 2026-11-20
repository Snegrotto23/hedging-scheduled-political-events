"""
Revisión (20/11/2026), pedido B.1: interés abierto y volumen en t0 de cada pata elegida (reglas principal, piso50, v1
y theta 10/50%), y qué opciones entran como líquidas solo por volumen >= 20 (hallazgo N1 del triage).
No cambia ningún resultado: lee los registros y los pickles de run_final.py y los datos crudos.

Filtro codificado (ivol_adapter.py 4150134ef2e9 + framework.py 221320a15437): bid > 0, ask > 0,
  spread <= 0,15·mid + 0,03 y TOTNEG >= 20, con TOTNEG = 20 si OI >= 100 y si no TOTNEG = volumen del día.
Filtro estricto (tabla de parámetros): mismo spread y OI >= 100. En B3 no hay OI: TOTNEG = negocios del día,
  así que los dos filtros coinciden.

Uso: python revision_b1_patas.py <dir_datos> <dir_res_v1> <dir_res_rob> <salida_dir>
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from ivol_adapter import load_ivol

D, R1, RR, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
OUT.mkdir(exist_ok=True, parents=True)
ZONE_LO, ZONE_HI = 0.7, 1.3

IV = load_ivol(sorted(p for p in (D / "ivol").iterdir() if p.suffix.lower() in (".csv", ".zip")))
B3 = pd.read_pickle(D / "cotahist_bova_petr.pkl")


def options(tk, day, expiry):
    """Cadena de un día y vencimiento con los campos crudos que hacen falta."""
    if tk == "BOVA11":
        o = B3[(B3.DATA == day) & B3.TPMERC.isin(["070", "080"]) & B3.CODNEG.str.startswith("BOVA")
               & (B3.DATVEN == expiry)].copy()
        o["OI"] = np.nan
        o["VOL"] = o.TOTNEG  # negocios del día
    else:
        o = IV[(IV.DATA == day) & IV.TPMERC.isin(["070", "080"]) & IV.CODNEG.str.startswith(tk)
               & (IV.DATVEN == expiry)].copy()
        o["VOL"] = o.VOLTOT
    o["type"] = o.TPMERC.map({"070": "C", "080": "P"})
    o["K"] = o.PREEXE.astype(float)
    o["quoted"] = (o.PREOFC > 0) & (o.PREOFV > 0) & (o.PREOFV >= o.PREOFC)
    o["mid"] = (o.PREOFC + o.PREOFV) / 2
    o["spread_ok"] = o.quoted & ((o.PREOFV - o.PREOFC) <= 0.15 * o.mid + 0.03)
    o["pasa_codificado"] = o.spread_ok & (o.TOTNEG >= 20)
    o["pasa_estricto"] = o.spread_ok & ((o.OI >= 100) if tk != "BOVA11" else (o.TOTNEG >= 20))
    o = o.sort_values("TOTNEG", ascending=False).drop_duplicates(["type", "K"])  # igual que framework.chain
    return o


def legs(patas):
    h = float(patas.split(" x ")[0])
    return h, [(s, t, float(k)) for s, t, k in re.findall(r"([+-])([PC])([\d.]+)", patas)]


rows, extra = [], []
for tag, base in [("reglas", R1), ("theta", RR)]:
    REG = pd.read_csv(base / "registro_final.csv")
    RS = pd.read_pickle(base / "framework_results_final.pkl")
    for _, r in REG.iterrows():
        if pd.isna(r.t0):
            continue
        key = (r.grupo, r.evento, r.activo, r.regla)
        o = RS[key]
        x1 = pd.Timestamp(o["curva"]["venc_evento"])
        t0 = pd.Timestamp(r.t0)
        ch = options(r.activo, t0, x1)
        S0 = o["curva"]["spot"]
        # opciones OTM en la zona que pasan el codificado y no el estricto (una vez por caso)
        if r.regla in ("principal", "theta10"):
            z = ch[((ch.type == "P") & (ch.K < S0) & (ch.K >= ZONE_LO * S0)) |
                   ((ch.type == "C") & (ch.K > S0) & (ch.K <= ZONE_HI * S0))]
            for _, q in z[z.pasa_codificado & ~z.pasa_estricto].iterrows():
                extra.append(dict(evento=r.evento, activo=r.activo, t0=t0.date(), vencimiento=x1.date(),
                                  opcion=f"{q.type}{q.K:g}", mny=q.K / S0 - 1, bid=q.PREOFC, ask=q.PREOFV,
                                  OI=q.OI, volumen=q.VOL))
            if r.regla == "principal":
                n = dict(puts_cod=int(((z.type == "P") & z.pasa_codificado).sum()),
                         calls_cod=int(((z.type == "C") & z.pasa_codificado).sum()),
                         puts_est=int(((z.type == "P") & z.pasa_estricto).sum()),
                         calls_est=int(((z.type == "C") & z.pasa_estricto).sum()))
                extra.append(dict(evento=r.evento, activo=r.activo, t0=t0.date(), vencimiento=x1.date(),
                                  opcion="CONTEO zona 0,7-1,3 S0", **n))
        el = o["decision"].get("elegida")
        if not isinstance(el, dict) or not isinstance(el.get("patas"), str):
            continue
        h, ls = legs(el["patas"])
        for s, t, k in ls:
            q = ch[(ch.type == t) & np.isclose(ch.K, k)]
            if q.empty:
                rows.append(dict(regla=r.regla, grupo=r.grupo, evento=r.evento, activo=r.activo,
                                 decision=r.decision, patas=el["patas"], pata=f"{s}{t}{k:g}", nota="no está en la cadena"))
                continue
            q = q.iloc[0]
            rows.append(dict(regla=r.regla, grupo=r.grupo, evento=r.evento, activo=r.activo, decision=r.decision,
                             patas=el["patas"], h=h, pata=f"{s}{t}{k:g}", lado="compra" if s == "+" else "venta",
                             t0=t0.date(), vencimiento=x1.date(), spot_t0=S0, mny=k / S0 - 1,
                             bid=q.PREOFC, ask=q.PREOFV, spread_rel=(q.PREOFV - q.PREOFC) / q.mid if q.mid else np.nan,
                             OI=q.OI, volumen_o_negocios=q.VOL, TOTNEG_codificado=int(q.TOTNEG),
                             pasa_codificado=bool(q.pasa_codificado), pasa_estricto=bool(q.pasa_estricto),
                             solo_por_volumen=bool(q.pasa_codificado and not q.pasa_estricto)))

P = pd.DataFrame(rows)
E = pd.DataFrame(extra)
P.to_csv(OUT / "revision_b1_patas_oi_volumen.csv", index=False)
E.to_csv(OUT / "revision_b1_liquidas_solo_volumen.csv", index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 500)
print("PATAS ELEGIDAS")
print(P.drop(columns=["grupo", "decision", "patas"]).to_string(index=False))
print("\nOPCIONES OTM 0,7-1,3 S0 QUE PASAN SOLO POR VOLUMEN (y conteos por caso)")
print(E.to_string(index=False))
