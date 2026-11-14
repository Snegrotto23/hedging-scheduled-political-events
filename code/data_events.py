"""
Datos de entrada por evento (paso 0 + paso 2 del protocolo), cargados a mano desde las búsquedas de Perplexity
(PDFs del 11/11/2026) y verificados en lo posible contra la fuente original.

Convenciones
- "bueno" = resultado pro-mercado para un inversor long-only (el que sube el activo); "malo" = el otro.
- Márgenes de encuestas siempre orientados bueno - malo, en puntos porcentuales.
  modo 'dos_vias'  : (b - m) / (b + m) * 100  (segundas vueltas, plebiscitos)
  modo 'diferencia': b - m en la base que publica la encuestadora (primeras vueltas, quién termina primero / pasa)
  modo 'umbral'    : signo * (participación - umbral) (ganar en 1ª vuelta, mayoría propia)
- REGLA DEL BINARIO (fijada el 11/11/2026, pre-registro):
  1) Para todos: definido con información pública al corte; resoluble con información pública el día del marcado (post);
     bueno/malo = dirección que las notas ex ante asignan al activo cubierto en la moneda del inversor, sin revisión ex post;
     alguna fuente con p en 5-95%, si no el evento no es elegible.
  2) 2ª vuelta / plebiscito: quién gana. Legislativa: el umbral de escaños al que las notas ex ante asocian el movimiento
     y que se resuelve al día siguiente. 1ª vuelta: del menú {alguien gana en 1ª, quién termina primero entre los dos
     punteros, quién ocupa el cupo disputado de la 2ª}, el binario al que las notas ex ante asocian el MAYOR movimiento con
     cifras, entre los que tienen alguna fuente en 5-95%; sin cifras, el de mayor p(1-p) con la mediana de la grilla;
     empate: el que define el par de la 2ª vuelta. Los binarios descartados se guardan con sufijo -ROB (robustez).
- r (solo Brasil, BOVA11): Selic over anualizada en la víspera (pre) de cada evento, BCB SGS 1178 (fijada 13/11/2026).
  Antes: 0,11 / 0,065 / 0,1365 / 0,145, heredadas del piloto sin fuente (meta en 2014 y 2018, over en 2022, desactualizada
  en 2026: la meta era 13,75% desde el 16/9/2026). Valores: 3/10 y 24/10/2014 10,90%; 5/10 y 26/10/2018 6,40%;
  30/9 y 28/10/2022 13,65%; 2/10 y 23/10/2026 13,65%.
- verificacion: 'si' = confirmado en esta sesión contra la fuente o una nota que la cita;
                'pdf' = tal como lo reporta Perplexity con su fuente, no pude abrirla;
                'no' / 'conflicto' = no se pudo confirmar o la fuente contradice el dato.
- en_grilla: la fuente entra a la grilla min/mediana/max si es ex ante, del binario exacto, la última de esa fuente
  antes del corte, posterior a la 1ª vuelta (si es una 2ª vuelta) y verificacion in {'si','pdf'}.
"""

