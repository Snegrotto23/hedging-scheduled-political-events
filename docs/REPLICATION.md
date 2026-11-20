# Replication

This is an English translation of the author's replication notes, with the folder layout and commands exactly as they were used. Nothing in `code/` needs to be edited: every script takes its paths as command-line arguments.

## Tested environment

The in-sample run was re-executed from scratch on 11 Nov 2026 with the original B3 and iVolatility ZIP files; the output matched `results/preregistration_2026-11-11/registro_eventos.csv` exactly (33 of 33 rows, difference 0.0) and `results/prueba_liquidez.txt`. Python 3.13, pandas 3.0, numpy 2.5, scipy 1.18 (any recent version should give the same numbers). `figuras.py` also needs matplotlib.

## 1. Folders

Run everything from a working folder (here `replica/`). `data_download/download_public_data.py replica` creates this layout and fills in the free data.

```
replica/
  codigo/          the .py files from code/
  datos/           event_inputs.csv (from inputs/)
  raw/cotahist/    COTAHIST_*.ZIP exactly as downloaded from B3
  raw/ivol/        iVolatility ZIP files exactly as downloaded (file names do not matter; all are read)
  raw/cierres/     Stooq daily closes: <ticker>_us_d.csv
  raw/fred/        DTB4WK.csv, VXEWZCLS.csv
  data/            built in step 2 (B3 database) plus data/ivol/ (copy or link of raw/ivol/*)
  out/             outputs
```

**B3 COTAHIST files:** M092014, M102014, M092018, M102018, M092022, M102022, M092026, M102026, D02102026, D05102026, D23102026, D26102026. Annual files (A2002, A2006, A2010) are ignored by the builder. M102026 is used only by the final run (13 Nov); the in-sample run (11 Nov) did not have it.

**iVolatility files:** product "Options prices (NBBO)", one ZIP per download. The exact ticker-days are listed in [`ivolatility_ticker_days.csv`](ivolatility_ticker_days.csv): the first purchase (11 Nov 2026: main sample and liquidity screen) and the second (12 Nov 2026, 30 ZIP files: hold-out Brazil and Argentina, base-volatility days). Duplicate files are harmless: rows are de-duplicated by date and option. AR-2019-1T (25 and 28 Oct 2019) was not bought; BMA and PAM were not bought.

**Stooq files:** `ewz_us_d.csv`, `eww_us_d.csv`, `inda_us_d.csv`, `ech_us_d.csv`, `argt_us_d.csv`, `ggal_us_d.csv`, `ypf_us_d.csv` from `https://stooq.com/q/d/l/?s=<ticker>.us&i=d`, downloaded on 13 Nov 2026.

**FRED files:** `DTB4WK.csv` and `VXEWZCLS.csv`, full range ("Max"), first column `observation_date`.

## 2. Commands

### Final run (13 Nov 2026), the one reported in the paper

```bash
pip install pandas numpy scipy matplotlib
python codigo/build_cotahist_pkl.py raw/cotahist data/cotahist_bova_petr.pkl
mkdir -p data/ivol && cp raw/ivol/* data/ivol/
python -W ignore codigo/run_final.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out 1     # with data window (paper)
python -W ignore codigo/run_final.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out_sv 0  # without data window
python -W ignore codigo/drag_permanente.py raw/cierres/ewz_us_d.csv raw/fred/VXEWZCLS.csv raw/fred/DTB4WK.csv out/registro_final.csv out/drag_permanente.txt
```

Complementary analysis and figures:

```bash
python -W ignore codigo/run_final.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out_rob 1 robustez   # theta 10% and 50%
python -W ignore codigo/analisis_extra.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out/registro_final.csv out/framework_results_final.pkl out out_rob/registro_final.csv out_rob/framework_results_final.pkl
python -W ignore codigo/figuras.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out figuras
```

`figuras.py` also needs `out/drag_permanente_meses.csv`, written by `drag_permanente.py`.

