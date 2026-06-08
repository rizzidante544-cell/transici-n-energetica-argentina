import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Simulador Transición Energética Argentina", layout="wide")

st.title("⚡ Simulador de Transición Energética Argentina 2035")
st.markdown("Ajustá los sliders para ver cómo cambia la matriz y el impacto en presupuesto, empleo y emisiones.")

# ── CONSTANTES BASE ──────────────────────────────────────────────────────────
PBI_ARG = 620_000       # USD millones
DEMANDA_2024 = 145_000  # GWh
TRABAJADORES_ACTUALES = 52_000
COSTO_RECONVERSION = 90_000
COSTO_RETIRO = 40_000
PORC_RETIRO = 0.35

# Capacidad instalada 2024 por fuente (GW) — base para calcular NUEVA capacidad
CAP_2024 = {
    "Térmica fósil": 25.8,
    "Hidro":         10.9,
    "Nuclear":        1.755,
    "Eólica":         4.2,
    "Solar":          1.1,
    "WtE":            0.0,
}
CAP_TOTAL_2035 = 45.0  # GW proyectados

# Costo de inversión SOLO para capacidad NUEVA (USD M / GW)
COSTO_NUEVO_POR_GW = {
    "Eólica":        1_200,
    "Solar":           900,
    "Nuclear":       8_500,
    "WtE":           4_600,
    "Hidro":         2_500,
    "Térmica fósil":   400,
}

# Costos fijos del plan (transmisión, BESS, eficiencia)
COSTOS_FIJOS = {
    "Transmisión AT": 5_200,
    "BESS":           2_200,
    "Eficiencia":       800,
}

EMISIONES_POR_GWH = {
    "Eólica": 0, "Solar": 0, "Nuclear": 0,
    "WtE": 50, "Hidro": 4, "Térmica fósil": 490,
}

# Empleos permanentes O&M por GW instalado
EMPLEOS_OM_POR_GW = {
    "Eólica": 400, "Solar": 300, "Nuclear": 800,
    "WtE": 700, "Hidro": 200, "Térmica fósil": 2_000,
}

COLORES = {
    "Térmica fósil": "#c0392b", "Hidro": "#2980b9",
    "Nuclear": "#8e44ad", "Eólica": "#27ae60",
    "Solar": "#f39c12", "WtE": "#7f8c8d",
}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.header("🎛️ Ajustá la matriz 2035")
st.sidebar.markdown("Los porcentajes deben sumar 100%")

termica  = st.sidebar.slider("🔴 Térmica fósil (%)", 0, 80, 10, step=1)
hidro    = st.sidebar.slider("🔵 Hidro (%)",          0, 40, 13, step=1)
nuclear  = st.sidebar.slider("🟣 Nuclear (%)",         0, 60, 20, step=1)
eolica   = st.sidebar.slider("🟢 Eólica (%)",          0, 60, 32, step=1)
solar    = st.sidebar.slider("🟡 Solar (%)",            0, 40, 18, step=1)
wte      = st.sidebar.slider("⚫ WtE (%)",              0, 20,  7, step=1)

total = termica + hidro + nuclear + eolica + solar + wte
if total != 100:
    st.sidebar.error(f"⚠️ Total: {total}% — debe ser exactamente 100%")
else:
    st.sidebar.success(f"✅ Total: {total}%")

# ── CÁLCULOS ──────────────────────────────────────────────────────────────────
mix = {
    "Térmica fósil": termica, "Hidro": hidro, "Nuclear": nuclear,
    "Eólica": eolica, "Solar": solar, "WtE": wte,
}

demanda_2035 = DEMANDA_2024 * (1.03 ** 10)
gen_por_fuente = {k: v/100 * demanda_2035 for k, v in mix.items()}

# Capacidad 2035 por fuente
cap_2035 = {k: v/100 * CAP_TOTAL_2035 for k, v in mix.items()}

# Capacidad NUEVA = 2035 - 2024 (solo positivos, no contamos retiros como inversión)
cap_nueva = {k: max(0, cap_2035[k] - CAP_2024[k]) for k in mix}

# Emisiones
emisiones_total = sum(gen_por_fuente[k] * EMISIONES_POR_GWH[k] / 1_000_000 for k in mix)
emisiones_2024 = 52.0

# Presupuesto: solo capacidad nueva + costos fijos + transición laboral
inversion_generacion = {k: cap_nueva[k] * COSTO_NUEVO_POR_GW[k] for k in mix}

reduccion_termica = max(0, (61 - termica) / 61)
desplazados = int(TRABAJADORES_ACTUALES * reduccion_termica)
a_reconvertir = int(desplazados * (1 - PORC_RETIRO))
a_retiro = desplazados - a_reconvertir
costo_laboral = (a_reconvertir * COSTO_RECONVERSION + a_retiro * COSTO_RETIRO) / 1_000_000

presupuesto = {
    **inversion_generacion,
    **COSTOS_FIJOS,
    "Transición laboral": costo_laboral,
}
total_presupuesto = sum(presupuesto.values())
porc_pbi = total_presupuesto / PBI_ARG * 100

# Empleos nuevos O&M permanentes (excluye térmica fósil)
empleos_nuevos = sum(cap_2035[k] * EMPLEOS_OM_POR_GW[k] for k in mix if k != "Térmica fósil")

# ── MÉTRICAS ──────────────────────────────────────────────────────────────────
if total != 100:
    st.warning("Ajustá los sliders para que sumen 100% y ver los resultados.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Inversión total", f"USD {total_presupuesto:,.0f}M", f"{porc_pbi:.1f}% del PBI")
