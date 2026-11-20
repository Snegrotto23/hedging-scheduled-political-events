# Revisión 20/11/2026: puntos B.1, B.2 y B.3 del pedido (análisis adicional)

Todo corre con `framework.py` 221320a15437 sin tocar, con los datos originales (62 ZIP de iVolatility, COTAHIST, Stooq, FRED) y los inputs actuales (`datos/event_inputs.csv`, Selic over, sin Nevasa). Ningún resultado del registro se reemplaza: esto es análisis adicional.

Código: `codigo/revision_b1_patas.py.txt` (2fa5ef294e9b), `codigo/ivol_adapter_estricto.py.txt` (c218cd58a420; copia, el original 4150134ef2e9 no se tocó), `codigo/run_final_estricto.py.txt` (a254e7b2f133; corre `run_final.py` a5cb66c3424f con el adaptador estricto), `codigo/revision_b3_marcado_ejecutable.py.txt` (1d7a8472c237).

## B.1: interés abierto y volumen en t0 de cada pata elegida
Archivos: `revision_b1_patas_oi_volumen.csv` (131 patas: tres reglas con ventana y θ 10/50%), `revision_b1_liquidas_solo_volumen.csv` (opciones OTM 0,7–1,3·S0 que pasan el filtro codificado y no el estricto).

- **YPF 2025-PBA: el C31 vendido entra solo por volumen** (OI 91, volumen 32). Pasa en principal, piso50, v1, θ10 y θ50. El collar depende de N1.
- **GGAL 2025-PBA: el call de más es el C42** (OI 96), no el C41 vendido (OI 151). El collar de GGAL no depende de N1.
- **ARGT 2025-LEG θ50: el C76 entra solo por volumen** (OI 34, volumen 27).
- Otras opciones que entran solo por volumen pero no se eligen: EWZ 2026-2T C51 (OI 35) y EWZ 2026-1T P30.5 (OI 88).
- El resto de las patas elegidas pasa el filtro estricto.

## B.2: corrida con el adaptador estricto (OI ≥ 100)
Archivos: `revision_b2_registro_estricto.csv` (con ventana), `revision_b2_registro_estricto_sin_ventana.csv`, `revision_b2_robustez_theta_estricto.csv`, `revision_b2_filtro_estricto_cambios.csv` (filas que cambian, codificado contra estricto), `revision_b2_framework_output_estricto.txt`.

| Corrida | Filas que cambian |
|---|---|
| Con ventana (150) | 3: YPF 2025-PBA en principal, piso50 y v1 |
| Sin ventana (150) | 0 (YPF 2025-PBA ya es "no hacer nada", \|d\| < 5%) |
| θ 10/50% (100) | 3: YPF 2025-PBA θ10 y θ50; ARGT 2025-LEG θ50 |

- **YPF 2025-PBA.** Collar 1 × (+P30, −C31) → **1 × (+P28, −C32)** en las cinco reglas. Real: mid −2,15% → −6,76%; intrínseco −2,02% → **−7,68%**. En piso50 el cambio es chico: mid −5,87 → −6,76; intrínseco −6,39 → −7,68.
- **ARGT 2025-LEG θ50.** Collar (+P60, −C76) → no hacer nada: +5,9% → +18,7%.
- GGAL 2025-PBA, EWZ y el resto no cambian.

**Titular de Buenos Aires 2025.**
- GGAL se confirma: −23,6 → −2,7% (intrínseco).
- YPF se corrige: −15,3 → −2,0% con el filtro codificado, **−15,3 → −7,7%** con el estricto.
- Neto del ciclo YPF (PBA × LEG, regla principal): sin cubrir +4,3%. Protocolo con el filtro codificado: +1,0% (mid) y +2,3% (intrínseco). Protocolo con el estricto: **−3,8% (mid) y −3,6% (intrínseco)**.

