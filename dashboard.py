import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

st.set_page_config(page_title="Simulador Transición Energética Argentina", layout="wide")

# ── CONSTANTES ───────────────────────────────────────────────────────────────
PBI_ARG        = 620_000
DEMANDA_2024   = 145_000
HORAS_AÑO      = 8_760
TRABAJADORES_TERMICOS = 52_000
COSTO_RECONVERSION = 90_000
COSTO_RETIRO       = 40_000
PORC_RETIRO        = 0.35
AHORRO_GNL_ANUAL   = 4_200

FACTOR_PLANTA = {
    "Térmica fósil": 0.45, "Hidro": 0.40, "Nuclear": 0.90,
    "Eólica": 0.30, "Solar": 0.22, "WtE": 0.75,
}
CAP_2024 = {
    "Térmica fósil": 25.8, "Hidro": 10.9, "Nuclear": 1.755,
    "Eólica": 4.2, "Solar": 1.1, "WtE": 0.0,
}
CAPEX_POR_GW = {
    "Eólica": 1_200, "Solar": 900, "Nuclear": 8_500,
    "WtE": 4_600, "Hidro": 2_500, "Térmica fósil": 400,
}
OPEX_POR_GWH = {
    "Térmica fósil": 80, "Hidro": 5, "Nuclear": 12,
    "Eólica": 8, "Solar": 5, "WtE": 20,
}
EMPLEOS_POR_GW = {
    "Eólica": 400, "Solar": 300, "Nuclear": 800,
    "WtE": 700, "Hidro": 200, "Térmica fósil": 2_000,
}
EMISIONES_POR_GWH = {
    "Térmica fósil": 490, "Hidro": 4, "Nuclear": 0,
    "Eólica": 0, "Solar": 0, "WtE": 50,
}
COSTOS_FIJOS = {"Transmisión AT": 5_200, "BESS": 2_200, "Eficiencia": 800}
COLORES = {
    "Térmica fósil": "#c0392b", "Hidro": "#2980b9",
    "Nuclear": "#8e44ad", "Eólica": "#27ae60",
    "Solar": "#f39c12", "WtE": "#7f8c8d",
}

ESCENARIOS = {
    "Plan original (doc.)":     {"Térmica fósil": 10, "Hidro": 13, "Nuclear": 20, "Eólica": 32, "Solar": 18, "WtE": 7},
    "Mín. impacto laboral":     {"Térmica fósil": 29, "Hidro": 12, "Nuclear":  5, "Eólica": 29, "Solar": 20, "WtE": 5},
    "Máx. renovables":          {"Térmica fósil":  5, "Hidro": 13, "Nuclear":  5, "Eólica": 42, "Solar": 28, "WtE": 7},
    "Nuclear pivote":           {"Térmica fósil":  5, "Hidro": 13, "Nuclear": 35, "Eólica": 25, "Solar": 15, "WtE": 7},
    "Balance económico":        {"Térmica fósil": 20, "Hidro": 13, "Nuclear":  8, "Eólica": 34, "Solar": 18, "WtE": 7},
}