# ---------------------------------------------------------------- eventos
EVENTS = [
    # id, pais, ronda, fecha, pre(local), post(local), pre_us, post_us, binario, bueno, malo, modo,
    # prior_pre, prior_post, prior_dp, prior_dp_fuente, r, activos, resultado_bueno, resultado, mov_real, principal, notas
    dict(id="BR-2014-1T", pais="Brasil", ronda="1T", fecha="2014-10-05", pre="2014-10-03", post="2014-10-06",
         pre_us="2014-10-03", post_us="2014-10-06",
         binario="Quién pasa a la 2ª vuelta contra Dilma: Aécio Neves vs Marina Silva", bueno="Aécio pasa", malo="Marina pasa",
         modo="diferencia", r=0.109, activos="BOVA11;EWZ;PETR4", resultado_bueno=1,
         resultado="Dilma 41,59%, Aécio 33,55%, Marina 21,32%", mov_real="Ibovespa +4,72% (6/10); Petrobras +11%",
         notas="Sin mercado de predicción ni probabilidad publicada del binario. Grilla solo con encuestas. Por la regla: sin "
               "notas con cifras; 'Dilma gana en 1ª' (~16%) y 'Aécio pasa' (~15%) empatan en p(1-p) y el desempate elige el que "
               "define el par de la 2ª vuelta. Los dos resolvieron 'bueno'."),
    dict(id="BR-2014-2T", pais="Brasil", ronda="2T", fecha="2014-10-26", pre="2014-10-24", post="2014-10-27",
         pre_us="2014-10-24", post_us="2014-10-27",
         binario="Dilma Rousseff vs Aécio Neves", bueno="Aécio", malo="Dilma", modo="dos_vias",
         prior_pre="2014-10-03", prior_post="2014-10-06", prior_dp=None,
         prior_dp_fuente="Sin la misma fuente antes y después de la 1ª vuelta (Citi 33% Aécio antes; UBS ~50/50 después): no se calcula",
         r=0.109, activos="BOVA11;EWZ;PETR4", resultado_bueno=0, resultado="Dilma 51,64%, Aécio 48,36%",
         mov_real="Ibovespa -2,77% (27/10; -6,2% intradía); real -1,9%; Petrobras >-12%",
         notas="Sin mercado de predicción ex ante. 'Betting markets 60% Rousseff' (Materials Risk, 25/10) es posterior al corte."),
    dict(id="BR-2018-1T", pais="Brasil", ronda="1T", fecha="2018-10-07", pre="2018-10-05", post="2018-10-08",
         pre_us="2018-10-05", post_us="2018-10-08",
         binario="Bolsonaro gana en 1ª vuelta (>50% de válidos)", bueno="Bolsonaro gana en 1ª", malo="Hay 2ª vuelta",
         modo="umbral", r=0.064, activos="BOVA11;EWZ;PETR4", resultado_bueno=0,
         resultado="Bolsonaro 46,03%, Haddad 29,28% (hubo 2ª vuelta)", mov_real="Ibovespa +4,6% (8/10) pese a 'malo': binario mal especificado",
         notas="El 7% del PDF 'Forecast as of 5 Oct 2018' es una estimación de Perplexity, no una fuente: excluido. "
               "Con encuestas p<1%: no elegible con este binario. El precio se movió por el tamaño de la ventaja de Bolsonaro, "
               "no por ganar en 1ª. Por la regla ningún binario del menú tiene fuente en 5-95% (el par Bolsonaro-Haddad y el primer "
               "lugar estaban decididos): no elegible. Sigue sirviendo para el event beta de la 2ª vuelta."),
    dict(id="BR-2018-2T", pais="Brasil", ronda="2T", fecha="2018-10-28", pre="2018-10-26", post="2018-10-29",
         pre_us="2018-10-26", post_us="2018-10-29",
         binario="Jair Bolsonaro vs Fernando Haddad", bueno="Bolsonaro", malo="Haddad", modo="dos_vias",
         prior_pre="2018-10-05", prior_post="2018-10-08", prior_dp=0.15,
         prior_dp_fuente="Eurasia 60% -> 75% (Money Times, 8/10/2018; verificado)",
         r=0.064, activos="BOVA11;EWZ;PETR4", resultado_bueno=1, resultado="Bolsonaro 55,13%, Haddad 44,87%",
         mov_real="Ver datos (USD/BRL ~3,655 e Ibovespa ~85k al corte)",
         notas="Sin precios de mercado en la semana de la 2ª vuelta: pedir Betfair Historical Data. "
               "Eurasia 85% (Bloomberg 27/10) es posterior al corte."),
    dict(id="BR-2022-1T", pais="Brasil", ronda="1T", fecha="2022-10-02", pre="2022-09-30", post="2022-10-03",
         pre_us="2022-09-30", post_us="2022-10-03",
         binario="Lula gana en 1ª vuelta (>50% de válidos)", bueno="No gana en 1ª (hay 2ª vuelta)", malo="Lula gana en 1ª",
         modo="umbral", r=0.1365, activos="BOVA11;EWZ;PETR4", resultado_bueno=1, resultado="Lula 48,43%, Bolsonaro 43,20%",
         mov_real="Ibovespa +5,54%; dólar -4,09% (3/10)",
         notas="Corrección al PDF: el 20% de BGC Liquidez SÍ es una probabilidad mediana (Bloomberg Línea, 1/10/2022), "
               "no solo el % de gestores que eligió el escenario. Error de encuestas aplicado a una participación (no a un margen): sigma 4 es holgado."),
    dict(id="BR-2022-2T", pais="Brasil", ronda="2T", fecha="2022-10-30", pre="2022-10-28", post="2022-10-31",
         pre_us="2022-10-28", post_us="2022-10-31",
         binario="Lula vs Jair Bolsonaro", bueno="Bolsonaro", malo="Lula", modo="dos_vias",
         prior_pre="2022-09-30", prior_post="2022-10-03", prior_dp=0.05,
         prior_dp_fuente="Eurasia 70% -> 65% Lula (verificado); valor ya usado en framework.py",
         r=0.1365, activos="BOVA11;EWZ;PETR4", resultado_bueno=0, resultado="Lula 50,90%, Bolsonaro 49,10%",
         mov_real="Ibovespa +1,3%; Petrobras >-8% (31/10)",
         notas="Las cuotas 'Betfair' de BNLData tienen ~10% de margen: son del sportsbook, no del exchange. "
               "La ref. [5] del PDF (Polymarket 72,4% 'eve of the vote') apunta a un artículo de 2026: dato descartado."),
    dict(id="BR-2026-1T", pais="Brasil", ronda="1T", fecha="2026-10-04", pre="2026-10-02", post="2026-10-05",
         pre_us="2026-10-02", post_us="2026-10-05",
         binario="Quién termina primero: Flávio Bolsonaro vs Lula", bueno="Flávio primero", malo="Lula primero",
         modo="diferencia", r=0.1365, activos="BOVA11;EWZ;PETR4", resultado_bueno=1,
         resultado="Flávio 47,03%, Lula 45,16% (sin ganador en 1ª)", mov_real="Ibovespa +7,70%; real >+4% (5/10)",
         notas="Binario secundario 'alguien gana en 1ª' (Kalshi 3,9%, Polymarket 4¢): fuera de 5-95%. "
               "Encuestas mezclan votos válidos (Datafolha) y totales (resto): el margen promedio subestima la ventaja de Lula en válidos."),
    dict(id="BR-2026-2T", pais="Brasil", ronda="2T", fecha="2026-10-25", pre="2026-10-23", post="2026-10-26",
         pre_us="2026-10-23", post_us="2026-10-26",
         binario="Flávio Bolsonaro vs Lula", bueno="Flávio", malo="Lula", modo="dos_vias",
         prior_pre="2026-10-02", prior_post="2026-10-05", prior_dp=0.27,
         prior_dp_fuente="Valor de framework.py; Polymarket da 55,6% (2/10) -> 84,8% (5/10) = 0,29 (Rio Times, verificado)",
         r=0.1365, activos="BOVA11;EWZ;PETR4", resultado_bueno=0, resultado="Lula 51,79%, Flávio 48,21%",
         mov_real="Ibovespa -13,88%; dólar +8,79% (26/10)",
         notas="framework.py usa poll_margin_good=1,84 y p_pm_good=[0,77;0,83]. Con la regla (última encuesta de cada "
               "encuestadora, 6) el margen es +1,65; el error de 1ª vuelta con las 4 encuestas finales es 5,0 (framework: 4,9 con Datafolha)."),
    dict(id="MX-2024", pais="México", ronda="única", fecha="2024-06-02", pre="2024-05-31", post="2024-06-03",
         pre_us="2024-05-31", post_us="2024-06-03",
         binario="Morena-PT-PVEM obtiene mayoría calificada (2/3) en Diputados", bueno="Sin mayoría calificada",
         malo="Mayoría calificada", modo="umbral_na", activos="EWW", resultado_bueno=0,
         resultado="Diputados: 364/500 (sí); Senado: 83/128 en la elección (no), 2/3 luego por defecciones",
         mov_real="IPC -6,11%; EWW -10,7%; peso -3,3% (3/6)",
         notas="No hay mercado del binario (Polymarket solo listó presidencia). Encuestas de voto al Congreso no se traducen "
               "a escaños sin un modelo de sobrerrepresentación: sin p por encuestas. Binario por la regla: 2/3 en Diputados, porque el "
               "conteo rápido del 3/6 lo resolvía (346-380 > 334) y el del Senado (76-88) cruzaba el umbral de 85/86: no resoluble al día siguiente."),
    dict(id="IN-2024", pais="India", ronda="conteo", fecha="2024-06-04", pre="2024-06-03", post="2024-06-04",
         pre_us="2024-06-03", post_us="2024-06-04",
         binario="BJP obtiene mayoría propia (>=272 escaños)", bueno="BJP >= 272", malo="BJP < 272", modo="umbral_na",
         activos="INDA", resultado_bueno=0, resultado="BJP 240, NDA 293", mov_real="Nifty -5,9% (4/6)",
         notas="Una sola fuente numérica del binario (Polymarket vía copia de terceros). Los exit polls dan escaños, no probabilidades. "
               "Por la regla: el mayor movimiento ex ante con cifras va a 'coalición' = BJP sin mayoría propia (Morgan Stanley: -5 a -25%), "
               "más que a NDA < 272 (SAMCO -10%)."),
    dict(id="CL-2017-2T", pais="Chile", ronda="2T", fecha="2017-12-17", pre="2017-12-15", post="2017-12-18",
         pre_us="2017-12-15", post_us="2017-12-18",
         binario="Sebastián Piñera vs Alejandro Guillier", bueno="Piñera", malo="Guillier", modo="dos_vias",
         prior_pre="2017-11-17", prior_post="2017-11-20", prior_dp=None, prior_dp_fuente="Sin probabilidad numérica antes y después de la 1ª vuelta",
         activos="ECH", resultado_bueno=1, resultado="Piñera 54,58%, Guillier 45,42%",
         mov_real="IPSA +6,9%; peso +2,4% (18/12)",
         notas="CONFLICTO: la cuota 1,30/3,20 (La Cuarta) no tiene fecha verificable y GenioBet, una de las dos casas citadas, "
               "tenía a Guillier favorito desde el 5/12 (El Desconcierto, 9/12/2017, verificado). Excluida de la grilla."),
    dict(id="CL-2021-1T", pais="Chile", ronda="1T", fecha="2021-11-21", pre="2021-11-19", post="2021-11-22",
         pre_us="2021-11-19", post_us="2021-11-22",
         binario="Quién termina primero: José Antonio Kast vs Gabriel Boric", bueno="Kast primero", malo="Boric primero",
         modo="diferencia", activos="ECH", resultado_bueno=1, resultado="Kast 27,91%, Boric 25,82%",
         mov_real="IPSA +9,69%; peso +2,13% (22/11)",
         notas="Las cuotas disponibles son de quién gana la presidencia (proxy), no del binario: fuera de la grilla."),
    dict(id="CL-2021-2T", pais="Chile", ronda="2T", fecha="2021-12-19", pre="2021-12-17", post="2021-12-20",
         pre_us="2021-12-17", post_us="2021-12-20",
         binario="Gabriel Boric vs José Antonio Kast", bueno="Kast", malo="Boric", modo="dos_vias",
         prior_pre="2021-11-19", prior_post="2021-11-22", prior_dp=None,
         prior_dp_fuente="Smarkets Kast ~47-50% antes de la 1ª vuelta; sin cotización fechada justo después",
         activos="ECH", resultado_bueno=0, resultado="Boric 55,87%, Kast 44,13%", mov_real="IPSA -6,18%; peso -3,5% (20/12)",
         notas="Corrección al PDF: Smarkets en La Tercera da Kast 31,25% (cuota 3,2), no 22,2%. Las encuestas del 13-17/12 "
               "circularon durante la veda vía medios extranjeros pero antes del corte."),
    dict(id="CL-2022-PLEB", pais="Chile", ronda="plebiscito", fecha="2022-09-04", pre="2022-09-02", post="2022-09-05",
         pre_us="2022-09-02", post_us="2022-09-06",
         binario="Apruebo vs Rechazo (plebiscito de salida)", bueno="Rechazo", malo="Apruebo", modo="dos_vias",
         activos="ECH", resultado_bueno=1, resultado="Rechazo 61,86%, Apruebo 38,14%",
         mov_real="Bolsa abre +3,65%, peso +3,2% (5/9); EE.UU. cerrado el 5/9 (Labor Day)",
         notas="Corrección al PDF: Pulso Ciudadano (Activa) da 45,8/32,9 = Rechazo 58,2% de válidos, no 53,5%. "
               "Encuestas (p~1) y casas (57-69%) muy separadas: grilla ancha."),
    dict(id="CL-2023-PLEB", pais="Chile", ronda="plebiscito", fecha="2023-12-17", pre="2023-12-15", post="2023-12-18",
         pre_us="2023-12-15", post_us="2023-12-18",
         binario="A favor vs En contra (plebiscito 2023)", bueno="A favor", malo="En contra", modo="dos_vias",
         activos="ECH", resultado_bueno=0, resultado="En contra 55,76%, A favor 44,24%", mov_real="Movimiento chico",
         notas="Sin mercado (Polymarket ~US$1.000 de volumen, sin precio). Única fuente cuantitativa: encuestas, p<1%. "
               "No elegible: se confirma el 'dudoso' del paso 0."),
    dict(id="CL-2025-1T-ROB", pais="Chile", ronda="1T", fecha="2025-11-16", pre="2025-11-14", post="2025-11-17",
         pre_us="2025-11-14", post_us="2025-11-17",
         binario="Quién termina primero: Kast vs Jara", bueno="Kast primero", malo="Jara primera", modo="diferencia",
         activos="ECH", resultado_bueno=0, resultado="Jara 26,85%, Kast 23,92%, Parisi 19,70%, Kaiser 13,94%, Matthei 12,47%",
         mov_real="IPSA y peso suben (17/11) pese a 'malo': el binario no fue el que movió precios",
         principal=0,
         notas="ROBUSTEZ (binario del paso 0). Descartado por la regla: ninguna nota ex ante asocia una cifra a quién termina "
               "primero; el escenario con cifras es Kaiser en la 2ª vuelta (Credicorp 13/11)."),
    dict(id="CL-2025-1T", pais="Chile", ronda="1T", fecha="2025-11-16", pre="2025-11-14", post="2025-11-17",
         pre_us="2025-11-14", post_us="2025-11-17",
         binario="Kaiser ocupa el cupo de la 2ª vuelta contra Jara (cupo disputado: Kast vs Kaiser)", bueno="Kaiser no pasa",
         malo="Kaiser pasa", modo="diferencia",
         activos="ECH", resultado_bueno=1, resultado="Jara 26,85%, Kast 23,92%; Kaiser 4º (13,94%)", mov_real="IPSA y peso suben (17/11)",
         principal=1,
         notas="Binario por la regla: es el escenario con la mayor cifra ex ante entre los que tienen p en 5-95% (Credicorp 13/11: "
               "Kaiser en 2ª vuelta = IPSA -5 a -10%). 'Jara gana en 1ª' (Morgan Stanley -20%) queda fuera: p ~0. "
               "Encuestas: margen Kast - Kaiser por el 2º lugar. Quién termina primero queda como CL-2025-1T-ROB."),
    dict(id="CL-2025-2T", pais="Chile", ronda="2T", fecha="2025-12-14", pre="2025-12-12", post="2025-12-15",
         pre_us="2025-12-12", post_us="2025-12-15",
         binario="José Antonio Kast vs Jeannette Jara", bueno="Kast", malo="Jara", modo="dos_vias",
         prior_pre="2025-11-14", prior_post="2025-11-17", prior_dp=0.26,
         prior_dp_fuente="Polymarket ganador: Kast 69,5% (14/11) -> 95,2% (snapshot sin fecha posterior a la 1ª vuelta); pdf",
         activos="ECH", resultado_bueno=1, resultado="Kast ~58%, Jara ~42%", mov_real="IPSA leve baja (15/12)",
         notas="p(Jara) ~1-2% en Polymarket al corte; solo cuotas sin fecha superan 5%. No elegible con la regla del paso 0 "
               "(p(Jara) >= 5%). Black & White 53/37 (Emol, 29/11) agregado: no estaba en el PDF."),
    dict(id="CO-2018-2T", pais="Colombia", ronda="2T", fecha="2018-06-17", pre="2018-06-15", post="2018-06-18",
         pre_us="2018-06-15", post_us="2018-06-18",
         binario="Iván Duque vs Gustavo Petro", bueno="Duque", malo="Petro", modo="dos_vias",
         prior_pre="2018-05-25", prior_post="2018-05-29", prior_dp=None, prior_dp_fuente="Sin la misma fuente antes y después",
         activos="EC;CIB;GXG", resultado_bueno=1, resultado="Duque 53,98%, Petro 41,81%", mov_real="Movimiento chico",
         notas="Sin mercado de predicción ex ante (pedir Betfair Historical Data). ANIF 65% es de abril y del ganador total: proxy."),
    dict(id="CO-2022-1T", pais="Colombia", ronda="1T", fecha="2022-05-29", pre="2022-05-27", post="2022-05-31",
         pre_us="2022-05-27", post_us="2022-05-31",
         binario="Quién pasa a la 2ª vuelta contra Petro: Rodolfo Hernández vs Federico Gutiérrez",
         bueno="Hernández pasa", malo="Gutiérrez pasa", modo="diferencia", activos="EC;CIB;GXG", resultado_bueno=1,
         resultado="Petro 40,34%, Hernández 28,17%, Gutiérrez 23,94%", mov_real="COLCAP +4,63%; peso +4,2% (31/5)",
         notas="30/5/2022 feriado en EE.UU. (Memorial Day): post_us = 31/5."),
    dict(id="CO-2022-2T", pais="Colombia", ronda="2T", fecha="2022-06-19", pre="2022-06-17", post="2022-06-21",
         pre_us="2022-06-17", post_us="2022-06-21",
         binario="Gustavo Petro vs Rodolfo Hernández", bueno="Hernández", malo="Petro", modo="dos_vias",
         prior_pre="2022-05-27", prior_post="2022-05-31", prior_dp=0.46,
         prior_dp_fuente="PredictIt Hernández 19% -> 65% (Corficolombiana vía El Colombiano); pdf",
         activos="EC;CIB;GXG", resultado_bueno=0, resultado="Petro 50,44%, Hernández 47,31%",
         mov_real="COLCAP -5,25% y Ecopetrol -11,2% (21/6, Resumen) vs -3,8% y -11,9% en el paso 0: revisar con datos",
         notas="20/6/2022 feriado en Colombia y EE.UU. (Juneteenth observado). Sin precios del 16-17/6."),
    dict(id="CO-2026-1T-ROB", pais="Colombia", ronda="1T", fecha="2026-05-31", pre="2026-05-29", post="2026-06-01",
         pre_us="2026-05-29", post_us="2026-06-01",
         binario="Quién termina primero: Abelardo de la Espriella vs Iván Cepeda", bueno="De la Espriella primero",
         malo="Cepeda primero", modo="diferencia", activos="EC;CIB;GXG", resultado_bueno=1,
         resultado="De la Espriella 43,78%, Cepeda 40,99%", mov_real="Bolsa +6,8%; USD/COP 3.646 -> 3.560 (2/6)",
         principal=0,
         notas="ROBUSTEZ (binario del paso 0). Descartado por la regla: las cifras ex ante (Itaú, Aval) se asocian a la "
               "continuidad con Cepeda, que la 1ª vuelta solo resuelve si Cepeda gana en 1ª. Encuestas subestimaron a De la Espriella ~10 pp."),
    dict(id="CO-2026-1T", pais="Colombia", ronda="1T", fecha="2026-05-31", pre="2026-05-29", post="2026-06-01",
         pre_us="2026-05-29", post_us="2026-06-01",
         binario="Iván Cepeda gana en 1ª vuelta (>50% de válidos)", bueno="Cepeda no gana en 1ª", malo="Cepeda gana en 1ª",
         modo="umbral", activos="EC;CIB;GXG", resultado_bueno=1,
         resultado="De la Espriella 43,78%, Cepeda 40,99% (sin ganador en 1ª)", mov_real="Bolsa +6,8%; USD/COP 3.646 -> 3.560 (2/6)",
         principal=1,
         notas="Binario por la regla: el mayor movimiento ex ante con cifras es el de continuidad con Cepeda (Itaú 25/5: USD/COP "
               "4.600-4.800; Aval 29/5: acciones -21%), y la 1ª vuelta lo resuelve solo con victoria en 1ª. 1/6/2026 feriado en "
               "Colombia: post local = 2/6. Encuestas en % de todos los encuestados (subestiman la participación en válidos). "
               "Quién termina primero queda como CO-2026-1T-ROB."),
    dict(id="CO-2026-2T", pais="Colombia", ronda="2T", fecha="2026-06-21", pre="2026-06-19", post="2026-06-22",
         pre_us="2026-06-18", post_us="2026-06-22",
         binario="Abelardo de la Espriella vs Iván Cepeda", bueno="De la Espriella", malo="Cepeda", modo="dos_vias",
         prior_pre="2026-05-29", prior_post="2026-06-01", prior_dp=0.14,
         prior_dp_fuente="Polymarket presidencia DLE 67% (28/5, Semana) -> 81% (1/6, DF); pdf/verificado parcial",
         activos="EC;CIB;GXG", resultado_bueno=1, resultado="De la Espriella 49,66%, Cepeda 48,70%",
         mov_real="COLCAP abre +4% y revierte; EC +1,2%",
         notas="19/6/2026 feriado en EE.UU. (Juneteenth): pre_us = 18/6. A. F. Arias (>90%) excluido por partidario. "
               "Guarumo: 52,6/45,0 (PDF, suma 100 con blanco 2,4) vs 53,6/45 en Portafolio: se usa 52,6."),
    dict(id="TR-2015-06", pais="Turquía", ronda="legislativa", fecha="2015-06-07", pre="2015-06-05", post="2015-06-08",
         pre_us="2015-06-05", post_us="2015-06-08",
         binario="AKP mantiene mayoría propia (>=276 escaños)", bueno="AKP mayoría", malo="Parlamento sin mayoría",
         modo="umbral", activos="TUR", resultado_bueno=0, resultado="AKP 40,9% y 258 escaños; HDP 13,1%",
         mov_real="BIST abre >-8%; lira mínimo 2,8094 (8/6)",
         notas="Sin cuotas ni probabilidades publicadas. p por encuestas con un proxy: mayoría del AKP <=> HDP bajo el 10% "
               "(Konsensus: 277 escaños si HDP pasa, 331 si no). Fuente única y proxy: usar con cuidado."),
    dict(id="TR-2015-11", pais="Turquía", ronda="legislativa", fecha="2015-11-01", pre="2015-10-30", post="2015-11-02",
         pre_us="2015-10-30", post_us="2015-11-02",
         binario="AKP recupera mayoría propia (>=276 escaños)", bueno="AKP mayoría", malo="Sin mayoría",
         modo="umbral", activos="TUR", resultado_bueno=1, resultado="AKP 49,5% y 317 escaños", mov_real="BIST +5,5%; lira +3,2-4% (2/11)",
         notas="Umbral de voto ~47% para 276 escaños según el propio AKP (pdf). BIST ya había subido ~9% en octubre."),
    dict(id="TR-2023-2T", pais="Turquía", ronda="2T", fecha="2023-05-28", pre="2023-05-26", post="2023-05-29",
         pre_us="2023-05-26", post_us="2023-05-30",
         binario="Recep Tayyip Erdoğan vs Kemal Kılıçdaroğlu", bueno="Kılıçdaroğlu", malo="Erdoğan", modo="dos_vias",
         prior_pre="2023-05-12", prior_post="2023-05-15", prior_dp=0.55,
         prior_dp_fuente="Polymarket: Kılıçdaroğlu 67% (~11/5) -> Erdoğan 88,6% (26/5); pdf",
         activos="TUR", resultado_bueno=0, resultado="Erdoğan 52,18%, Kılıçdaroğlu 47,82%",
         mov_real="BIST +4,4% (alivio), lira mínimo récord -0,6%: acciones y moneda en direcciones opuestas",
         notas="29/5/2023 feriado en EE.UU. (Memorial Day): post_us = 30/5. Las encuestas del 25-26/5 pueden haberse "
               "publicado después del corte (sin confirmar). Falta el PDF de la 1ª vuelta (14/5/2023). Bueno = Kılıçdaroğlu por la "
               "regla (notas ex ante: Erdoğan = venta de la lira; TUR cotiza en USD); que el BIST subiera es resultado, no se redefine."),
]

