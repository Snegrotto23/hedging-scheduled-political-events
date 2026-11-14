"""
Fuentes de probabilidad por evento.
kind: 'odds'  -> vals = cuotas decimales de todos los resultados listados (labels), good_idx = índice del bueno
      'price' -> vals = precios (0-1) de todos los contratos del mercado (exchange / prediction market)
      'price1'-> vals = [p del bueno] derivada de un solo lado del mercado (sin margen que quitar)
      'prob'  -> vals = [p del bueno] publicada por una consultora/modelo/encuesta a inversores
      'prob_range' -> vals = [p_min, p_max] del bueno; se usa el punto medio
binario: 'exacto' (mismo binario del evento) | 'proxy' (otro contrato correlacionado) | 'otro'
latest: 1 si es la última cotización de esa fuente antes del corte (las anteriores quedan fuera de la grilla)
pre1T: 1 si en una 2ª vuelta la fuente es anterior a la 1ª vuelta (queda fuera de la grilla)
"""

P = []


def add(ev, fuente, tipo, contrato, binario, fecha, kind, vals, good_idx=0, labels=None, ex_ante=1, latest=1,
        pre1T=0, verif="pdf", url="", nota=""):
    P.append(dict(ev=ev, fuente=fuente, tipo=tipo, contrato=contrato, binario=binario, fecha=fecha, kind=kind,
                  vals=vals, good_idx=good_idx, labels=labels or [], ex_ante=ex_ante, latest=latest, pre1T=pre1T,
                  verif=verif, url=url, nota=nota))


# ------------------------------------------------------------ BR-2014-1T
add("BR-2014-1T", "Citibank (nota a clientes, vía Reuters)", "consultora", "Dilma reelecta", "otro", "2014-10-03",
    "prob", [0.67], verif="si", url="https://voanews.com/a/reu-brazil-election/2472149.html",
    nota="P(Dilma gana la elección), no el binario Aécio vs Marina")
# ------------------------------------------------------------ BR-2014-2T
add("BR-2014-2T", "UBS", "consultora", "ganador 2ª vuelta", "exacto", "2014-10 (tras 1ª vuelta)", "prob", [0.50],
    verif="pdf", nota="'about 50/50' para Aécio tras la 1ª vuelta; fecha exacta no indicada")
add("BR-2014-2T", "Citibank", "consultora", "Dilma reelecta", "exacto", "2014-10-03", "prob", [0.33], pre1T=1,
    verif="si", url="https://voanews.com/a/reu-brazil-election/2472149.html", nota="anterior a la 1ª vuelta")
add("BR-2014-2T", "Materials Risk ('betting markets')", "mercado sin nombre", "ganador", "exacto", "2014-10-25",
    "prob", [0.40], ex_ante=0, verif="pdf", nota="posterior al corte (24/10); solo sensibilidad")
# ------------------------------------------------------------ BR-2018-1T
add("BR-2018-1T", "Perplexity (estimación propia)", "estimación IA", "Bolsonaro gana en 1ª", "exacto", "2018-10-05",
    "prob", [0.07], ex_ante=0, verif="no", nota="no es una fuente: modelo de Perplexity. Excluida")
add("BR-2018-1T", "Betfair Exchange (vía GamesBras)", "exchange", "ganador de la elección", "otro", "2018-10-04",
    "odds", [1.61, 2.10], 0, ["Bolsonaro", "Haddad"], verif="no",
    url="https://www.gamesbras.com/english-version/2018/10/5/betting-on-brazils-presidential-election-bolsonaro-pays-161-at-betfair-markets-10040.html",
    nota="no pude abrir la fuente; mercado del ganador total, no del binario; ~US$78.000 negociados")
# ------------------------------------------------------------ BR-2018-2T
add("BR-2018-2T", "Eurasia Group", "consultora", "ganador 2ª vuelta", "exacto", "2018-10-08", "prob", [0.75], latest=0,
    verif="si", url="https://www.moneytimes.com.br/chance-de-bolsonaro-presidente-vai-a-75-avalia-eurasia/",
    nota="sube de 60% a 75%")
add("BR-2018-2T", "Eurasia Group", "consultora", "ganador 2ª vuelta", "exacto", "2018-10-20", "prob", [0.75],
    verif="pdf", url="https://www.em.com.br/app/noticia/internacional/2018/10/20/interna_internacional,998781/haddad-ainda-pode-vencer-a-eleicao.shtml",
    nota="'Haddad has a 25% chance' (Estado de Minas/AFP)")
add("BR-2018-2T", "Nomura (nota a clientes)", "banco", "ganador 2ª vuelta", "exacto", "2018-10-08", "prob", [0.70],
    verif="pdf", url="https://www.forbes.com/sites/kenrapoza/2018/10/08/market-gives-brazils-bolsonaro-70-chance-of-winning/",
    nota="'over 70%': se usa 70% como cota inferior")
add("BR-2018-2T", "PollingData", "modelo", "ganador 2ª vuelta", "exacto", "2018-10-26", "prob", [0.98], verif="pdf",
    url="https://www.vox.com/mischiefs-of-faction/2018/10/26/18029494/why-did-brazilian-pollsters-go-wrong")
add("BR-2018-2T", "Spinelli (corretora)", "corredora", "ganador si hay 2ª vuelta", "exacto", "2018-10-05", "prob",
    [0.70], pre1T=1, verif="pdf", nota="anterior a la 1ª vuelta")
add("BR-2018-2T", "Betfair Exchange (vía GamesBras)", "exchange", "ganador de la elección", "exacto", "2018-10-04",
    "odds", [1.61, 2.10], 0, ["Bolsonaro", "Haddad"], pre1T=1, verif="no",
    nota="anterior a la 1ª vuelta y no verificada")
add("BR-2018-2T", "Eurasia Group (vía Bloomberg)", "consultora", "ganador", "exacto", "2018-10-27", "prob", [0.85],
    ex_ante=0, verif="pdf", nota="posterior al corte")
