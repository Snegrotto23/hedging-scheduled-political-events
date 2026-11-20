# Hedging Scheduled Political Events with Listed Options: A Mechanical Rule for Long-Only Emerging-Market Investors

Code, inputs and results for the paper

> Negrotto, Santiago (2026). *Hedging Scheduled Political Events with Listed Options: A Mechanical Rule for Long-Only Emerging-Market Investors.* SSRN Working Paper. <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7701898>

The paper proposes a mechanical rule that tells a long-only investor holding an emerging-market equity position whether to hedge a scheduled political event (an election round, a primary, a vote count) and, if so, with which listed option structure. Using only information available on the last business day before the event, the rule builds a grid of probabilities for the outcome from prediction markets, polls and published forecasts; estimates the price move each outcome would cause from the option term structure (and from an "event beta" when an earlier shock is available); prices the options with a two-scenario lognormal mixture; and picks, among the structures that fit a cash budget and an insurance-load limit, the one with the smallest loss in the bad scenario. If no structure passes, the decision is not to hedge, and that case is recorded too.

The main rule was fixed on 11 November 2026, after the 2026 Brazilian runoff and after the eleven in-sample cases had been examined; the code was frozen the same day, and every case added afterward (the hold-out cases) was run with it unchanged. There was no dated public registration before the events. The paper's Table 2 dates every step.

This repository lets anyone check the exact code that produced the paper's numbers, re-run it, and compare the output line by line with the published registry.

## How to cite

Please cite the paper (above). To cite this repository specifically, use the metadata in [`CITATION.cff`](CITATION.cff) (GitHub shows a "Cite this repository" button) or the Zenodo DOI of the release you used.

```bibtex
@techreport{negrotto2026hedging,
  author      = {Negrotto, Santiago},
  title       = {Hedging Scheduled Political Events with Listed Options: A Mechanical Rule for Long-Only Emerging-Market Investors},
  institution = {SSRN},
  type        = {Working Paper},
  year        = {2026},
  url         = {https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7701898}
}
```

## The framework is frozen

`code/framework.py` (SHA-256 prefix `221320a15437`) was frozen on 11 November 2026, after the in-sample cases had been examined and before the hold-out cases were run. Every number in the paper comes from that file, directly or through scripts that recompute marks from its output without running the framework. Since v1.2.0 the record reported in the paper is the run with `ivol_adapter_estricto.py`, a corrected copy of the data adapter that applies the liquidity filter for U.S.-listed options as specified (open interest of at least 100 contracts); the run with the adapter frozen on 11 November 2026, which also admitted options by daily volume, is kept and compared in Section 7.5 of the paper (see `CHANGELOG.md`). **It will not be edited in this repository.** Any correction, extension or bug fix will be released as a separate, clearly versioned file and reported separately, so the frozen version always stays available and verifiable. The same applies to the other scripts listed in the hash table below: they are byte-for-byte the files used for the paper.

If you modify any file in `code/`, your results are no longer a replication of the paper.

## What is in the repository

```
code/                 the 25 Python scripts used for the paper (see hashes below)
inputs/               event inputs: probabilities, polls, scenarios, dates (built from code/data_*.py)
results/              outputs of the final run (13 Nov 2026) with the frozen adapter;
                      revision_out.json (intrinsic-value marks, v1.1.0);
                      revision_b*.csv/.txt/.md and revision_out_estricto.json (v1.2.0):
                      the record with the corrected adapter, reported in the paper,
                      open interest of every leg and executable marks
results/preregistration_2026-11-11/
                      the run of 11 Nov 2026 (in-sample cases), kept as a time stamp;
                      the folder name is historical: the run was not pre-registered
CHANGELOG.md          what changed in each release
data_download/        helper script that downloads the free raw data (B3, Stooq, FRED)
docs/REPLICATION.md   step-by-step replication, and how to read the outputs
docs/DATA_SOURCES.md  every raw-data source, what is and is not included, and why
docs/ivolatility_ticker_days.csv   exact list of the 125 purchased option-chain ticker-days
docs/stooq_windows.csv             date windows of daily closes used for each case
```

### Data that is **not** included

| Source | What | Why it is not here | How to get it |
|---|---|---|---|
| iVolatility | End-of-day option chains (NBBO) for US-listed ETFs/ADRs | Purchased data; the licence does not allow redistribution | Buy the ticker-days in [`docs/ivolatility_ticker_days.csv`](docs/ivolatility_ticker_days.csv) ("Options prices (NBBO)") |
| B3 | COTAHIST files (BOVA11 spot and options) | Kept at the source; public download | `data_download/download_public_data.py` |
| Stooq | Daily closes of EWZ, EWW, INDA, ECH, ARGT, GGAL, YPF | Stooq's terms forbid redistribution without consent | `data_download/download_public_data.py` |
| FRED | `DTB4WK` (4-week T-bill), `VXEWZCLS` (CBOE Brazil ETF vol index) | Kept at the source; public download | `data_download/download_public_data.py` |

