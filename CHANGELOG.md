# Changelog

## v1.2.0 — November 20, 2026

Accompanies the SSRN version of November 20, 2026 (second revision of that day) and the manuscript prepared for journal submission.

`code/framework.py` is still `221320a15437`, and no file of v1.1.0 was modified.

### Changed: the liquidity filter for U.S.-listed options is applied as specified
- The paper specifies that a U.S.-listed option is liquid if, besides the spread condition, it has an open interest of at least 100 contracts. The adapter frozen on 11 November 2026 (`ivol_adapter.py`, `4150134ef2e9`) also admitted an option with lower open interest if at least 20 contracts traded that day (the known issue of v1.1.0).
- `code/ivol_adapter_estricto.py` (`c218cd58a420`) is a copy of that adapter with one change: without open interest of at least 100, the trade count is capped at 19, so the option cannot be a leg. `code/run_final_estricto.py` (`a254e7b2f133`) runs `run_final.py` unchanged with this adapter. **The record reported in the paper is now `results/revision_b2_registro_estricto.csv`**; `results/registro_final.csv` remains as the record of the frozen adapter.
- Effect: 3 of 150 rows change, all for YPF in the 2025 Buenos Aires election (main rule and v1 move from 1 x (+P30, -C31) to 1 x (+P28, -C32); the upside floor from 1 x (+P28, -C31) to the same collar). The sold 31 call had open interest 91 and volume 32. Without the data window no row changes. With the insurance-load limit at 50%, ARGT in the 2025 legislative election is no longer hedged (the 76 call had open interest 34). At intrinsic value the hedged return of YPF falls from -2.0% to -7.7%, and the ten-case net of the main rule from +7.3 to +1.6 percentage points (hold-out cases: from -24.5 to -30.1).

### Added
- `code/revision_b1_patas.py` (`2fa5ef294e9b`) and `results/revision_b1_patas_oi_volumen.csv`, `results/revision_b1_liquidas_solo_volumen.csv`: open interest and volume on t0 of every selected leg, and the options that pass only on volume.
- `code/revision_b3_marcado_ejecutable.py` (`1d7a8472c237`) and `results/revision_b3_marcado_ejecutable.csv`, `results/revision_b3_patas_t1.csv`: each structure closed at the bid (bought legs) and the ask (sold legs) on t1, with the mid and intrinsic marks alongside, under both adapters.
- `code/revision_cuentas_estricto.py` (`6e03913b88bf`) and `results/revision_out_estricto.json`: the intrinsic-value marks and totals of the paper under the corrected adapter; with the path of `revision_b3_marcado_ejecutable.csv` as argument it also prints the totals at executable prices.
- `results/revision_b2_*`: the record, the record without the data window, the insurance-load records and the detailed log with the corrected adapter, and the rows that differ between the adapters.
- `results/revision_b_resumen_2026-11-20.md`: summary of the three analyses, in Spanish.


## v1.1.0 — November 20, 2026

Accompanies the SSRN version of November 20, 2026 ("Hedging Scheduled Political Events with Listed Options: A Mechanical Rule for Long-Only Emerging-Market Investors").

The frozen framework is unchanged: `code/framework.py` is still `221320a15437`, and no file of v1.0.0 was modified. Everything below is an additional analysis computed from the archived record.

### Added
- `code/revision_cuentas.py` (SHA-256, first 12: `38b44ef173ec`). Marks every structure chosen by the three rules, the naive put and the equivalent reduction at intrinsic value on t1, which equals the payoff at expiry if the spot stays at its t1 level: `R = ret + h * sum(q * intrinsic(K, S1)) / S0 - cost`, with `S1 = S0 * (1 + ret)`. It also computes the totals by rule, the in-sample and hold-out split, the bad-outcome and good-outcome split, and the rows of Table IA.4. The inputs are transcribed in the file from `results/registro_final.csv` (returns, legs, costs, bad-scenario P&L, d) and `results/framework_output_final_2026-11-13.txt` (spots S0 to two decimals). No raw data are needed. Run it with `python revision_cuentas.py`; it writes `revision_out.json` to the working directory.
- `results/revision_out.json` (`9114e8f8c93d`): the output of that script.

### Changed (documentation only)
- The paper's new title in `README.md`, `CITATION.cff` and `.zenodo.json`.
- "Pre-registered" and "out-of-sample" no longer appear in the documentation. The main rule was fixed after the 2026 Brazilian runoff and after the in-sample cases had been examined, and there was no dated public registration before the events. The runs are now described as the in-sample run (11 Nov) and the hold-out cases. The folder `results/preregistration_2026-11-11/` and the `oos-*` group labels inside the CSV files keep their names, so that paths and files stay byte-identical to v1.0.0. The keyword "pre-registration" was removed from the citation metadata.

### Known issue (resolved in v1.2.0; documented in Sections 4.1 and 7.5 of the paper)
- Liquidity flag for U.S.-listed options. `code/ivol_adapter.py` (`4150134ef2e9`) sets the trade count to 20 when open interest is at least 100, and to the day's volume otherwise. `framework.py` admits a leg with a trade count of at least 20. A U.S. option with open interest below 100 is therefore admitted if its volume that day is at least 20. The liquidity test (`code/liquidity_test.py`, Table IA.3) applies open interest of at least 100 alone. This difference affects ARGT 2025 legislative (the call of the collar chosen with an insurance-load limit of 50%), and one call each in GGAL and YPF for the 2025 provincial election. A rerun with the strict filter is pending.

### Unchanged
- `framework.py` and every other file and hash of v1.0.0.