# ---------------------------------------------------------------- encuestas
# (evento, encuestadora, campo, publicada, n, bueno, malo, base, incluida, verificacion, nota)
# base: 'validos' | 'totales' | 'dos_vias'; en modo 'umbral', bueno = participación y malo = umbral
POLLS = [
    # BR-2014-1T  (bueno = Aécio, malo = Marina)
    ("BR-2014-1T", "Datafolha", "1-2 oct", "2 oct", 12022, 24, 27, "validos", 1, "pdf", ""),
    ("BR-2014-1T", "Ibope", "29 sep-1 oct", "2 oct", 3010, 22, 28, "validos", 1, "pdf", ""),
    ("BR-2014-1T", "Sensus", "n/d", "3 oct", None, 20.6, 22.5, "totales", 1, "pdf", ""),
    ("BR-2014-1T", "CNT/MDA", "fines sep", "29 sep", 2002, 19.8, 25.2, "totales", 1, "pdf", ""),
    ("BR-2014-1T", "Datafolha", "29-30 sep", "30 sep", 7520, 20, 25, "totales", 0, "pdf", "ola anterior de la misma encuestadora"),
    # BR-2014-2T  (bueno = Aécio)
    ("BR-2014-2T", "Datafolha", "22-23 oct", "23 oct", 9910, 47, 53, "validos", 1, "pdf", ""),
    ("BR-2014-2T", "Ibope", "20-22 oct", "22 oct", 3010, 46, 54, "validos", 1, "pdf", ""),
    ("BR-2014-2T", "CNT/MDA", "18-19 oct", "~20 oct", None, 44.5, 45.5, "totales", 1, "pdf", ""),
    # BR-2018-1T  (umbral: Bolsonaro válidos vs 50)
    ("BR-2018-1T", "Datafolha", "3-4 oct", "4 oct", 10930, 39, 50, "validos", 1, "pdf", "Bolsonaro % válidos vs 50"),
    # BR-2018-2T  (bueno = Bolsonaro)
    ("BR-2018-2T", "Datafolha", "24-25 oct", "25 oct", 9173, 56, 44, "validos", 1, "si", "48/38 totales (IHU/El País)"),
    ("BR-2018-2T", "Paraná Pesquisas", "23-25 oct", "~25 oct", 2120, 53, 35, "totales", 1, "pdf", ""),
    ("BR-2018-2T", "RealTime Big Data", "24 oct", "~25 oct", 5000, 49, 38, "totales", 1, "pdf", ""),
    ("BR-2018-2T", "XP/Ipespe", "23-24 oct", "~25 oct", 2000, 51, 37, "totales", 1, "pdf", ""),
    ("BR-2018-2T", "Ibope", "21-23 oct", "23 oct", 3010, 57, 43, "validos", 1, "si", "50/37 totales (Monitor Mercantil)"),
    ("BR-2018-2T", "CNT/MDA", "20-21 oct", "22 oct", 2002, 57, 43, "validos", 1, "pdf", ""),
    ("BR-2018-2T", "FSB/BTG Pactual", "20-21 oct", "22 oct", 2000, 60, 40, "validos", 1, "si", "Mercopress"),
    # BR-2022-1T  (umbral: 50 - Lula válidos)
    ("BR-2022-1T", "Datafolha", "27-29 sep", "29 sep", 6800, 50, 50, "validos", 1, "pdf", "Lula % válidos"),
    ("BR-2022-1T", "Exame/Ideia", "23-28 sep", "29 sep", 1500, 49, 50, "validos", 1, "pdf", ""),
    ("BR-2022-1T", "AtlasIntel", "24-28 sep", "30 sep", 4500, 50.7, 50, "validos", 1, "pdf", ""),
    ("BR-2022-1T", "Genial/Quaest", "24-27 sep", "28 sep", 2000, 50.5, 50, "validos", 1, "pdf", ""),
    ("BR-2022-1T", "PoderData", "25-27 sep", "28 sep", None, 48, 50, "validos", 1, "pdf", ""),
    ("BR-2022-1T", "Ipec", "25-26 sep", "26 sep", 3008, 52, 50, "validos", 1, "pdf", ""),
    ("BR-2022-1T", "BTG/FSB", "23-25 sep", "26 sep", 2000, 48, 50, "validos", 1, "pdf", ""),
    # BR-2022-2T  (bueno = Bolsonaro)
    ("BR-2022-2T", "Datafolha", "25-27 oct", "27 oct", 4580, 47, 53, "validos", 1, "si", "BP Money"),
    ("BR-2022-2T", "ModalMais/Futura", "24-26 oct", "~26 oct", 2000, 50.3, 49.7, "validos", 1, "pdf", ""),
    ("BR-2022-2T", "PoderData", "23-25 oct", "26 oct", 5000, 47, 53, "validos", 1, "si", "BP Money"),
    ("BR-2022-2T", "Genial/Quaest", "23-25 oct", "26 oct", 2000, 47, 53, "validos", 1, "si", "BP Money"),
    ("BR-2022-2T", "Ipec", "22-24 oct", "24 oct", 3008, 46, 54, "validos", 1, "si", "BP Money"),
    ("BR-2022-2T", "Abrapel/Ipespe", "22-24 oct", "25 oct", 1100, 47, 53, "validos", 1, "si", "BP Money"),
    ("BR-2022-2T", "Paraná Pesquisas", "20-24 oct", "~25 oct", 2020, 49.8, 50.2, "validos", 1, "si", "Monitor Mercantil"),
    # BR-2026-1T  (bueno = Flávio, malo = Lula)
    ("BR-2026-1T", "Datafolha", "29 sep-1 oct", "1 oct", 2506, 40, 45, "validos", 1, "pdf", ""),
    ("BR-2026-1T", "Vox Brasil", "29 sep-1 oct", "~1 oct", 2100, 41.2, 40.4, "totales", 1, "pdf", ""),
    ("BR-2026-1T", "Real Time Big Data", "26-30 sep", "~30 sep", 2000, 39, 43, "totales", 1, "pdf", ""),
    ("BR-2026-1T", "Futura", "25-29 sep", "~29 sep", 2000, 42.2, 39.4, "totales", 1, "pdf", ""),
    ("BR-2026-1T", "AtlasIntel/Bloomberg", "23-28 sep", "29 sep", 5005, 42.2, 45.3, "totales", 1, "pdf", ""),
    ("BR-2026-1T", "Quaest", "24-27 sep", "28 sep", 2004, 34, 39, "totales", 1, "pdf", ""),
    # BR-2026-2T  (bueno = Flávio)
    ("BR-2026-2T", "Datafolha", "20-22 oct", "22 oct", 2154, 50, 50, "validos", 1, "si", "Rio Times"),
    ("BR-2026-2T", "PoderData/Aya", "19-21 oct", "22 oct", 4000, 51, 49, "validos", 1, "pdf", ""),
    ("BR-2026-2T", "Quaest", "17-20 oct", "21 oct", 2154, 50.56, 49.44, "validos", 1, "pdf", ""),
    ("BR-2026-2T", "AtlasIntel/Bloomberg", "13-18 oct", "19 oct", 4998, 51.1, 48.9, "validos", 1, "si", "Rio Times"),
    ("BR-2026-2T", "RealTime Big Data", "19-22 oct", "23 oct", 2000, 52, 48, "validos", 1, "pdf", ""),
    ("BR-2026-2T", "BTG/Nexus", "16-18 oct", "19 oct", 2002, 50.3, 49.7, "validos", 1, "si", "Rio Times"),
    # CL-2017-2T  (bueno = Piñera)
    ("CL-2017-2T", "Cadem", "29 nov-1 dic", "1-2 dic", 1439, 40.0, 38.6, "totales", 1, "pdf", "último antes de la veda"),
    ("CL-2017-2T", "Criteria", "22-28 nov", "30 nov", 1595, 47, 45, "totales", 1, "pdf", "todos los encuestados (votantes probables: 51/46)"),
    ("CL-2017-2T", "Cadem", "22-24 nov", "~26 nov", 1442, 39.8, 37.3, "totales", 0, "pdf", "ola anterior"),
    # CL-2021-1T  (bueno = Kast, malo = Boric)
    ("CL-2021-1T", "AtlasIntel", "5-6 nov", "~6 nov", None, 27.2, 21.9, "totales", 1, "pdf", ""),
    ("CL-2021-1T", "Activa/Pulso Ciudadano", "2-5 nov", "~6 nov", 2352, 21.7, 17.7, "totales", 1, "pdf", ""),
    ("CL-2021-1T", "Cadem", "2-4 nov", "~5 nov", 1010, 25, 19, "totales", 1, "pdf", ""),
    ("CL-2021-1T", "Panel Ciudadano UDD", "2-3 nov", "~4 nov", None, 25, 22, "totales", 1, "pdf", ""),
    ("CL-2021-1T", "Criteria", "n/d", "4 nov", None, 23, 24, "totales", 1, "pdf", ""),
    ("CL-2021-1T", "Data Influye", "29-31 oct", "~1 nov", 1743, 27, 32, "totales", 1, "pdf", ""),
    # CL-2021-2T  (bueno = Kast)
    ("CL-2021-2T", "Cadem", "15-16 dic", "16 dic", None, 45, 55, "validos", 1, "si", "24horas"),
    ("CL-2021-2T", "Panel Ciudadano UDD", "15-16 dic", "17 dic", None, 46, 54, "validos", 1, "pdf", "filtrada a Clarín"),
    ("CL-2021-2T", "AtlasIntel", "14-16 dic", "16-17 dic", 2218, 48.5, 48.4, "totales", 1, "pdf", ""),
    ("CL-2021-2T", "Black & White", "13-14 dic", "15 dic", None, 50, 50, "validos", 1, "pdf", ""),
    ("CL-2021-2T", "La Cosa Nostra", "27 nov-7 dic", "14 dic", 600, 47.5, 52.5, "validos", 1, "pdf", ""),
    ("CL-2021-2T", "Cadem (privada)", "9-10 dic", "14 dic", 1000, 36, 39, "totales", 0, "pdf", "ola anterior de Cadem"),
    # CL-2022-PLEB  (bueno = Rechazo)
    ("CL-2022-PLEB", "Cadem", "17-19 ago", "19-20 ago", 1007, 46, 37, "totales", 1, "si", "The Clinic / Mega"),
    ("CL-2022-PLEB", "Activa/Pulso Ciudadano", "16-19 ago", "19 ago", 2089, 45.8, 32.9, "totales", 1, "si", "Mega / La Tercera"),
    ("CL-2022-PLEB", "AtlasIntel", "16-19 ago", "~20 ago", 2735, 54.8, 39.0, "totales", 1, "pdf", ""),
    ("CL-2022-PLEB", "Signos", "14-19 ago", "~20 ago", 1095, 46, 43, "totales", 1, "pdf", ""),
    ("CL-2022-PLEB", "Panel Ciudadano UDD", "mediados ago", "~20 ago", None, 47, 37, "totales", 1, "pdf", "fila mezclada con Black & White en el PDF"),
    # CL-2023-PLEB  (bueno = A favor)
    ("CL-2023-PLEB", "Cadem", "22-24 nov", "26 nov", 705, 38, 46, "totales", 1, "pdf", ""),
    ("CL-2023-PLEB", "Panel Ciudadano UDD", "29-30 nov", "~1 dic", 7812, 35, 47, "totales", 1, "pdf", ""),
    ("CL-2023-PLEB", "Activa/Pulso Ciudadano", "27-30 nov", "~1 dic", 1607, 40.3, 59.7, "validos", 1, "pdf", "pronóstico propio en válidos"),
    ("CL-2023-PLEB", "Data Influye", "23-27 nov", "~28 nov", 1113, 27, 50, "totales", 1, "pdf", ""),
    ("CL-2023-PLEB", "Partner 305", "olas", "1 dic", 12000, 53.42, 42.78, "totales", 1, "pdf", "difusión restringida"),
    # CL-2025-1T  (bueno = Kast, malo = Jara)
    ("CL-2025-1T-ROB", "Panel Ciudadano UDD", "30-31 oct", "~1 nov", None, 21, 26, "totales", 1, "pdf", ""),
    ("CL-2025-1T-ROB", "Activa/Pulso Ciudadano", "28-31 oct", "1 nov", None, 19.9, 29.3, "validos", 1, "pdf", "Activa 16,9/24,9 en totales: misma encuesta"),
    ("CL-2025-1T-ROB", "Black & White", "28-29 oct", "~30 oct", None, 23, 30, "totales", 1, "pdf", ""),
    ("CL-2025-1T-ROB", "Criteria", "27-29 oct", "~30 oct", None, 23, 27, "totales", 1, "pdf", ""),
    ("CL-2025-1T-ROB", "Cadem", "22-24 oct", "~26 oct", None, 20, 27, "totales", 1, "pdf", ""),
    # CL-2025-1T-ALT  (bueno = Kast por delante de Kaiser en el 2º lugar)
    ("CL-2025-1T", "Panel Ciudadano UDD", "30-31 oct", "~1 nov", None, 21, 14, "totales", 1, "pdf", "Kast vs Kaiser"),
    ("CL-2025-1T", "Activa/Pulso Ciudadano", "28-31 oct", "1 nov", None, 19.9, 14.3, "validos", 1, "pdf", ""),
    ("CL-2025-1T", "Black & White", "28-29 oct", "~30 oct", None, 23, 20, "totales", 1, "pdf", ""),
    ("CL-2025-1T", "Criteria", "27-29 oct", "~30 oct", None, 23, 15, "totales", 1, "pdf", ""),
    ("CL-2025-1T", "Cadem", "22-24 oct", "~26 oct", None, 20, 14, "totales", 1, "pdf", ""),
    # CL-2025-2T  (bueno = Kast)
    ("CL-2025-2T", "Cadem", "26-28 nov", "~29 nov", None, 58, 42, "validos", 1, "si", "Emol / Cadem"),
    ("CL-2025-2T", "Activa/Pulso Ciudadano", "n/d", "29 nov", None, 45.2, 31.6, "totales", 1, "pdf", ""),
    ("CL-2025-2T", "Panel Ciudadano UDD", "n/d", "28 nov", None, 50, 34, "totales", 1, "pdf", ""),
    ("CL-2025-2T", "Criteria", "n/d", "27 nov", None, 51, 35, "totales", 1, "si", "Ex-Ante: 59/41 en válidos"),
    ("CL-2025-2T", "Data Influye", "22-27 nov", "~28 nov", None, 49, 34, "totales", 1, "pdf", ""),
    ("CL-2025-2T", "AtlasIntel", "22-26 nov", "~27 nov", None, 56.9, 35, "totales", 1, "pdf", ""),
    ("CL-2025-2T", "Black & White", "n/d", "28 nov", None, 53, 37, "totales", 1, "si", "Emol 29/11; no estaba en el PDF"),
    # CO-2018-2T  (bueno = Duque)
    ("CO-2018-2T", "Guarumo-EcoAnalítica", "2-6 jun", "10 jun", 3955, 52.5, 36.0, "totales", 1, "pdf", ""),
    ("CO-2018-2T", "CNC", "n/d", "9 jun", 1591, 51, 38, "totales", 1, "pdf", ""),
    ("CO-2018-2T", "Cifras & Conceptos", "n/d", "8 jun", 1983, 45.3, 36.4, "totales", 1, "pdf", ""),
    ("CO-2018-2T", "Datexco", "3-6 jun", "~7 jun", 1993, 46.2, 40.2, "totales", 1, "pdf", ""),
    ("CO-2018-2T", "Invamer", "2-5 jun", "~6 jun", 1200, 57.2, 37.3, "totales", 1, "pdf", ""),
    ("CO-2018-2T", "YanHaas", "31 may-4 jun", "~5 jun", 1251, 52, 34, "totales", 1, "pdf", ""),
    # CO-2022-1T  (bueno = Hernández, malo = Gutiérrez)
    ("CO-2022-1T", "AtlasIntel", "17-20 may", "~20 may", 2781, 21.4, 26.7, "totales", 1, "pdf", ""),
    ("CO-2022-1T", "CELAG", "16-20 may", "~21 may", 2174, 20.4, 20.1, "totales", 1, "pdf", ""),
    ("CO-2022-1T", "Guarumo", "16-19 may", "~20 may", 2258, 20.3, 30.8, "totales", 1, "pdf", ""),
    ("CO-2022-1T", "CNC/Semana", "13-19 may", "~21 may", 3860, 21.9, 23.9, "totales", 1, "pdf", "muestra 41/23,9/21,9"),
    ("CO-2022-1T", "Invamer", "13-18 may", "~20 may", 1312, 20.9, 27.1, "totales", 1, "pdf", ""),
    ("CO-2022-1T", "Mosqueteros", "15-18 may", "~20 may", 6000, 15.8, 22.4, "totales", 1, "pdf", ""),
    # CO-2022-2T  (bueno = Hernández)
    ("CO-2022-2T", "AtlasIntel", "8-11 jun", "~11 jun", 4467, 50.2, 47.5, "totales", 1, "pdf", ""),
    ("CO-2022-2T", "YanHaas", "5-10 jun", "~11 jun", 1234, 35, 45, "totales", 1, "pdf", ""),
    ("CO-2022-2T", "GAD3 (tracking)", "30 may-10 jun", "~11 jun", 5236, 47.9, 47.1, "totales", 1, "pdf", ""),
    ("CO-2022-2T", "Guarumo/EcoAnalítica", "6-9 jun", "11 jun", 2029, 48.2, 46.5, "totales", 1, "pdf", ""),
    ("CO-2022-2T", "Mosqueteros", "7-8 jun", "~10 jun", 6000, 44.68, 43.83, "totales", 1, "pdf", ""),
    ("CO-2022-2T", "Invamer", "3-7 jun", "10 jun", 1329, 48.2, 47.2, "totales", 1, "pdf", ""),
    ("CO-2022-2T", "CNC", "31 may-2 jun", "~3 jun", None, 41, 44.9, "totales", 1, "pdf", ""),
    # CO-2026-1T  (bueno = De la Espriella, malo = Cepeda)
    ("CO-2026-1T-ROB", "CNC/Cambio", "16-22 may", "~23 may", 2202, 30.9, 33.4, "totales", 1, "pdf", ""),
    ("CO-2026-1T-ROB", "AtlasIntel/Semana", "18-21 may", "~22 may", 4531, 37.3, 38.7, "totales", 1, "pdf", "Reuters 38,7/37,3"),
    ("CO-2026-1T-ROB", "Invamer/Caracol", "13-20 may", "21 may", 2224, 31.6, 44.6, "totales", 1, "pdf", ""),
    ("CO-2026-1T-ROB", "Guarumo-EcoAnalítica", "11-19 may", "21 may", 3787, 27.5, 37.1, "totales", 1, "si", "El Colombiano"),
    ("CO-2026-1T-ROB", "CB Global Data", "15-20 may", "~22 may", 2503, 35.3, 36.8, "totales", 1, "pdf", ""),
    ("CO-2026-1T-ROB", "Miguel Maldonado Manjarrez", "19-22 may", "~23 may", 5167, 19.3, 37.3, "totales", 1, "pdf", ""),
    # CO-2026-1T  (umbral: bueno = Cepeda por debajo de 50; participación en % de todos los encuestados)
    ("CO-2026-1T", "CNC/Cambio", "16-22 may", "~23 may", 2202, 33.4, 50, "totales", 1, "pdf", "Cepeda %"),
    ("CO-2026-1T", "AtlasIntel/Semana", "18-21 may", "~22 may", 4531, 38.7, 50, "validos", 1, "pdf", "Reuters 38,7 (probablemente válidos)"),
    ("CO-2026-1T", "Invamer/Caracol", "13-20 may", "21 may", 2224, 44.6, 50, "totales", 1, "pdf", ""),
    ("CO-2026-1T", "Guarumo-EcoAnalítica", "11-19 may", "21 may", 3787, 37.1, 50, "totales", 1, "si", "El Colombiano"),
    ("CO-2026-1T", "CB Global Data", "15-20 may", "~22 may", 2503, 36.8, 50, "totales", 1, "pdf", ""),
    ("CO-2026-1T", "Miguel Maldonado Manjarrez", "19-22 may", "~23 may", 5167, 37.3, 50, "totales", 1, "pdf", ""),
    # CO-2026-2T  (bueno = De la Espriella)
    ("CO-2026-2T", "CB Global Data", "13-17 jun", "18 jun", None, 50.1, 45.1, "totales", 1, "pdf", "publicada durante la veda"),
    ("CO-2026-2T", "Celag Data", "n/d", "14 jun", None, 39.7, 40.8, "totales", 1, "pdf", ""),
    ("CO-2026-2T", "CNC/Cambio", "6-13 jun", "13 jun", 2186, 48.6, 44.7, "totales", 1, "pdf", ""),
    ("CO-2026-2T", "AtlasIntel/Semana", "9-11 jun", "13 jun", 2992, 52.4, 44.4, "validos", 1, "pdf", ""),
    ("CO-2026-2T", "Guarumo-EcoAnalítica", "8-12 jun", "13 jun", 2073, 52.6, 45.0, "totales", 1, "si", "Portafolio publica 53,6/45"),
    ("CO-2026-2T", "AtlasIntel/Semana", "5-10 jun", "10 jun", 3681, 52.6, 44.8, "validos", 0, "si", "ola anterior (El Colombiano)"),
    # TR-2015-06  (umbral proxy: bueno = HDP < 10 -> participación HDP vs 10, signo invertido)
    ("TR-2015-06", "Gezici", "2 jun", "~3 jun", 4860, 12.5, 10, "validos", 1, "pdf", "HDP %"),
    ("TR-2015-06", "ORC", "30 may-1 jun", "~2 jun", 3850, 9.0, 10, "validos", 1, "pdf", ""),
    ("TR-2015-06", "Konda", "30-31 may", "~1 jun", 3543, 12.6, 10, "validos", 1, "pdf", ""),
    ("TR-2015-06", "ANAR", "27 may", "~28 may", None, 11.0, 10, "validos", 1, "pdf", ""),
    ("TR-2015-06", "MAK", "18-26 may", "~27 may", 2155, 9.9, 10, "validos", 1, "pdf", ""),
    ("TR-2015-06", "SONAR", "25 may", "~26 may", 3000, 10.4, 10, "validos", 1, "pdf", ""),
    # TR-2015-11  (umbral: AKP vs 47)
    ("TR-2015-11", "Andy-Ar", "24-29 oct", "~29 oct", 2400, 43.7, 47, "validos", 1, "pdf", "AKP %"),
    ("TR-2015-11", "Konda", "24-25 oct", "~27 oct", 3574, 41.7, 47, "validos", 1, "pdf", ""),
    ("TR-2015-11", "A&G", "24-25 oct", "~27 oct", 4536, 47.2, 47, "validos", 1, "pdf", ""),
    ("TR-2015-11", "Gezici", "24-25 oct", "~27 oct", 4864, 43.0, 47, "validos", 1, "pdf", ""),
    ("TR-2015-11", "MetroPoll", "22-24 oct", "~26 oct", 2576, 43.3, 47, "validos", 1, "pdf", ""),
    ("TR-2015-11", "ORC", "21-24 oct", "~26 oct", 2650, 43.3, 47, "validos", 1, "pdf", ""),
    # TR-2023-2T  (bueno = Kılıçdaroğlu, malo = Erdoğan)
    ("TR-2023-2T", "İEA", "25-26 may", "¿26 may?", None, 48.1, 51.9, "dos_vias", 1, "pdf", "publicación posiblemente posterior al corte"),
    ("TR-2023-2T", "BETİMAR", "25-26 may", "¿26 may?", 6601, 47.8, 52.2, "dos_vias", 1, "pdf", "idem"),
    ("TR-2023-2T", "Özdemir", "25-26 may", "¿26 may?", 3250, 46.06, 53.94, "dos_vias", 1, "pdf", "idem"),
    ("TR-2023-2T", "ALF", "25-26 may", "¿26 may?", 2500, 50.3, 49.7, "dos_vias", 1, "pdf", "idem"),
    ("TR-2023-2T", "SER-AR", "25-26 may", "¿26 may?", 2200, 51.3, 48.7, "dos_vias", 1, "pdf", "idem"),
    ("TR-2023-2T", "ORC", "24-25 may", "~25 may", 3950, 50.8, 49.2, "dos_vias", 1, "pdf", ""),
    ("TR-2023-2T", "Area", "24-25 may", "~25 may", 2026, 50.6, 49.4, "dos_vias", 1, "pdf", ""),
    ("TR-2023-2T", "KONDA", "20-21 may", "~22 may", 3607, 47.3, 52.7, "dos_vias", 1, "pdf", ""),
    ("TR-2023-2T", "Areda", "20-21 may", "~22 may", 10491, 47.6, 52.4, "dos_vias", 1, "pdf", ""),
]