# ------------------------------------------------------------ BR-2022-1T  (bueno = NO hay victoria en 1ª)
add("BR-2022-1T", "Eurasia Group", "consultora", "Lula gana en 1ª vuelta", "exacto", "2022-09-23", "prob_range",
    [0.75, 0.80], verif="si", url="https://istoedinheiro.com.br/lula-tem-70-de-chance-de-vencer-eleicao-e-entre-20-e-25-de-ganhar-no-1o-turno",
    nota="20-25% de que Lula gane en 1ª (p bueno = 75-80%)")
add("BR-2022-1T", "BGC Liquidez (212 institucionales)", "encuesta a inversores", "Lula gana en 1ª vuelta", "exacto",
    "2022-09-29", "prob", [0.80], verif="si",
    url="https://www.bloomberglinea.com.br/2022/10/01/as-apostas-da-faria-lima-para-as-eleicoes-e-o-que-esperar-dos-mercados/",
    nota="probabilidad mediana 20% de victoria en 1ª (corrección: sí es una probabilidad)")
add("BR-2022-1T", "Betfair Exchange", "exchange", "ganador de la elección", "otro", "2022-09-30", "odds", [1.37, 3.6], 1,
    ["Lula", "Bolsonaro"], verif="pdf", nota="mercado del ganador total; Bolsonaro 3,6 es la mejor cuota de Odds Scanner")
# ------------------------------------------------------------ BR-2022-2T  (bueno = Bolsonaro)
for d, o in [("2022-10-25", (1.57, 2.20)), ("2022-10-26", (1.44, 2.50)), ("2022-10-27", (1.36, 2.63)),
             ("2022-10-28", (1.33, 2.88))]:
    add("BR-2022-2T", "Betfair (sportsbook, vía BNLData)", "casa de apuestas", "ganador", "exacto", d, "odds", list(o), 1,
        ["Lula", "Bolsonaro"], latest=int(d == "2022-10-28"), verif="si",
        url="https://bnldata.com.br/lula-sempre-foi-favorito-nas-casas-de-apostas-a-pixbet-criou-uma-odd-de-5-00-no-lula-e-1-20-no-bolsonaro/",
        nota="margen ~10%: sportsbook, no exchange")
add("BR-2022-2T", "bet365 (vía BNLData)", "casa de apuestas", "ganador", "exacto", "2022-10-28", "odds", [1.44, 2.62], 1,
    ["Lula", "Bolsonaro"], verif="si", url="https://bnldata.com.br/odds-de-sabado-mantem-lula-como-favorito-nas-eleicoes-presidenciais/")
add("BR-2022-2T", "Pixbet (vía BNLData)", "casa de apuestas", "ganador", "exacto", "2022-10-28", "odds", [1.50, 2.50], 1,
    ["Lula", "Bolsonaro"], verif="si", url="https://bnldata.com.br/lula-sempre-foi-favorito-nas-casas-de-apostas-a-pixbet-criou-uma-odd-de-5-00-no-lula-e-1-20-no-bolsonaro/")
add("BR-2022-2T", "1xBet (vía iGamingBrazil)", "casa de apuestas", "ganador", "exacto", "2022-10-28", "odds",
    [1.32, 2.808], 1, ["Lula", "Bolsonaro"], verif="no",
    nota="13/11/2026: Perplexity no encuentra ni la nota de iGamingBrazil ni el original de 1xBet; no verificable: sale de la grilla")
add("BR-2022-2T", "Betfair Exchange (electionbettingodds)", "exchange", "ganador", "exacto", "2022-10-26 17:47 EDT",
    "price1", [0.322], verif="pdf", url="https://electionbettingodds.com/Brazil2022.html",
    nota="Bolsonaro 31,7-32,7%; punto medio; US$16,18M. 13/11: captura del 26/10 no verificada (la página actual es del 31/10; TrackRecord: Bolsonaro 31,8%)")
add("BR-2022-2T", "Smarkets (electionbettingodds)", "exchange", "ganador", "exacto", "2022-10-26", "price1", [0.3195],
    verif="pdf", nota="Lula 67,6-68,5% -> Bolsonaro 1 - punto medio")
add("BR-2022-2T", "PredictIt (electionbettingodds)", "prediction market", "ganador", "exacto", "2022-10-26", "price1",
    [0.27], verif="pdf", nota="Lula 72,5-73,5%")
add("BR-2022-2T", "FTX (electionbettingodds)", "exchange", "ganador", "exacto", "2022-10-26", "price1", [0.312],
    verif="pdf", nota="Bolsonaro 30,7-31,7%")
add("BR-2022-2T", "Eurasia Group", "consultora", "ganador", "exacto", "2022-10-28", "prob", [0.35], verif="si",
    url="https://www.bloomberglinea.com.br/2022/10/28/eurasia-cita-media-de-pesquisas-e-diz-que-chance-de-vitoria-de-lula-vai-a-65/",
    nota="Lula 65% (sube desde 60% del 24/10)")
add("BR-2022-2T", "Eurasia Group", "consultora", "ganador", "exacto", "2022-10-24", "prob", [0.40], latest=0, verif="si",
    url="https://istoedinheiro.com.br/eurasia-diminui-probabilidade-de-vitoria-de-lula-de-65-para-60")
add("BR-2022-2T", "BGC Liquidez (230 institucionales)", "encuesta a inversores", "ganador", "exacto", "2022-10-28", "prob",
    [0.34], verif="si", url="https://static.poder360.com.br/2022/10/20221028_BGCStrategy_BZElections.pdf",
    nota="mediana 34% (diap. 3; promedio 33,8%), relevamiento 28/10 12-16 h; 230 institucionales (gestores, traders, economistas), no solo traders. Lula sin impugnación 35%, con impugnación 30%")