Details, file lists and caveats are in [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md). Without the iVolatility files the ETF cases cannot be re-run; the BOVA11 cases need only B3 data.

## Replication in short

Python 3.13 with pandas 3.0, numpy 2.5, scipy 1.18 and matplotlib was used; any recent version should give the same numbers.

```bash
pip install -r requirements.txt
python data_download/download_public_data.py replica      # B3, Stooq, FRED
# put the iVolatility ZIP files in replica/raw/ivol/ and replica/data/ivol/
cp inputs/event_inputs.csv replica/datos/
cp -r code replica/codigo && cd replica
python codigo/build_cotahist_pkl.py raw/cotahist data/cotahist_bova_petr.pkl
python -W ignore codigo/run_final.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out 1
```

Then compare `out/registro_final.csv` with `results/registro_final.csv` (150 rows: 50 cases × 3 rules). The full sequence, including the 11 Nov in-sample run, the robustness runs, the permanent-hedge comparison and the figures, is in [`docs/REPLICATION.md`](docs/REPLICATION.md).

## File hashes

SHA-256 of every file in `code/` (the first 12 characters are the identifiers used in the paper's appendix).

| File | SHA-256 (first 12) | Role |
|---|---|---|
| `framework.py` | `221320a15437` | the protocol (frozen 11 Nov 2026) |
| `event_inputs.py` | `0918fae8c2e5` | reads `inputs/event_inputs.csv` |
| `ivol_adapter.py` | `4150134ef2e9` | reads iVolatility ZIP files |
| `cotahist.py` | `d27f5c04d432` | parses B3 COTAHIST |
| `mixture.py` | `0567196bc9ac` | two-lognormal mixture fitted to an option chain |
| `build_cotahist_pkl.py` | `b0e3d60ebf6d` | builds the B3 database |
| `run_events.py` | `48d17ece9776` | in-sample run (11 Nov) |
| `run_oos.py` | `f7bbd7da6f46` | first hold-out run (12 Nov) |
| `liquidity_test.py` | `72b28f84d289` | liquidity screen |
| `run_final.py` | `a5cb66c3424f` | final run used in the paper (13 Nov) |
| `drag_permanente.py` | `8fd4a916e256` | permanent-hedge comparison |
| `analisis_extra.py` | `5b91b6a71140` | marking at the larger of mid and intrinsic value, severity check |
| `figuras.py` | `d6055c7ee855` | figures 1–4 |
| `revision_cuentas.py` | `38b44ef173ec` | intrinsic-value marks and totals under the frozen adapter (added in v1.1.0) |
| `ivol_adapter_estricto.py` | `c218cd58a420` | corrected adapter: liquidity filter as specified (added in v1.2.0) |
| `run_final_estricto.py` | `a254e7b2f133` | runs `run_final.py` with the corrected adapter; the record in the paper (v1.2.0) |
| `revision_b1_patas.py` | `2fa5ef294e9b` | open interest and volume of every selected leg (v1.2.0) |
| `revision_b3_marcado_ejecutable.py` | `1d7a8472c237` | executable, mid and intrinsic marks on t1 (v1.2.0) |
| `revision_cuentas_estricto.py` | `6e03913b88bf` | intrinsic-value marks and totals under the corrected adapter: Table 8, Table IA.4 (v1.2.0) |
| `data_events.py` | `79d22f900935` | event definitions and polls (source data) |
| `data_probs.py` | `ad1fedc54d47` | prediction-market and forecast sources (source data) |
| `data_scen.py` | `22ff91489076` | scenario definitions (source data) |
| `devig.py` | `a63bb3032513` | removes the bookmaker margin from odds |
| `build_event_inputs.py` | `1a15dc273b5c` | builds `inputs/*.csv` from `data_*.py` |
| `fichas_eventos.py` | `60ce684cfbe3` | prints the event cards (Appendix B) |

Full 64-character hashes are in [`docs/REPLICATION.md`](docs/REPLICATION.md#full-hashes). Check them with `sha256sum code/*.py` (Linux/macOS) or `Get-FileHash code\*.py` (Windows PowerShell).

## Language

The code comments, column names and printed logs are in Spanish, the author's working language; they are kept exactly as run. A glossary of the terms needed to read the outputs is in [`docs/REPLICATION.md`](docs/REPLICATION.md#reading-the-outputs).

## Licence

- Code (`code/`, `data_download/`): MIT, see [`LICENSE`](LICENSE).
- Inputs, results and documentation (`inputs/`, `results/`, `docs/`): CC BY 4.0, see [`LICENSE-DATA`](LICENSE-DATA).

Third-party data (iVolatility, B3, Stooq, FRED) are not covered by these licences and remain subject to their providers' terms.

## Contact

Santiago Negrotto, Montevideo, Uruguay. Questions and replication reports are welcome through GitHub issues.