@st.cache_data
def calcular(mix_tuple):
    demanda_2035 = DEMANDA_2024 * (1.03 ** 10)
    gen = {k: v/100 * demanda_2035 for k, v in mix.items()}
    gw = {k: gen[k] / (HORAS_AÑO * FACTOR_PLANTA[k]) for k in mix}
    gw_nuevo = {k: max(0, gw[k] - CAP_2024[k]) for k in mix}
    inversion_gen = {k: gw_nuevo[k] * CAPEX_POR_GW[k] for k in mix}

    desplazados   = int(TRABAJADORES_TERMICOS * max(0, (61 - mix["Térmica fósil"]) / 61))
    a_reconvertir = int(desplazados * (1 - PORC_RETIRO))
    a_retiro      = desplazados - a_reconvertir
    costo_laboral = (a_reconvertir * COSTO_RECONVERSION + a_retiro * COSTO_RETIRO) / 1_000_000

    presupuesto = {**inversion_gen, **COSTOS_FIJOS, "Transición laboral": costo_laboral}
    total_inv = sum(presupuesto.values())

    emisiones = sum(gen[k] * EMISIONES_POR_GWH[k] / 1_000_000 for k in mix)
    red_emis  = (52 - emisiones) / 52 * 100

    empleos   = sum(gw[k] * EMPLEOS_POR_GW[k] for k in mix if k != "Térmica fósil")
    cobertura = empleos / max(desplazados, 1)

    mix_2024_base = {"Térmica fósil": 0.61, "Hidro": 0.16, "Nuclear": 0.08,
                     "Eólica": 0.10, "Solar": 0.03, "WtE": 0.02}
    cop_2024 = sum(mix_2024_base[k] * DEMANDA_2024 * OPEX_POR_GWH[k] for k in mix_2024_base)
    cop_2035 = sum((mix[k]/100) * demanda_2035 * OPEX_POR_GWH[k] for k in mix)
    ahorro_op    = (cop_2024 - cop_2035) / 1_000
    ahorro_total = ahorro_op + AHORRO_GNL_ANUAL
    payback      = total_inv / max(ahorro_total, 1)
    roi_20       = (ahorro_total * 20 - total_inv) / total_inv * 100

    return {
        "inversion": total_inv, "pbi": total_inv / PBI_ARG * 100,
        "presupuesto": presupuesto, "inversion_gen": inversion_gen,
        "emisiones": emisiones, "red_emis": red_emis,
        "desplazados": desplazados, "a_reconvertir": a_reconvertir,
        "a_retiro": a_retiro, "costo_laboral": costo_laboral,
        "empleos": empleos, "cobertura": cobertura,
        "gw": gw, "gw_nuevo": gw_nuevo,
        "ahorro_op": ahorro_op, "ahorro_total": ahorro_total,
        "payback": payback, "roi_20": roi_20,
        "gen": gen, "demanda_2035": demanda_2035,
        "cop_2024": cop_2024 / 1_000, "cop_2035": cop_2035 / 1_000,
    }

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.header("🎛️ Ajustá la matriz 2035")
st.sidebar.markdown("Los valores se normalizan automáticamente a 100%.")

escenario_sel = st.sidebar.selectbox("📋 Cargar escenario predefinido",
    ["— personalizado —"] + list(ESCENARIOS.keys()))

if escenario_sel != "— personalizado —":
    defaults = ESCENARIOS[escenario_sel]
else:
    defaults = {"Térmica fósil": 10, "Hidro": 13, "Nuclear": 20, "Eólica": 32, "Solar": 18, "WtE": 7}

termica_raw = st.sidebar.slider("🔴 Térmica fósil", 0, 100, defaults["Térmica fósil"], step=1)
hidro_raw   = st.sidebar.slider("🔵 Hidro",          0, 100, defaults["Hidro"],         step=1)
nuclear_raw = st.sidebar.slider("🟣 Nuclear",         0, 100, defaults["Nuclear"],       step=1)
eolica_raw  = st.sidebar.slider("🟢 Eólica",          0, 100, defaults["Eólica"],        step=1)
solar_raw   = st.sidebar.slider("🟡 Solar",           0, 100, defaults["Solar"],         step=1)
wte_raw     = st.sidebar.slider("⚫ WtE",             0, 100, defaults["WtE"],           step=1)

suma_raw = termica_raw + hidro_raw + nuclear_raw + eolica_raw + solar_raw + wte_raw
suma_raw = max(suma_raw, 1)  # evita división por cero si ponés todo en 0

termica = termica_raw / suma_raw * 100
hidro   = hidro_raw   / suma_raw * 100
nuclear = nuclear_raw / suma_raw * 100
eolica  = eolica_raw  / suma_raw * 100
solar   = solar_raw   / suma_raw * 100
wte     = wte_raw     / suma_raw * 100

st.sidebar.success(f"✅ Normalizado a 100% (Térmica {termica:.0f}% · Hidro {hidro:.0f}% · Nuclear {nuclear:.0f}% · Eólica {eolica:.0f}% · Solar {solar:.0f}% · WtE {wte:.0f}%)")

mix = {"Térmica fósil": termica, "Hidro": hidro, "Nuclear": nuclear,
       "Eólica": eolica, "Solar": solar, "WtE": wte}
r = calcular(tuple(mix.items()))

