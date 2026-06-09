import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Simulador Transición Energética Argentina", layout="wide")

st.title("⚡ Simulador de Transición Energética Argentina 2035")
st.markdown("Ajustá los sliders para ver cómo cambia la matriz y el impacto en presupuesto, empleo, emisiones y retorno económico.")

# ── CONSTANTES ───────────────────────────────────────────────────────────────
PBI_ARG        = 620_000
DEMANDA_2024   = 145_000   # GWh
HORAS_AÑO      = 8_760
TRABAJADORES_TERMICOS = 52_000
COSTO_RECONVERSION = 90_000
COSTO_RETIRO       = 40_000
PORC_RETIRO        = 0.35

# Factor de planta real por tecnología
FACTOR_PLANTA = {
    "Térmica fósil": 0.45,
    "Hidro":         0.40,
    "Nuclear":       0.90,
    "Eólica":        0.30,
    "Solar":         0.22,
    "WtE":           0.75,
}

# Capacidad instalada 2024 (GW)
CAP_2024 = {
    "Térmica fósil": 25.8,
    "Hidro":         10.9,
    "Nuclear":        1.755,
    "Eólica":         4.2,
    "Solar":          1.1,
    "WtE":            0.0,
}

# Costo de inversión por GW nuevo (USD M/GW)
CAPEX_POR_GW = {
    "Eólica":        1_200,
    "Solar":           900,
    "Nuclear":       8_500,
    "WtE":           4_600,
    "Hidro":         2_500,
    "Térmica fósil":   400,
}

# Costo operativo por GWh (USD/GWh) — combustible + O&M
OPEX_POR_GWH = {
    "Térmica fósil": 80,
    "Hidro":          5,
    "Nuclear":        12,
    "Eólica":          8,
    "Solar":           5,
    "WtE":            20,
}

# Empleos O&M permanentes por GW instalado
EMPLEOS_POR_GW = {
    "Eólica":        400,
    "Solar":         300,
    "Nuclear":       800,
    "WtE":           700,
    "Hidro":         200,
    "Térmica fósil": 2_000,
}

# Emisiones CO2 por GWh (tCO2/GWh)
EMISIONES_POR_GWH = {
    "Térmica fósil": 490,
    "Hidro":           4,
    "Nuclear":         0,
    "Eólica":          0,
    "Solar":           0,
    "WtE":            50,
}

COSTOS_FIJOS = {"Transmisión AT": 5_200, "BESS": 2_200, "Eficiencia": 800}
AHORRO_GNL_ANUAL = 4_200  # USD M/año desde 2033

COLORES = {
    "Térmica fósil": "#c0392b", "Hidro": "#2980b9",
    "Nuclear": "#8e44ad", "Eólica": "#27ae60",
    "Solar": "#f39c12", "WtE": "#7f8c8d",
}

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
st.sidebar.header("🎛️ Ajustá la matriz 2035")
st.sidebar.markdown("Los % representan participación en la **generación anual**. Deben sumar 100%.")

termica = st.sidebar.slider("🔴 Térmica fósil (%)", 0, 80, 10, step=1)
hidro   = st.sidebar.slider("🔵 Hidro (%)",          0, 40, 13, step=1)
nuclear = st.sidebar.slider("🟣 Nuclear (%)",         0, 40, 20, step=1)
eolica  = st.sidebar.slider("🟢 Eólica (%)",          0, 70, 32, step=1)
solar   = st.sidebar.slider("🟡 Solar (%)",            0, 50, 18, step=1)
wte     = st.sidebar.slider("⚫ WtE (%)",              0, 20,  7, step=1)

total = termica + hidro + nuclear + eolica + solar + wte
if total != 100:
    st.sidebar.error(f"⚠️ Total: {total}% — debe ser 100%")
else:
    st.sidebar.success(f"✅ Total: {total}%")

if total != 100:
    st.warning("Ajustá los sliders para que sumen 100%.")
    st.stop()

# ── CÁLCULOS ─────────────────────────────────────────────────────────────────
mix = {
    "Térmica fósil": termica, "Hidro": hidro, "Nuclear": nuclear,
    "Eólica": eolica, "Solar": solar, "WtE": wte,
}

demanda_2035 = DEMANDA_2024 * (1.03 ** 10)

# Generación por fuente (GWh)
gen_2035 = {k: v/100 * demanda_2035 for k, v in mix.items()}

# GW instalados necesarios según factor de planta real
gw_2035 = {k: gen_2035[k] / (HORAS_AÑO * FACTOR_PLANTA[k]) for k in mix}
gw_total_2035 = sum(gw_2035.values())

# GW nuevos a construir (solo incrementos)
gw_nuevo = {k: max(0, gw_2035[k] - CAP_2024[k]) for k in mix}

# Inversión en generación
inversion_gen = {k: gw_nuevo[k] * CAPEX_POR_GW[k] for k in mix}

