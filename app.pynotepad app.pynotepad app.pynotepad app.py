import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador de Generador Radioquímico", layout="wide")

st.title("🧪 Simulador de Ecuaciones de Bateman - Generadores Radioquímicos")
st.markdown("Herramienta interactiva para el cálculo teórico y experimental de eluciones (UNSAM 2026).")

# --- BARRA LATERAL: CONFIGURACIÓN Y SELECCIÓN ---
st.sidebar.header("⚙️ Configuración del Sistema")

# Selector con múltiples pares radionucleídicos
sistema = st.sidebar.selectbox(
    "Seleccionar Par Radionucleídico (Madre / Hija)",
    [
        "Mo-99 / Tc-99m (Estándar)",
        "Sn-113 / In-113m",
        "Ge-68 / Ga-68 (PET)",
        "Sr-82 / Rb-82 (PET Cardíaco)",
        "Personalizado (Ingresar vidas medias)"
    ]
)

# Valores por defecto según el sistema seleccionado (vidas medias en horas)
if sistema == "Mo-99 / Tc-99m (Estándar)":
    default_th_madre = 66.0       # 66 horas
    default_th_hija = 6.02       # 6.02 horas
elif sistema == "Sn-113 / In-113m":
    default_th_madre = 2762.4    # ~115.1 días
    default_th_hija = 1.658      # ~99.5 minutos
elif sistema == "Ge-68 / Ga-68 (PET)":
    default_th_madre = 6504.0    # ~271 días
    default_th_hija = 1.133      # ~68 minutos
elif sistema == "Sr-82 / Rb-82 (PET Cardíaco)":
    default_th_madre = 607.2     # ~25.3 días
    default_th_hija = 0.0208     # ~1.25 minutos
else:
    default_th_madre = 66.0
    default_th_hija = 6.02

# Campos editables para vidas medias
st.sidebar.subheader("Vidas Medias ($T_{1/2}$)")
t_half_madre = st.sidebar.number_input("T1/2 Madre (horas)", value=float(default_th_madre), format="%.4f")
t_half_hija = st.sidebar.number_input("T1/2 Hija (horas)", value=float(default_th_hija), format="%.4f")

# Cálculo de constantes de desintegración lambda = ln(2) / T_1/2
lam_madre = np.log(2) / t_half_madre
lam_hija = np.log(2) / t_half_hija

st.sidebar.markdown(f"**$\lambda$ Madre:** `{lam_madre:.6f} h⁻¹`")
st.sidebar.markdown(f"**$\lambda$ Hija:** `{lam_hija:.6f} h⁻¹`")

st.sidebar.subheader("Parámetros Iniciales")
A0_madre = st.sidebar.number_input("Actividad inicial Madre ($A_{10}$ en mCi o MBq)", value=100.0)
tiempo_max = st.sidebar.slider("Tiempo total de simulación (horas)", min_value=12, max_value=336, value=72, step=12)

# --- ECUACIONES DE BATEMAN ---
t = np.linspace(0, tiempo_max, 500)

# Actividad de la Madre
A_madre = A0_madre * np.exp(-lam_madre * t)

# Actividad de la Hija
if abs(lam_hija - lam_madre) > 1e-6:
    A_hija = A0_madre * (lam_hija / (lam_hija - lam_madre)) * (np.exp(-lam_madre * t) - np.exp(-lam_hija * t))
else:
    A_hija = A0_madre * lam_madre * t * np.exp(-lam_madre * t)

# --- VISUALIZACIÓN EN PANTALLA ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Curvas de Desintegración y Crecimiento (Ecuaciones de Bateman)")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(t, A_madre, label="Madre (Padre)", color="crimson", linewidth=2.5)
    ax.plot(t, A_hija, label="Hija (Generada)", color="dodgerblue", linewidth=2.5)
    
    ax.set_xlabel("Tiempo (horas)", fontsize=11)
    ax.set_ylabel("Actividad Relativa", fontsize=11)
    ax.set_title("Evolución temporal del sistema generador", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(fontsize=11)
    st.pyplot(fig)

with col2:
    st.subheader("⏱️ Datos Clave de Crecimiento")
    if lam_hija > lam_madre:
        t_max = np.log(lam_hija / lam_madre) / (lam_hija - lam_madre)
        st.success(f"**Máximo de actividad hija:**\nA las **{t_max:.2f} horas**")
    else:
        st.warning("El sistema no presenta un régimen de crecimiento transitorio clásico (equilibrio secular/transitorio condicionado).")
    
    st.info("💡 **Tip:** Ahora podés elegir entre los generadores de Tecnecio, Indio, Galio o Rubidio desde el menú desplegable de arriba.")

# --- SECCIÓN DE DATOS EXPERIMENTALES ---
st.markdown("---")
st.subheader("📋 Registro de Datos Experimentales vs Teóricos")
st.markdown("Ingresá tus valores medidos en el laboratorio para compararlos con la curva teórica:")

df_default = pd.DataFrame({
    "Tiempo de Elución (h)": [0.0, 6.0, 12.0, 24.0, 48.0],
    "Actividad Experimental Hija (mCi)": [0.0, 35.5, 55.0, 68.2, 70.1]
})

df_user = st.data_editor(df_default, num_rows="dynamic", use_container_width=True)