add("BR-2022-2T", "RPS Capital (lectura de precios)", "analista", "ganador", "exacto", "2022-10-29 07:00", "prob", [0.40],
    ex_ante=0, verif="si",
    url="https://valor.globo.com/financas/noticia/2022/10/29/lula-x-bolsonaro-para-onde-vao-ibovespa-e-dolar-apos-o-2o-turno-das-eleicoes.ghtml",
    nota="13/11/2026: Valor 29/10 07:00 ('uns 60% de chance de Lula contra 40% de Bolsonaro'), posterior al corte del 28/10; además es lectura de precios ('Olhando para os preços que estão na tela'): sale de la grilla")
# ------------------------------------------------------------ BR-2026-1T  (bueno = Flávio primero)
add("BR-2026-1T", "Kalshi", "prediction market", "ganador de la 1ª vuelta", "exacto", "2026-10-02", "price1", [0.26],
    verif="si", url="https://news.kalshi.com/p/brazil-election-odds-2026", nota="Lula 74% -> Flávio 1 - 0,74")
add("BR-2026-1T", "Polymarket", "prediction market", "ganador de la 1ª vuelta", "exacto", "2026-10-02", "price",
    [0.73, 0.28], 1, ["Lula", "Flávio"], verif="pdf", url="https://nextpredict.io/market-news/politics/brazil-election-tests-prediction-markets-edge/",
    nota="US$586k negociados")
add("BR-2026-1T", "Polymarket (Action Network)", "prediction market", "ganador de la 1ª vuelta", "exacto", "2026-10-02?",
    "price", [0.74, 0.30], 1, ["Lula", "Flávio"], latest=0, verif="pdf", nota="página actualizada el 7/10: hora incierta")
add("BR-2026-1T", "Plano Político (modelo)", "modelo", "Flávio termina primero", "exacto", "2026-09-30", "prob", [0.29],
    verif="pdf", url="https://planopolitico.com.br/modelos-eleitorais/presidencial/notas/")
add("BR-2026-1T", "Gestora grande sin nombre (Valor)", "gestora", "Flávio termina primero", "exacto", "2026-10-02",
    "prob", [0.35], verif="pdf", url="https://valorinternational.globo.com/markets/news/2026/10/02/markets-brace-for-sharp-moves-after-brazil-vote.ghtml")
add("BR-2026-1T", "Kalshi", "prediction market", "alguien gana en 1ª", "otro", "2026-10-02", "price1", [0.039],
    verif="si", url="https://news.kalshi.com/p/brazil-election-odds-2026", nota="binario secundario")
add("BR-2026-1T", "Polymarket (Rio Times)", "prediction market", "ganador de la elección", "otro", "2026-10-02",
    "price", [0.425, 0.556], 1, ["Lula", "Flávio"], verif="si",
    url="https://www.riotimesonline.com/brazil-runoff-prediction-markets-polymarket-kalshi-odds/",
    nota="corrección: Lula 42,5% (el PDF dice 44%)")
add("BR-2026-1T", "Eurasia Group", "consultora", "ganador de la elección", "otro", "2026-09-28", "prob", [0.45],
    verif="si", url="https://acritica.net/eleicoes-2026/eurasia-group-ve-eleicao-apertada-e-aponta-fatores-que-podem-mexer-na-reta-final/",
    nota="Lula 55% con sesgo a la baja; modelos 50/50")
# ------------------------------------------------------------ BR-2026-2T  (bueno = Flávio)
add("BR-2026-2T", "Polymarket", "prediction market", "ganador", "exacto", "2026-10-23 20:52 ET", "price", [0.767, 0.235],
    0, ["Flávio", "Lula"], verif="pdf", url="https://www.riotimesonline.com/brazil-markets-ibovespa-real-friday-october-23-2026",
    nota="~US$193M negociados. 13/11: Rio Times 23/10 8:25 ET da Polymarket 76,9% / Lula 23,5% (riotimesonline.com/brazil-inflation-eases-before-runoff-vote), consistente")
add("BR-2026-2T", "Polymarket (RG.org)", "prediction market", "ganador", "exacto", "2026-10-23 13:52 ET", "price",
    [0.77, 0.24], 0, ["Flávio", "Lula"], latest=0, verif="si",
    url="https://rg.org/news/prediction-markets/polymarket-daily-brazil-runoff-la-mayor-world-series-october-23-2026",
    nota="US$192,3M")
add("BR-2026-2T", "Kalshi", "prediction market", "ganador", "exacto", "2026-10-23 09:20 ET", "price", [0.76, 0.24], 0,
    ["Flávio", "Lula"], verif="pdf", url="https://www.riotimesonline.com/datafolha-poll-flavio-50-lula-50-runoff-2026",
    nota="13/11: fuente secundaria automatizada de Rio Times ('As of 23 October, 9:20 am ET', 'Flávio Bolsonaro 76% · Lula 24%'); sin registro original de Kalshi")
add("BR-2026-2T", "Kalshi/Polymarket (Rio Times)", "prediction market", "ganador", "exacto", "2026-10-22 09:20 ET",
    "price", [0.79, 0.22], 0, ["Flávio", "Lula"], latest=0, verif="si",
    url="https://www.riotimesonline.com/brazil-runoff-margin-odds-narrow-win/")
add("BR-2026-2T", "Eurasia Group", "consultora", "ganador", "exacto", "2026-10-23", "prob", [0.60], verif="si",
    url="https://www.bloomberglinea.com.br/brasil/eurasia-reduz-de-70-para-60-a-chance-de-vitoria-de-flavio-bolsonaro-no-segundo-turno/",
    nota="baja de 70% a 60%")
add("BR-2026-2T", "Plano Político (modelo)", "modelo", "ganador", "exacto", "2026-10-23", "prob", [0.84], verif="pdf",
    url="https://planopolitico.com.br/en/modelos-eleitorais/presidencial/notas/")
add("BR-2026-2T", "Le Millénaire (vía The Economist)", "modelo", "ganador", "exacto", "2026-10-21", "prob", [0.82],
    verif="si", url="https://www.economist.com/the-americas/2026/10/21/can-lula-now-the-underdog-pull-off-one-last-trick",
    nota="13/11: The Economist 21/10 ('puts his odds of victory at 82%'); reproducción en Estadão 22/10 ('estima suas chances de vitória em 82%')")