# Signo en modo 'umbral': +1 si bueno = participación por encima del umbral; -1 si bueno = por debajo.
UMBRAL_SIGNO = {"BR-2018-1T": +1, "BR-2022-1T": -1, "TR-2015-06": -1, "TR-2015-11": +1, "CO-2026-1T": -1}

# ---------------------------------------------------------------- error de encuestas de la 1ª vuelta
# (evento 2T, fuente, margen encuestas bueno-malo, margen real bueno-malo) en pp; bueno/malo = candidatos de la 2T
MISS_1T = [
    ("BR-2014-2T", "Datafolha 3-4 oct", 26 - 44, 33.55 - 41.59),
    ("BR-2014-2T", "Ibope 2-4 oct", 27 - 46, 33.55 - 41.59),
    ("BR-2018-2T", "Datafolha 5-6 oct", 40 - 25, 46.03 - 29.28),
    ("BR-2018-2T", "Ibope 5-6 oct", 41 - 25, 46.03 - 29.28),
    ("BR-2018-2T", "CNT/MDA 4-5 oct", 42.6 - 27.8, 46.03 - 29.28),
    ("BR-2022-2T", "Datafolha 30 sep-1 oct", 36 - 50, 43.20 - 48.43),
    ("BR-2022-2T", "Ipec 1 oct", 37 - 51, 43.20 - 48.43),
    ("BR-2026-2T", "Datafolha 3 oct", 42 - 45, 47.03 - 45.16),
    ("BR-2026-2T", "Quaest 3 oct", 45 - 46, 47.03 - 45.16),
    ("BR-2026-2T", "AtlasIntel 3 oct", 44.1 - 47, 47.03 - 45.16),
    ("BR-2026-2T", "CNT/MDA 3 oct", 42.1 - 47.8, 47.03 - 45.16),
    ("CL-2017-2T", "Cadem 31 oct-2 nov", 45 - 23, 36.64 - 22.70),
    ("CL-2017-2T", "CEP 22 sep-16 oct", 44.4 - 19.7, 36.64 - 22.70),
    ("CL-2021-2T", "Promedio 6 encuestas (PDF)", 28.1 - 25.1, 27.91 - 25.83),
    ("CL-2025-2T", "Última encuesta por encuestadora (CL-2025-1T)", "@CL-2025-1T-ROB", 23.92 - 26.85),
    ("CO-2018-2T", "Agregado El País 19 may", 37 - 27, 39.14 - 25.08),
    ("CO-2022-2T", "Promedio 6 encuestadoras (PDF)", 20.1 - 41.6, 28.15 - 40.32),
    ("CO-2026-2T", "Última encuesta por encuestadora (CO-2026-1T)", "@CO-2026-1T-ROB", 43.74 - 40.90),
    ("TR-2023-2T", "POLITICO 12 may", 50 - 46, 44.88 - 49.52),
    ("TR-2023-2T", "Euronews 12 may", 48.9 - 45.8, 44.88 - 49.52),
    ("TR-2023-2T", "600vekil 13 may", 49.3 - 47.0, 44.88 - 49.52),
]

