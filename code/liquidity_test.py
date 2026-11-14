"""
Prueba de liquidez (criterio 3 del paso 0) sobre la compra de prueba de iVolatility (solo la víspera).
Para cada ticker-día: vencimiento del evento = primero con >= 2 días hábiles después de t1 (post_us).
Métricas en ese vencimiento:
  n_cot_85_110 : strikes (put o call) con bid > 0 y ask > 0 entre 0,85 y 1,10 del spot (criterio del paso 0: ~10)
  n_liq        : opciones que pasan el filtro del paso 1 (spread <= 15% del mid + 0,03 y OI >= 100), 0,7-1,3 S
  puts_leg / calls_leg : patas posibles para el paso 6 (puts líquidos OTM >= 0,8 S; calls líquidos OTM <= 1,25 S)
  spread_atm   : spread relativo mediano de las 4 opciones más cercanas al dinero
  iv_atm       : IV ATM (para ver si la term structure es medible)
  n_opc_85_110 : opciones (puts + calls) cotizadas en la misma banda. Con strikes de US$1 y spot bajo US$40, la banda
                 0,85-1,10 tiene 4-7 strikes como máximo: el umbral de "~10 strikes" del paso 0 es inalcanzable por
                 construcción en ECH/EC/TUR; se reportan las dos cuentas.
Veredicto (operabilidad del paso 6, que usa el filtro congelado del paso 1):
  PASA      : al menos un put y un call líquidos dentro de los rangos del paso 6 (se puede armar un collar)
  SOLO PUT  : hay put líquido pero ningún call (solo put o put spread)
  NO PASA   : ningún put líquido -> el framework termina en "sin opciones líquidas" sin importar el resto.
Uso: python liquidity_test.py <dir ivol> <event_inputs.csv> <salida.csv>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from event_inputs import load_events
from mixture import implied_vol

D = Path(sys.argv[1])
E = load_events(sys.argv[2], only_eligible=False, only_main=False, us_dates=True)
MAP = {  # (ticker, víspera en EE.UU.) -> evento
    ("ECH", "2017-12-15"): "CL-2017-2T", ("ECH", "2021-11-19"): "CL-2021-1T", ("ECH", "2021-12-17"): "CL-2021-2T",
    ("ECH", "2022-09-02"): "CL-2022-PLEB", ("ECH", "2023-12-15"): "CL-2023-PLEB", ("ECH", "2025-11-14"): "CL-2025-1T",
    ("ECH", "2025-12-12"): "CL-2025-2T",
    ("EC", "2018-06-15"): "CO-2018-2T", ("EC", "2022-05-27"): "CO-2022-1T", ("CIB", "2022-05-27"): "CO-2022-1T",
    ("EC", "2022-06-17"): "CO-2022-2T", ("CIB", "2022-06-17"): "CO-2022-2T", ("EC", "2026-05-29"): "CO-2026-1T",
    ("CIB", "2026-05-29"): "CO-2026-1T", ("EC", "2026-06-18"): "CO-2026-2T", ("CIB", "2026-06-18"): "CO-2026-2T",
    ("TUR", "2015-06-05"): "TR-2015-06", ("TUR", "2015-10-30"): "TR-2015-11", ("TUR", "2023-05-12"): "TR-2023-1T",
    ("TUR", "2023-05-26"): "TR-2023-2T",
}
# 12/11/2026: Argentina (fuera de muestra), ARGT y ADRs como activos propios; víspera en EE.UU. de cada evento AR-*.
AR_PRE = {"AR-2015-1T": "2015-10-23", "AR-2015-2T": "2015-11-20", "AR-2017-LEG": "2017-10-20",
          "AR-2019-PASO": "2019-08-09", "AR-2019-1T": "2019-10-25", "AR-2021-PASO": "2021-09-10",
          "AR-2021-LEG": "2021-11-12", "AR-2023-PASO": "2023-08-11", "AR-2023-1T": "2023-10-20",
          "AR-2023-2T": "2023-11-17", "AR-2025-PBA": "2025-09-05", "AR-2025-LEG": "2025-10-24"}
MAP.update({(tk, d): ev for ev, d in AR_PRE.items() for tk in ("ARGT", "GGAL", "YPF", "BMA", "PAM")})
POST_EXTRA = {"TR-2023-1T": ("2023-05-14", "2023-05-15")}   # sin fila en event_inputs.csv (sin probabilidades)
R_US = {2015: 0.0, 2017: 0.012, 2018: 0.019, 2019: 0.020, 2021: 0.0005, 2022: 0.02, 2023: 0.052, 2025: 0.039, 2026: 0.037}

files = sorted(f for f in D.iterdir() if f.suffix.lower() in (".csv", ".zip"))   # los .zip de iVolatility se leen directo
raw = pd.concat([pd.read_csv(f) for f in files], ignore_index=True).drop_duplicates(["date", "option symbol"])
raw["DATA"] = pd.to_datetime(raw.date, format="%m/%d/%Y")
raw["EXP"] = pd.to_datetime(raw.expiration, format="%m/%d/%Y")
rows = []
for (tk, d), g in raw.groupby(["symbol", "DATA"]):
    key = (tk, d.strftime("%Y-%m-%d"))
    if key not in MAP:
        continue
    ev = MAP[key]
    if ev in E:
        post, fecha = pd.Timestamp(E[ev]["post"]), E[ev]["fecha_evento"]
    else:
        fecha, post = POST_EXTRA[ev][0], pd.Timestamp(POST_EXTRA[ev][1])
    S = float(g.unadjusted.iloc[0])
    exps = sorted(x for x in g.EXP.unique() if np.busday_count(post.date(), pd.Timestamp(x).date()) >= 2)
    x1 = pd.Timestamp(exps[0])
    c = g[g.EXP == x1].copy()
    c["mid"] = (c.bid + c.ask) / 2
    q = c[(c.bid > 0) & (c.ask > 0) & (c.ask >= c.bid)]
    q = q.assign(liq=((q.ask - q.bid) <= 0.15 * q.mid + 0.03) & (q["open interest"] >= 100))
    band = q[(q.strike >= 0.85 * S) & (q.strike <= 1.10 * S)]
    n_band = band.strike.nunique()
    n_opc = len(band)
    z = q[q.liq & (((q["call/put"] == "P") & (q.strike < S) & (q.strike >= 0.7 * S)) |
                   ((q["call/put"] == "C") & (q.strike > S) & (q.strike <= 1.3 * S)))]
    puts_leg = int(((z["call/put"] == "P") & (z.strike >= 0.8 * S)).sum())
    calls_leg = int(((z["call/put"] == "C") & (z.strike <= 1.25 * S)).sum())
    near = q.iloc[(q.strike - S).abs().argsort()[:4]]
    spr = float(np.median((near.ask - near.bid) / near.mid)) if len(near) else np.nan
    T = np.busday_count(d.date(), x1.date()) / 252
    r = R_US.get(d.year, 0.02)
    F = S * np.exp(r * T)
    ivs = []
    for t in ["C", "P"]:
        y = q[q["call/put"] == t]
        if y.empty:
            continue
        row = y.iloc[(y.strike - F).abs().argsort()[:1]].iloc[0]
        if abs(row.strike / F - 1) <= 0.05:
            ivs.append(implied_vol(row.mid * np.exp(r * T), F, row.strike, T, t))
    ivs = [v for v in ivs if np.isfinite(v)]
    verdict = "PASA" if puts_leg >= 1 and calls_leg >= 1 else ("SOLO PUT" if puts_leg >= 1 else "NO PASA")
    rows.append(dict(evento=ev, ticker=tk, vispera=key[1], fecha_evento=fecha, spot=S, venc_evento=x1.date(),
                     vencimientos=len(g.EXP.unique()), n_cot_85_110=n_band, n_opc_85_110=n_opc, n_liq=len(z), puts_leg=puts_leg,
                     calls_leg=calls_leg, oi_venc=int(c["open interest"].sum()), spread_atm=spr,
                     iv_atm=float(np.mean(ivs)) if ivs else np.nan, veredicto=verdict))
T = pd.DataFrame(rows).sort_values(["evento", "ticker"])
pd.set_option("display.width", 250)
print(T.round(3).to_string(index=False))
T.to_csv(sys.argv[3], index=False)