add("BR-2026-2T", "Opinião Inteligência Política (agregador)", "modelo", "ganador", "exacto", "2026-10-23", "prob",
    [0.79], verif="si", url="https://brasil61.com/n/agregador-de-pesquisas-indica-chance-de-79-de-vitoria-de-flavio-bolsonaro-bras2617364",
    nota="fuente nueva, no estaba en el PDF; rango del modelo 71-79%")
# ------------------------------------------------------------ MX-2024  (bueno = sin mayoría calificada)
add("MX-2024", "MNI Political Risk", "consultora", "Sheinbaum + supermayoría", "exacto", "2024-05 (datos al 28/5)",
    "prob", [0.70], verif="pdf", url="https://media.marketnews.com/MNIPOLITICALRISK_Mexico_Election_Preview_589d33fa3d.pdf",
    nota="30% supermayoría; el PDF de MNI no se pudo abrir (detrás de registro)")
add("MX-2024", "Jeffrey Weldon (ITAM), vía Bloomberg", "académico", "2/3 en Diputados", "exacto", "2024-05-29", "prob",
    [0.50], verif="pdf", nota="'pretty close to a 50-50 chance'")
add("MX-2024", "UBS GWM", "banco", "'Concentration of power'", "proxy", "2024-04-22", "prob", [0.70], verif="pdf",
    nota="30% de 'mayoría amplia de Morena'; no equivale exactamente a 2/3")
add("MX-2024", "Polymarket", "prediction market", "ganador presidencia", "otro", "2024-05-31 18:00 UTC", "price",
    [0.89, 0.12, 0.0015], 0, ["Sheinbaum", "Gálvez", "Máynez"], verif="pdf", nota="presidencia, no el binario")
# ------------------------------------------------------------ IN-2024  (bueno = BJP >= 272)
for d, p in [("2024-05-31", 0.835), ("2024-06-01", 0.81), ("2024-06-02", 0.96), ("2024-06-03", 0.889)]:
    add("IN-2024", "Polymarket (copia de terceros)", "prediction market", "BJP gana mayoría", "exacto", d, "price1", [p],
        latest=int(d == "2024-06-03"), verif="pdf", nota="precio del Sí; historial no recuperable en Polymarket")
add("IN-2024", "SAMCO", "corredora", "NDA < 272", "otro", "2024-05-29", "prob", [0.90], verif="pdf",
    nota="NDA, no BJP: 20% NDA 400+, 70% 272-400, 10% < 272")
add("IN-2024", "Jefferies (blog secundario)", "banco", "derrota del BJP", "otro", "sin fecha", "prob", [0.90], verif="no")
# ------------------------------------------------------------ CL-2017-2T  (bueno = Piñera)
add("CL-2017-2T", "FantasticBet / GenioBet (La Cuarta)", "casa de apuestas", "ganador", "exacto", "sin fecha",
    "odds", [1.30, 3.20], 0, ["Piñera", "Guillier"], verif="conflicto",
    url="https://www.lacuarta.com/cronica/noticia/pinera-favorito-apuestas/237957/",
    nota="fecha no verificable; GenioBet tenía a Guillier favorito desde el 5/12 (El Desconcierto 9/12)")
# ------------------------------------------------------------ CL-2021-1T  (bueno = Kast primero; cuotas = presidencia)
add("CL-2021-1T", "RojaBet (La Tercera)", "casa de apuestas", "ganador presidencia", "proxy", "2021-11-12", "odds",
    [1.80, 1.90], 0, ["Kast", "Boric"], latest=0, verif="pdf")
add("CL-2021-1T", "Smarkets (Chilevisión)", "exchange", "ganador presidencia", "proxy", "~2021-11-12", "odds",
    [2.14, 1.96], 0, ["Kast", "Boric"], verif="pdf")
add("CL-2021-1T", "RojaBet (Publimetro, contenido pagado)", "casa de apuestas", "ganador presidencia", "proxy",
    "2021-11-17", "odds", [2.25, 1.50], 0, ["Kast", "Boric"], verif="pdf")
add("CL-2021-1T", "Credicorp Capital", "corredora", "gobierno de derecha", "proxy", "2021-11-22", "prob", [0.50],
    ex_ante=0, verif="pdf", nota="publicado después del evento; dice repetir informes previos")
# ------------------------------------------------------------ CL-2021-2T  (bueno = Kast)
add("CL-2021-2T", "Smarkets (La Tercera)", "exchange", "ganador", "exacto", "~2021-12-13", "price", [0.7407, 0.3125], 1,
    ["Boric", "Kast"], latest=0, verif="si",
    url="https://www.latercera.com/la-tercera-pm/noticia/all-in-casas-de-apuestas-se-la-juegan-por-un-triunfo-de-boric-frente-a-kast-este-domingo/EXR3443MCFD67P6SLCHLQM7OJI/",
    nota="corrección: Kast 31,25% (cuota 3,2), no 22,2%")
add("CL-2021-2T", "Smarkets (The Clinic)", "exchange", "ganador", "exacto", "2021-12-14", "odds", [1.35, 2.52], 1,
    ["Boric", "Kast"], verif="si", url="https://www.theclinic.cl/2021/12/14/casas-apuestas-segunda-vuelta-boric-kast/")
add("CL-2021-2T", "RojaBet (The Clinic)", "casa de apuestas", "ganador", "exacto", "2021-12-14", "odds", [1.50, 2.40], 1,
    ["Boric", "Kast"], verif="si", url="https://www.theclinic.cl/2021/12/14/casas-apuestas-segunda-vuelta-boric-kast/")
add("CL-2021-2T", "FantasticBet (The Clinic)", "casa de apuestas", "ganador", "exacto", "2021-12-14", "odds",
    [1.65, 2.25], 1, ["Boric", "Kast"], verif="si", url="https://www.theclinic.cl/2021/12/14/casas-apuestas-segunda-vuelta-boric-kast/")