# ==================================================================== ARGENTINA 2015-2025 (fuera de muestra, 12/11/2026)
# Fuente: PDF "Argentina 2015-2025: datos ex ante de 12 eventos electorales" (Perplexity, 12/11/2026). Se agregan sin tocar
# las filas anteriores. Activo cubierto principal: ARGT (USD, fechas EE.UU.); ADRs GGAL/YPF/BMA/PAM y Merval en pesos como
# referencia. r en blanco (la tasa en pesos no es la del inversor en USD).
# EXTENSIONES DE LA REGLA (a confirmar): (a) PASO = 1ª vuelta del ciclo para el error de encuestas: σ de la 1ª vuelta y de
# la legislativa = error de las encuestas en la PASO/evento previo del mismo ciclo; (b) PASO y elección provincial se tratan
# como 'legislativa': el umbral de votos que citan las notas, el de mayor movimiento con cifras entre los que tienen fuente
# en 5-95%; (c) si las notas ex ante no fijan el signo de un binario del menú, ese binario sale del menú.
NAN = float("nan")
AR = "ARGT;GGAL;YPF;BMA;PAM;MERVAL"
EVENTS += [
    dict(id="AR-2015-1T", pais="Argentina", ronda="1T", fecha="2015-10-25", pre="2015-10-23", post="2015-10-26",
         pre_us="2015-10-23", post_us="2015-10-26",
         binario="Scioli gana en 1ª vuelta (≥45%, o ≥40% con 10 pts sobre el segundo)", bueno="Hay balotaje",
         malo="Scioli gana en 1ª", modo="umbral", activos=AR, resultado_bueno=1,
         resultado="Scioli 37,08%, Macri 34,15%, Massa 21,39% (balotaje)",
         mov_real="ARGT +5,17%; GGAL +12,63%; YPF +7,94%; Merval +4,40%",
         notas="Sin cifras ex ante ni probabilidades: grilla solo con encuestas. Margen = 10 - ventaja de Scioli sobre Macri "
               "(se usa la condición de 10 pts; Scioli medía 37-42%, así que la de 45% no ataba). Ninguna PASO previa con error "
               "medido en el PDF: σ = 4. Por la regla, sin cifras: el binario del menú con mayor p(1-p)."),
    dict(id="AR-2015-2T", pais="Argentina", ronda="2T", fecha="2015-11-22", pre="2015-11-20", post="2015-11-23",
         pre_us="2015-11-20", post_us="2015-11-23",
         binario="Mauricio Macri vs Daniel Scioli", bueno="Macri", malo="Scioli", modo="dos_vias",
         prior_pre="2015-10-23", prior_post="2015-10-26", prior_dp=None,
         prior_dp_fuente="Sin la misma fuente antes y después de la 1ª vuelta: no se calcula",
         activos=AR, resultado_bueno=1, resultado="Macri 51,34%, Scioli 48,66%",
         mov_real="ARGT -2,94%; GGAL -8,94%; YPF -5,46%; Merval -5,12% (ganó el bueno y el activo cayó: estaba en precio)",
         notas="Bueno = Macri por la nota de Citi (ganancia para los holdouts si gana Macri). Citi 55% Macri (29/10) es la "
               "única probabilidad. Error de 1ª vuelta = 9 encuestadoras del PDF (8,2 pp)."),
    dict(id="AR-2017-LEG", pais="Argentina", ronda="legislativa", fecha="2017-10-22", pre="2017-10-20", post="2017-10-23",
         pre_us="2017-10-20", post_us="2017-10-23",
         binario="Senado PBA: Esteban Bullrich (Cambiemos) vs Cristina Kirchner", bueno="Bullrich", malo="Cristina Kirchner",
         modo="diferencia", activos=AR, resultado_bueno=1, resultado="Bullrich 41,38%, CFK 37,25%; Cambiemos 42,0% nacional",
         mov_real="ARGT +1,91%; GGAL +5,89%; YPF +5,44%; Merval +2,98%",
         notas="Las notas no citan umbral de bancas ni cifras: se toma el binario que nombran (la pelea por el Senado en PBA). "
               "Encuestas débiles (3 mediciones, dos sin encuestadora identificada); sin mercado ni probabilidad. Sin error "
               "de la PASO 2017 en el PDF: σ = 4."),
    dict(id="AR-2019-PASO", pais="Argentina", ronda="PASO", fecha="2019-08-11", pre="2019-08-09", post="2019-08-12",
         pre_us="2019-08-09", post_us="2019-08-12",
         binario="Fernández aventaja a Macri por más de 7 pts en la PASO", bueno="Ventaja ≤ 7 pts", malo="Ventaja > 7 pts",
         modo="umbral", activos=AR, resultado_bueno=0, resultado="Fernández 47,79%, Macri 31,80% (ventaja 15,99)",
         mov_real="ARGT -24,43%; GGAL -56,12%; YPF -34,05%; Merval -37,93%",
         notas="Regla (PASO como legislativa, umbral con cifras): Balanz asocia ventaja > 7 a bonos -15% y peso -10%, el mayor "
               "movimiento con cifras. Fuentes de probabilidad del PDF condicionan sobre el resultado de la PASO (Balanz, "
               "Poliarquía): no son p del binario. Grilla solo con encuestas (18). Robustez: AR-2019-PASO-ROB (quién sale primero)."),
    dict(id="AR-2019-PASO-ROB", pais="Argentina", ronda="PASO", fecha="2019-08-11", pre="2019-08-09", post="2019-08-12",
         pre_us="2019-08-09", post_us="2019-08-12",
         binario="Quién sale primero en la PASO: Macri vs Fernández", bueno="Macri primero", malo="Fernández primero",
         modo="diferencia", activos=AR, resultado_bueno=0, resultado="Fernández 47,79%, Macri 31,80%",
         mov_real="ARGT -24,43%", principal=0,
         notas="Binario descartado por la regla (las notas asocian la cifra al umbral de 7 pts). Se usa también para el error "
               "de la PASO que entra en la σ de AR-2019-1T."),
    dict(id="AR-2019-1T", pais="Argentina", ronda="1T", fecha="2019-10-27", pre="2019-10-25", post="2019-10-28",
         pre_us="2019-10-25", post_us="2019-10-28",
         binario="Alberto Fernández gana en 1ª vuelta (≥45%)", bueno="Hay balotaje", malo="Fernández gana en 1ª",
         modo="umbral", activos=AR, resultado_bueno=0, resultado="Fernández 48,24%, Macri 40,28%",
         mov_real="ARGT -2,22%; GGAL -11,39%; YPF -4,75%; Merval -3,90%",
         notas="Con σ = 4 la p del bueno es ~3% (no elegible); entra solo por la extensión (a): σ = error de la PASO 2019 "
               "(11,9 pp). Eurasia 80% (15/8) es P(Fernández presidente), proxy. Se usa el umbral de 45% (Fernández medía "
               ">50%, también cumplía 40%+10)."),
    dict(id="AR-2021-PASO", pais="Argentina", ronda="PASO", fecha="2021-09-12", pre="2021-09-10", post="2021-09-13",
         pre_us="2021-09-10", post_us="2021-09-13",
         binario="PBA: Juntos (Santilli + Manes) vs Frente de Todos (Tolosa Paz)", bueno="Juntos", malo="Frente de Todos",
         modo="diferencia", activos=AR, resultado_bueno=1, resultado="PBA: Juntos 37,98% (Santilli 22,79 + Manes 15,19), Tolosa Paz 33,64%",
         mov_real="ARGT +2,22%; GGAL +9,28%; YPF +5,24%; Merval +5,50%",
         notas="Sin cifras ex ante ni probabilidades. Las notas (operadores en TN, Emso, LCG) ligan la suba a una victoria "
               "opositora en PBA; el umbral de LCG (oficialismo +6) es del 12/9, no ex ante. Opinaia excluida (Paz 16% con 22% "
               "de indecisos, no comparable)."),
    dict(id="AR-2021-LEG", pais="Argentina", ronda="legislativa", fecha="2021-11-14", pre="2021-11-12", post="2021-11-15",
         pre_us="2021-11-12", post_us="2021-11-15",
         binario="PBA (diputados): Juntos vs Frente de Todos", bueno="Juntos", malo="Frente de Todos", modo="diferencia",
         activos=AR, resultado_bueno=1, resultado="PBA: Juntos 39,77%, FdT 38,59%; nacional JxC 41,89%, FdT 33,03%",
         mov_real="ARGT +0,03%; GGAL -1,13%; YPF -1,16%; Merval -2,07% (ganó el bueno, sin suba: en precio)",
         notas="Las notas no citan umbral de bancas resoluble al día siguiente con cifras; se toma la pelea en PBA, que es "
               "la que nombran. σ = error de la PASO 2021 en PBA (extensión a)."),
    dict(id="AR-2023-PASO", pais="Argentina", ronda="PASO", fecha="2023-08-13", pre="2023-08-11", post="2023-08-14",
         pre_us="2023-08-11", post_us="2023-08-14",
         binario="Milei (LLA) sale primero en la PASO", bueno="LLA no sale primera", malo="LLA sale primera",
         modo="diferencia", activos=AR, resultado_bueno=0, resultado="LLA 29,86%, JxC 28,00%, UxP 27,28%",
         mov_real="ARGT -2,90%; GGAL -5,78%; YPF -1,93%; Merval +3,30% (pesos; devaluación del 14/8)",
         notas="PPI (12/7) da cifras por escenario: batacazo de Milei 5% con CCL a 762 (el mayor movimiento). Margen = JxC - LLA. "
               "AtlasIntel (publicada el día previo a la elección) queda fuera por posterior al corte. Polymarket 'Milei "
               "presidente' (50,5%) es proxy. Robustez: AR-2023-PASO-ROB."),
    dict(id="AR-2023-PASO-ROB", pais="Argentina", ronda="PASO", fecha="2023-08-13", pre="2023-08-11", post="2023-08-14",
         pre_us="2023-08-11", post_us="2023-08-14",
         binario="JxC aventaja a UxP por más de 5 pts (escenario 'contundente' de PPI)", bueno="JxC > UxP + 5",
         malo="JxC ≤ UxP + 5", modo="umbral", activos=AR, resultado_bueno=0, resultado="JxC 28,00%, UxP 27,28%",
         mov_real="ARGT -2,90%", principal=0,
         notas="Escenario de PPI con 30%; el umbral de 5 pts es mi lectura de 'contundente'. Solo robustez."),
    dict(id="AR-2023-1T", pais="Argentina", ronda="1T", fecha="2023-10-22", pre="2023-10-20", post="2023-10-23",
         pre_us="2023-10-20", post_us="2023-10-23",
         binario="Bullrich entra al balotaje (cupo disputado con Massa/Milei)", bueno="Bullrich entra", malo="Bullrich queda afuera",
         modo="diferencia", activos=AR, resultado_bueno=0, resultado="Massa 36,78%, Milei 29,99%, Bullrich 23,81%",
         mov_real="ARGT -2,26%; GGAL +1,32%; YPF -6,51%; Merval -12,44%",
         notas="Regla: la única cifra ex ante (Adcap 18/10, ~70% de devaluación en precio) no se liga a un binario; sin cifras "
               "gana el de mayor p(1-p) entre los del menú con signo fijado por las notas: 'Bullrich entra' (Emso: Bullrich-Massa "
               "favorable; Massa-Milei 'the worst of all possible scenarios') le gana a 'alguien gana en 1ª' (Polymarket 13,5%). "
               "'Quién sale primero, Massa o Milei' queda afuera: las notas no le dan signo (Massa fuerte negativo, Milei en "
               "1ª el peor). Margen = Bullrich - el menor de Massa y Milei. σ = error de la PASO 2023 (extensión a). "
               "Robustez: AR-2023-1T-ROB."),
    dict(id="AR-2023-1T-ROB", pais="Argentina", ronda="1T", fecha="2023-10-22", pre="2023-10-20", post="2023-10-23",
         pre_us="2023-10-20", post_us="2023-10-23",
         binario="Alguien gana en 1ª vuelta (≥45%)", bueno="Hay balotaje", malo="Alguien gana en 1ª", modo="umbral",
         activos=AR, resultado_bueno=1, resultado="Massa 36,78%, Milei 29,99% (balotaje)", mov_real="ARGT -2,26%",
         principal=0, notas="Polymarket 'second round' 86,5% (20/10). Margen = 45 - el mayor de Massa y Milei."),
    dict(id="AR-2023-2T", pais="Argentina", ronda="2T", fecha="2023-11-19", pre="2023-11-17", post="2023-11-21",
         pre_us="2023-11-17", post_us="2023-11-20",
         binario="Javier Milei vs Sergio Massa", bueno="Milei", malo="Massa", modo="dos_vias",
         prior_pre="2023-10-20", prior_post="2023-10-23", prior_dp=-0.295,
         prior_dp_fuente="Polymarket 'Milei gana' 76,5% (20/10 19:00 UTC) -> 47,0% (23/10 19:00 UTC), API CLOB según el PDF",
         activos=AR, resultado_bueno=1, resultado="Milei 55,65%, Massa 44,35%",
         mov_real="ARGT +11,56%; GGAL +17,20%; YPF +39,89%; BMA +20,16%; PAM +17,92% (20/11); Merval +11,85% (21/11)",
         notas="El 20/11 fue feriado en Argentina: post local = 21/11, ADRs y ARGT el 20/11. Signo débil ex ante: el PDF no "
               "trae una nota que asigne dirección a acciones en USD; bueno = Milei por XP/Bernal (Bloomberg, antes del "
               "balotaje: Massa = continuidad que el mercado no quiere) y Emso (Massa fuerte = negativo). Marcar en el paper."),
    dict(id="AR-2025-PBA", pais="Argentina", ronda="provincial", fecha="2025-09-07", pre="2025-09-05", post="2025-09-08",
         pre_us="2025-09-05", post_us="2025-09-08",
         binario="Fuerza Patria le gana a LLA en PBA por más de 5 pts", bueno="Ventaja de FP ≤ 5 (o gana LLA)",
         malo="FP gana por más de 5", modo="umbral", activos=AR, resultado_bueno=0,
         resultado="Fuerza Patria 47,28%, LLA 33,71% (13,57 pts)",
         mov_real="ARGT -10,56%; GGAL -23,57%; YPF -15,34%; BMA -23,48%; PAM -16,70%; Merval -13,25%",
         notas="Regla (como legislativa): el mayor movimiento con cifras es el umbral de 10 pts (Osinaga: Merval en USD 1.400 "
               "-> 1.000; Romano: riesgo país 900-1.000) pero no tiene fuente en 5-95% (encuestas: 99%): queda como -ROB. Le "
               "sigue el de 5 pts (JP Morgan: dólar al techo de la banda, $1.460; Adcap, Criteria). Sin mercado de la PBA; "
               "Polymarket/Kalshi son de la elección nacional (proxy). 4 encuestas sin etiquetas de partido excluidas."),
    dict(id="AR-2025-PBA-ROB", pais="Argentina", ronda="provincial", fecha="2025-09-07", pre="2025-09-05", post="2025-09-08",
         pre_us="2025-09-05", post_us="2025-09-08",
         binario="Fuerza Patria le gana a LLA en PBA por 10 pts o más", bueno="Ventaja de FP < 10", malo="FP gana por ≥ 10",
         modo="umbral", activos=AR, resultado_bueno=0, resultado="FP +13,57", mov_real="ARGT -10,56%", principal=0,
         notas="Umbral con la mayor cifra ex ante (Merval USD -29%); p del bueno ~99% con encuestas: no elegible."),
    dict(id="AR-2025-LEG", pais="Argentina", ronda="legislativa", fecha="2025-10-26", pre="2025-10-24", post="2025-10-27",
         pre_us="2025-10-24", post_us="2025-10-27",
         binario="LLA saca 35% o más del voto nacional", bueno="LLA ≥ 35%", malo="LLA < 35%", modo="umbral",
         activos=AR, resultado_bueno=1, resultado="LLA 40,84%, Fuerza Patria 31,69%; LLA 64 de 127 bancas en Diputados",
         mov_real="ARGT +18,84%; GGAL +38,70%; YPF +23,78%; BMA +37,63%; PAM +23,75%; Merval +21,77%",
         notas="El umbral de bancas que citan las notas (LLA+PRO > 86 diputados, JP Morgan) no tiene ninguna fuente de "
               "probabilidad y el PDF no informa si se resolvió al día siguiente: no elegible. Se toma el umbral de votos que "
               "citan Reuters, Lacunza y JP Morgan (35%). σ = error de las encuestas en la PBA del 7/9 (extensión a; otro "
               "electorado). Polymarket 'LLA gana más bancas' es otro binario: AR-2025-LEG-ROB."),
    dict(id="AR-2025-LEG-ROB", pais="Argentina", ronda="legislativa", fecha="2025-10-26", pre="2025-10-24", post="2025-10-27",
         pre_us="2025-10-24", post_us="2025-10-27",
         binario="LLA gana más bancas en disputa en Diputados que UP (contrato de Polymarket)", bueno="LLA", malo="UP",
         modo="diferencia", activos=AR, resultado_bueno=1, resultado="LLA 64 de 127 bancas en disputa", mov_real="ARGT +18,84%",
         principal=0, notas="Solo Polymarket; las notas no ligan este binario a una cifra."),
]

