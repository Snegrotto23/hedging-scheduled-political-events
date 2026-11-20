# Changelog

## v1.1.0 — November 20, 2026

Accompanies the SSRN version of November 20, 2026 ("Hedging Scheduled Political Events with Listed Options: A Mechanical Rule for Long-Only Emerging-Market Investors").

The frozen framework is unchanged: `code/framework.py` is still `221320a15437`, and no file of v1.0.0 was modified. Everything below is an additional analysis computed from the archived record.

### Added
- `code/revision_cuentas.py` (SHA-256, first 12: `38b44ef173ec`). Marks every structure chosen by the three rules, the naive put and the equivalent reduction at intrinsic value on t1, which equals the payoff at expiry if the spot stays at its t1 level: `R = ret + h * sum(q * intrinsic(K, S1)) / S0 - cost`, with `S1 = S0 * (1 + ret)`. It also computes the totals by rule, the in-sample and hold-out split, the bad-outcome and good-outcome split, and the rows of Table IA.4. The inputs are transcribed in the file from `results/registro_final.csv` (returns, legs, costs, bad-scenario P&L, d) and `results/framework_output_final_2026-11-13.txt` (spots S0 to two decimals). No raw data are needed. Run it with `python revision_cuentas.py`; it writes `revision_out.json` to the working directory.
- `results/revision_out.json` (`9114e8f8c93d`): the output of that script.

### Changed (documentation only)
- The paper's new title in `README.md`, `CITATION.cff` and `.zenodo.json`.
- "Pre-registered" and "out-of-sample" no longer appear in the documentation. The main rule was fixed after the 2026 Brazilian runoff and after the in-sample cases had been examined, and there was no dated public registration before the events. The runs are now described as the in-sample run (11 Nov) and the hold-out cases. The folder `results/preregistration_2026-11-11/` and the `oos-*` group labels inside the CSV files keep their names, so that paths and files stay byte-identical to v1.0.0. The keyword "pre-registration" was removed from the citation metadata.

### Known issue (documented in Sections 4.1 and 7 of the paper)
- Liquidity flag for U.S.-listed options. `code/ivol_adapter.py` (`4150134ef2e9`) sets the trade count to 20 when open interest is at least 100, and to the day's volume otherwise. `framework.py` admits a leg with a trade count of at least 20. A U.S. option with open interest below 100 is therefore admitted if its volume that day is at least 20. The liquidity test (`code/liquidity_test.py`, Table IA.3) applies open interest of at least 100 alone. This difference affects ARGT 2025 legislative (the call of the collar chosen with an insurance-load limit of 50%), and one call each in GGAL and YPF for the 2025 provincial election. A rerun with the strict filter is pending.

### Unchanged
- `framework.py` and every other file and hash of v1.0.0.
