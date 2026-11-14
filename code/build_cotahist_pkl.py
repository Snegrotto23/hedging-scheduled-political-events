"""
Arma la base de B3 que usa run_events.py a partir de los COTAHIST tal como se bajan de B3 (.ZIP o .TXT).
Conserva solo BOVA (BOVA11 y sus opciones) y PETR (PETR4 y sus opciones); vista y opciones (TPMERC 010/070/080).

Uso: python build_cotahist_pkl.py <carpeta con COTAHIST_*.ZIP> <salida .pkl>
Archivos usados el 11/11/2026: COTAHIST_M092014, M102014, M092018, M102018, M092022, M102022, M092026,
D02102026, D05102026, D23102026, D26102026 (los anuales 2002/2006/2010 no hacen falta para estas corridas).
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from cotahist import read_cotahist

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
files = sorted(p for p in src.iterdir() if p.name.upper().startswith("COTAHIST_") and p.suffix.upper() in (".ZIP", ".TXT")
               and not p.name.upper().startswith("COTAHIST_A"))
dfs = []
for f in files:
    d = read_cotahist(f, roots=("BOVA", "PETR"))
    print(f"{f.name}: {len(d)} registros")
    dfs.append(d)
df = pd.concat(dfs, ignore_index=True).drop_duplicates(["DATA", "CODNEG", "TPMERC", "DATVEN", "PREEXE"])
df.to_pickle(dst)
print(f"{dst}: {len(df)} registros, {df.DATA.nunique()} días")
