"""Cuentas de la revisión con el filtro de liquidez estricto (20/11/2026, conversación E).
Igual que revision_cuentas.py (38b44ef173ec), salvo YPF 2025-PBA: con el adaptador estricto
(ivol_adapter_estricto.py c218cd58a420, OI >= 100; corrida run_final_estricto.py a254e7b2f133) el collar de las tres
reglas es 1 x (+P28, -C32), costo -0,0162; P_malo -0,0768; P_real (mid) -0,0676
(resultados/revision_b2_filtro_estricto_cambios.csv). El resto de los casos no cambia con el filtro estricto.
Marcado 'a vencimiento' = valor intrínseco de cada pata en t1 = pago al vencimiento si el spot se queda en S1.
R = ret + h * sum(q * intr(S1)) / S0 - costo, con S1 = S0 * (1 + ret).  Sin datos crudos.
Opcional: python revision_cuentas_estricto.py resultados/revision_b3_marcado_ejecutable.csv
agrega los totales con el marcado ejecutable (filtro estricto, regla principal)."""
import json

def intr(t, K, S): return max(K - S, 0.0) if t == "P" else max(S - K, 0.0)

def R(ret, S0, h, legs, cost):
    S1 = S0 * (1 + ret)
    return ret + h * sum(q * intr(t, K, S1) for q, t, K in legs) / S0 - cost

# caso: S0, ret, grupo, resultado, P_real mid {regla: valor}, estructura {regla: (h, legs, costo)}, put ingenuo (K, costo, P_real mid), P_malo/d (principal)
C = {}
def add(k, S0, ret, g, res, **kw): C[k] = dict(S0=S0, ret=ret, g=g, res=res, **kw)

P, Cc = "P", "C"
add("BOVA11 22-2T", 110.63, 0.006850996995160008, "I", "malo",
    main=(0.75, [(1,P,106),(-1,P,105)], 0.0023727514801804616, 0.006613721847141964),
    piso=(0.75, [(1,P,110),(-1,P,104),(-1,Cc,115)], -0.0026439230779153724, 0.006478136048274506),
    v1=(1.0, [(1,P,110),(-1,P,102),(-1,Cc,112)], -0.012293112430649254, 0.001743931904485868),
    naive=(105, 0.0154, -0.0029111805232967525), pm=-0.04997333707055096, d=-0.054360518396084384)
add("BOVA11 26-2T", 202.31, -0.141901705386399, "I", "malo",
    main=(1.0, [(1,P,199),(-1,Cc,205)], 0.0012357495737391963, -0.006562412070481888),
    piso=(1.0, [(1,P,192),(-1,Cc,209)], 0.0004942998294956841, -0.06654569637978264),
    v1=(0.75, [(1,P,199),(-1,Cc,205)], 0.0009268121803043972, -0.04039723539946116),
    naive=(192, 0.0267, -0.08456292516490016), pm=-0.017582440235347496, d=-0.20409889582451796)
add("EWZ 26-2T", 42.56, -0.19779996545995737, "I", "malo",
    main=(1.0, [(1,P,41),(-1,Cc,43)], -0.002114860054634772, -0.03953793803812222),
    piso=(0.5, [(1,P,41),(-1,Cc,43)], -0.001057430027317386, -0.1186689517490398),
    v1=None, naive=(40, 0.0498, -0.1089758431652971), pm=-0.034447238904123045, d=-0.31915657492619864)
add("INDA 24", 54.70, -0.06065409444546077, "I", "malo",
    main=(1.0, [(1,P,54),(-1,Cc,55)], -0.004570144328460134, -0.020436824355011582),
    piso="main", v1="main", naive=(52, 0.0046, -0.038717401668852125), pm=-0.008265255286438344, d=-0.10788331992167412)
add("BOVA11 22-1T", 105.90, 0.053033947774099754, "I", "bueno",
    main=(1.0, [(1,P,105),(-1,P,100),(-1,Cc,108)], -0.013409467447897632, 0.018849249068895936),
    piso="main", v1="main", naive=(100, 0.0118, 0.04269354858012236), pm=0.005063991378906375, d=-0.04079381185462339)
add("EWZ 22-1T", 29.60, 0.10032765277596867, "O", "bueno",
    main=(1.0, [(1,P,29.5),(-1,P,26),(-1,Cc,30)], 0.0010134507017009187, 0.01097508257600402),
    piso=(1.0, [(1,P,29),(-1,P,26.5),(-1,Cc,30.5)], -0.0020269014034018477, 0.028372652955203206),
    v1=(1.0, [(1,P,29),(-1,P,25),(-1,Cc,30)], -0.004391619707370665, 0.015704519183941668),
    naive=(28, 0.0213, 0.08005863874195022), pm=-0.004454137094597327, d=-0.11397026841771676)
add("GGAL 25-PBA", 40.13, -0.2362835939684933, "O", "malo",
    main=(1.0, [(1,P,39),(-1,Cc,41)], -0.0012458668940155057, -0.03383022369097313),
    piso=(1.0, [(1,P,38),(-1,Cc,41)], -0.01121280204613958, -0.048780626419159256),
    v1="main", naive=(38, 0.0486, -0.10172996941481838), pm=-0.026975907310356095, d=-0.4343123140284348)