# ── HEADER ───────────────────────────────────────────────────────────────────
st.title("⚡ Simulador Transición Energética Argentina 2035")
st.markdown("Ajustá los sliders o elegí un escenario predefinido. Los números se actualizan en tiempo real.")

# ── MÉTRICAS ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Inversión total", f"USD {r['inversion']:,.0f}M", f"{r['pbi']:.1f}% del PBI en 10 años")
c2.metric("🌿 Emisiones CO₂ 2035", f"{r['emisiones']:.1f} Mt", f"{r['emisiones']-52:.1f} Mt vs 2024")
c3.metric("👷 Desplazados", f"{r['desplazados']:,}", f"{r['a_reconvertir']:,} reconversión / {r['a_retiro']:,} retiro")
c4.metric("📅 Payback inversión", f"{r['payback']:.1f} años", f"ROI 20 años: {r['roi_20']:.0f}%")

# ── ALERTAS DE TRADEOFFS ─────────────────────────────────────────────────────
st.markdown("---")
st.subheader("⚠️ Tensiones del escenario")
t1, t2, t3 = st.columns(3)

with t1:
    st.markdown("**Empleo vs Descarbonización**")
    costo_por_ton = r['costo_laboral'] / max((52 - r['emisiones']), 0.1)
    if termica <= 10:
        st.error(f"Térmica en {termica}%: máximo impacto laboral.\n{r['desplazados']:,} trabajadores desplazados.\nCada punto menos de térmica = +{int(52_000/61):,} desplazados.")
    elif termica <= 25:
        st.warning(f"Térmica en {termica}%: impacto laboral moderado.\n{r['desplazados']:,} desplazados.")
    else:
        st.success(f"Térmica en {termica}%: menor impacto laboral.\n{r['desplazados']:,} desplazados.\nPero CO₂ solo baja {r['red_emis']:.1f}%.")

with t2:
    st.markdown("**Nuclear: generación vs costo**")
    gw_nuclear = r['gw']['Nuclear']
    inv_nuclear = r['inversion_gen']['Nuclear']
    if nuclear >= 20:
        st.error(f"Nuclear al {nuclear}%: necesitás {gw_nuclear:.1f} GW.\nInversión nuclear: USD {inv_nuclear:,.0f}M.\nEl plan original solo prevé 2.8 GW (USD 8.500M).")
    elif nuclear >= 10:
        st.warning(f"Nuclear al {nuclear}%: {gw_nuclear:.1f} GW necesarios.\nInversión: USD {inv_nuclear:,.0f}M.")
    else:
        st.success(f"Nuclear al {nuclear}%: {gw_nuclear:.1f} GW.\nInversión contenida: USD {inv_nuclear:,.0f}M.\nPero perdés generación base 24/7.")

with t3:
    st.markdown("**Renovables: % generación vs GW reales**")
    gw_sol_eol = r['gw']['Solar'] + r['gw']['Eólica']
    pct_sol_eol = solar + eolica
    if pct_sol_eol >= 50:
        st.warning(f"Solar+Eólica al {pct_sol_eol}% de generación requiere {gw_sol_eol:.0f} GW instalados.\nFactor de planta bajo (solar 22%, eólica 30%) = mucha capacidad para poca generación efectiva.\nNecesitás BESS para gestionar intermitencia.")
    else:
        st.success(f"Solar+Eólica al {pct_sol_eol}%: {gw_sol_eol:.0f} GW instalados.\nIntermitencia manejable con BESS actual.")

st.markdown("---")

# ── GRÁFICOS FILA 1 ──────────────────────────────────────────────────────────
st.subheader("📊 Matriz y capacidad instalada")
r1c1, r1c2 = st.columns(2)

with r1c1:
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    vals = [v for v in mix.values() if v > 0]
    labs = [f"{k}\n{v}%" for k, v in mix.items() if v > 0]
    cols = [COLORES[k] for k, v in mix.items() if v > 0]
    ax1.pie(vals, labels=labs, colors=cols, autopct='%1.0f%%',
            startangle=90, textprops={'fontsize': 8})
    ax1.set_title("Participación en generación 2035", fontsize=11)
    st.pyplot(fig1)
    plt.close(fig1)