add("CL-2021-2T", "PredictIt (The Clinic)", "prediction market", "ganador", "exacto", "2021-12-14", "price1", [0.25],
    verif="si", url="https://www.theclinic.cl/2021/12/14/casas-apuestas-segunda-vuelta-boric-kast/",
    nota="'Boric vale tres veces más que Kast': aproximación 75/25")
add("CL-2021-2T", "Nevasa (lectura de precios)", "corredora", "ganador (lectura del mercado)", "exacto", "2021-12-17",
    "prob", [0.50], verif="pdf",
    nota="'asset prices implied roughly 50/50'; 13/11/2026: lectura de precios de activos, no un pronóstico (misma regla "
         "que RBC en CO-2022-2T y RPS en BR-2022-2T): sale de la grilla (decisión 9)")
# ------------------------------------------------------------ CL-2022-PLEB  (bueno = Rechazo)
add("CL-2022-PLEB", "Smarkets (La Tercera)", "exchange", "resultado", "exacto", "2022-08-21", "odds", [1.03, 6.4], 0,
    ["Rechazo", "Apruebo"], latest=0, verif="pdf")
add("CL-2022-PLEB", "Smarkets (La Tercera)", "exchange", "resultado", "exacto", "2022-08-26", "odds", [1.83, 1.80], 0,
    ["Rechazo", "Apruebo"], latest=0, verif="pdf")
add("CL-2022-PLEB", "Smarkets (La Tercera)", "exchange", "resultado", "exacto", "~2022-08-31", "odds", [1.54, 2.10], 0,
    ["Rechazo", "Apruebo"], verif="si",
    url="https://www.latercera.com/la-tercera-pm/noticia/casas-de-apuestas-y-el-plebiscito-mantienen-al-rechazo-como-favorito-pero-apruebo-recorta-distancia/ETCHOB5XHJE6NDV3K56BJ6UWEI/",
    nota="La Tercera: Rechazo entre 1,33 y 1,65; Apruebo entre 2,15 y 3")
add("CL-2022-PLEB", "Coolbet (La Tercera)", "casa de apuestas", "resultado", "exacto", "~2022-08-31", "odds",
    [1.65, 2.15], 0, ["Rechazo", "Apruebo"], verif="si")
add("CL-2022-PLEB", "Juégalo (La Tercera)", "casa de apuestas", "resultado", "exacto", "~2022-08-31", "odds",
    [1.33, 3.00], 0, ["Rechazo", "Apruebo"], verif="si")
# ------------------------------------------------------------ CL-2023-PLEB
add("CL-2023-PLEB", "Polymarket", "prediction market", "Chile cambia su constitución", "exacto", "2023-12-15",
    "price1", [float("nan")], verif="pdf", nota="creado el 15/12 21:09 UTC, ~US$1.008 de volumen total, sin precio recuperable")
# ------------------------------------------------------------ CL-2025-1T  (bueno = Kast primero)
add("CL-2025-1T-ROB", "Polymarket", "prediction market", "ganador 1ª vuelta", "exacto", "2025-11-14 23:00", "price",
    [0.92, 0.077, 0.007, 0.0035, 0.002], 1, ["Jara", "Kast", "Kaiser", "Matthei", "Parisi"], verif="pdf",
    url="https://polymarket.com/event/chile-presidential-election-1st-round-winner", nota="volumen total US$3,77M")
add("CL-2025-1T-ROB", "Kalshi", "prediction market", "ganador 1ª vuelta", "exacto", "2025-11-15 02:00", "price",
    [0.91, 0.07, 0.02, 0.01], 1, ["Jara", "Kast", "Kaiser", "Matthei"], verif="pdf",
    nota="vela diaria que cierra 2 h después del corte")
add("CL-2025-1T-ROB", "Betsson (La Hora)", "casa de apuestas", "ganador 1ª vuelta", "exacto", "2025-11-14", "odds",
    [1.2, 4, 12, 14], 1, ["Jara", "Kast", "Matthei", "Kaiser"], verif="pdf",
    url="https://lahora.cl/cronica/2025/11/14/todo-definido-que-dicen-las-casas-de-apuestas-sobre-los-candidatos-presidenciales",
    nota="falta Parisi en la lista: el margen está subestimado")
add("CL-2025-1T-ROB", "Polymarket", "prediction market", "ganador de la elección", "otro", "2025-11-14 23:00", "price",
    [0.695, 0.1475, 0.1335, 0.021, 0.008], 0, ["Kast", "Jara", "Kaiser", "Matthei", "Parisi"], verif="pdf")
add("CL-2025-1T-ROB", "Credicorp Capital", "corredora", "quién enfrenta a Jara", "otro", "2025-11-13", "prob", [0.70],
    verif="pdf", nota="Kast 70%, Kaiser 15%, Matthei 15%")
# ------------------------------------------------------------ CL-2025-1T-ALT  (bueno = Kaiser no pasa)
add("CL-2025-1T", "Polymarket (1º + 2º lugar)", "prediction market", "Kaiser en la 2ª vuelta", "exacto",
    "2025-11-14 23:00", "price1", [1 - (0.007 + 0.14)], verif="pdf", nota="suma de Kaiser 1º (0,7%) y 2º (14,0%)")
add("CL-2025-1T", "Credicorp Capital", "corredora", "Kaiser enfrenta a Jara", "exacto", "2025-11-13", "prob", [0.85],
    verif="pdf", url="https://eldiariodesantiago.cl/2025/11/13/credicorp-alerta-triunfo-de-kast-ya-esta-asumido-pero-kaiser-podria-hacer-temblar-al-mercado")
# ------------------------------------------------------------ CL-2025-2T  (bueno = Kast)
add("CL-2025-2T", "Polymarket (La Tercera)", "prediction market", "ganador", "exacto", "2025-12-12", "price",
    [0.99, 0.01], 0, ["Kast", "Jara"], verif="pdf",
    url="https://www.latercera.com/pulso/noticia/cuanto-paga-un-triunfo-de-jara-o-kast-en-las-apuestas-las-probabilidades-en-polymarket-ad-portas-de-la-eleccion",
    nota="el pago de US$49.411 por US$1.000 a Jara implica ~2%")