### Intrinsic-value marks (v1.1.0)

```bash
python codigo/revision_cuentas.py
```

No data and no arguments: the inputs are transcribed in the file from `results/registro_final.csv` and `results/framework_output_final_2026-11-13.txt`. It writes `revision_out.json` to the working folder; compare it with `results/revision_out.json` (identical bytes). See `CHANGELOG.md` for the formula.

### Revision of 20 Nov 2026 (v1.2.0): liquidity filter as specified and executable marks

The record reported in the paper uses the corrected adapter. `run_final_estricto.py` takes the same arguments as `run_final.py` and runs it unchanged with `ivol_adapter_estricto.py` in place of `ivol_adapter.py`; `framework.py` is not touched.

```bash
python -W ignore codigo/run_final_estricto.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out_est 1             # record in the paper
python -W ignore codigo/run_final_estricto.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out_est_sv 0          # without data window
python -W ignore codigo/run_final_estricto.py data datos/event_inputs.csv raw/cierres raw/fred/DTB4WK.csv out_est_rob 1 robustez # theta 10% and 50%
python -W ignore codigo/revision_b1_patas.py data out out_rob out_rev
python -W ignore codigo/revision_b3_marcado_ejecutable.py data out_rev codificado=out codificado_theta=out_rob estricto=out_est estricto_theta=out_est_rob
python codigo/revision_cuentas_estricto.py out_rev/revision_b3_marcado_ejecutable.csv
```

Compare `out_est/registro_final.csv` with `results/revision_b2_registro_estricto.csv` (150 rows), `out_est_sv/registro_final.csv` with `results/revision_b2_registro_estricto_sin_ventana.csv`, `out_est_rob/registro_final.csv` with `results/revision_b2_robustez_theta_estricto.csv`, the log with `results/revision_b2_framework_output_estricto.txt`, the outputs of the two `revision_b*` scripts with the files of the same name in `results/`, and `revision_out_estricto.json` with `results/revision_out_estricto.json`. `results/revision_b2_filtro_estricto_cambios.csv` lists the rows that differ between the two adapters (three in the record: YPF in the 2025 Buenos Aires election). `results/revision_b_resumen_2026-11-20.md` summarizes the three analyses (in Spanish).

### In-sample run (11 Nov 2026)

```bash
python codigo/run_events.py data datos/event_inputs.csv out_pre
python codigo/liquidity_test.py raw/ivol datos/event_inputs.csv out_pre/prueba_liquidez.csv > out_pre/prueba_liquidez.txt
```

Use only the B3 files available on 11 Nov (all of the above except M102026) and only the first iVolatility purchase. **Always pass the three arguments to `run_events.py`:** its built-in defaults point to the working folders of the original session and will not exist on your machine.

The inputs in `inputs/` are the corrected version of 13 Nov (see "Input changes" below). With them, `run_events.py` reproduces the 11 Nov registry except one row (rule `v1` of EWZ, BR-2022-2T) and the small rate effects on BOVA11 listed in `results/cambio_tasa_bova11.csv`. The 33/33 exact match was obtained with the 11 Nov inputs.

`run_events.py` should be run with only the first iVolatility purchase in `data/ivol/`. The frozen `framework.py` does not bound the backward search for the base volatility in events without an earlier first round, and RV20 takes the last 21 closes available; with several windows of the same ticker in one folder (EWZ now has 2014, 2018, 2022 and 2026) RV20 would mix days from other years. `run_oos.py` and `run_final.py` avoid this by passing to `framework.py` only the data in [t0 − 45 days, t1] of each event (argument `1` above); argument `0` runs without that window and gives `results/registro_final_sin_ventana.csv`.

### First hold-out run (12 Nov 2026)

```bash
python -W ignore codigo/run_oos.py raw/ivol datos/event_inputs.csv out_oos
```

Its outputs are superseded by the final run and are not included in `results/`.

### Rebuilding the inputs