col2.metric("🌿 Emisiones CO₂ 2035", f"{emisiones_total:.1f} Mt", f"{emisiones_total - emisiones_2024:.1f} Mt vs 2024")
col3.metric("👷 Trabajadores desplazados", f"{desplazados:,}", f"{a_reconvertir:,} reconversión / {a_retiro:,} retiro")
col4.metric("🔋 Renovables + Nuclear", f"{eolica + solar + hidro + nuclear + wte}%", "sin térmica fósil")

st.markdown("---")

# ── GRÁFICOS ──────────────────────────────────────────────────────────────────
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("🥧 Matriz eléctrica 2035")
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    valores = [v for v in mix.values() if v > 0]
    etiquetas = [f"{k}\n{v}%" for k, v in mix.items() if v > 0]
    colores = [COLORES[k] for k, v in mix.items() if v > 0]
    ax1.pie(valores, labels=etiquetas, colors=colores, autopct='%1.0f%%',
            startangle=90, textprops={'fontsize': 8})
    ax1.set_title("Participación por fuente", fontsize=11)
    st.pyplot(fig1)
    plt.close()

with row1_col2:
    st.subheader("📊 Simulación vs Plan original")
    original = {"Térmica fósil": 10, "Hidro": 13, "Nuclear": 20, "Eólica": 32, "Solar": 18, "WtE": 7}
    fuentes = list(mix.keys())
    x = np.arange(len(fuentes))
    width = 0.35
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    ax2.bar(x - width/2, [original[f] for f in fuentes], width,
            label='Plan original', color=[COLORES[f] for f in fuentes], alpha=0.5)
    ax2.bar(x + width/2, [mix[f] for f in fuentes], width,
            label='Tu simulación', color=[COLORES[f] for f in fuentes], alpha=1)
    ax2.set_xticks(x)
    ax2.set_xticklabels(fuentes, rotation=30, ha='right', fontsize=8)
    ax2.set_ylabel('Participación (%)')
    ax2.legend()
    ax2.set_title("Comparación con plan original", fontsize=11)
    st.pyplot(fig2)
    plt.close()

st.markdown("---")
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("💰 Desglose de inversión")
    fig3, ax3 = plt.subplots(figsize=(6, 5))
    # Solo mostrar items con valor > 0
    items = {k: v for k, v in presupuesto.items() if v > 0}
    componentes = list(items.keys())
    valores_p = list(items.values())
    colores_p = ['#27ae60','#8e44ad','#7f8c8d','#2980b9','#f39c12','#c0392b',
                 '#e67e22','#3498db','#95a5a6','#e74c3c']
    bars = ax3.barh(componentes, valores_p, color=colores_p[:len(componentes)])
    ax3.set_xlabel('USD Millones')
    ax3.set_title(f'Total: USD {total_presupuesto:,.0f}M ({porc_pbi:.1f}% PBI)', fontsize=10)
    for bar, val in zip(bars, valores_p):
        ax3.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                f'${val:,.0f}M', va='center', fontsize=7)
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

with row2_col2:
    st.subheader("👷 Impacto laboral")
    fig4, ax4 = plt.subplots(figsize=(6, 5))
    categorias = ['Desplazados\ntotal', 'A reconvertir', 'A retiro', 'Empleos\nnuevos O&M']
    valores_l = [desplazados, a_reconvertir, a_retiro, int(empleos_nuevos)]
    colores_l = ['#e74c3c', '#e67e22', '#95a5a6', '#27ae60']
    bars4 = ax4.bar(categorias, valores_l, color=colores_l)
    for bar, val in zip(bars4, valores_l):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                f'{val:,}', ha='center', fontsize=9, fontweight='bold')
    ax4.set_ylabel('Personas')
    ax4.set_title(f'Costo transición laboral: USD {costo_laboral:,.0f}M', fontsize=10)
    st.pyplot(fig4)
    plt.close()

st.markdown("---")

# ── ANÁLISIS ──────────────────────────────────────────────────────────────────
st.subheader("📋 Análisis de tu escenario")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("**🌿 Ambiental**")
    reduccion = ((emisiones_2024 - emisiones_total) / emisiones_2024) * 100
    if reduccion >= 45:
        st.success(f"Reducción de {reduccion:.1f}% ✅\nMeta del plan: 45%")
    elif reduccion >= 20:
        st.warning(f"Reducción de {reduccion:.1f}% ⚠️\nMeta del plan: 45%")
    else:
        st.error(f"Reducción de solo {reduccion:.1f}% ❌\nMeta del plan: 45%")

with col_b:
    st.markdown("**💰 Económico**")
    if porc_pbi <= 7:
        st.success(f"{porc_pbi:.1f}% del PBI ✅\nViable en 10 años")
    elif porc_pbi <= 10:
        st.warning(f"{porc_pbi:.1f}% del PBI ⚠️\nExigente pero posible")
    else:
        st.error(f"{porc_pbi:.1f}% del PBI ❌\nMuy alta para el contexto")

with col_c:
    st.markdown("**👷 Social**")
    cobertura = empleos_nuevos / max(desplazados, 1)
    if cobertura >= 1.5:
        st.success(f"{int(empleos_nuevos):,} empleos nuevos ✅\nCubre {cobertura:.1f}x desplazados")
    elif cobertura >= 1:
        st.warning(f"{int(empleos_nuevos):,} empleos nuevos ⚠️\nCubre {cobertura:.1f}x desplazados")
    else:
        st.error(f"{int(empleos_nuevos):,} empleos nuevos ❌\nNo cubre desplazados ({cobertura:.1f}x)")

st.markdown("---")
st.caption("Datos base: CAMMESA, Secretaría de Energía, CNEA, IRENA. Análisis: Dante Rizzi — Proyecto personal UNMDP 2025.")