add("YPF 25-PBA", 30.87, -0.1534494452676286, "O", "malo",
    main=(1.0, [(1,P,28),(-1,Cc,32)], -0.016195658201556537, -0.06761245679937895),
    piso="main",
    v1="main", naive=(30, 0.0389, -0.062753759338912), pm=-0.07682085349066853, d=-0.27880679080620785)
add("GGAL 25-LEG", 35.67, 0.37773302611852233, "O", "bueno",
    main=(1.0, [(1,P,30),(-1,Cc,36)], -0.05747563499273446, 0.05600965463480145),
    piso=(1.0, [(1,P,30),(-1,Cc,40)], -0.01822398182696458, 0.11909266865121737),
    v1=None, naive=(35, 0.1402, 0.24455777430608885), pm=-0.10123750476438714, d=-0.30767008603670587)
add("YPF 25-LEG", 27.12, 0.23218815019520034, "O", "bueno",
    main=(1.0, [(1,P,25),(-1,Cc,28)], -0.011063699758839265, 0.03211957955619016),
    piso=(1.0, [(1,P,24),(-1,Cc,29)], -0.014751599678452368, 0.09020400329009634),
    v1=(0.75, [(1,P,25),(-1,P,24),(-1,Cc,33)], -0.01936147457796871, 0.18862483239477068),
    naive=(25, 0.0811, 0.1556642268632287), pm=-0.06692667017733966, d=-0.3468926058278715)
# casos que solo cubren las alternativas
add("EWZ 22-2T", 31.43, 0.03981762165897429, "I", "malo", main=None,
    piso=(1.0, [(1,P,30),(-1,P,29),(-1,Cc,34)], -0.011136866965585239, 0.04522695704225855),
    v1=(0.75, [(1,P,31),(-1,P,28),(-1,Cc,32)], -0.005011590134513359, 0.021680438315021186),
    naive=(30, 0.0286, 0.015157416235178401))
add("EWZ 14-2T", 41.59, -0.04814782038599441, "O", "malo", main=None,
    piso=(1.0, [(1,P,39),(-1,P,38),(-1,Cc,45)], -0.02308256314709255, -0.01953505981824427),
    v1=(1.0, [(1,P,39),(-1,Cc,42)], -0.030536307496674516, -0.0102779902227957),
    naive=(39.5, 0.0353, -0.0678641764074693))
add("EWZ 18-2T", 40.03, -0.033198751569484375, "O", "bueno", main=None, piso=None,
    v1=(0.75, [(1,P,38.5),(-1,Cc,40.5)], -0.0031854529926942246, -0.019332662071874222),
    naive=(38, 0.0195, -0.038945058928854345))
add("EWZ 26-1T", 38.18, 0.12546543871534532, "O", "bueno", main=None,
    piso=(0.5, [(1,P,38),(-1,P,36),(-1,Cc,38.5)], -0.007072052487578815, 0.07393113031048862),
    v1=(1.0, [(1,P,38),(-1,P,35),(-1,Cc,38.5)], -0.008381691837130452, 0.016503444832649594),
    naive=(36.5, 0.0238, 0.1017609664884608))
# put ingenuo en el resto de los casos con put líquido (sin cobertura de ninguna regla)
for k, S0, ret, g, res, K, c, m in [
    ("BOVA11 26-1T", 196.60, 0.04087541615043411, "I", "bueno", 185, 0.0157, 0.02564151513043523),
    ("ECH 21-2T", 24.27, -0.11379943505478407, "O", "malo", 24, 0.0783, -0.08187264599155127),
    ("EWZ 14-1T", 43.32, 0.06208934272270161, "O", "bueno", 42, 0.0168, 0.04650939282678844),
    ("YPF 23-PASO", 14.51, -0.01786758050241488, "O", "malo", 14, 0.0517, -0.04371215095066008),
    ("GGAL 23-1T", 11.33, 0.03854578033331291, "O", "malo", 11, 0.1059, 0.012067404340373802),
    ("ARGT 25-LEG", 74.31, 0.18736072834997475, "O", "bueno", 60, 0.0195, 0.16818500725367858)]:
    add(k, S0, ret, g, res, main=None, piso=None, v1=None, naive=(K, c, m))

def struct(c, rule):
    s = c[rule]
    return c["main"] if s == "main" else s

out = {}
for k, c in C.items():
    o = dict(g=c["g"], res=c["res"], ret=c["ret"])
    for rule in ("main", "piso", "v1"):
        s = struct(c, rule)
        if s:
            h, legs, cost, mid = s
            o[rule] = (R(c["ret"], c["S0"], h, legs, cost), mid)
        else:
            o[rule] = (c["ret"], c["ret"])
    K, cost, mid = c["naive"]
    o["naive"] = (R(c["ret"], c["S0"], 1.0, [(1, P, K)], cost), mid, cost)
    if "pm" in c and c["main"]:
        hA = min(max(c["pm"] / c["d"], 0.0), 1.0)
        o["red"] = (hA * c["ret"], hA)
    out[k] = o