add("CL-2025-2T", "Casas sin nombre (estimación)", "casa de apuestas", "ganador", "exacto", "sin fecha", "odds",
    [1.06, 7.50], 0, ["Kast", "Jara"], verif="no", nota="sin fecha: excluida")
# ------------------------------------------------------------ CO-2018-2T  (bueno = Duque)
add("CO-2018-2T", "El País (Llaneras y Galindo), modelo", "modelo", "ganador", "exacto", "2018-06-10", "prob", [0.80],
    verif="pdf", url="https://elpais.com/internacional/2018/06/10/colombia/1528643627_957392.html",
    nota="error histórico de encuestas; con el error de la 1ª vuelta da 90%")
add("CO-2018-2T", "ANIF", "gremio", "ganador de la elección", "proxy", "2018-04", "prob", [0.65], pre1T=1, verif="si",
    url="https://www.valoraanalitik.com/?p=5795", nota="Duque 65%, Petro 25%, Vargas Lleras 12% (abril)")
# ------------------------------------------------------------ CO-2022-1T  (bueno = Hernández pasa)
add("CO-2022-1T", "El País (Recetas Electorales), modelo", "modelo", "Hernández pasa a la 2ª", "exacto", "2022-05-21",
    "prob", [0.22], verif="pdf",
    url="https://elpais.com/america-colombia/2022-05-21/el-despegue-de-rodolfo-hernandez-en-las-encuestas-complica-el-pase-a-segunda-vuelta-de-fico-gutierrez.html")
add("CO-2022-1T", "MNI Political Risk", "consultora", "2ª vuelta Petro vs Hernández", "exacto", "pre 29/5 (sin fecha)",
    "prob", [0.40], verif="pdf", nota="Petro-Gutiérrez 60%, Petro-Hernández 40%")
add("CO-2022-1T", "PredictIt", "prediction market", "ganador de la elección", "otro", "2022-05-20", "price",
    [0.70, 0.23, 0.12], 2, ["Petro", "Gutiérrez", "Hernández"], verif="pdf")
# ------------------------------------------------------------ CO-2022-2T  (bueno = Hernández)
add("CO-2022-2T", "PredictIt", "prediction market", "ganador", "exacto", "2022-06-06", "price", [0.66, 0.34], 0,
    ["Hernández", "Petro"], latest=0, verif="si",
    url="https://www.asuntoslegales.com.co/actualidad/apostadores-en-ee-uu-a-traves-de-predictit-pujan-por-las-presidenciales-de-colombia-3382868")
add("CO-2022-2T", "PredictIt", "prediction market", "ganador", "exacto", "2022-06-13", "price", [0.61, 0.37], 0,
    ["Hernández", "Petro"], verif="si",
    url="https://www.asuntoslegales.com.co/actualidad/apostadores-en-ee-uu-a-traves-de-predictit-pujan-por-las-presidenciales-de-colombia-3382868")
add("CO-2022-2T", "PredictIt (Semana)", "prediction market", "ganador", "exacto", "~2022-06-03", "price", [0.66, 0.35], 0,
    ["Hernández", "Petro"], latest=0, verif="pdf")
add("CO-2022-2T", "RBC Capital Markets", "banco", "lectura del mercado", "exacto", "2022-05-31", "prob", [0.90],
    verif="pdf", nota="'el mercado descontará una victoria de Hernández con >90%': afirmación sobre precios, no pronóstico. Fuera")
# ------------------------------------------------------------ CO-2026-1T  (bueno = DLE primero)
add("CO-2026-1T-ROB", "Polymarket", "prediction market", "ganador 1ª vuelta", "exacto", "~2026-05-27", "price",
    [0.65, 0.351], 1, ["Cepeda", "De la Espriella"], verif="pdf",
    url="https://www.predictionmarkets.org/beyond-the-headline-odds-how-colombias-election-markets-fit-together/",
    nota="pedir el tick del 29/5 por la API de precios (token IDs en el PDF)")
add("CO-2026-1T-ROB", "Polymarket", "prediction market", "ganador 1ª vuelta", "exacto", "2026-05-10", "price", [0.89, 0.11],
    1, ["Cepeda", "De la Espriella"], latest=0, verif="pdf")
add("CO-2026-1T-ROB", "Polymarket (Semana / La Silla Vacía)", "prediction market", "ganador de la elección", "otro",
    "2026-05-26/28", "price", [0.68, 0.33], 0, ["De la Espriella", "Cepeda"], verif="si",
    url="https://www.lasillavacia.com/?p=424093", nota="presidencia, no 1ª vuelta")
# ------------------------------------------------------------ CO-2026-1T  (bueno = Cepeda NO gana en 1ª)
add("CO-2026-1T", "Polymarket (mercado relacionado)", "prediction market", "victoria en 1ª vuelta", "exacto", "~2026-05-27",
    "price1", [0.85], verif="pdf", url="https://www.predictionmarkets.org/beyond-the-headline-odds-how-colombias-election-markets-fit-together/",
    nota="'outright first-round win ~15%' en el mismo artículo de la 1ª vuelta")
add("CO-2026-1T", "Latin America Risk Report (J. Bosworth)", "analista", "Cepeda gana en 1ª", "exacto", "2026-05-26", "prob",
    [0.80], verif="pdf", url="https://boz.substack.com/p/colombia-election-notes-may-2026", nota="~20% de victoria de Cepeda en 1ª")
add("CO-2026-1T", "Itaú", "banco", "ningún candidato pro-mercado gana la 1ª vuelta", "exacto", "2026-05-25", "prob", [0.85],
    verif="pdf", url="https://banco.itau.co/documents/d/personas/perspectiva-semanal-de-estrategia-25-29",
    nota="~15% para su escenario 'no pro-market candidate wins the first round': lectura = Cepeda gana en 1ª; confirmar en el PDF de Itaú")
