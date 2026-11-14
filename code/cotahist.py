"""
Parser del archivo COTAHIST de B3 (layout oficial, registros de 245 caracteres).

Uso:
    from cotahist import read_cotahist, option_chain
    df = read_cotahist("COTAHIST_M102022.ZIP")          # acepta .ZIP o .TXT
    chain = option_chain(df, date="2022-10-28", underlying="BOVA11")

Layout (posiciones 1-based, B3 "SeriesHistoricas_Layout"):
  TIPREG 1-2 | DATA 3-10 | CODBDI 11-12 | CODNEG 13-24 | TPMERC 25-27 | NOMRES 28-39
  ESPECI 40-49 | PRAZOT 50-52 | MODREF 53-56 | PREABE 57-69 | PREMAX 70-82
  PREMIN 83-95 | PREMED 96-108 | PREULT 109-121 | PREOFC 122-134 | PREOFV 135-147
  TOTNEG 148-152 | QUATOT 153-170 | VOLTOT 171-188 | PREEXE 189-201 | INDOPC 202
  DATVEN 203-210 | FATCOT 211-217 | PTOEXE 218-230 | CODISI 231-242 | DISMES 243-245
Precios con 2 decimales implícitos. TPMERC: 010 vista, 070 opción de compra, 080 opción de venta.

11/11/2026: se agrega `roots` a read_cotahist para filtrar por raíz de CODNEG al leer (archivos de 90 MB).
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

_COLS = [
    ("TIPREG", 0, 2), ("DATA", 2, 10), ("CODBDI", 10, 12), ("CODNEG", 12, 24),
    ("TPMERC", 24, 27), ("NOMRES", 27, 39), ("ESPECI", 39, 49), ("PRAZOT", 49, 52),
    ("MODREF", 52, 56), ("PREABE", 56, 69), ("PREMAX", 69, 82), ("PREMIN", 82, 95),
    ("PREMED", 95, 108), ("PREULT", 108, 121), ("PREOFC", 121, 134), ("PREOFV", 134, 147),
    ("TOTNEG", 147, 152), ("QUATOT", 152, 170), ("VOLTOT", 170, 188), ("PREEXE", 188, 201),
    ("INDOPC", 201, 202), ("DATVEN", 202, 210), ("FATCOT", 210, 217), ("PTOEXE", 217, 230),
    ("CODISI", 230, 242), ("DISMES", 242, 245),
]
_PRICE = ["PREABE", "PREMAX", "PREMIN", "PREMED", "PREULT", "PREOFC", "PREOFV", "PREEXE"]


def _lines(path: Path):
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                with z.open(name) as fh:
                    for raw in io.TextIOWrapper(fh, encoding="latin-1"):
                        yield raw
    else:
        with open(path, encoding="latin-1") as fh:
            yield from fh


def read_cotahist(path, keep_markets=("010", "070", "080"), roots=None) -> pd.DataFrame:
    """Lee un COTAHIST (anual, mensual o diario). Devuelve solo registros tipo 01.
    roots: tupla de prefijos de CODNEG a conservar (p.ej. ("BOVA",)); None = todos."""
    path = Path(path)
    rows = []
    for line in _lines(path):
        if not line.startswith("01"):
            continue
        tp = line[24:27]
        if keep_markets and tp not in keep_markets:
            continue
        if roots and not line[12:24].startswith(roots):
            continue
        rows.append([line[a:b].strip() for _, a, b in _COLS])
    df = pd.DataFrame(rows, columns=[c for c, _, _ in _COLS])
    if df.empty:
        return df
    df["DATA"] = pd.to_datetime(df["DATA"], format="%Y%m%d")
    df["DATVEN"] = pd.to_datetime(df["DATVEN"], format="%Y%m%d", errors="coerce")
    for c in _PRICE:
        df[c] = df[c].astype("int64") / 100.0
    for c in ["TOTNEG", "QUATOT", "FATCOT"]:
        df[c] = df[c].astype("int64")
    df["VOLTOT"] = df["VOLTOT"].astype("int64") / 100.0
    # precios por unidad (FATCOT = factor de cotización, normalmente 1)
    for c in _PRICE:
        df[c] = df[c] / df["FATCOT"].clip(lower=1)
    return df


def spot(df: pd.DataFrame, date, ticker: str) -> float:
    d = pd.Timestamp(date)
    s = df[(df.DATA == d) & (df.TPMERC == "010") & (df.CODNEG == ticker)]
    if s.empty:
        raise ValueError(f"No hay precio vista para {ticker} el {d.date()}")
    return float(s.iloc[0].PREULT)


def option_chain(df: pd.DataFrame, date, underlying: str, nomres: str | None = None) -> pd.DataFrame:
    """
    Cadena de opciones de un subyacente en una fecha.
    En COTAHIST la opción no trae el ticker del subyacente; se identifica por NOMRES
    (nombre resumido de la empresa, p.ej. 'ISHARES BOVA', 'PETROBRAS') y la raíz del código
    (las primeras 4 letras: BOVA, PETR, VALE...).
    """
    d = pd.Timestamp(date)
    root = underlying[:4]
    o = df[(df.DATA == d) & (df.TPMERC.isin(["070", "080"])) & (df.CODNEG.str.startswith(root))].copy()
    if nomres:
        o = o[o.NOMRES == nomres]
    o["type"] = o.TPMERC.map({"070": "C", "080": "P"})
    o["K"] = o.PREEXE
    o["bid"] = o.PREOFC
    o["ask"] = o.PREOFV
    o["last"] = o.PREULT
    o["trades"] = o.TOTNEG
    o["volume_brl"] = o.VOLTOT
    o["expiry"] = o.DATVEN
    cols = ["CODNEG", "ESPECI", "type", "K", "expiry", "bid", "ask", "last", "trades", "volume_brl"]
    return o[cols].sort_values(["expiry", "type", "K"]).reset_index(drop=True)