UMBRAL_SIGNO.update({"AR-2015-1T": -1, "AR-2019-PASO": -1, "AR-2019-1T": -1, "AR-2023-PASO-ROB": +1,
                     "AR-2023-1T-ROB": -1, "AR-2025-PBA": -1, "AR-2025-PBA-ROB": -1, "AR-2025-LEG": +1})

T = "citado por terceros (PDF)"
_ar_polls = {
    # AR-2015-1T: b = ventaja Scioli - Macri, m = 10 (umbral, signo -1 => margen bueno = 10 - ventaja)
    "AR-2015-1T": [("Ricardo Rouvier", "21/10", 40.1 - 29.2), ("CEOP", "últimos 5 días, pub. 19/10", 37.9 - 26.3),
                   ("Ipsos-Mora y Araujo", "pub. 19/10", 14.0), ("Giacobbe", "17/10", 40.3 - 28.7),
                   ("Circuitos", "16/10", 39.1 - 26.9), ("Dicen", "7-10/10", 40.9 - 25.8), ("Poliarquía", "2-7/10", 37.1 - 26.2),
                   ("González y Valladares", "06/10", 35.4 - 25.3), ("Julio Aurelio", "05/10", 41.0 - 30.0),
                   ("Elypsis", "21/9-4/10", 39.4 - 30.9), ("Polldata", "28/9-2/10", 37.2 - 27.5)],
}
for who, campo, lead in _ar_polls["AR-2015-1T"]:
    POLLS.append(("AR-2015-1T", who, campo, "", None, round(lead, 2), 10.0, "ventaja Scioli-Macri vs umbral 10", 1, "pdf", T))
