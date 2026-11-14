"""
Adaptador iVolatility (Data Download, "Options prices NBBO") -> esquema tipo COTAHIST que usa framework.py.

Columnas de entrada: symbol, exchange, date, adjusted close, option symbol, expiration, strike, call/put,
style, ask, bid, volume, open interest, unadjusted.

Reglas (protocolo, paso 1, mercado EE.UU.):
  - spot del día = 'unadjusted' (precio sin ajustar, consistente con los strikes)
  - opción líquida: bid > 0, ask > 0, spread <= 15% del mid + 0,03 y open interest >= 100
    (tabla de parámetros congelada). Se codifica en TOTNEG = 20 si OI >= 100 para reusar los filtros de
    framework.py; si no, TOTNEG = volumen del día (sirve para el umbral de 5 negocios de la IV ATM).
    11/11/2026: se quita la alternativa "volumen >= 20" de la versión anterior: no está en la tabla de parámetros.
  - no hay último negocio: PREULT de la opción = mid
  - estilo americano: se valúa como europeo (Black-76); con 1-3 semanas a vencimiento la prima de ejercicio
    anticipado es chica, salvo puts muy dentro del dinero.
"""
import pandas as pd


def load_ivol(paths, symbols=None):
    d = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    if symbols:
        d = d[d.symbol.isin(symbols)]
    d = d.drop_duplicates(["date", "option symbol"])
    d["DATA"] = pd.to_datetime(d["date"], format="%m/%d/%Y")
    d["DATVEN"] = pd.to_datetime(d["expiration"], format="%m/%d/%Y")
    liq = d["open interest"] >= 100
    opt = pd.DataFrame({
        "DATA": d.DATA,
        "TPMERC": d["call/put"].map({"C": "070", "P": "080"}),
        "CODNEG": d["option symbol"].str.replace(" ", "", regex=False),
        "NOMRES": d.symbol,
        "PREEXE": d.strike.astype(float),
        "PREOFC": d.bid.astype(float),
        "PREOFV": d.ask.astype(float),
        "PREULT": ((d.bid + d.ask) / 2).astype(float),
        "TOTNEG": liq.map({True: 20, False: 0}).where(liq, d.volume).astype(int),
        "VOLTOT": d.volume.astype(float),
        "OI": d["open interest"].astype(int),
        "DATVEN": d.DATVEN,
    })
    spot = (d.groupby(["symbol", "DATA"]).agg(PREULT=("unadjusted", "first"), ADJ=("adjusted close", "first"))
            .reset_index())
    spot = pd.DataFrame({"DATA": spot.DATA, "TPMERC": "010", "CODNEG": spot.symbol, "NOMRES": spot.symbol,
                         "PREEXE": 0.0, "PREOFC": 0.0, "PREOFV": 0.0, "PREULT": spot.PREULT, "TOTNEG": 0,
                         "VOLTOT": 0.0, "OI": 0, "DATVEN": pd.NaT})
    return pd.concat([opt, spot], ignore_index=True)
