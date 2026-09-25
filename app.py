import streamlit as st

# 1. Borrar todos los archivos sucios de app que se hayan creado mal
Remove-Item "*app*.py*" -ErrorAction SilentlyContinue

# 2. Crear el archivo app.py correctamente limpio
Set-Content -Path "app.py" -Value 'import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.title("🧪 Simulador de Eluciones - Generador $^{99}\text{Mo} / ^{99m}\text{Tc}$")
st.markdown("Herramienta interactiva para calcular ecuaciones de Bateman, comparar con valores reales y graficar curvas.")

st.sidebar.header("1. Parámetros Iniciales")
radiofarmaco = st.sidebar.selectbox("Seleccioná el Radiofármaco:", ["Molibdeno-99 / Tecnecio-99m (99Mo/99mTc)"])

lambda_mo = np.log(2) / 66.0
lambda_tc = np.log(2) / 6.0

fecha_ini = st.sidebar.date_input("Fecha inicial (Base)", value=datetime(2016, 4, 25).date())
hora_ini_str = st.sidebar.text_input("Hora inicial (HH:MM)", value="08:00")
actividad_inicial = st.sidebar.number_input("Actividad de referencia inicial (mCi)", value=887.0)

try:
    h_i, m_i = map(int, hora_ini_str.split(":"))
    dt_inicial = datetime.combine(fecha_ini, datetime.min.time()) + timedelta(hours=h_i, minutes=m_i)
except:
    st.sidebar.error("Formato de hora inicial inválido. Usá HH:MM")
    dt_inicial = datetime.combine(fecha_ini, datetime.min.time()) + timedelta(hours=8)

st.sidebar.header("2. Ingreso de Eluciones a Evaluar")
datos_por_defecto = """25/04/2016, 08:00, 887
25/04/2016, 13:30, 397
26/04/2016, 08:00, 530
26/04/2016, 13:55, 307
27/04/2016, 08:00, 415
27/04/2016, 14:00, 230
28/04/2016, 08:00, 342
28/04/2016, 14:00, 174
29/04/2016, 08:20, 255
29/04/2016, 14:00, 139"""

texto_eluciones = st.sidebar.text_area("Formato: Fecha (DD/MM/AAAA), Hora (HH:MM), Actividad Real (mCi)", value=datos_por_defecto, height=200)

registros = []
for linea in texto_eluciones.strip().split("\n"):
    try:
        partes = [p.strip() for p in linea.split(",")]
        f_str, h_str, act_real = partes[0], partes[1], float(partes[2])
        f_date = datetime.strptime(f_str, "%d/%m/%Y").date()
        hh, mm = map(int, h_str.split(":"))
        dt_elusion = datetime.combine(f_date, datetime.min.time()) + timedelta(hours=hh, minutes=mm)
        delta_t = (dt_elusion - dt_inicial).total_seconds() / 3600.0
        if delta_t < 0: continue
        mo_t = actividad_inicial * np.exp(-lambda_mo * delta_t)
        tc_t = (lambda_tc / (lambda_tc - lambda_mo)) * actividad_inicial * (np.exp(-lambda_mo * delta_t) - np.exp(-lambda_tc * delta_t))
        dif_porcentual = abs(act_real - tc_t) / act_real * 100 if act_real > 0 else 0.0
        registros.append({"Fecha": f_str, "Hora": h_str, "Δt (h)": round(delta_t, 2), "Mo-99 Teórico (mCi)": round(mo_t, 2), "Tc-99m Teórico (mCi)": round(tc_t, 2), "Actividad Real (mCi)": act_real, "Dif. Porcentual (%)": round(dif_porcentual, 2)})
    except: continue

df_res = pd.DataFrame(registros)
st.subheader("📊 Resultados y Comparación con Valores Reales")
if not df_res.empty:
    st.dataframe(df_res)
    st.subheader("Curva Teórica vs Puntos Reales")
    fig, ax = plt.subplots(figsize=(10, 5))
    t_max = df_res["Δt (h)"].max() * 1.1 if df_res["Δt (h)"].max() > 0 else 24
    t_curva = np.linspace(0, t_max, 200)
    mo_curva = actividad_inicial * np.exp(-lambda_mo * t_curva)
    tc_curva = (lambda_tc / (lambda_tc - lambda_mo)) * actividad_inicial * (np.exp(-lambda_mo * t_curva) - np.exp(-lambda_tc * t_curva))
    ax.plot(t_curva, mo_curva, label="Decaimiento 99Mo", color="blue", linestyle="--")
    ax.plot(t_curva, tc_curva, label="Acumulación Teórica 99mTc (Bateman)", color="green")
    ax.scatter(df_res["Δt (h)"].astype(float), df_res["Actividad Real (mCi)"].astype(float), color="red", label="Valores Reales", zorder=5)
    ax.set_xlabel("Tiempo transcurrido (horas)")
    ax.set_ylabel("Actividad (mCi)")
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend()
    st.pyplot(fig)
    st.success("✅ ¡Cálculos actualizados!")
else:
    st.warning("Revisá el formato de los datos.")' -Encoding utf8

# 3. Subir los cambios limpios a GitHub
git add .
git commit -m "Corregir nombre de archivo y limpiar codigo para Streamlit Cloud"
git push origin main