TEN = ["BOVA11 22-2T","BOVA11 26-2T","EWZ 26-2T","INDA 24","GGAL 25-PBA","YPF 25-PBA",
       "BOVA11 22-1T","EWZ 22-1T","GGAL 25-LEG","YPF 25-LEG"]

print("Tabla de casos cubiertos (a vencimiento | mid), %:")
for k in TEN:
    o = out[k]
    print(f"{k:13s} sin {o['ret']*100:+6.1f} | princ {o['main'][0]*100:+6.2f} ({o['main'][1]*100:+6.2f}) | ingenuo {o['naive'][0]*100:+6.2f} (caja {o['naive'][2]*100:.2f}) | achicar {o['red'][0]*100:+6.2f} ({o['red'][1]:.0%}) | piso {o['piso'][0]*100:+6.2f} | v1 {o['v1'][0]*100:+6.2f}")

def tot(keys, col, i=0):
    t = dict(all=0, I=0, O=0, malo=0, bueno=0)
    for k in keys:
        o = out[k]; x = (o[col][i] - o["ret"]) * 100
        t["all"] += x; t[o["g"]] += x; t[o["res"]] += x
    return t
print("\nTotales de P&L de cobertura en los 10 casos (pp):")
for col, lab in [("main","principal"),("naive","put ingenuo"),("red","achicar"),("piso","piso de suba"),("v1","v1")]:
    a = tot(TEN, col, 0)
    print(f"  {lab:13s} a venc.: total {a['all']:+6.1f} in {a['I']:+6.1f} out {a['O']:+6.1f} malo {a['malo']:+6.1f} bueno {a['bueno']:+6.1f}", end="")
    if col in ("main","piso","v1","naive"):
        b = tot(TEN, col, 1)
        print(f" || mid: total {b['all']:+6.1f} in {b['I']:+6.1f} out {b['O']:+6.1f} malo {b['malo']:+6.1f} bueno {b['bueno']:+6.1f}")
    else: print()
ALL = list(C.keys())
for col, lab in [("piso","piso de suba"),("v1","v1"),("naive","put ingenuo (20 casos)")]:
    a = tot(ALL, col, 0); b = tot(ALL, col, 1)
    print(f"  todos sus casos {lab}: a venc. {a['all']:+.1f} (in {a['I']:+.1f}, out {a['O']:+.1f}) | mid {b['all']:+.1f}")

# ciclo argentino 2025 compuesto, a vencimiento
for tk in ("GGAL","YPF"):
    a, b = out[f"{tk} 25-PBA"], out[f"{tk} 25-LEG"]
    print(f"{tk} 2025 compuesto: sin cubrir {((1+a['ret'])*(1+b['ret'])-1)*100:+.1f} | principal a venc. {((1+a['main'][0])*(1+b['main'][0])-1)*100:+.1f} | mid {((1+a['main'][1])*(1+b['main'][1])-1)*100:+.1f}")
# drag EWZ (145 meses = 12,083 años; drag_permanente.txt)
yrs = 145/12
e26 = (out["EWZ 26-2T"]["main"][0]-out["EWZ 26-2T"]["ret"])*100
e22 = (out["EWZ 22-1T"]["main"][0]-out["EWZ 22-1T"]["ret"])*100
print(f"EWZ eventos a venc.: 2026 {e26:+.2f}, 2022-1T {e22:+.2f}; total {(e26+e22)/yrs*100:+.0f} pb/año; sin 2026 {e22/yrs*100:+.0f} pb/año")
# costos de los buenos (rango) a vencimiento
print("costo en buenos a venc.:", [round((out[k]['main'][0]-out[k]['ret'])*100,1) for k in TEN[6:]])
# marcado ejecutable (opcional): totales de la regla principal en los 10 casos, filtro estricto
import sys
if len(sys.argv) > 1:
    import csv
    name = {"BR-2022-2T": "22-2T", "BR-2026-2T": "26-2T", "IN-2024": "24", "BR-2022-1T": "22-1T",
            "AR-2025-PBA": "25-PBA", "AR-2025-LEG": "25-LEG"}
    ex = {}
    for r in csv.DictReader(open(sys.argv[1], encoding="utf-8")):
        if r["filtro"] == "estricto" and r["regla"] == "principal":
            ex[f"{r['activo']} {name[r['evento']]}"] = float(r["P_real_ejecutable"])
    t = dict(all=0, I=0, O=0, malo=0, bueno=0)
    print("\nMarcado ejecutable, regla principal (filtro estricto), %:")
    for k in TEN:
        o = out[k]; x = (ex[k] - o["ret"]) * 100
        out[k]["main_ejec"] = ex[k]
        print(f"  {k:13s} {ex[k]*100:+6.2f}")
        t["all"] += x; t[o["g"]] += x; t[o["res"]] += x
    print(f"  total {t['all']:+6.1f} in {t['I']:+6.1f} out {t['O']:+6.1f} malo {t['malo']:+6.1f} bueno {t['bueno']:+6.1f}")
json.dump(out, open("revision_out_estricto.json","w"), indent=1)
