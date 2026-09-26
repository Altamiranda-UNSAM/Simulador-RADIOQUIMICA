import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulador Radioquímica 99Mo/99mTc", layout="wide")

# Título original exacto con superíndices correctos en HTML
st.markdown("# 🧪 Simulador de Eluciones - Generador <sup>99</sup>Mo / <sup>99m</sup>Tc", unsafe_allow_html=True)
st.markdown("Herramienta interactiva basada en el modelo de Bateman, factor de ramificación y gestión de eluciones sucesivas.")

# --- CONSTANTES DE MATLAB ---
T12Mo = 66.0
T12Tc = 6.0067
lambda_mo = np.log(2) / T12Mo
lambda_tc = np.log(2) / T12Tc
br = 0.9625  # Factor de ramificación exacto (Padre -> Hijo)

# --- MOTOR DE CONVERSIÓN DE UNIDADES MATLAB (Base Bq exacta) ---
def convertir_a_bq(valor, unidad):
    if unidad == 'Bq': return valor
    elif unidad == 'kBq': return valor * 1e3
    elif unidad == 'MBq': return valor * 1e6
    elif unidad == 'GBq': return valor * 1e9
    elif unidad == 'mCi': return valor * 3.7e7
    elif unidad == 'uCi': return valor * 3.7e4
    elif unidad == 'dpm': return valor / 60.0
    return valor

def convertir_desde_bq(bq, unidad):
    if unidad == 'Bq': return bq
    elif unidad == 'kBq': return bq / 1e3
    elif unidad == 'MBq': return bq / 1e6
    elif unidad == 'GBq': return bq / 1e9
    elif unidad == 'mCi': return bq / 3.7e7
    elif unidad == 'uCi': return bq / 3.7e4
    elif unidad == 'dpm': return bq * 60.0
    return bq

# --- PANEL LATERAL ---
st.sidebar.header("1. Parámetros del Generador y Conversión")

tipo_actividad = st.sidebar.selectbox("Actividad conocida:", ["99mTc en equilibrio", "99Mo"])

# Selector completo de unidades de MATLAB
unidades_disponibles = ["mCi", "uCi", "MBq", "GBq", "Bq", "kBq", "dpm"]
unidad_ingreso = st.sidebar.selectbox("Unidad de Actividad (Ingreso):", unidades_disponibles, index=0)
unidad_resultado = st.sidebar.selectbox("Unidad de Resultados y Gráfico:", unidades_disponibles, index=0)

actividad_ingresada = st.sidebar.number_input("Actividad:", value=500.0, min_value=0.0)

# Conversión exacta utilizando Bq como pivote (idéntico a MATLAB)
ain_bq = convertir_a_bq(actividad_ingresada, unidad_ingreso)

if tipo_actividad == '99mTc en equilibrio':
    # Si se ingresa Tc en equilibrio, calculamos el Mo inicial considerando el factor de ramificación (br)
    mo_ini_bq = ain_bq / br
else:
    mo_ini_bq = ain_bq

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
        f_str, h_str, act_medida_ing = partes[0], partes[1], float(partes[2])
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
            "act_medida_ing": act_medida_ing
        })
    except:
        continue

lista_eluciones = sorted(lista_eluciones, key=lambda x: x["datetime"])

