"""
Drag del hedge permanente sobre EWZ (13/11/2026): put a 1 mes rodado cada mes, valuado con Black-Scholes con la
vol implícita del VXEWZ de Cboe (FRED VXEWZCLS) y la T-bill a 4 semanas (FRED DTB4WK) del día de compra, cobrado
con el cierre de EWZ el día de la siguiente compra. Contra el P&L de cobertura del protocolo en los eventos de
Brasil con EWZ (registro_final.csv, regla principal).

Aproximaciones (decirlas en el texto):
  - VXEWZ es una vol a 30 días cercana al dinero: un put 5% fuera del dinero cuesta más por el skew, así que el
    drag del put OTM está SUBESTIMADO (favorece al hedge permanente; la comparación es conservadora).
  - Cierres de Stooq ajustados por dividendos (retorno total) con q = 0: el put se valúa sobre el retorno total.
  - Compra el primer día hábil de cada mes con VXEWZ disponible; sin spread bid-ask.
Uso: python drag_permanente.py <ewz_us_d.csv> <VXEWZCLS.csv> <DTB4WK.csv> <registro_final.csv> <salida.txt>
"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

px = pd.read_csv(sys.argv[1], parse_dates=["Date"]).set_index("Date")["Close"].astype(float)
vx = pd.read_csv(sys.argv[2], parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
vx = pd.to_numeric(vx, errors="coerce").dropna() / 100
tb = pd.read_csv(sys.argv[3], parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
tb = pd.to_numeric(tb, errors="coerce").dropna() / 100
R = pd.read_csv(sys.argv[4])


def bs_put(S, K, T, r, s):
    d1 = (np.log(S / K) + (r + 0.5 * s * s) * T) / (s * np.sqrt(T))
    return K * np.exp(-r * T) * norm.cdf(-(d1 - s * np.sqrt(T))) - S * norm.cdf(-d1)


days = px.index.intersection(vx.index)
first = [pd.Timestamp(x) for x in pd.Series(days, index=days).groupby([days.year, days.month]).first().values]
rows = []
for a, b in zip(first[:-1], first[1:]):
    S0, S1, s = px[a], px[b], vx[a]
    r = float(tb[tb.index <= a].iloc[-1])
    T = (b - a).days / 365
    for m in (1.00, 0.95):
        K = m * S0
        prem = bs_put(S0, K, T, r, s)
        pay = max(K - S1, 0.0)
        rows.append(dict(compra=a, vence=b, mny=m, vol=s, prima=prem / S0, pago=pay / S0,
                         pnl=(pay - prem * np.exp(r * T)) / S0, ret_ewz=S1 / S0 - 1))
P = pd.DataFrame(rows)

out = []
for lo, hi, tag in [("2014-10-01", "2026-11-01", "oct-2014 a oct-2026 (muestra de eventos de Brasil)"),
                    ("2011-04-01", "2026-11-01", "abr-2011 a oct-2026 (toda la historia del VXEWZ)")]:
    X = P[(P.compra >= lo) & (P.compra < hi)]
    yrs = (pd.Timestamp(min(pd.Timestamp(hi), X.vence.max())) - pd.Timestamp(lo)).days / 365.25
    out.append(f"\n{tag}: {X.compra.nunique()} meses, {yrs:.1f} años")
    for m, g in X.groupby("mny"):
        prem_y = g.prima.sum() / yrs
        pay_y = g.pago.sum() / yrs
        drag_y = g.pnl.sum() / yrs
        worst = g.ret_ewz.min()
        out.append(f"  put {'ATM' if m == 1 else '5% OTM'}: prima {prem_y:.1%}/año, pago {pay_y:.1%}/año, "
                   f"P&L neto {drag_y:+.1%}/año ({drag_y * 1e4:+.0f} pb); meses con pago {int((g.pago > 0).sum())}; "
                   f"peor mes de EWZ {worst:+.1%}")

# protocolo: P&L de cobertura marcado en t1 (P_real_protocolo - retorno_real), regla principal, eventos de Brasil
B = R[(R.regla == "principal") & (R.activo == "EWZ")].copy()
B["pnl_cobertura"] = B.P_real_protocolo - B.retorno_real
yrs = (pd.Timestamp("2026-10-26") - pd.Timestamp("2014-10-03")).days / 365.25
out.append(f"\nProtocolo (regla principal), EWZ, eventos de Brasil oct-2014 a oct-2026 ({yrs:.1f} años):")
for _, r in B.sort_values("evento").iterrows():
    out.append(f"  {r.evento}: {r.decision} {'' if r.decision == 'no hacer nada' else r.patas} | sin cubrir "
               f"{r.retorno_real:+.1%} -> {r.P_real_protocolo:+.1%} | P&L cobertura {r.pnl_cobertura:+.1%} | caja {r.costo:+.2%}")
out.append(f"  Total P&L cobertura {B.pnl_cobertura.sum():+.1%} = {B.pnl_cobertura.sum() / yrs * 1e4:+.0f} pb/año; "
           f"caja neta pagada {B.costo.clip(lower=0).sum():.2%} en {yrs:.0f} años; eventos cubiertos {int((B.decision != 'no hacer nada').sum())} de {len(B)}")
txt = "DRAG DEL HEDGE PERMANENTE (EWZ, VXEWZ) vs PROTOCOLO\n" + "\n".join(out) + "\n"
open(sys.argv[5], "w").write(txt)
P.to_csv(sys.argv[5].replace(".txt", "_meses.csv"), index=False)
print(txt)