# ------------------------------------------------------------ CO-2026-2T  (bueno = DLE)
add("CO-2026-2T", "Polymarket (CLOB)", "prediction market", "ganador", "exacto", "2026-06-20 00:00 UTC", "price",
    [0.895, 0.105], 0, ["De la Espriella", "Cepeda"], verif="pdf", nota="= 19/6 19:00 Bogotá")
add("CO-2026-2T", "Polymarket (La República)", "prediction market", "ganador", "exacto", "2026-06-17", "price",
    [0.89, 0.09], 0, ["De la Espriella", "Cepeda"], latest=0, verif="si",
    url="https://www.larepublica.co/especiales/es-la-economia-estupido-2026/asi-estan-las-predicciones-en-polymarket-para-la-segunda-vuelta-presidencial-4416220",
    nota="Cepeda 9% confirmado; DLE 89% según el PDF")
add("CO-2026-2T", "Kalshi", "prediction market", "ganador", "exacto", "2026-06-17", "price", [0.90, 0.12], 0,
    ["De la Espriella", "Cepeda"], verif="pdf")
add("CO-2026-2T", "PredictIt", "prediction market", "ganador", "exacto", "2026-06-17", "price", [0.94, 0.19], 0,
    ["De la Espriella", "Cepeda"], verif="pdf")
add("CO-2026-2T", "El País (simulación)", "modelo", "ganador", "exacto", "2026-06-17", "prob", [0.83], verif="pdf",
    url="https://elpais.com/america-colombia/elecciones-presidenciales/2026-06-17/que-dicen-las-encuestas-en-colombia-de-la-espriella-claro-favorito-ante-cepeda.html")
add("CO-2026-2T", "Semana (columna J. M. Charry)", "analista", "ganador", "exacto", "2026-06-18", "prob", [0.75],
    verif="si", url="https://www.semana.com/opinion/articulo/probabilidades-para-la-segunda-vuelta-presidencial/202600/")
add("CO-2026-2T", "Morgan Stanley", "banco", "ganador", "exacto", "2026-06-02", "prob", [0.70], verif="pdf",
    url="https://www.bloomberglinea.com/latinoamerica/colombia/la-cautela-de-morgan-stanley-ante-la-segunda-vuelta-en-colombia-y-por-que-bajo-el-dolar")
add("CO-2026-2T", "A. F. Arias (Monte Carlo)", "modelo partidario", "ganador", "exacto", "2026-06-12", "prob", [0.90],
    verif="no", nota="ex ministro partidario: excluido")
# ------------------------------------------------------------ TR-2015-06 / TR-2015-11
add("TR-2015-11", "Carnegie Europe (Sinan Ülgen)", "think tank", "AKP mayoría", "exacto", "2015-10-27", "prob", [0.20],
    verif="si", url="https://carnegieendowment.org/posts/2015/10/turkey-votes-again",
    nota="AKP-CHP 40%, nueva elección 20%, AKP-MHP 15%, CHP-MHP 5%")
# ------------------------------------------------------------ TR-2023-2T  (bueno = Kılıçdaroğlu)
add("TR-2023-2T", "Polymarket (mercado lateral, media del día)", "prediction market", "ganador", "exacto", "2023-05-26",
    "price1", [1 - 0.8858], verif="pdf", nota="Erdoğan 88,58¢ de media muestreada cada 10 min")
add("TR-2023-2T", "Casa británica sin nombre", "casa de apuestas", "ganador", "exacto", "~2023-05-24", "odds",
    [1 + 1 / 7, 6.5], 1, ["Erdoğan", "Kılıçdaroğlu"], verif="pdf", nota="1/7 y 11/2 fraccionales")
add("TR-2023-2T", "Eurasia Group", "consultora", "ganador", "exacto", "2023-05-21", "prob", [0.20], verif="si",
    url="https://www.citizen.co.za/news/news-world/erdogan-eyes-third-decade-runoff-may-2023/", nota="Erdoğan 80%")
add("TR-2023-2T", "Verisk Maplecroft", "consultora", "ganador", "exacto", "2023-05-28", "prob", [0.13], ex_ante=0,
    verif="pdf", nota="reportado el 28/5: posterior al corte")
add("TR-2023-2T", "Wells Fargo", "banco", "ganador", "exacto", "2023-03-08", "prob", [0.425], pre1T=1, verif="pdf",
    nota="Erdoğan 55-60%, anterior a la 1ª vuelta")

# ==================================================================== ARGENTINA (fuera de muestra, PDF del 12/11/2026)
# Polymarket/Kalshi: el PDF los leyó de la API CLOB / histórica ("verificado en la fuente"); desde esta sesión la API está
# fuera de la lista de acceso, así que quedan como 'pdf'. Hora = último punto horario antes del cierre del viernes.
PM = "https://polymarket.com/event/argentina-presidential-election-who-will-win"
# ------------------------------------------------------------ AR-2015-2T (bueno = Macri)
add("AR-2015-2T", "Citi (nota a clientes)", "consultora", "Macri gana el balotaje", "exacto", "2015-10-29", "prob", [0.55],
    verif="pdf", nota="citado por terceros")
# ------------------------------------------------------------ AR-2019-PASO (bueno = ventaja de Fernández <= 7)
add("AR-2019-PASO", "Poliarquía (encuesta a +50 gestores)", "encuesta a inversores", "Macri-Pichetto gana la presidencial",
    "otro", "2019-07-21", "prob", [0.65], verif="pdf", nota="P(Macri presidente); esperaban Fernández +3 en la PASO")
add("AR-2019-PASO", "Balanz Capital", "consultora", "P(Macri) condicional al resultado de la PASO", "otro", "2019-08-09",
    "prob_range", [0.30, 0.80], verif="pdf", nota="probabilidades condicionales, no del binario")
# ------------------------------------------------------------ AR-2019-1T (bueno = hay balotaje)
add("AR-2019-1T", "Eurasia Group", "consultora", "Fernández gana la presidencial", "proxy", "2019-08-15", "prob", [0.20],
    verif="pdf", nota="80% Fernández presidente; no es P(gana en 1ª)")