# --- CÁLCULO DE TABLA (ECUACIONES DE BATEMAN Y CONVERSIÓN DE UNIDADES) ---
registros_tabla = []
for i, el in enumerate(lista_eluciones):
    t_abs = el["delta_inicio"]
    # Mo decae en función del tiempo absoluto en Bq
    mo_el_bq = mo_ini_bq * np.exp(-lambda_mo * t_abs)
    
    if i == 0:
        t_acumulado = t_abs
        tc_el_bq = br * (lambda_tc / (lambda_tc - lambda_mo)) * mo_ini_bq * (np.exp(-lambda_mo * t_acumulado) - np.exp(-lambda_tc * t_acumulado))
    else:
        t_desde_anterior = (el["datetime"] - lista_eluciones[i-1]["datetime"]).total_seconds() / 3600.0
        dt_ant = lista_eluciones[i-1]["delta_inicio"]
        mo_anterior_bq = mo_ini_bq * np.exp(-lambda_mo * dt_ant)
        tc_el_bq = br * (lambda_tc / (lambda_tc - lambda_mo)) * mo_anterior_bq * (np.exp(-lambda_mo * t_desde_anterior) - np.exp(-lambda_tc * t_desde_anterior))

    # Convertir valores teóricos finales a la unidad seleccionada por el usuario
    mo_val_res = convertir_desde_bq(mo_el_bq, unidad_resultado)
    tc_val_res = convertir_desde_bq(tc_el_bq, unidad_resultado)
    act_medida_res = el["act_medida_ing"]

    dif_porcentual = abs(act_medida_res - tc_val_res) / act_medida_res * 100 if act_medida_res > 0 else 0.0
    
    registros_tabla.append({
        "Elusión N°": i + 1,
        "Fecha/Hora": f"{el['fecha_str']} {el['hora_str']}",
        "Δt Total (h)": round(t_abs, 2),
        f"Mo-99 Teórico ({unidad_resultado})": round(mo_val_res, 4),
        f"Tc-99m Teórico ({unidad_resultado})": round(tc_val_res, 4),
        f"Actividad Medida ({unidad_resultado})": act_medida_res,
        "Dif. (%)": round(dif_porcentual, 2)
    })

df_res = pd.DataFrame(registros_tabla)

# --- VISTA PRINCIPAL ---
st.subheader("📋 Tabla de Eluciones")
if not df_res.empty:
    st.dataframe(df_res, use_container_width=True)
else:
    st.warning("No hay eluciones válidas cargadas.")

st.markdown("---")

st.subheader("📊 Proyección Gráfica")
fig, ax = plt.subplots(figsize=(11, 5))

t_curva = np.arange(0, duracion_grafico + paso_grafico, paso_grafico)
fechas_curva = [dt_inicial + timedelta(hours=float(t)) for t in t_curva]

mo_curva_bq = mo_ini_bq * np.exp(-lambda_mo * t_curva)
mo_curva_res = [convertir_desde_bq(val, unidad_resultado) for val in mo_curva_bq]

tc_curva_bq = np.zeros_like(t_curva)
fechas_el_dt = [el["datetime"] for el in lista_eluciones]

for k, t_val in enumerate(t_curva):
    actual_dt = dt_inicial + timedelta(hours=float(t_val))
    anteriores = [f for f in fechas_el_dt if f <= actual_dt]
    
    if not anteriores:
        tc_curva_bq[k] = br * (lambda_tc / (lambda_tc - lambda_mo)) * mo_ini_bq * (np.exp(-lambda_mo * t_val) - np.exp(-lambda_tc * t_val))
    else:
        ultima_fecha = anteriores[-1]
        t_desde_ultima = (actual_dt - ultima_fecha).total_seconds() / 3600.0
        t_hasta_ultima = (ultima_fecha - dt_inicial).total_seconds() / 3600.0
        mo_ultima_bq = mo_ini_bq * np.exp(-lambda_mo * t_hasta_ultima)
        tc_curva_bq[k] = br * (lambda_tc / (lambda_tc - lambda_mo)) * mo_ultima_bq * (np.exp(-lambda_mo * t_desde_ultima) - np.exp(-lambda_tc * t_desde_ultima))

tc_curva_res = [convertir_desde_bq(val, unidad_resultado) for val in tc_curva_bq]

ax.plot(fechas_curva, mo_curva_res, label=f"99Mo (Padre) [{unidad_resultado}]", color="blue", linewidth=2, linestyle="--")
ax.plot(fechas_curva, tc_curva_res, label=f"99mTc (Hijo - Acumulación) [{unidad_resultado}]", color="green", linewidth=2)

for el in lista_eluciones:
    ax.axvline(el["datetime"], color="red", linestyle=":", alpha=0.7)
    
ax.set_xlabel("Fecha y hora")
ax.set_ylabel(f"Actividad ({unidad_resultado})")
ax.grid(True, linestyle=":", alpha=0.7)
ax.legend(loc="upper right")
plt.xticks(rotation=25)
st.pyplot(fig)

# --- PIE DE PÁGINA (MARCA DE AGUA) ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 14px;'>Una creación de Exequiel Altamiranda, Cinthya Sturz, Lucia Gomez, para la Universidad de San Martin</p>",
    unsafe_allow_html=True
)