`inputs/*.csv` are generated from the source-data modules:

```bash
cd codigo && python build_event_inputs.py ../inputs_rebuilt
```

The generated files are identical to `inputs/` except for line endings (the csv module writes CRLF on all platforms; `inputs/` uses LF). Compare with `diff <(tr -d '\r' < ../inputs_rebuilt/event_inputs.csv) ../inputs/event_inputs.csv`.

## 3. What to compare

| Your output | Published file | Notes |
|---|---|---|
| `out/registro_final.csv` | `results/registro_final.csv` | 150 rows = 50 cases × 3 rules (principal, piso50, v1) |
| `out/framework_output_final.txt` | `results/framework_output_final_2026-11-13.txt` | per-case detail, main rule, plus summary of the three rules |
| `out_sv/registro_final.csv` | `results/registro_final_sin_ventana.csv` | without the [t0 − 45, t1] data window |
| `out_rob/registro_final.csv` | `results/registro_robustez_theta.csv` | insurance-load limit θ = 10% and 50% |
| `out/drag_permanente.txt` | `results/drag_permanente.txt` | permanent-hedge comparison (EWZ, VXEWZ) |
| `out/analisis_extra.txt`, `out/marcado_intrinseco.csv`, `out/severidad_estimada_vs_realizada.csv` | same names in `results/` | intrinsic-value marking and severity check |
| `figuras/fig1..fig4`, `figuras/tabla_cuatro_resultados.csv` | `results/tabla_cuatro_resultados.csv` | figures are not stored in the repository; they are regenerated |
| `out_pre/registro_eventos.csv` | `results/preregistration_2026-11-11/registro_eventos.csv` | in-sample run of 11 Nov, 33 rows |
| `out_pre/framework_output.txt` | `results/preregistration_2026-11-11/framework_output_2026-11-11.txt` | main sample, per-case detail |
| `out_pre/framework_output_bova_otros.txt` | `results/preregistration_2026-11-11/framework_output_bova_otros.txt` | exploratory BOVA11 cases |
| `out/escalas_cierres.csv` | `results/escalas_cierres.csv` | Stooq-to-iVolatility scale factors (see the Stooq caveat) |
| `out_pre/prueba_liquidez.txt` | `results/prueba_liquidez.txt` and `results/prueba_liquidez_ar.txt` | 11 Nov rows; Argentina rows need the second purchase |

Key columns: `decision`, `patas`, `costo`, `P_malo_protocolo`, `retorno_real`, `P_real_protocolo`.

**Stooq caveat.** Stooq closes are dividend-adjusted and Stooq re-adjusts the history when new distributions occur, so a later download can be scaled differently. `run_final.py` rescales the Stooq series to iVolatility's unadjusted closes on common days; the factors obtained with the 13 Nov 2026 files are in `results/escalas_cierres.csv`. Small differences in RV20-based fields after a re-adjustment are expected; decisions should not change.

## Input changes after the 11 Nov run

- **13 Nov:** `event_inputs.csv` and `event_probabilities.csv` use the Brazil 2022-2T grid without RPS and 1xBet. With the 11 Nov version the registry is the same except 1 row (v1 of EWZ 2022-2T).
- **13 Nov (11:30):** the rate `r` of the BR events is the Selic over rate at t0 (BCB SGS series 1178: 10.90 / 6.40 / 13.65 / 13.65%). With the earlier rates (0.11 / 0.065 / 0.1365 / 0.145) 15 BOVA11 rows change by at most 1.7 bp (`results/cambio_tasa_bova11.csv`).
- **13 Nov (afternoon):** Nevasa is removed from the CL-2021-2T grid (a market-reading, not an independent forecast; same rule that excludes RBC in CO-2022-2T). Grid 0.1261 / 0.3280 / 0.5000 → 0.1261 / 0.2890 / 0.4192. Only the 3 ECH rows (and 2 θ rows) change, with no change in decision (`results/cambio_nevasa_ech.csv`).

