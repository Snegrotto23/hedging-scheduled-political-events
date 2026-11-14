"""
Análisis complementario del registro final (13/11/2026). No cambia ninguna decisión: re-marca y mide.
  1. Marcado alternativo en t1: cada pata de la estructura elegida a max(mid, intrínseco) en vez de mid (caso INDA:
     el 4/6/2024 el P54 tenía mid 2,125 < intrínseco 2,58). Se aplica a comprados y vendidos (conservador para los
     vendidos). Se reporta para las tres reglas y para θ 10% / 50% si se pasa el registro de robustez.
  2. Severidad estimada vs realizada, regla principal: u y d del modelo (p central) contra el retorno realizado de t0 a
     t1; salto implícito ex ante (term structure, paso 3) contra el salto ex post de Dubinsky et al. (2019) por la
     caída de la IV del mismo vencimiento: sigma_post^2 = IV_t0^2 T_t0 - IV_t1^2 T_t1 - base^2 (t1 - t0).
Repite la carga de datos de run_final.py (misma ventana [t0 - 45, t1], mismos cierres reescalados, misma tasa) para
no ejecutar run_final al importarlo.
Uso: python analisis_extra.py <dir_datos> <event_inputs.csv> <dir_cierres> <DTB4WK.csv> <registro_final.csv>
                               <framework_results_final.pkl> <dir_salida> [<registro_robustez.csv> <results_robustez.pkl>]
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import framework as fw
from event_inputs import load_events
from ivol_adapter import load_ivol

D, CSV, CL, TB, REG, PKL, OUT = (Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), sys.argv[4], sys.argv[5],
                                 sys.argv[6], Path(sys.argv[7]))
EXTRA = (sys.argv[8], sys.argv[9]) if len(sys.argv) > 9 else None
OUT.mkdir(exist_ok=True)
WINDOW_DAYS = 45

tb = pd.read_csv(TB, parse_dates=["observation_date"]).dropna().set_index("observation_date").iloc[:, 0].astype(float) / 100
EV_LOC = load_events(CSV, only_eligible=True)
EV_US = load_events(CSV, only_eligible=True, us_dates=True)
for v in EV_US.values():
    v["r"] = float(tb[tb.index <= pd.Timestamp(v["pre"])].iloc[-1])
COT = pd.read_pickle(D / "cotahist_bova_petr.pkl")
IVOL_FILES = sorted(p for p in (D / "ivol").iterdir() if p.suffix.lower() in (".csv", ".zip"))
cache, closes = {}, {}


def stooq(tk):
    if tk not in closes:
        f = sorted(CL.glob(f"*{tk.lower()}_us_d.csv"))
        closes[tk] = (pd.read_csv(f[0], parse_dates=["Date"]).set_index("Date")["Close"].astype(float)
                      if f else pd.Series(dtype=float))
    return closes[tk]


def with_closes(A, tk, lo, hi):
    s = stooq(tk)
    s = s[(s.index >= lo) & (s.index <= hi)]
    sp = A[(A.TPMERC == "010") & (A.CODNEG == tk)].drop_duplicates("DATA").set_index("DATA").PREULT
    common = s.index.intersection(sp[(sp.index >= lo) & (sp.index <= hi)].index)
    if s.empty or len(common) == 0:
        return A
    k = float((sp.loc[common] / s.loc[common]).median())
    new = s[~s.index.isin(sp.index)] * k
    rows = pd.DataFrame({"DATA": new.index, "TPMERC": "010", "CODNEG": tk, "NOMRES": tk, "PREEXE": 0.0, "PREOFC": 0.0,
                         "PREOFV": 0.0, "PREULT": new.values, "TOTNEG": 0, "VOLTOT": 0.0, "OI": 0, "DATVEN": pd.NaT})
    return pd.concat([A, rows], ignore_index=True)


def set_data(grp, ek, tk, root):
    E = EV_LOC if (tk == "BOVA11") else EV_US
    ev = E[ek]
    t0, t1 = pd.Timestamp(ev["pre"]), pd.Timestamp(ev["post"])
    lo = t0 - pd.Timedelta(days=WINDOW_DAYS)
    if tk == "BOVA11":
        A = COT
    else:
        if tk not in cache:
            cache[tk] = load_ivol(IVOL_FILES, symbols=[tk])
        A = with_closes(cache[tk], tk, lo, t1)
    fw.DF_ALL = A[(A.DATA >= lo) & (A.DATA <= t1)].reset_index(drop=True)
    return ev


LEG = re.compile(r"([+-])([PC])([\d.]+)")


def remark(ev, root, tk, o, patas):
    """P_real con mid (control) y con max(mid, intrínseco)."""
    h = float(patas.split(" x ")[0])
    legs = [(1 if s == "+" else -1, t, float(k)) for s, t, k in LEG.findall(patas)]
    x1 = pd.Timestamp(o["curva"]["venc_evento"])
    S0, S1, ret = o["curva"]["spot"], o["real"]["spot_post"], o["real"]["retorno"]
    pre = fw.chain(ev["pre"], root, x1).set_index(["type", "K"])
    post = fw.chain(ev["post"], root, x1).set_index(["type", "K"])
    a = b = 0.0
    for side, t, K in legs:
        px = pre.loc[(t, K), "ask" if side > 0 else "bid"]
        m = float(post.loc[(t, K), "mid"])
        intr = max(K - S1, 0) if t == "P" else max(S1 - K, 0)
        a += side * (m - px)
        b += side * (max(m, intr) - px)
    return ret + h * a / S0, ret + h * b / S0


R = pd.read_csv(REG)
RES = pd.read_pickle(PKL)
regs = [(R, RES)]
if EXTRA:
    regs.append((pd.read_csv(EXTRA[0]), pd.read_pickle(EXTRA[1])))

# ---------------------------------------------------------------- 1. marcado alternativo
rows = []
for RR, RS in regs:
    for _, r in RR[RR.cubrio == True].iterrows():  # noqa: E712
        root = "BOVA" if r.activo == "BOVA11" else r.activo
        ev = set_data(r.grupo, r.evento, r.activo, root)
        o = RS[(r.grupo, r.evento, r.activo, r.regla)]
        p_mid, p_int = remark(ev, root, r.activo, o, r.patas)
        rows.append(dict(grupo=r.grupo, evento=r.evento, activo=r.activo, regla=r.regla, patas=r.patas,
                         retorno_real=r.retorno_real, P_real_mid=p_mid, P_real_registro=r.P_real_protocolo,
                         P_real_intrinseco=p_int, diferencia_pp=(p_int - p_mid) * 100))
M = pd.DataFrame(rows)
M["control_ok"] = (M.P_real_mid - M.P_real_registro).abs() < 1e-9
M.to_csv(OUT / "marcado_intrinseco.csv", index=False)

# ---------------------------------------------------------------- 2. severidad estimada vs realizada (principal)
rows = []
P = R[(R.regla == "principal") & R.decision.ne("NO EVALUABLE")]
for _, r in P.iterrows():
    root = "BOVA" if r.activo == "BOVA11" else r.activo
    ev = set_data(r.grupo, r.evento, r.activo, root)
    o = RES[(r.grupo, r.evento, r.activo, "principal")]
    c = o["curva"]
    x1 = pd.Timestamp(c["venc_evento"])
    S1 = o["real"]["spot_post"]
    T0, T1 = fw.bdT(ev["pre"], x1), fw.bdT(ev["post"], x1)
    iv1 = fw.atm_iv(ev["post"], root, x1, S1, ev["r"])
    var_post = c["iv_evento"] ** 2 * T0 - (iv1 ** 2 * T1 if np.isfinite(iv1) else np.nan) \
        - c["vol_base"] ** 2 * fw.bdT(ev["pre"], ev["post"])
    salto_post = float(np.sqrt(var_post)) if np.isfinite(var_post) and var_post > 0 else (0.0 if np.isfinite(var_post) else np.nan)
    est = r.d if r.resultado == "malo" else r.u
    rows.append(dict(grupo=r.grupo, evento=r.evento, activo=r.activo, resultado=r.resultado, p_central=r.p_central,
                     u=r.u, d=r.d, metodo=r.metodo, escenario_estimado=est, retorno_real=r.retorno_real,
                     ratio_real_estimado=r.retorno_real / est if est else np.nan,
                     salto_ex_ante=c["salto_implicito"], iv_t0=c["iv_evento"], iv_t1=iv1, salto_ex_post=salto_post,
                     abs_ret=abs(r.retorno_real), decision=r.decision, cubrio=r.cubrio))
S = pd.DataFrame(rows)
S.to_csv(OUT / "severidad_estimada_vs_realizada.csv", index=False)

# ---------------------------------------------------------------- resumen
pd.set_option("display.width", 260)
txt = ["MARCADO max(mid, intrínseco) vs mid, estructuras elegidas (pp = diferencia en el P&L real del caso)",
       f"control: P_real con mid reproduce el registro en {int(M.control_ok.sum())} de {len(M)} filas",
       M[["grupo", "evento", "activo", "regla", "patas", "retorno_real", "P_real_mid", "P_real_intrinseco",
          "diferencia_pp"]].round(4).to_string(index=False),
       "\nSEVERIDAD ESTIMADA vs REALIZADA (regla principal; escenario estimado = d si salió malo, u si salió bueno)",
       S[["grupo", "evento", "activo", "resultado", "p_central", "metodo", "escenario_estimado", "retorno_real",
          "ratio_real_estimado", "salto_ex_ante", "salto_ex_post", "abs_ret"]].round(3).to_string(index=False)]
ok = S[S.salto_ex_post.notna() & (S.salto_ex_ante > 0)]
txt.append(f"\nCasos con salto ex ante y ex post: {len(ok)}; correlación de Spearman salto ex ante vs |retorno| "
           f"{ok.salto_ex_ante.corr(ok.abs_ret, method='spearman'):.2f}; salto ex post vs |retorno| "
           f"{ok.salto_ex_post.corr(ok.abs_ret, method='spearman'):.2f}; mediana salto ex post / ex ante "
           f"{(ok.salto_ex_post / ok.salto_ex_ante).median():.2f}")
(OUT / "analisis_extra.txt").write_text("\n".join(txt) + "\n")
print("\n".join(txt))