## B.3: marcado ejecutable en t1
Archivos:
- `revision_b3_marcado_ejecutable.csv`: 111 estructuras, filtro codificado y estricto, con y sin θ.
- `revision_b3_patas_t1.csv`: una fila por pata, con bid y ask en t1, si cotiza, mid usado, último negocio, volumen o negocios, intrínseco y salida ejecutable.

Medidas:
- **P_real_mid** reproduce el registro (111 de 111).
- **P_real_ejecutable**: la comprada sale al bid y la vendida al ask. Es NaN si falta esa punta.
- **P_real_ejec_o_intr**: igual, pero la pata sin punta se valúa al intrínseco.
- **P_real_intrinseco**: todas las patas al intrínseco.

Cotizaciones en t1:
- 57 de 111 estructuras tienen al menos una pata sin doble punta. El registro las marca a (bid+ask)/2 con una punta en cero (iVolatility) o al último negocio (B3).
- En 15 de 111 falta la punta de salida.
- Casi todas son patas muy fuera del dinero después del salto: valen ~0 y no mueven el resultado.

Ejecutable contra mid, filtro codificado y regla principal (pp de S0):

| Caso | Mid | Ejecutable | Intrínseco |
|---|---|---|---|
| BOVA11 2026-2T | −0,7 | −4,0 | −1,8 |
| EWZ 2026-2T | −4,0 | −4,7 | −3,4 |
| INDA 2024 | −2,0 | −3,6 | −0,8 |
| GGAL 2025-PBA | −3,4 | −4,4 | −2,7 |
| YPF 2025-PBA | −2,2 | −3,0 | −2,0 |
| GGAL 2025-LEG | +5,6 | +3,6 | +6,7 |
| YPF 2025-LEG | +3,2 | +1,3 | +4,4 |

En promedio, el costo de salida pesa unos 1,1 pp por estructura.

**Diagnóstico de BOVA11 2026-2T** (S0 202,31; S1 173,60; cotizaciones de cierre de B3):

| Pata | Entrada | Bid t1 | Ask t1 | Último negocio (negocios) | Intrínseco | Marca del registro |
|---|---|---|---|---|---|---|
| +P199 | 7,70 | 20,98 | 34,30 | 26,02 (48) | 25,40 | mid 27,64 (spread 48% del mid) |
| −C205 | 7,45 | 0 | 0,01 | 0,01 (101) | 0 | último negocio 0,01 |
| +P192 (piso50) | 5,40 | 6,81 | — | 17,00 (50) | 18,40 | último negocio 17,00 |
| −C209 (piso50) | 5,30 | 0,01 | 3,30 | 0,01 (42) | 0 | mid 1,655 |

- **Principal y v1, P199/C205.** El C205 está bien marcado (vale cero). El problema es el P199: su mid de 27,64 queda 2,24 por encima del intrínseco, con un spread de 13,3. Resultados (principal; v1 entre paréntesis):
  - mid: −0,66 (−4,04);
  - último negocio: −1,46 (−4,64);
  - intrínseco: −1,76 (−4,87);
  - ejecutable: −3,95 (−6,51).

  El ejecutable sale contra un bid de 21 en un put que vale 25,4 al intrínseco. Eso es costo de cierre del book de B3, no valor.
- **Piso50, P192/C209.** Las dos marcas están sesgadas en contra de la cobertura:
  - el P192 no tiene ask y se marca a 17,00, 1,40 por debajo del intrínseco;
  - el C209 vendido se marca al mid de 0,01/3,30 = 1,655, cuando vale cero y su último negocio fue 0,01.

  Resultados: registro −6,65; último negocio −5,84; intrínseco −5,14. El ejecutable de −12,50 no es informativo: vende un put con intrínseco 18,40 contra un bid de 6,81 y recompra un call sin valor a 3,30.
- **Conclusión para BOVA11.** El intrínseco es la medida defendible. Cierra con el titular de la revisión (−14,2 → −1,8%). El ejecutable a cierre de B3 no sirve en este caso porque el book de cierre está vacío o es viejo en las puntas relevantes.