for who, why in [("Raúl Aragón", "sin cifra de Macri"), ("OPSM", "sin cifra de Macri"), ("Management & Fit", "sin cifra de Macri")]:
    POLLS.append(("AR-2015-1T", who, "", "", None, 0.0, 10.0, "-", 0, "pdf", "excluida: " + why))

POLLS += [
    # AR-2015-2T (b = Macri, m = Scioli)
    ("AR-2015-2T", "González y Valladares", "19/11", "", None, 56.1, 43.6, "no indicado", 1, "pdf", T),
    ("AR-2015-2T", "Elypsis", "", "18/11", None, 54.4, 45.6, "proyectado", 1, "pdf", T),
    ("AR-2015-2T", "Quorus", "10-16/11", "", None, 47.02, 45.98, "no indicado", 1, "pdf", T),
    ("AR-2015-2T", "Univ. Nacional de San Martín", "14/11", "", None, 42.55, 45.55, "no indicado", 1, "pdf", T),
    ("AR-2015-2T", "Giacobbe", "31/10-13/11", "", None, 49.0, 42.1, "no indicado", 1, "pdf", T + "; otra entrada 53,8/46,2 (misma proporción)"),
    ("AR-2015-2T", "Management & Fit", "9-12/11", "", None, 52.0, 43.7, "no indicado", 1, "pdf", T),
    ("AR-2015-2T", "FUNDITRA", "10-11/11", "", None, 43.56, 41.79, "no indicado", 1, "pdf", T),
    ("AR-2015-2T", "Hugo Haime", "", "11/11", None, 52.85, 47.15, "ventaja proyectada 5,7", 1, "pdf", T),
    ("AR-2015-2T", "Raúl Aragón", "10/11", "", None, 54.0, 46.0, "no indicado", 1, "pdf", T),
    ("AR-2015-2T", "Poliarquía", "9-10/11", "", None, 48.7, 40.2, "no indicado", 1, "pdf", T),
    ("AR-2015-2T", "Ipsos", "31/10-1/11", "", None, 51.2, 39.9, "no indicado", 1, "pdf", T),
    ("AR-2015-2T", "Polldata", "28-30/10", "", None, 50.3, 39.7, "no indicado", 1, "pdf", T),
    # AR-2017-LEG (b = Bullrich, m = CFK)
    ("AR-2017-LEG", "Encuestas citadas por A. Collante (no identificadas)", "", "17/10", None, 2.5, 0.0, "ventaja 'dos o tres'", 1, "pdf", T),
    ("AR-2017-LEG", "Consultora anónima", "", "23/09", None, 42.8, 33.7, "no indicado", 1, "pdf", T),
    ("AR-2017-LEG", "Firma no identificada", "", "13/09", None, 4.0, 0.0, "ventaja 4", 1, "pdf", T),
    ("AR-2017-LEG", "Taquion", "", "desconocida", None, 0.0, 1.6, "ventaja CFK 1,6", 0, "pdf", "excluida: fecha desconocida"),
]
# AR-2019-PASO / -ROB: ventaja Fernández - Macri
_ar19 = [("Federico González", "", "02/08", 44.5, 36.8), ("Dicen", "", "02/08", 43.7, 38.1), ("Management & Fit", "2/08", "", 41.2, 39.2),
         ("CELAG", "", "02/08", 42.5, 33.4), ("Raúl Aragón", "2/08", "", 41.6, 36.1), ("Ricardo Rouvier", "2/08", "", 39.0, 34.0),
         ("Gustavo Córdoba", "2/08", "", 38.2, 34.1), ("Opina Argentina", "2/08", "", 39.0, 35.0), ("Trespuntozero", "2/08", "", 43.6, 36.0),
         ("Ideia Big Data", "2/08", "", 37.0, 40.0), ("Oh! Panel", "", "02/08", 41.0, 35.0), ("Marketing y Estadística", "", "02/08", 41.0, 37.0),
         ("Real Time Data", "31/07", "", 39.0, 38.0), ("CIGP", "26-31/07", "", 40.08, 39.56), ("Circuitos", "24-29/07", "", 39.6, 34.7),
         ("Reale Dallatorre", "26-28/07", "", 37.6, 35.9), ("Giacobbe", "27-28/07", "", 40.0, 38.5), ("Tendencias", "23/07", "", 38.5, 32.7)]
for who, campo, pub, f_, m_ in _ar19:
    POLLS.append(("AR-2019-PASO", who, campo, pub, None, round(f_ - m_, 2), 7.0, "ventaja Fernández-Macri vs umbral 7", 1, "pdf", T))
    POLLS.append(("AR-2019-PASO-ROB", who, campo, pub, None, m_, f_, "no indicado", 1, "pdf", T))
# AR-2019-1T: b = Fernández (% ), m = 45
for who, pub, fz in [("Trespuntozero", "19/10", 52.5), ("Clivajes", "19/10", 53.7), ("CIGP", "19/10", 51.37),
                     ("Federico González", "19/10", 54.0), ("Giacobbe", "18/10", 51.0), ("Ricardo Rouvier", "18/10", 52.3),
                     ("Proyección", "18/10", 53.8), ("Circuitos", "18/10", 53.6), ("Opina Argentina", "~18/10", 52.0),
                     ("Gustavo Córdoba", "13/10", 52.2)]:
    POLLS.append(("AR-2019-1T", who, "", pub, None, fz, 45.0, "Fernández vs umbral 45", 1, "pdf", T))