with r1c2:
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    fuentes = list(mix.keys())
    x = np.arange(len(fuentes))
    w = 0.35
    ax2.bar(x - w/2, [CAP_2024[f] for f in fuentes], w,
            label='GW instalados 2024', color=[COLORES[f] for f in fuentes], alpha=0.4)
    ax2.bar(x + w/2, [r['gw'][f] for f in fuentes], w,
            label='GW necesarios 2035', color=[COLORES[f] for f in fuentes], alpha=1)
    ax2.set_xticks(x)
    ax2.set_xticklabels(fuentes, rotation=30, ha='right', fontsize=8)
    ax2.set_ylabel('GW')
    ax2.legend(fontsize=8)
    ax2.set_title(f"Capacidad instalada real necesaria: {sum(r['gw'].values()):.0f} GW totales", fontsize=10)
    st.pyplot(fig2)
    plt.close(fig2)

st.markdown("---")

# ── GRÁFICOS FILA 2 ──────────────────────────────────────────────────────────
st.subheader("💰 Presupuesto e impacto laboral")
r2c1, r2c2 = st.columns(2)

with r2c1:
    fig3, ax3 = plt.subplots(figsize=(6, 5))
    items = {k: v for k, v in r['presupuesto'].items() if v > 0}
    comp = list(items.keys())
    vals_p = list(items.values())
    colors_p = ['#c0392b','#2980b9','#8e44ad','#27ae60','#f39c12','#7f8c8d',
                '#e67e22','#3498db','#95a5a6','#e74c3c','#1abc9c']
    bars3 = ax3.barh(comp, vals_p, color=colors_p[:len(comp)])
    ax3.set_xlabel('USD Millones')
    ax3.set_title(f'Total: USD {r["inversion"]:,.0f}M ({r["pbi"]:.1f}% PBI)', fontsize=10)
    for bar, val in zip(bars3, vals_p):
        ax3.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                f'${val:,.0f}M', va='center', fontsize=7)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)

with r2c2:
    fig4, ax4 = plt.subplots(figsize=(6, 5))
    cats = ['Desplazados\ntotal', 'A reconvertir', 'A retiro', 'Empleos\nnuevos O&M']
    vals_l = [r['desplazados'], r['a_reconvertir'], r['a_retiro'], int(r['empleos'])]
    cols_l = ['#e74c3c', '#e67e22', '#95a5a6', '#27ae60']
    bars4 = ax4.bar(cats, vals_l, color=cols_l)
    for bar, val in zip(bars4, vals_l):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                f'{val:,}', ha='center', fontsize=9, fontweight='bold')
    ax4.axhline(y=r['desplazados'], color='red', linestyle='--', alpha=0.5, label='Desplazados total')
    ax4.set_ylabel('Personas')
    ax4.set_title(f'Cobertura laboral: {r["cobertura"]:.2f}x desplazados\nCosto transición: USD {r["costo_laboral"]:,.0f}M', fontsize=10)
    ax4.legend(fontsize=8)
    st.pyplot(fig4)
    plt.close(fig4)

st.markdown("---")

# ── ROI ──────────────────────────────────────────────────────────────────────
st.subheader("📈 Retorno económico")
rc1, rc2, rc3, rc4 = st.columns(4)
rc1.metric("⚙️ Ahorro operativo anual", f"USD {r['ahorro_op']:,.0f}M", "vs costo matriz 2024")
rc2.metric("🛢️ Ahorro GNL anual", "USD 4,200M", "desde 2033")
rc3.metric("📅 Payback simple", f"{r['payback']:.1f} años", "recupero total")
rc4.metric("💵 Valor neto 20 años", f"USD {r['ahorro_total']*20 - r['inversion']:,.0f}M", f"ROI {r['roi_20']:.0f}%")

fig5, ax5 = plt.subplots(figsize=(12, 4))
años = list(range(0, 21))

# Escenario optimista (100% ahorros desde año 1)
flujo_opt = [-r['inversion'] + r['ahorro_total'] * a for a in años]
# Escenario pesimista (ahorros al 60%, inversión privada no llega completa)
flujo_pes = [-r['inversion'] * 1.3 + r['ahorro_total'] * 0.6 * a for a in años]

