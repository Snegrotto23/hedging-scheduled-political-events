"""
Figuras y tablas del paper (13/11/2026), a partir del registro final. No cambia ningún resultado.
Textos de las figuras en inglés (13/11, tarde; antes en español): mismos nombres de archivo, mismos números.
  fig1_curva_brasil2026   : probabilidad de quedar por debajo de K que cobra el mercado (spreads verticales, mids)
                            vs la mezcla del framework (p central, u, d, vol base) vs una lognormal a la IV ATM;
                            EWZ y BOVA11, víspera del 2T de 2026.
  fig2_payoff_collars2026 : resultado al vencimiento del collar elegido vs sin cubrir, EWZ y BOVA11 2026-2T.
  fig3_severidad          : escenario estimado (d si salió malo, u si salió bueno) vs retorno realizado.
  fig4_drag               : P&L acumulado del put permanente sobre EWZ (ATM y 5% OTM) vs el protocolo, 2014-2026.
  tabla_cuatro_resultados.csv : regla principal, una fila por evento x activo.
Paleta: slots 1-3 de la paleta de referencia (validada all-pairs, modo claro); el 3 (verde agua) está bajo 3:1 de
contraste: se compensa con etiquetas directas y marcadores de forma distinta.
Uso: python figuras.py <dir_datos> <event_inputs.csv> <dir_cierres> <DTB4WK.csv> <dir_resultados> <dir_figuras>
     <dir_resultados> = salida de run_final.py (registro_final.csv, framework_results_final.pkl) y de
     drag_permanente.py (drag_permanente_meses.csv) y analisis_extra.py (severidad_estimada_vs_realizada.csv)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import framework as fw
from event_inputs import load_events
from ivol_adapter import load_ivol

D, CSV, CL, TB, RES, FIG = (Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5]),
                            Path(sys.argv[6]))
FIG.mkdir(exist_ok=True)
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "savefig.facecolor": SURF, "lines.linewidth": 2})
pct = matplotlib.ticker.PercentFormatter(1.0, decimals=0)

R = pd.read_csv(RES / "registro_final.csv")
RS = pd.read_pickle(RES / "framework_results_final.pkl")
tb = pd.read_csv(TB, parse_dates=["observation_date"]).dropna().set_index("observation_date").iloc[:, 0].astype(float) / 100
EV_LOC = load_events(CSV, only_eligible=True)
EV_US = load_events(CSV, only_eligible=True, us_dates=True)
for v in EV_US.values():
    v["r"] = float(tb[tb.index <= pd.Timestamp(v["pre"])].iloc[-1])


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


def load_case(tk, ek):
    ev = EV_LOC[ek] if tk == "BOVA11" else EV_US[ek]
    t0, t1 = pd.Timestamp(ev["pre"]), pd.Timestamp(ev["post"])
    A = pd.read_pickle(D / "cotahist_bova_petr.pkl") if tk == "BOVA11" else load_ivol(
        sorted(p for p in (D / "ivol").iterdir() if p.suffix.lower() in (".csv", ".zip")), symbols=[tk])
    fw.DF_ALL = A[(A.DATA >= t0 - pd.Timedelta(days=45)) & (A.DATA <= t1)].reset_index(drop=True)
    return ev



def ev_en(e):
    """Event code -> English label for the figures (BR-2026-2T -> 2026 runoff)."""
    y, k = e[3:7], e[8:]
    return f"{y} " + {"1T": "1st round", "2T": "runoff", "PASO": "primary", "LEG": "legislative",
                      "PBA": "provincial"}.get(k, k)


# ---------------------------------------------------------------- fig 1: curva implícita vs mezcla
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
for ax, (tk, root, grp) in zip(axes, [("EWZ", "EWZ", "main"), ("BOVA11", "BOVA", "main")]):
    ev = load_case(tk, "BR-2026-2T")
    o = RS[(grp, "BR-2026-2T", tk, "principal")]
    c = o["curva"]
    S0, x1, r, sb, iv1 = c["spot"], pd.Timestamp(c["venc_evento"]), ev["r"], c["vol_base"], c["iv_evento"]
    T1 = fw.bdT(ev["pre"], x1)
    DF = np.exp(-r * T1)
    p = o["registro"]["p_central"]
    u, d = o["registro"]["u"], o["registro"]["d"]
    ch = fw.chain(ev["pre"], root, x1)
    ch = ch[ch.quoted & ((ch.ask - ch.bid) <= 0.20 * ch.mid + 0.02) & (ch.TOTNEG >= 5)]   # filtro "tight" del paso 5a
    pts = []
    puts = ch[(ch.type == "P") & (ch.K <= S0 * 1.02)].sort_values("K")
    for (k1, m1), (k2, m2) in zip(puts[["K", "mid"]].values[:-1], puts[["K", "mid"]].values[1:]):
        pts.append(((k1 + k2) / 2, (m2 - m1) / (k2 - k1) / DF))
    calls = ch[(ch.type == "C") & (ch.K >= S0 * 0.98)].sort_values("K")
    for (k1, m1), (k2, m2) in zip(calls[["K", "mid"]].values[:-1], calls[["K", "mid"]].values[1:]):
        pts.append(((k1 + k2) / 2, 1 - (m1 - m2) / (k2 - k1) / DF))
    pts = np.array([q for q in pts if 0.6 * S0 <= q[0] <= 1.3 * S0 and -0.05 <= q[1] <= 1.05])
    K = np.linspace(0.65 * S0, 1.25 * S0, 300)
    mix = fw.mix_prob_below(S0, K, T1, p, u, d, sb, r)
    logn = fw.mix_prob_below(S0, K, T1, 1.0, 0.0, 0.0, iv1, r)
    x = K / S0 - 1
    ax.plot(x, logn, color=C2, lw=1.5, ls=(0, (4, 2)), label=f"lognormal at the ATM IV ({iv1:.0%})")
    ax.plot(x, mix, color=C1, lw=2, label=f"framework mixture (p={p:.2f}, u={u:+.0%}, d={d:+.0%})")
    ax.scatter(pts[:, 0] / S0 - 1, pts[:, 1], s=22, color=INK2, zorder=3, edgecolor=SURF, linewidth=0.8,
               label="market (vertical spreads, mid)")
    S1 = o["real"]["spot_post"]
    for xv, lab in [(d, "d"), (u, "u"), (S1 / S0 - 1, "realized")]:
        ax.axvline(xv, color=INK2, lw=0.8, ls=":")
        ax.text(xv, 1.02, lab, ha="center", va="bottom", color=INK2, fontsize=8, transform=ax.get_xaxis_transform())
    ax.set_title(f"{tk}, day before the 2026 runoff (expiry {x1:%b} {x1.day})", fontsize=9, color=INK, loc="left", pad=14)
    ax.set_xlabel("strike vs spot")
    ax.xaxis.set_major_formatter(pct)
    ax.yaxis.set_major_formatter(pct)
    ax.set_ylim(-0.02, 1.0)
axes[0].set_ylabel("probability of ending below the strike")
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, ["lognormal at the ATM IV", "framework mixture (central p, u, d, base volatility)", "market (vertical spreads, mid)"],
           loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.06), fontsize=8)
fig.tight_layout(rect=(0, 0.06, 1, 1))
save(fig, "fig1_curva_brasil2026")

# ---------------------------------------------------------------- fig 2: payoff de los collars 2026-2T
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
for ax, (tk, root) in zip(axes, [("EWZ", "EWZ"), ("BOVA11", "BOVA")]):
    ev = load_case(tk, "BR-2026-2T")
    o = RS[("main", "BR-2026-2T", tk, "principal")]
    ch_el = o["decision"]["elegida"]
    c = o["curva"]
    S0, x1, r = c["spot"], pd.Timestamp(c["venc_evento"]), ev["r"]
    T1 = fw.bdT(ev["pre"], x1)
    growth = np.exp(r * T1)
    chain = fw.chain(ev["pre"], root, x1).set_index(["type", "K"])
    import re
    h = float(ch_el["patas"].split(" x ")[0])
    legs = [(1 if s == "+" else -1, t, float(k)) for s, t, k in re.findall(r"([+-])([PC])([\d.]+)", ch_el["patas"])]
    xr = np.linspace(-0.40, 0.25, 400)
    ST = S0 * (1 + xr)
    hedge = sum(s * (fw.payoff(t, K, ST) - chain.loc[(t, K), "ask" if s > 0 else "bid"] * growth) for s, t, K in legs) / S0
    ax.plot(xr, xr, color=C2, lw=1.5, ls=(0, (4, 2)), label="unhedged")
    ax.plot(xr, xr + h * hedge, color=C1, lw=2, label=f"collar {ch_el['patas']}")
    u, d = o["registro"]["u"], o["registro"]["d"]
    for xv, lab in [(d, "d"), (u, "u")]:
        ax.axvline(xv, color=INK2, lw=0.8, ls=":")
        ax.text(xv, 1.02, lab, ha="center", va="bottom", color=INK2, fontsize=8, transform=ax.get_xaxis_transform())
    ret, preal = o["real"]["retorno"], o["registro"]["P_real_protocolo"]
    ax.scatter([ret], [ret], s=40, color=C2, zorder=4, edgecolor=SURF, linewidth=1.5)
    ax.scatter([ret], [preal], s=40, color=C1, zorder=4, edgecolor=SURF, linewidth=1.5, marker="D")
    ax.annotate(f"at $t_1$: {ret:+.1%} → {preal:+.1%}", xy=(ret, preal), xytext=(ret + 0.06, preal - 0.14),
                fontsize=8, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
    ax.set_title(f"{tk}, 2026 runoff: {ch_el['patas']}, net cash {ch_el['costo']:+.2%}", fontsize=9, color=INK, loc="left", pad=14)
    ax.set_xlabel("asset return at expiry")
    ax.xaxis.set_major_formatter(pct)
    ax.yaxis.set_major_formatter(pct)
    ax.axhline(0, color=INK2, lw=0.6)
axes[0].set_ylabel("position return")
fig.legend([plt.Line2D([], [], color=C2, lw=1.5, ls=(0, (4, 2))), plt.Line2D([], [], color=C1, lw=2)],
           ["unhedged", "with the main-rule collar (payoff at expiry; marker = realized mark at $t_1$)"],
           loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.06), fontsize=8)
fig.tight_layout(rect=(0, 0.06, 1, 1))
save(fig, "fig2_payoff_collars2026")

# ---------------------------------------------------------------- fig 3: severidad estimada vs realizada
S = pd.read_csv(RES / "severidad_estimada_vs_realizada.csv")
S["region"] = np.where(S.evento.str.startswith("BR"), "Brazil (BOVA11 and EWZ)",
                       np.where(S.evento.str.startswith("AR"), "Argentina (ARGT, GGAL, YPF)", "India, Mexico, Chile"))
fig, ax = plt.subplots(figsize=(5.6, 4.6))
lim = (-0.62, 0.42)
ax.plot(lim, lim, color=INK2, lw=0.8, ls=(0, (4, 2)))
ax.text(0.16, 0.20, "estimated = realized", color=INK2, fontsize=7.5, rotation=40)
ax.axhline(0, color=INK2, lw=0.6)
ax.axvline(0, color=INK2, lw=0.6)
fuera = S[(S.escenario_estimado < lim[0]) | (S.escenario_estimado > lim[1])]
for (reg, col, mk) in [("Brazil (BOVA11 and EWZ)", C1, "o"), ("Argentina (ARGT, GGAL, YPF)", C2, "s"),
                       ("India, Mexico, Chile", C3, "^")]:
    g = S[(S.region == reg) & ~S.index.isin(fuera.index)]
    ax.scatter(g.escenario_estimado, g.retorno_real, s=34, color=col, marker=mk, edgecolor=SURF, linewidth=1.2,
               label=f"{reg} (n={len(g)})", zorder=3)
for ek, tk, dx, dy in [("BR-2026-2T", "EWZ", 0.02, -0.08), ("AR-2019-PASO", "GGAL", 0.02, 0.0),
                       ("AR-2025-LEG", "GGAL", -0.40, 0.0), ("CL-2021-2T", "ECH", 0.07, -0.10),
                       ("MX-2024", "EWW", 0.03, -0.03), ("AR-2025-PBA", "GGAL", -0.12, 0.09)]:
    q = S[(S.evento == ek) & (S.activo == tk)].iloc[0]
    ax.annotate(f"{tk} {ev_en(ek)}", xy=(q.escenario_estimado, q.retorno_real),
                xytext=(q.escenario_estimado + dx, q.retorno_real + dy), fontsize=7.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.5))
ax.set_xlim(lim)
ax.set_ylim(lim)
ax.xaxis.set_major_formatter(pct)
ax.yaxis.set_major_formatter(pct)
ax.set_xlabel("ex ante scenario (d if the bad outcome occurred, u if the good one)")
ax.set_ylabel("realized return from $t_0$ to $t_1$")
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.92), fontsize=7.5)
if len(fuera):
    fig.text(0.02, -0.01, "Off the chart (estimated scenario with p near 1):\n" + "; ".join(
        f"{a} {ev_en(e)} ({x:+.0%}, realized {y:+.1%})" for e, a, x, y in
        fuera[["evento", "activo", "escenario_estimado", "retorno_real"]].values), fontsize=6.5, color=INK2, ha="left")
fig.tight_layout(rect=(0, 0.05, 1, 1))
save(fig, "fig3_severidad")

# ---------------------------------------------------------------- fig 4: drag acumulado
M = pd.read_csv(RES / "drag_permanente_meses.csv", parse_dates=["compra", "vence"])
M = M[(M.compra >= "2014-10-01") & (M.compra < "2026-11-01")]
fig, ax = plt.subplots(figsize=(8, 3.6))
for mny, col, ls, lab in [(1.00, C2, "-", "1-month ATM put, rolled"), (0.95, C3, "-", "1-month 5% OTM put, rolled")]:
    g = M[M.mny == mny].sort_values("vence")
    y = g.pnl.cumsum()
    ax.step(g.vence, y, where="post", color=col, lw=2, label=lab)
    ax.text(g.vence.iloc[-1] + pd.Timedelta(days=40), y.iloc[-1], f"{lab.split(', ')[0]}: {y.iloc[-1]:+.0%}",
            color=INK, fontsize=8, va="center")
B = R[(R.regla == "principal") & (R.activo == "EWZ")].copy()
B["pnl"] = B.P_real_protocolo - B.retorno_real
B["t1"] = pd.to_datetime(B.t1)
B = B.sort_values("t1")
xs = [pd.Timestamp("2014-10-01")] + list(B.t1) + [pd.Timestamp("2026-11-01")]
ys = [0.0] + list(B.pnl.cumsum()) + [B.pnl.sum()]
ax.step(xs, ys, where="post", color=C1, lw=2, label="event hedging (main rule), 7 Brazilian events")
ax.text(xs[-1] + pd.Timedelta(days=40), ys[-1], f"event hedging: {ys[-1]:+.0%}", color=INK, fontsize=8, va="center")
for _, b in B[B.decision != "no hacer nada"].iterrows():
    ax.annotate(f"{ev_en(b.evento)}: {b.pnl:+.1%}", xy=(b.t1, B[B.t1 <= b.t1].pnl.sum()), xytext=(0, 22),
                textcoords="offset points", ha="center", fontsize=7.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.5))
ax.axhline(0, color=INK2, lw=0.6)
ax.yaxis.set_major_formatter(pct)
ax.set_ylabel("cumulative hedge P&L\n(sum, % of notional)")
ax.set_xlim(pd.Timestamp("2014-08-01"), pd.Timestamp("2028-06-01"))
ax.legend(loc="lower left", fontsize=8)
ax.set_title("EWZ, Oct 2014 to Oct 2026: permanent put (priced with VXEWZ) vs hedging only the events",
             fontsize=9, color=INK, loc="left")
fig.tight_layout()
save(fig, "fig4_drag")

# ---------------------------------------------------------------- tabla de cuatro resultados
P = R[R.regla == "principal"].copy()
P["estado"] = np.where(P.motivo.fillna("").str.contains("sin opciones líquidas|sin IV ATM"), "sin opciones",
                       np.where(P.cubrio == True, "cubrió", "no cubrió"))  # noqa: E712
P["region"] = np.where(P.evento.str.startswith("BR"), "Brasil", "Resto")
P["pnl_cobertura"] = P.P_real_protocolo - P.retorno_real
P[["region", "grupo", "evento", "activo", "resultado", "estado", "decision", "motivo", "patas", "costo", "retorno_real",
   "P_real_protocolo", "pnl_cobertura", "P_real_ingenuo"]].to_csv(FIG / "tabla_cuatro_resultados.csv", index=False)
print(pd.crosstab([P.region, P.estado], P.resultado.fillna("n/e")))
