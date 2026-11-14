"""
Download the public (freely available) raw data needed to replicate the paper.

This script is NOT part of the frozen code in code/. It only fetches files and puts
them where the replication commands in docs/REPLICATION.md expect them. It does not
touch iVolatility data, which is purchased and must be bought separately
(see docs/ivolatility_ticker_days.csv).

Usage (from the repository root):
    python data_download/download_public_data.py replica

Creates:
    replica/raw/cotahist/COTAHIST_*.ZIP     B3 historical quotes (BOVA11 options and spot)
    replica/raw/cierres/<ticker>_us_d.csv   Stooq daily closes (EWZ, EWW, INDA, ECH, ARGT, GGAL, YPF)
    replica/raw/fred/DTB4WK.csv             FRED 4-week T-bill
    replica/raw/fred/VXEWZCLS.csv           FRED CBOE Brazil ETF volatility index

Notes
- Stooq prices are dividend-adjusted and Stooq re-adjusts its history when new
  distributions occur. The paper used files downloaded on 13 Nov 2026; the scale
  factors relating those files to iVolatility's unadjusted closes are in
  results/escalas_cierres.csv. A later download may differ slightly.
- Stooq's terms do not allow redistribution of its data, which is why the files
  are not in this repository. If Stooq asks for a captcha or an API key, download
  each file manually from https://stooq.com/q/d/?s=<ticker>.us (link "Download
  data in csv file") and save it as raw/cierres/<ticker>_us_d.csv.
- B3 occasionally moves its download host. If a COTAHIST link fails, look for
  "Series historicas" on b3.com.br and download the same file names by hand.
"""
import sys
import urllib.request
from pathlib import Path

COTAHIST = ["M092014", "M102014", "M092018", "M102018", "M092022", "M102022",
            "M092026", "M102026", "D02102026", "D05102026", "D23102026", "D26102026"]
B3_URL = "https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_{}.ZIP"

STOOQ = ["ewz", "eww", "inda", "ech", "argt", "ggal", "ypf"]
STOOQ_URL = "https://stooq.com/q/d/l/?s={}.us&i=d"

FRED = ["DTB4WK", "VXEWZCLS"]
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"


def fetch(url, dest, check=None):
    if dest.exists():
        print(f"  exists  {dest}")
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=120).read()
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED  {url}  ({e})")
        return False
    if check and not check(data):
        print(f"  FAILED  {url}  (unexpected content; download it by hand, see the notes in this file)")
        return False
    dest.write_bytes(data)
    print(f"  ok      {dest}  ({len(data):,} bytes)")
    return True


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "replica")
    for sub in ("raw/cotahist", "raw/cierres", "raw/fred", "raw/ivol", "datos", "data", "out"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    ok = True
    print("B3 COTAHIST")
    for f in COTAHIST:
        ok &= fetch(B3_URL.format(f), root / "raw/cotahist" / f"COTAHIST_{f}.ZIP",
                    check=lambda d: d[:2] == b"PK")
    print("Stooq daily closes")
    for t in STOOQ:
        ok &= fetch(STOOQ_URL.format(t), root / "raw/cierres" / f"{t}_us_d.csv",
                    check=lambda d: d.startswith(b"Date,Open,High,Low,Close"))
    print("FRED")
    for s in FRED:
        ok &= fetch(FRED_URL.format(s), root / "raw/fred" / f"{s}.csv",
                    check=lambda d: d.startswith(b"observation_date"))

    print("\nNext: copy inputs/event_inputs.csv to", root / "datos",
          "and put the iVolatility ZIP files in", root / "raw/ivol")
    print("All downloads succeeded." if ok else "Some downloads failed; see messages above.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