# Transición laboral
reduccion_termica = max(0, (61 - termica) / 61)
desplazados   = int(TRABAJADORES_TERMICOS * reduccion_termica)
a_reconvertir = int(desplazados * (1 - PORC_RETIRO))
a_retiro      = desplazados - a_reconvertir
costo_laboral = (a_reconvertir * COSTO_RECONVERSION + a_retiro * COSTO_RETIRO) / 1_000_000

# Presupuesto total
presupuesto = {**inversion_gen, **COSTOS_FIJOS, "Transición laboral": costo_laboral}
total_presupuesto = sum(presupuesto.values())
porc_pbi = total_presupuesto / PBI_ARG * 100

# Emisiones
emisiones_2024 = 52.0
emisiones_2035 = sum(gen_2035[k] * EMISIONES_POR_GWH[k] / 1_000_000 for k in mix)
reduccion_emisiones = (emisiones_2024 - emisiones_2035) / emisiones_2024 * 100

# Empleos
empleos_nuevos = sum(gw_2035[k] * EMPLEOS_POR_GW[k] for k in mix if k != "Térmica fósil")
cobertura = empleos_nuevos / max(desplazados, 1)

# ROI y ahorros operativos
mix_2024_base = {"Térmica fósil": 0.61, "Hidro": 0.16, "Nuclear": 0.08,
                 "Eólica": 0.10, "Solar": 0.03, "WtE": 0.02}
costo_op_2024 = sum(mix_2024_base[k] * DEMANDA_2024 * OPEX_POR_GWH[k] for k in mix_2024_base)
costo_op_2035 = sum((mix[k]/100) * demanda_2035 * OPEX_POR_GWH[k] for k in mix)
ahorro_op_anual = (costo_op_2024 - costo_op_2035) / 1_000  # USD M
ahorro_total_anual = ahorro_op_anual + AHORRO_GNL_ANUAL
payback = total_presupuesto / max(ahorro_total_anual, 1)
roi_20 = (ahorro_total_anual * 20 - total_presupuesto) / total_presupuesto * 100
valor_neto_20 = ahorro_total_anual * 20 - total_presupuesto

# ── MÉTRICAS PRINCIPALES ─────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Inversión total", f"USD {total_presupuesto:,.0f}M", f"{porc_pbi:.1f}% del PBI")
col2.metric("🌿 Emisiones CO₂ 2035", f"{emisiones_2035:.1f} Mt", f"{emisiones_2035 - emisiones_2024:.1f} Mt vs 2024")
col3.metric("👷 Trabajadores desplazados", f"{desplazados:,}", f"{a_reconvertir:,} reconversión / {a_retiro:,} retiro")
col4.metric("⚡ Capacidad instalada 2035", f"{gw_total_2035:.0f} GW", f"vs 44 GW en 2024")

st.markdown("---")

# ── GRÁFICOS FILA 1 ──────────────────────────────────────────────────────────
r1c1, r1c2 = st.columns(2)

with r1c1:
    st.subheader("🥧 Matriz eléctrica 2035 (generación)")
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    vals = [v for v in mix.values() if v > 0]
    labs = [f"{k}\n{v}%" for k, v in mix.items() if v > 0]
    cols = [COLORES[k] for k, v in mix.items() if v > 0]
    ax1.pie(vals, labels=labs, colors=cols, autopct='%1.0f%%',
            startangle=90, textprops={'fontsize': 8})
    ax1.set_title("Participación en generación anual", fontsize=11)
    st.pyplot(fig1)
    plt.close()

with r1c2:
    st.subheader("📊 GW instalados necesarios vs 2024")
    fuentes = list(mix.keys())
    x = np.arange(len(fuentes))
    w = 0.35
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    ax2.bar(x - w/2, [CAP_2024[f] for f in fuentes], w,
            label='2024 (actual)', color=[COLORES[f] for f in fuentes], alpha=0.5)
    ax2.bar(x + w/2, [gw_2035[f] for f in fuentes], w,
            label='2035 (necesario)', color=[COLORES[f] for f in fuentes], alpha=1)
    ax2.set_xticks(x)
    ax2.set_xticklabels(fuentes, rotation=30, ha='right', fontsize=8)
    ax2.set_ylabel('GW instalados')
    ax2.legend()
    ax2.set_title("Capacidad instalada por fuente (GW)", fontsize=11)
    st.pyplot(fig2)
    plt.close()

st.markdown("---")

# ── GRÁFICOS FILA 2 ──────────────────────────────────────────────────────────
r2c1, r2c2 = st.columns(2)

with r2c1:
    st.subheader("💰 Desglose de inversión")
    fig3, ax3 = plt.subplots(figsize=(6, 5))
    items = {k: v for k, v in presupuesto.items() if v > 0}
    comp = list(items.keys())
    vals_p = list(items.values())
    colors_p = ['#c0392b','#2980b9','#8e44ad','#27ae60','#f39c12','#7f8c8d',
                '#e67e22','#3498db','#95a5a6','#e74c3c']
    bars3 = ax3.barh(comp, vals_p, color=colors_p[:len(comp)])
    ax3.set_xlabel('USD Millones')
    ax3.set_title(f'Total: USD {total_presupuesto:,.0f}M ({porc_pbi:.1f}% PBI)', fontsize=10)
    for bar, val in zip(bars3, vals_p):
        ax3.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                f'${val:,.0f}M', va='center', fontsize=7)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