POLLS.append(("AR-2019-1T", "Universidad de San Andrés", "1-10/10", "17/10", None, NAN, 45.0, "-", 0, "pdf",
              "excluida: solo rango de ventaja (8-17), sin participación"))
# AR-2021-PASO (PBA): b = Santilli + Manes, m = Tolosa Paz
_ar21p = [("Raúl Aragón", "1-3/9", 32.6, 33.4), ("Tendencias", "30/8-2/9", 24.1 + 10.2, 33.4), ("Federico González", "29-31/8", 19.6 + 10.6, 31.2),
          ("Clivajes", "23-31/8", 27.6 + 6.5, 39.1), ("Trespuntozero", "27-31/8", 23.4 + 9.8, 32.4), ("CIGP", "25-31/8", 23.2 + 9.7, 33.3),
          ("CB Consultora", "27-29/8", 18.9 + 13.2, 31.1), ("Giacobbe", "27-29/8", 27.4 + 9.9, 31.2), ("Circuitos", "24-28/8", 17.5 + 9.2, 33.5),
          ("Observatorio Electoral", "20-23/8", 26 + 18, 35.0), ("OPSA", "12-16/8", 14.7 + 11.1, 25.7), ("CEOP", "15/8", 20.2 + 10.0, 38.4),
          ("Ricardo Rouvier", "23/7-4/8", 15.2 + 13.0, 38.3), ("Management & Fit", "26/7-2/8", 23.4 + 10.0, 38.4),
          ("UNLAM", "25-28/7", 20.9 + 9.4, 34.1)]
for who, campo, j, p in _ar21p:
    POLLS.append(("AR-2021-PASO", who, campo, "", None, round(j, 2), p, "no indicado", 1, "pdf", T))
POLLS.append(("AR-2021-PASO", "Opinaia", "19-27/8", "", None, 29.0, 16.0, "no indicado", 0, "pdf",
              "excluida: Paz 16% con 22% de indecisos, fuera de rango"))
# AR-2021-LEG (PBA): b = Juntos, m = FdT
_ar21l = [("Circuitos", "1-2/11", 39.8, 35.7), ("Opina Argentina", "30-31/10", 36.0, 32.0), ("Políticos en Redes", "26-28/10", 39.7, 36.3),
          ("CIGP", "21-25/10", 40.7, 34.3), ("Trespuntozero", "10-19/10", 37.8, 34.0), ("Raúl Aragón", "14-16/10", 39.4, 37.1)]
for who, campo, j, p in _ar21l:
    POLLS.append(("AR-2021-LEG", who, campo, "", None, j, p, "no indicado", 1, "pdf", T))
# AR-2023-PASO: b = JxC, m = LLA ; -ROB: b = ventaja JxC - UxP, m = 5
_ar23p = [("Opina Argentina", "04/08", 32, 20, 31), ("Federico González", "03/08", 36.4, 19.5, 30.1), ("Univ. de San Andrés", "01/08", 28, 15, 21),
          ("Inteligencia Analítica", "01/08", 34.3, 19.6, 29.8), ("Analogías", "01/08", 32.7, 17.8, 32.3), ("Clivajes", "01/08", 33.9, 18.4, 30.5),
          ("Observatorio Electoral", "01/08", 40, 15, 28), ("CB Consultora", "01/08", 33, 20, 30), ("Circuitos", "01/08", 34, 16, 30),
          ("Zuban Córdoba", "01/08", 33, 24.5, 27.1), ("Giacobbe", "31/07", 38, 18.8, 32.2)]
for who, pub, j, l, u in _ar23p:
    POLLS.append(("AR-2023-PASO", who, "", pub, None, j, l, "no indicado", 1, "pdf", T + ("; UxP = JxC - 12" if who.startswith("Observ") else "")))
    POLLS.append(("AR-2023-PASO-ROB", who, "", pub, None, round(j - u, 2), 5.0, "ventaja JxC-UxP vs umbral 5", 1, "pdf", T))
POLLS.append(("AR-2023-PASO", "AtlasIntel", "", "día previo a la elección", None, 32.6, 24.5, "no indicado", 0, "pdf",
              "excluida: publicada después del corte (vie 11/8)"))
# AR-2023-1T: (Massa, Bullrich, Milei)
_ar23 = [("AtlasIntel", "10-13/10", 30.9, 24.4, 26.5), ("Tendencias", "9-12/10", 29.8, 23.1, 30.2), ("Circuitos", "9-11/10", 32.3, 24.4, 34.1),
         ("CB Consultora", "9-11/10", 29.1, 21.8, 29.9), ("Clivajes", "9-11/10", 31.4, 26.8, 33.1), ("Opinaia", "2-11/10", 29.0, 22.0, 32.0),
         ("DC Consultores", "7-10/10", 26.2, 28.9, 35.6), ("Proyección", "3-9/10", 30.9, 23.2, 35.5), ("CIGP", "5-8/10", 28.1, 20.9, 27.2),
         ("Giacobbe", "30/9-7/10", 28.5, 27.3, 32.9), ("Fixer", "2-5/10", 26.1, 25.4, 34.3), ("Zuban Córdoba", "3-4/10", 32.7, 25.0, 34.7),
         ("Reale Dalla Torre", "28/9-3/10", 24.7, 21.8, 36.2), ("Aresco", "21-29/9", 32.1, 25.9, 35.0),
         ("Univ. de San Andrés", "14-25/9", 29.8, 26.4, 34.7), ("CELAG", "1-20/9", 32.2, 28.1, 33.2)]
for who, campo, ma, bu, mi in _ar23:
    POLLS.append(("AR-2023-1T", who, campo, "", None, bu, min(ma, mi), "Bullrich vs menor de Massa/Milei", 1, "pdf", T))
    POLLS.append(("AR-2023-1T-ROB", who, campo, "", None, max(ma, mi), 45.0, "mayor de Massa/Milei vs umbral 45", 1, "pdf", T))
# AR-2023-2T: b = Milei, m = Massa
POLLS += [
    ("AR-2023-2T", "AtlasIntel", "5-9/11", "", None, 48.6, 44.6, "no indicado", 1, "pdf", T),
    ("AR-2023-2T", "CELAG", "25/10-8/11", "", None, 49.2, 50.8, "proyectado", 1, "pdf", T),
    ("AR-2023-2T", "CB Consultora", "1-6/11", "", None, 46.3, 43.1, "no indicado", 1, "pdf", T),
    ("AR-2023-2T", "Proyección", "1-6/11", "07/11", 3879, 44.6, 42.9, "no indicado", 1, "pdf", T),
    ("AR-2023-2T", "CIGP", "", "06/11", None, 49.6, 47.0, "validos proyectados", 1, "pdf", T),
    ("AR-2023-2T", "Analogías", "", "06/11", None, 34.3, 42.4, "no indicado", 1, "pdf", T),
    ("AR-2023-2T", "Zuban Córdoba", "", "06/11", None, 43.1, 45.4, "no indicado", 1, "pdf", T),
    ("AR-2023-2T", "Inteligencia Analítica", "", "06/11", None, 43.3, 43.1, "no indicado", 1, "pdf", T),
    ("AR-2023-2T", "Aresco", "25-27/10", "04/11", 6000, 52.4, 47.6, "proyectado", 1, "pdf", T),
    ("AR-2023-2T", "CB/Proyección y Clivajes/Zuban (LatinFinance)", "", "16/11", None, NAN, NAN, "-", 0, "pdf",
     "excluida: solo dirección (Milei +2-3 / Massa estrecho), sin cifras"),
]
# AR-2025-PBA / -ROB: b = ventaja FP - LLA, m = umbral
for who, campo, fp, lla in [("Aresco", "pub. 02/09", 41.7, 39.5), ("Proyección", "24/7-5/8", 38.1, 37.3),
                            ("Giacobbe", "23-28/7", 38.8, 40.9), ("Analogías", "pub. 20/07", 38.6, 36.7), ("Rubikon", "n/d", 32.8, 34.1)]:
    POLLS.append(("AR-2025-PBA", who, campo, "", None, round(fp - lla, 2), 5.0, "ventaja FP-LLA vs umbral 5", 1, "pdf", T))
    POLLS.append(("AR-2025-PBA-ROB", who, campo, "", None, round(fp - lla, 2), 10.0, "ventaja FP-LLA vs umbral 10", 1, "pdf", T))
for who in ["Nueva Comunicación", "CB Consultora", "Tendencias", "Pulso Research"]:
    POLLS.append(("AR-2025-PBA", who, "", "", None, 0.0, 5.0, "-", 0, "pdf", "excluida: el PDF no trae las etiquetas de partido"))
# AR-2025-LEG: b = LLA (% nacional), m = 35
for who, campo, pub, lla, base in [("Trespuntozero / La Sastrería", "", "18/10", 40.0, "no indicado"),
                                   ("CB Consultora", "11-15/10", "23/10", 40.8, "proyectado (37,1 crudo)"),
                                   ("Proyección", "8-14/10", "16/10", 36.4, "no indicado"),
                                   ("Management & Fit", "15-25/9", "20/10", 39.6, "no indicado"),
                                   ("Univ. de San Andrés (ESPOP)", "15-24/9", "20/10", 31.0, "totales (incluye blanco y no votaría)"),
                                   ("Trends", "8-17/9", "18/10", 42.0, "no indicado"),
                                   ("Reale Dallatorre (RDT)", "10-15/9", "18/10", 35.0, "no indicado"),
                                   ("AtlasIntel / Bloomberg", "10-14/9", "", 39.8, "no indicado")]:
    POLLS.append(("AR-2025-LEG", who, campo, pub, None, lla, 35.0, base, 1, "pdf", T))

MISS_1T += [
    # 2ª vuelta 2015: 1ª vuelta Macri - Scioli, encuesta vs real (9 encuestadoras del PDF)
    *[("AR-2015-2T", who, -lead, 34.15 - 37.08) for who, lead in
      [("Rouvier", 10.9), ("Giacobbe", 11.6), ("Circuitos", 12.2), ("Dicen", 15.1), ("Poliarquía", 10.9),
       ("González y Valladares", 10.1), ("Julio Aurelio", 11.0), ("Elypsis", 8.5), ("Polldata", 9.7)]],
    # extensión (a): PASO como 1ª vuelta del ciclo
    ("AR-2019-1T", "PASO 2019: promedio de 18 encuestas (AR-2019-PASO-ROB)", "@AR-2019-PASO-ROB", 31.80 - 47.79),
    *[("AR-2021-LEG", "PASO 2021 PBA: " + who, round(j - p, 2), 37.98 - 33.64) for who, _, j, p in _ar21p],
    ("AR-2023-1T", "PASO 2023 JxC - LLA: promedio de 11 encuestas (AR-2023-PASO)", "@AR-2023-PASO", 28.00 - 29.86),
    ("AR-2023-1T-ROB", "PASO 2023 JxC - LLA: promedio de 11 encuestas (AR-2023-PASO)", "@AR-2023-PASO", 28.00 - 29.86),
    *[("AR-2023-2T", who, mi - ma, 29.99 - 36.78) for who, _, ma, bu, mi in _ar23],
    *[("AR-2025-LEG", "PBA 7/9 FP - LLA: " + who, fp - lla, 47.28 - 33.71) for who, fp, lla in
      [("Aresco", 41.7, 39.5), ("Proyección", 38.1, 37.3), ("Giacobbe", 38.8, 40.9), ("Analogías", 38.6, 36.7), ("Rubikon", 32.8, 34.1)]],
]