All files in `results/` (outside `preregistration_2026-11-11/`) were produced with the inputs in `inputs/`, that is, after all three changes.

## 4. Inputs written in the scripts (with their source)

- US rate for the ETFs: 4-week T-bill. `run_events.py`: auction closest to t0 (2022 3.9%; 2024 5.37%; 2026 3.95%). `run_oos.py`: approximated by year (2014 0.02%; 2015 0.1%; 2017 1.0%; 2018 2.2%; 2019 2.0%; 2021 0.05%; 2023 5.3%; 2025 4.0%). `run_final.py` reads FRED `DTB4WK`. The effect is negligible (1–4 weeks to expiry, spot by put–call parity).
- r_previo of EWZ for the 2026 first round in the 11 Nov run (no chains for 2 and 5 Oct in the first purchase): 38.19 → 42.98 = +12.54%, from press reports (Rio Times via UA.News; Kalkine). The final run uses the purchased chains instead.
- Probabilities, polls and dates: all from `inputs/event_inputs.csv` (sources in `inputs/event_probabilities.csv` and `code/data_probs.py`).

## 5. Known limitations of the runs

- 11 Nov run: ETF base volatility outside the rule (the ideal-day chains and 21 daily closes were missing); flagged in each case as "FUERA DE REGLA".
- BOVA11 2026-2T in the 11 Nov run: base volatility measured on 5 Oct (the COTAHIST of 20 Oct 2026 was not yet available). The final run uses M102026.
- BOVA11 2026-1T: spot by parity broken on 2 Oct (196.6 against a last trade of 190.0); result not conclusive. EWZ 2026-1T is conclusive.
- Argentina: no option chains before the eve, so in most cases the base volatility is a 20-day realized volatility; AR-2019-1T has no data; several GGAL/YPF cases are not evaluable (no ATM implied volatility).

## Reading the outputs

Logs, column names and decisions are in Spanish. The terms needed to read them:

| Term | Meaning |
|---|---|
| `evento`, `activo` | event id (e.g. `BR-2026-2T` = Brazil 2026, second round), underlying |
| `t0`, `t1` | eve (víspera: last business day before the event), mark day (first business day after) |
| `p_central`, `u`, `d` | central probability of the good outcome; modelled return in the good (`u`) and bad (`d`) scenario |
| `metodo` | severity method: `term structure`, `event beta`, or `promedio` (average of both) |
| `decision` | `no hacer nada` = no hedge; `put`, `put spread`, `collar`, `put spread collar`; `NO EVALUABLE` = case cannot be evaluated |
| `motivo` | reason: `sin cobertura barata` = no cheap hedge passes; `sin opciones líquidas` = no liquid options; `\|d\| < 5% en toda la grilla` = bad-scenario move below threshold; `menor pérdida en el escenario malo…` = smallest bad-scenario loss among structures that pass cost and load |
| `patas` | legs, e.g. `1 x (+P199, -C205)` = per unit of position, long put 199, short call 205 |
| `costo` | net premium as a fraction of the position (negative = credit) |
| `P_malo_protocolo`, `P_bueno_protocolo` | hedged portfolio return in the bad / good scenario |
| `retorno_real` | realized unhedged return t0 → t1 |
| `P_real_protocolo`, `P_real_ingenuo` | realized hedged return with the protocol / with the naive benchmark (put about 5% out of the money) |
| `resultado` | realized outcome: `malo` (bad) / `bueno` (good); `cubrio` = a hedge was bought |
| `regla` | `principal` (main rule), `piso50`, `v1` (the two alternative rules), `theta10`, `theta50` (load-limit robustness) |
| `grupo` | `main` (in-sample cases), `expl` (exploratory BOVA11), `oos-BR`, `oos-CL`, `oos-AR` (hold-out cases; the `oos` labels are historical) |
| `marcas` | data flags, e.g. `último negocio` = last trade used instead of parity; `FUERA DE REGLA` = outside the rule |
| `vispera`, `veredicto` (liquidity screen) | eve; `PASA` = passes, `NO PASA` = fails, `SOLO PUT` = only the put side passes |