with r2c2:
    st.subheader("👷 Impacto laboral")
    fig4, ax4 = plt.subplots(figsize=(6, 5))
    cats = ['Desplazados\ntotal', 'A reconvertir', 'A retiro', 'Empleos\nnuevos O&M']
    vals_l = [desplazados, a_reconvertir, a_retiro, int(empleos_nuevos)]
    cols_l = ['#e74c3c', '#e67e22', '#95a5a6', '#27ae60']
    bars4 = ax4.bar(cats, vals_l, color=cols_l)
    for bar, val in zip(bars4, vals_l):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                f'{val:,}', ha='center', fontsize=9, fontweight='bold')
    ax4.set_ylabel('Personas')
    ax4.set_title(f'Costo transición laboral: USD {costo_laboral:,.0f}M', fontsize=10)
    st.pyplot(fig4)
    plt.close()

st.markdown("---")

# ── ROI Y AHORROS ────────────────────────────────────────────────────────────
st.subheader("📈 Retorno económico de la transición")

rc1, rc2, rc3, rc4 = st.columns(4)
rc1.metric("⚙️ Ahorro operativo anual", f"USD {ahorro_op_anual:,.0f}M", "vs matriz 2024")
rc2.metric("🛢️ Ahorro GNL anual", f"USD {AHORRO_GNL_ANUAL:,}M", "desde 2033")
rc3.metric("📅 Payback simple", f"{payback:.1f} años", "recupero de inversión")
rc4.metric("💵 ROI bruto 20 años", f"{roi_20:.0f}%", f"Valor neto USD {valor_neto_20:,.0f}M")

# Gráfico de flujo de caja acumulado
años = list(range(0, 21))
flujo_acum = [-total_presupuesto + ahorro_total_anual * a for a in años]

fig5, ax5 = plt.subplots(figsize=(10, 4))
colores_flujo = ['#27ae60' if v >= 0 else '#c0392b' for v in flujo_acum]
ax5.bar(años, flujo_acum, color=colores_flujo, alpha=0.8)
ax5.axhline(y=0, color='black', linewidth=1)
ax5.axvline(x=payback, color='orange', linewidth=2, linestyle='--', label=f'Payback: {payback:.1f} años')
ax5.set_xlabel('Años desde inicio del plan')
ax5.set_ylabel('USD Millones (acumulado)')
ax5.set_title('Flujo de caja acumulado — Inversión vs Ahorros operativos + GNL', fontsize=11)
ax5.legend()
ax5.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}M'))
plt.tight_layout()
st.pyplot(fig5)
plt.close()

st.markdown(f"""
**Supuestos del cálculo de ROI:**
- Costo operativo matriz actual (combustible + O&M): USD {costo_op_2024/1_000:,.0f}M/año
- Costo operativo matriz 2035 con tu mix: USD {costo_op_2035/1_000:,.0f}M/año  
- Ahorro en importación de GNL desde 2033: USD {AHORRO_GNL_ANUAL:,}M/año (fuente: documento original)
- No incluye inflación, tasa de descuento ni externalidades ambientales
- Vida útil promedio de los activos: 25-40 años
""")

st.markdown("---")

# ── ANÁLISIS DE ESCENARIO ────────────────────────────────────────────────────
st.subheader("📋 Análisis de tu escenario")
ca, cb, cc = st.columns(3)

with ca:
    st.markdown("**🌿 Ambiental**")
    if reduccion_emisiones >= 45:
        st.success(f"Reducción de {reduccion_emisiones:.1f}% ✅\nMeta del plan: 45%")
    elif reduccion_emisiones >= 20:
        st.warning(f"Reducción de {reduccion_emisiones:.1f}% ⚠️\nMeta: 45%")
    else:
        st.error(f"Reducción de {reduccion_emisiones:.1f}% ❌\nMeta: 45%")

with cb:
    st.markdown("**💰 Económico**")
    if porc_pbi <= 7:
        st.success(f"{porc_pbi:.1f}% del PBI ✅\nViable en 10 años")
    elif porc_pbi <= 10:
        st.warning(f"{porc_pbi:.1f}% del PBI ⚠️\nExigente pero posible")
    else:
        st.error(f"{porc_pbi:.1f}% del PBI ❌\nMuy alta para el contexto")

with cc:
    st.markdown("**👷 Social**")
    if cobertura >= 1.5:
        st.success(f"{int(empleos_nuevos):,} empleos ✅\nCubre {cobertura:.1f}x desplazados")
    elif cobertura >= 1:
        st.warning(f"{int(empleos_nuevos):,} empleos ⚠️\nCubre {cobertura:.1f}x desplazados")
    else:
        st.error(f"{int(empleos_nuevos):,} empleos ❌\nSolo {cobertura:.1f}x desplazados")

st.markdown("---")
st.caption("Datos base: CAMMESA, Secretaría de Energía, CNEA, IRENA, BID. Análisis: Dante Rizzi — Proyecto personal UNMDP 2025.")