ax5.fill_between(años, flujo_pes, flujo_opt, alpha=0.15, color='#27ae60', label='Rango optimista/pesimista')
ax5.plot(años, flujo_opt, color='#27ae60', linewidth=2, label='Escenario optimista')
ax5.plot(años, flujo_pes, color='#e74c3c', linewidth=2, linestyle='--', label='Escenario pesimista')
ax5.axhline(y=0, color='black', linewidth=1)
payback_opt = r['inversion'] / r['ahorro_total']
ax5.axvline(x=payback_opt, color='#27ae60', linewidth=1.5, linestyle=':', alpha=0.8)
ax5.text(payback_opt + 0.2, min(flujo_pes)*0.3, f'Payback opt.\n{payback_opt:.1f} años', fontsize=8, color='#27ae60')
ax5.set_xlabel('Años desde inicio del plan')
ax5.set_ylabel('USD Millones (acumulado)')
ax5.set_title('Flujo de caja acumulado — optimista vs pesimista', fontsize=11)
ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}M'))
ax5.legend(fontsize=8)
plt.tight_layout()
st.pyplot(fig5)
plt.close(fig5)

st.markdown(f"""
**Supuestos del ROI:**  
Costo operativo 2024: USD {r['cop_2024']:,.0f}M/año → 2035: USD {r['cop_2035']:,.0f}M/año  
Escenario pesimista: inversión +30% por demoras/sobrecostos, ahorros al 60% por implementación parcial  
No incluye tasa de descuento ni externalidades ambientales (precio carbono, salud pública)
""")

st.markdown("---")

# ── COMPARADOR DE ESCENARIOS ─────────────────────────────────────────────────
st.subheader("🔄 Comparador de escenarios")
st.markdown("Todos los escenarios predefinidos calculados con el mismo modelo:")

filas = []
for nombre, m in ESCENARIOS.items():
    rc = calcular(tuple(m.items()))
    filas.append({
        "Escenario": nombre,
        "Inversión (USD M)": f"{rc['inversion']:,.0f}",
        "% PBI": f"{rc['pbi']:.1f}%",
        "Red. CO₂": f"{rc['red_emis']:.1f}%",
        "Desplazados": f"{rc['desplazados']:,}",
        "Payback": f"{rc['payback']:.1f} años",
        "Cobert. laboral": f"{rc['cobertura']:.2f}x",
    })

import pandas as pd
df = pd.DataFrame(filas)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")

# ── ANÁLISIS FINAL ───────────────────────────────────────────────────────────
st.subheader("📋 Viabilidad de tu escenario")
ca, cb, cc = st.columns(3)

with ca:
    st.markdown("**🌿 Ambiental**")
    if r['red_emis'] >= 45:
        st.success(f"Reducción de {r['red_emis']:.1f}% ✅\nMeta del plan: 45%")
    elif r['red_emis'] >= 20:
        st.warning(f"Reducción de {r['red_emis']:.1f}% ⚠️\nMeta: 45% — no alcanza")
    else:
        st.error(f"Reducción de {r['red_emis']:.1f}% ❌\nMuy por debajo de la meta")

with cb:
    st.markdown("**💰 Económico**")
    if r['pbi'] <= 7:
        st.success(f"{r['pbi']:.1f}% del PBI ✅\nViable en 10 años")
    elif r['pbi'] <= 12:
        st.warning(f"{r['pbi']:.1f}% del PBI ⚠️\nExigente — requiere estabilidad macro")
    else:
        st.error(f"{r['pbi']:.1f}% del PBI ❌\nMuy alto para el contexto argentino")

with cc:
    st.markdown("**👷 Social**")
    if r['cobertura'] >= 1.5:
        st.success(f"Cobertura {r['cobertura']:.2f}x ✅\nEmpleos nuevos superan desplazados")
    elif r['cobertura'] >= 0.8:
        st.warning(f"Cobertura {r['cobertura']:.2f}x ⚠️\nFondo de transición laboral necesario")
    else:
        st.error(f"Cobertura {r['cobertura']:.2f}x ❌\nDesplazados sin cobertura: {int(r['desplazados'] - r['empleos']):,} personas\nFondo laboral imprescindible")

st.markdown("---")
st.caption("Modelo basado en: CAMMESA, Secretaría de Energía, CNEA, IRENA, BID. Factores de planta reales por tecnología. Análisis: Dante Rizzi — UNMDP 2025.")
