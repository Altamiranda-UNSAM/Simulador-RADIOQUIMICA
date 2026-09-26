import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulador Radioquímica 99Mo/99mTc", layout="wide")

st.title("🧪 Simulador de Eluciones - Generador $^{99}\text{Mo} / ^{99m}\text{Tc}$")
st.markdown("Herramienta interactiva basada en el modelo de Bateman y gestión de eluciones sucesivas.")

# --- CONSTANTES ---
T12Mo = 66.0
T12Tc = 6.0067
lambda_mo = np.log(2) / T12Mo
lambda_tc = np.log(2) / T12Tc

# --- PANEL LATERAL ---
st.sidebar.header("1. Parámetros del Generador")

unidad = st.sidebar.selectbox("Unidad de Actividad:", ["mCi", "MBq", "GBq"], index=0)
actividad_ingresada = st.sidebar.number_input("Actividad de referencia:", value=500.0, min_value=0.0)

def convertir_a_mci(val, un):
    if un == "mCi":
        return val
    elif un == "MBq":
        return val / 37.0
    elif un == "GBq":
        return val * 1000.0 / 37.0
    return val

actividad_inicial = convertir_a_mci(actividad_ingresada, unidad)

fecha_ini = st.sidebar.date_input("Fecha inicial (Calibración)", value=datetime(2016, 4, 25).date())
hora_ini_str = st.sidebar.text_input("Hora inicial (HH:MM)", value="08:00")

try:
    h_i, m_i = map(int, hora_ini_str.split(":"))
    dt_inicial = datetime.combine(fecha_ini, datetime.min.time()) + timedelta(hours=h_i, minutes=m_i)
except:
    st.sidebar.error("Formato de hora inicial inválido. Use HH:MM")
    dt_inicial = datetime.combine(fecha_ini, datetime.min.time()) + timedelta(hours=8)

duracion_grafico = st.sidebar.number_input("Duración gráfico (horas):", value=144.0, min_value=1.0)
paso_grafico = st.sidebar.number_input("Paso gráfico (horas):", value=0.25, min_value=0.01)

st.sidebar.header("2. Registro de Eluciones")
datos_por_defecto = """25/04/2016, 08:00, 500
26/04/2016, 08:00, 300
27/04/2016, 08:00, 200"""

texto_eluciones = st.sidebar.text_area("Formato: Fecha (DD/MM/AAAA), Hora (HH:MM), Actividad Medida", value=datos_por_defecto, height=150)

# --- PROCESAMIENTO DE ELUCIONES ---
lista_eluciones = []
for linea in texto_eluciones.strip().split("\n"):
    if not linea.strip():
        continue
    try:
        partes = [p.strip() for p in linea.split(",")]
        f_str, h_str, act_medida = partes[0], partes[1], float(partes[2])
        f_date = datetime.strptime(f_str, "%d/%m/%Y").date()
        hh, mm = map(int, h_str.split(":"))
        dt_elusion = datetime.combine(f_date, datetime.min.time()) + timedelta(hours=hh, minutes=mm)
        
        delta_t_inicio = (dt_elusion - dt_inicial).total_seconds() / 3600.0
        if delta_t_inicio < 0:
            continue
            
        lista_eluciones.append({
            "datetime": dt_elusion,
            "fecha_str": f_str,
            "hora_str": h_str,
            "delta_inicio": delta_t_inicio,
            "act_medida": act_medida
        })
    except:
        continue

lista_eluciones = sorted(lista_eluciones, key=lambda x: x["datetime"])

# --- CÁLCULO DE TABLA ---
registros_tabla = []
for i, el in enumerate(lista_eluciones):
    t_abs = el["delta_inicio"]
    mo_el = actividad_inicial * np.exp(-lambda_mo * t_abs)
    
    if i == 0:
        t_acumulado = t_abs
        tc_el = (lambda_tc / (lambda_tc - lambda_mo)) * actividad_inicial * (np.exp(-lambda_mo * t_acumulado) - np.exp(-lambda_tc * t_acumulado))
    else:
        t_desde_anterior = (el["datetime"] - lista_eluciones[i-1]["datetime"]).total_seconds() / 3600.0
        mo_anterior = actividad_inicial * np.exp(-lambda_mo * lista_eluciones[i-1]["delta_inicio"])
        tc_el = (lambda_tc / (lambda_tc - lambda_mo)) * mo_anterior * (np.exp(-lambda_mo * t_desde_anterior) - np.exp(-lambda_tc * t_desde_anterior))

    dif_porcentual = abs(el["act_medida"] - tc_el) / el["act_medida"] * 100 if el["act_medida"] > 0 else 0.0
    
    registros_tabla.append({
        "Elusión N°": i + 1,
        "Fecha/Hora": f"{el['fecha_str']} {el['hora_str']}",
        "Δt Total (h)": round(t_abs, 2),
        "Mo-99 Teórico (mCi)": round(mo_el, 2),
        "Tc-99m Teórico (mCi)": round(tc_el, 2),
        "Actividad Medida": el["act_medida"],
        "Dif. (%)": round(dif_porcentual, 2)
    })

df_res = pd.DataFrame(registros_tabla)

# --- VISUALIZACIÓN ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 Tabla de Eluciones")
    if not df_res.empty:
        st.dataframe(df_res, use_container_width=True)
    else:
        st.warning("No hay eluciones válidas cargadas.")

with col2:
    st.subheader("📊 Proyección Gráfica")
    fig, ax = plt.subplots(figsize=(9, 5))
    
    t_curva = np.arange(0, duracion_grafico + paso_grafico, paso_grafico)
    fechas_curva = [dt_inicial + timedelta(hours=float(t)) for t in t_curva]
    
    mo_curva = actividad_inicial * np.exp(-lambda_mo * t_curva)
    
    # Lógica de curva de Tc con reseteo en cada elución (dientes de sierra)
    tc_curva = np.zeros_like(t_curva)
    fechas_el_dt = [el["datetime"] for el in lista_eluciones]
    
    for k, t_val in enumerate(t_curva):
        actual_dt = dt_inicial + timedelta(hours=float(t_val))
        anteriores = [f for f in fechas_el_dt if f <= actual_dt]
        
        if not anteriores:
            tc_curva[k] = (lambda_tc / (lambda_tc - lambda_mo)) * actividad_inicial * (np.exp(-lambda_mo * t_val) - np.exp(-lambda_tc * t_val))
        else:
            ultima_fecha = anteriores[-1]
            t_desde_ultima = (actual_dt - ultima_fecha).total_seconds() / 3600.0
            t_hasta_ultima = (ultima_fecha - dt_inicial).total_seconds() / 3600.0
            mo_ultima = actividad_inicial * np.exp(-lambda_mo * t_hasta_ultima)
            tc_curva[k] = (lambda_tc / (lambda_tc - lambda_mo)) * mo_ultima * (np.exp(-lambda_mo * t_desde_ultima) - np.exp(-lambda_tc * t_desde_ultima))

    ax.plot(fechas_curva, mo_curva, label="99Mo (Padre)", color="blue", linewidth=2, linestyle="--")
    ax.plot(fechas_curva, tc_curva, label="99mTc (Hijo - Acumulación)", color="green", linewidth=2)
    
    for el in lista_eluciones:
        ax.axvline(el["datetime"], color="red", linestyle=":", alpha=0.7)
        
    ax.set_xlabel("Fecha y hora")
    ax.set_ylabel(f"Actividad ({unidad})")
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend(loc="upper right")
    plt.xticks(rotation=25)
    st.pyplot(fig)
    