# ------------------------------------------------------------ AR-2023-PASO (bueno = LLA no sale primera)
add("AR-2023-PASO", "PPI (escenarios PASO)", "consultora", "batacazo de Milei (gana la PASO)", "exacto", "2023-07-12", "prob",
    [0.95], verif="pdf", nota="PPI: Milei batacazo 5% (CCL 515 -> 762); p del bueno = 1 - 5%")
add("AR-2023-PASO", "Polymarket (API CLOB)", "prediction market", "Milei gana la presidencial 2023", "proxy",
    "2023-08-11 19:00 UTC", "price1", [1 - 0.505], verif="pdf", url=PM, nota="Milei presidente 50,5%; proxy")
add("AR-2023-PASO-ROB", "PPI (escenarios PASO)", "consultora", "triunfo contundente de JxC", "exacto", "2023-07-12", "prob",
    [0.30], verif="pdf", nota="CCL 515 -> 291-364")
# ------------------------------------------------------------ AR-2023-1T (bueno = Bullrich entra al balotaje)
add("AR-2023-1T", "Polymarket (API CLOB)", "prediction market", "Bullrich gana la presidencial", "proxy",
    "2023-10-20 19:00 UTC", "price1", [0.085], verif="pdf", url=PM, nota="cota inferior de P(Bullrich entra al balotaje)")
add("AR-2023-1T-ROB", "Polymarket (API CLOB)", "prediction market", "hay segunda vuelta", "exacto", "2023-10-20 19:00 UTC",
    "price1", [0.865], verif="pdf", url="https://polymarket.com/event/argentina-presidential-election-who-will-win",
    nota="vol. 7.009 USD; 88,0% el 22/10 (no ex ante)")
# ------------------------------------------------------------ AR-2023-2T (bueno = Milei)
add("AR-2023-2T", "Polymarket (API CLOB)", "prediction market", "ganador (contratos Milei y Massa)", "exacto",
    "2023-11-17 19:00 UTC", "price", [0.575, 0.425], 0, ["Milei", "Massa"], verif="pdf", url=PM,
    nota="vol. 573.123 y 174.888 USD; los dos lados suman 1,000: sin margen")
add("AR-2023-2T", "Polymarket (API CLOB)", "prediction market", "ganador (contratos Milei y Massa)", "exacto",
    "2023-10-23 19:00 UTC", "price", [0.47, 0.525], 0, ["Milei", "Massa"], latest=0, verif="pdf", url=PM,
    nota="día después de la 1ª vuelta")
add("AR-2023-2T", "Polymarket (API CLOB)", "prediction market", "Milei gana por más de 5 pts", "otro",
    "2023-11-17 19:00 UTC", "price1", [0.275], verif="pdf", url="https://polymarket.com/event/margin-in-argentina-presidential-election")
add("AR-2023-2T", "Polymarket (API CLOB)", "prediction market", "ganador (contratos Milei y Massa)", "exacto",
    "2023-11-19 20:00 UTC", "price", [0.635, 0.365], 0, ["Milei", "Massa"], ex_ante=0, verif="pdf", url=PM,
    nota="día de la elección: posterior al corte")
add("AR-2023-2T", "PPI (escenarios balotaje)", "consultora", "escenarios condicionales al ganador", "otro", "2023-11-18",
    "prob", [float("nan")], ex_ante=0, verif="pdf", nota="70/30 y 80/20 son probabilidades de sub-escenarios, no del ganador")
# ------------------------------------------------------------ AR-2025-PBA (bueno = ventaja FP <= 5)
add("AR-2025-PBA", "Polymarket (API CLOB)", "prediction market", "LLA gana más bancas en Diputados (elección NACIONAL)",
    "otro", "2025-09-05 19:00 UTC", "price", [0.80, 0.185], 0, ["LLA", "UP"], verif="pdf", nota="otra elección; proxy de clima")
add("AR-2025-PBA", "JP Morgan", "consultora", "FP gana por más de 5: 'baja probabilidad'", "exacto", "2025-09-05", "prob",
    [float("nan")], verif="pdf", nota="cualitativa, sin número")
add("AR-2025-PBA", "Max Capital", "consultora", "continuidad hacia 2027", "otro", "2025-09-06", "prob", [0.68], ex_ante=0,
    verif="pdf")
# ------------------------------------------------------------ AR-2025-LEG (bueno = LLA >= 35%)
add("AR-2025-LEG", "Polymarket (API CLOB)", "prediction market", "LLA gana más bancas en disputa", "otro",
    "2025-10-24 19:00 UTC", "price", [0.795, 0.215], 0, ["LLA", "UP"], verif="pdf", nota="binario distinto: ver -ROB")
add("AR-2025-LEG", "Kalshi (API histórica)", "prediction market", "partido con mayor ganancia neta de bancas", "otro",
    "2025-10-24 20:00 UTC", "price1", [0.925], verif="pdf", nota="compra 0,86 / venta 0,99, punto medio; 10.444 contratos")
add("AR-2025-LEG", "BTG Pactual", "consultora", "empate LLA-FP cerca de 35%", "otro", "2025-10-26", "prob", [0.50], ex_ante=0,
    verif="pdf")
add("AR-2025-LEG-ROB", "Polymarket (API CLOB)", "prediction market", "LLA gana más bancas en disputa (vs UP)", "exacto",
    "2025-10-24 19:00 UTC", "price", [0.795, 0.215], 0, ["LLA", "UP"], verif="pdf",
    nota="vol. 1.602.204 y 1.257.274 USD; 'hold the most seats' (composición total, UP 94,6%) es otro contrato")
add("AR-2025-LEG-ROB", "Polymarket (API CLOB)", "prediction market", "LLA gana más bancas en disputa (vs UP)", "exacto",
    "2025-09-08 19:00 UTC", "price", [0.635, 0.335], 0, ["LLA", "UP"], latest=0, verif="pdf", nota="día después de la PBA")
