# Data sources

Everything the code reads, where it comes from, and whether it is in this repository.

## In the repository

| Folder | Content | Origin |
|---|---|---|
| `inputs/event_inputs.csv` | one row per event: dates, rate, probability grid, polls, priors | built by `code/build_event_inputs.py` |
| `inputs/event_probabilities.csv` | every prediction-market price, bookmaker quote (margin removed) and published forecast used in the grids, with source and date | `code/data_probs.py` |
| `inputs/event_polls.csv` | polls used for each event | `code/data_events.py` |
| `inputs/event_poll_miss_1T.csv` | historical first-round poll errors | `code/data_events.py` |
| `inputs/event_scenarios.csv` | good/bad outcome definitions per event | `code/data_scen.py` |
| `results/` | outputs of the runs, see [`REPLICATION.md`](REPLICATION.md) | produced by `code/` |

The probability, poll and forecast figures were compiled by the author from public sources (prediction markets, exchanges, bookmakers, pollsters, banks, consultancies, forecasting models and press reports), collected with a web research assistant (an AI search tool, Perplexity) and checked one by one (paper, Section 4, "Probabilities, Polls and Scenarios"). Each probability source in `code/data_probs.py` records its source, date, contract, URL when available and a verification status `verif`:

- `si`: verified against the original publication;
- `pdf`: taken as reported, with its citation and date, by the research assistant; the original could not be opened;
- `no`: not verifiable; excluded from the grids;
- `conflicto`: sources disagree; see the note on that entry.

The column `verificacion` of `inputs/event_inputs.csv` gives, per event, how many of the grid sources were verified against the original. Estimates produced by the research assistant itself are recorded and excluded.

## Not in the repository

### iVolatility (purchased)

End-of-day option chains for the US-listed ETFs and ADRs (EWZ, EWW, INDA, ECH, EC, CIB, TUR, ARGT, GGAL, YPF), product "Data Download → Options prices (NBBO)". The licence does not allow redistribution, so the files are not included.

- Exact list: [`ivolatility_ticker_days.csv`](ivolatility_ticker_days.csv), 125 ticker-days in two purchases (11 and 12 Nov 2026).
- Columns read by `code/ivol_adapter.py`: symbol, exchange, date, adjusted close, option symbol, expiration, strike, call/put, style, ask, bid, volume, open interest, unadjusted.
- Place the ZIP files, unchanged, in `replica/raw/ivol/` and `replica/data/ivol/`.

Without these files the ETF cases cannot be re-run. The BOVA11 cases (B3 data only) can.

### B3 (public)

COTAHIST historical-quote files for BOVA11 spot and options:

| Type | Files |
|---|---|
| Monthly | `COTAHIST_M092014`, `M102014`, `M092018`, `M102018`, `M092022`, `M102022`, `M092026`, `M102026` |
| Daily | `COTAHIST_D02102026`, `D05102026`, `D23102026`, `D26102026` |

Download: `https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_<name>.ZIP` (B3 → Market data → Historical series). `data_download/download_public_data.py` fetches all twelve. `M102026` is needed only for the final run.

### Stooq (public, not redistributable)

Daily closes (Date, Open, High, Low, Close, Volume) used to compute the 20-day realized volatility filter and the event beta, and, for EWZ, the permanent-hedge comparison.

- Tickers: EWZ, EWW, INDA, ECH, ARGT, GGAL, YPF; URL `https://stooq.com/q/d/l/?s=<ticker>.us&i=d`; saved as `<ticker>_us_d.csv`.
- Downloaded on 13 Nov 2026.
- Windows actually used: [`stooq_windows.csv`](stooq_windows.csv) ([t0 − 45 days, t1] per case; full EWZ history for the permanent-hedge comparison).
- Stooq's terms state that redistribution of its data is not allowed without Stooq's consent; the files are therefore not included, only the download script, the windows and the scale factors (`results/escalas_cierres.csv`) that link the 13 Nov 2026 files to iVolatility's unadjusted prices.
- Stooq re-adjusts its history after new distributions, so a later download may be scaled differently; see the caveat in [`REPLICATION.md`](REPLICATION.md).

### FRED (public)

| Series | Use | URL |
|---|---|---|
| `DTB4WK` | 4-week T-bill, risk-free rate for the US-listed ETFs | `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB4WK` |
| `VXEWZCLS` | CBOE Brazil ETF volatility index, permanent-hedge comparison | `https://fred.stlouisfed.org/graph/fredgraph.csv?id=VXEWZCLS` |

Full range; the code reads the first data column after `observation_date`.

### Banco Central do Brasil (public, already in the inputs)

The BOVA11 rate is the Selic over rate at t0, BCB SGS series 1178 (10.90%, 6.40%, 13.65%, 13.65% for the 2014, 2018, 2022 and 2026 events). The values are written in `inputs/event_inputs.csv`; they can be checked at `https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados?formato=csv&dataInicial=dd/mm/aaaa&dataFinal=dd/mm/aaaa`.