## Full hashes

```
221320a15437205d64b84497f3283558fd0575258a52d613e70719b8fa77afdc  framework.py
0918fae8c2e58912c51a21f1bd6962dae61dbbcad9a1ad25a5564bb8c8f33e16  event_inputs.py
4150134ef2e92f40eed98daced83d79a3e9474862f5d6ef06ce31ad031927610  ivol_adapter.py
d27f5c04d432c0c6b9e63822a08131fadfb931dbbc1d09118b4c668d9d5317d2  cotahist.py
0567196bc9ac5e99af00b779a2e58d2c919cd63dca051b0deee74942d53be4a1  mixture.py
b0e3d60ebf6d58f12c323ded3d306d76e823745cf72b54f74002cdee15218761  build_cotahist_pkl.py
48d17ece97768b3778eabc14ea0d16f3b7fc81ddcd531f3d3c6b86bf79396d16  run_events.py
f7bbd7da6f460e03bbcd1336d04e70a22ef22f886aaa179e4ad04561fb005827  run_oos.py
72b28f84d2897caab9cb274a21adab25868e8018e143d9109681539a3bec66c8  liquidity_test.py
a5cb66c3424f96fef07e94ef9ea107631ce61bcb5ffa36a2b396f90b4b8e8bac  run_final.py
8fd4a916e256f4fd80eda199d1233acf04ee73d6c1aa990360df183bcece09c1  drag_permanente.py
5b91b6a71140f4aedcc81870ffb6d475a2856662990bc8dbfb1fca020ef9f983  analisis_extra.py
d6055c7ee855292a916c73b62cf7e335cbe2f39426f209ae4ee6b1c3e399f2d3  figuras.py
79d22f900935964b362dafa3ec2bef89d75bbcd9fc370b83b5e44ba94b657f35  data_events.py
ad1fedc54d47c882aa5399f4b31fce9f39b4e04aa0c1a948ada179b5f83c4040  data_probs.py
22ff91489076232831bfad88954bfd972f2ee6b916f246b4a6de0c20c1641f34  data_scen.py
a63bb3032513f98a6ae96b31b43fcf537cd264298ee566de4bd6387db16a7dd6  devig.py
1a15dc273b5c543a1e8ce618680e702c26d81e07a623861aebbe940cdc4c5f92  build_event_inputs.py
60ce684cfbe3c4eed240755894195bf687d5b8d9d75eb003e2879cf453c44b00  fichas_eventos.py
38b44ef173ecd28d16ed7ecffa43eb0c83a2c37cf1e5592840389b5f1b9f659e  revision_cuentas.py
c218cd58a420ce74890ef8aa4370ed4899a32cc33df7844b0e5808ee3b5ea5d0  ivol_adapter_estricto.py
a254e7b2f133b557c5f782887a5a845413e1b0673a2f60ae9760286201345ae8  run_final_estricto.py
2fa5ef294e9bac435afbd0a6c49f92c6615daa371ca2d55d8ddc18023d2e0f4c  revision_b1_patas.py
1d7a8472c2370a3ada34ee7bbc855c6bd37ee44c2fe0c394828088b810541964  revision_b3_marcado_ejecutable.py
6e03913b88bf28d4f32baa7550237ae35758914c546beff0dfe9b26c5cdc4641  revision_cuentas_estricto.py
```

`framework.py` 221320a15437 is identical to its earlier draft b1b8428a56f0 except that the probability grid is bounded to [0.01, 0.99], which changes no result. Earlier versions of other scripts that give the same numbers: `run_final.py` 84787a9d1ab2 (before the robustness mode was added), `figuras.py` e6ad3e3f0108 (Spanish labels), `liquidity_test.py` 84bd5a609c12 (before Argentina was added).
