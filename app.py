import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Radioquímica - UNSAM", layout="wide")

# --- CONSTANTES ---
T12Mo = 66.0
T12Tc = 6.0067
lambda_mo = np.log(2) / T12Mo
lambda_tc = np.log(2) / T12Tc
br = 0.9625  # Factor de ramificación

# Función auxiliar de conversión a mCi
def convertir_a_mci(val, un):
    if un == "mCi":
        return val
    elif un == "uCi":
        return val / 1000.0
    elif un == "MBq":
        return val / 37.0
    elif un == "GBq":
        return val * 1000.0 / 37.0
    elif un == "Bq":
        return val / 3.7e7
    return val

def convertir_desde_mci(val_mci, un_destino):
    if un_destino == "mCi":
        return val_mci, "mCi"
    elif un_destino == "uCi":
        return val_mci * 1000.0, "uCi"
    elif un_destino == "MBq":
        return val_mci * 37.0, "MBq"
    elif un_destino == "GBq":
        return val_mci * 37.0 / 1000.0, "GBq"
    elif un_destino == "Bq":
        return val_mci * 3.7e7, "Bq"
    return val_mci, un_destino

# --- TÍTULO PRINCIPAL ---
st.markdown("# ☢️ RADIOQUÍMICA", unsafe_allow_html=True)
st.markdown("Herramienta de cálculo de actividad radioquímica - Universidad de San Martín")
st.markdown("---")

# --- MENÚ PRINCIPAL MEDIANTE PESTAÑAS (TABS) ---
tab_calc, tab_planificador, tab_info = st.tabs(["🧮 CALCULADORA", "📅 PLANIFICADOR DE ELUSIONES", "ℹ️ INFORMACIÓN"])

# ==========================================
# PESTAÑA 1: CALCULADORA INDIVIDUAL
# ==========================================
with tab_calc:
    st.subheader("Módulo de Cálculos Puntuales")
    
    opcion_calc = st.selectbox("¿Qué querés calcular?", [
        "99Mo a partir de 99mTc (en equilibrio)",
        "99mTc a partir de 99Mo",
        "99Mo después de un tiempo (Decaimiento simple)",
        "99mTc después de un tiempo (Decaimiento simple)",
        "Conversión de unidades"
    ])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Datos de entrada")
        val_ingresado = st.number_input("Actividad:", value=500.0, min_value=0.0, key="val_calc")
        unidad_ingresada = st.selectbox("Unidad:", ["mCi", "uCi", "MBq", "GBq", "Bq"], key="un_calc")
        
        tiempo_dec = 0.0
        if "después de un tiempo" in opcion_calc:
            tiempo_dec = st.number_input("Tiempo transcurrido:", value=24.0, min_value=0.0, key="t_dec")
            unidad_tiempo = st.selectbox("Unidad de tiempo:", ["horas", "días"], key="un_t")
            if unidad_tiempo == "días":
                tiempo_dec *= 24.0  # Pasar a horas
                
        unidad_resultado = st.selectbox("Unidad resultado:", ["mCi", "uCi", "MBq", "GBq", "Bq"], key="un_res")

    with col2:
        st.markdown("### Resultado y Fórmula")
        val_mci = convertir_a_mci(val_ingresado, unidad_ingresada)
        
        if st.button("🧮 Calcular Operación", key="btn_operacion"):
            if opcion_calc == "99Mo a partir de 99mTc (en equilibrio)":
                res_mci = val_mci / br
                formula_txt = f"A(Mo) = A(Tc) / Br = {val_ingresado} / {br}"
            elif opcion_calc == "99mTc a partir de 99Mo":
                res_mci = val_mci * br
                formula_txt = f"A(Tc) = A(Mo) * Br = {val_ingresado} * {br}"
            elif opcion_calc == "99Mo después de un tiempo (Decaimiento simple)":
                res_mci = val_mci * np.exp(-lambda_mo * tiempo_dec)
                formula_txt = f"A(t) = A0 * exp(-lambda_mo * t) [t = {tiempo_dec} h]"
            elif opcion_calc == "99mTc después de un tiempo (Decaimiento simple)":
                res_mci = val_mci * np.exp(-lambda_tc * tiempo_dec)
                formula_txt = f"A(t) = A0 * exp(-lambda_tc * t) [t = {tiempo_dec} h]"
            else:  # Conversión
                res_mci = val_mci
                formula_txt = "Conversión directa de unidades."
                
            res_final, un_final = convertir_desde_mci(res_mci, unidad_resultado)
            
            st.success(f"**Resultado:** {res_final:.5f} {un_final}")
            st.info(f"**Fórmula utilizada:**\n\n{formula_txt}")

# ==========================================
# PESTAÑA 2: PLANIFICADOR DE ELUSIONES
# ==========================================
with tab_planificador:
    st.subheader("Simulador de Eluciones Sucesivas y Curvas de Bateman")
    
    with st.sidebar:
        st.header("Parámetros del Generador")
        tipo_actividad = st.selectbox("Actividad base conocida:", ["99mTc en equilibrio", "99Mo"])
        unidad_gen = st.selectbox("Unidad:", ["mCi", "MBq", "GBq"], index=0)
        actividad_gen = st.number_input("Valor de Actividad:", value=450.0, min_value=0.0)

        fecha_ini = st.date_input("Fecha inicial (Calibración)", value=datetime(2016, 4, 25).date())
        hora_ini_str = st.text_input("Hora inicial (HH:MM)", value="08:00")

        duracion_grafico = st.number_input("Duración gráfico (horas):", value=144.0, min_value=1.0)
        paso_grafico = st.number_input("Paso gráfico (horas):", value=0.25, min_value=0.01)

        st.header("Registro de Eluciones")
        datos_por_defecto = """25/04/2016, 08:00, 450
26/04/2016, 08:00, 300
27/04/2016, 08:00, 200"""
        texto_eluciones = st.text_area("Formato: DD/MM/AAAA, HH:MM, Actividad", value=datos_por_defecto, height=150)
        boton_calcular_gen = st.button("🧮 Simular Generador")

    # Procesamiento del generador
    ain_gen = convertir_a_mci(actividad_gen, unidad_gen)
    factor_eq = br * (lambda_tc / (lambda_tc - lambda_mo))
    
    if tipo_actividad == '99mTc en equilibrio':
        actividad_inicial_mo = ain_gen / factor_eq
    else:
        actividad_inicial_mo = ain_gen

    try:
        h_i, m_i = map(int, hora_ini_str.split(":"))
        dt_inicial = datetime.combine(fecha_ini, datetime.min.time()) + timedelta(hours=h_i, minutes=m_i)
    except:
        dt_inicial = datetime.combine(fecha_ini, datetime.min.time()) + timedelta(hours=8)

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

    # Tabla de eluciones
    registros_tabla = []
    for i, el in enumerate(lista_eluciones):
        t_abs = el["delta_inicio"]
        mo_el = actividad_inicial_mo * np.exp(-lambda_mo * t_abs)
        
        if i == 0:
            t_acumulado = t_abs
            tc_el = br * (lambda_tc / (lambda_tc - lambda_mo)) * actividad_inicial_mo * (np.exp(-lambda_mo * t_acumulado) - np.exp(-lambda_tc * t_acumulado))
        else:
            t_desde_anterior = (el["datetime"] - lista_eluciones[i-1]["datetime"]).total_seconds() / 3600.0
            mo_anterior = actividad_inicial_mo * np.exp(-lambda_mo * lista_eluciones[i-1]["delta_inicio"])
            tc_el = br * (lambda_tc / (lambda_tc - lambda_mo)) * mo_anterior * (np.exp(-lambda_mo * t_desde_anterior) - np.exp(-lambda_tc * t_desde_anterior))

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

    st.subheader("📋 Tabla de Eluciones Sucesivas")
    if not df_res.empty:
        st.dataframe(df_res, use_container_width=True)
    else:
        st.warning("No hay eluciones válidas cargadas.")

    st.markdown("---")
    st.subheader("📊 Proyección Gráfica del Generador")
    
    fig, ax = plt.subplots(figsize=(11, 5))
    t_curva = np.arange(0, duracion_grafico + paso_grafico, paso_grafico)
    fechas_curva = [dt_inicial + timedelta(hours=float(t)) for t in t_curva]
    mo_curva = actividad_inicial_mo * np.exp(-lambda_mo * t_curva)
    tc_curva = np.zeros_like(t_curva)
    fechas_el_dt = [el["datetime"] for el in lista_eluciones]

    for k, t_val in enumerate(t_curva):
        actual_dt = dt_inicial + timedelta(hours=float(t_val))
        anteriores = [f for f in fechas_el_dt if f <= actual_dt]
        
        if not anteriores:
            tc_curva[k] = br * (lambda_tc / (lambda_tc - lambda_mo)) * actividad_inicial_mo * (np.exp(-lambda_mo * t_val) - np.exp(-lambda_tc * t_val))
        else:
            ultima_fecha = anteriores[-1]
            t_desde_ultima = (actual_dt - ultima_fecha).total_seconds() / 3600.0
            t_hasta_ultima = (ultima_fecha - dt_inicial).total_seconds() / 3600.0
            mo_ultima = actividad_inicial_mo * np.exp(-lambda_mo * t_hasta_ultima)
            tc_curva[k] = br * (lambda_tc / (lambda_tc - lambda_mo)) * mo_ultima * (np.exp(-lambda_mo * t_desde_ultima) - np.exp(-lambda_tc * t_desde_ultima))

    ax.plot(fechas_curva, mo_curva, label="99Mo (Padre)", color="blue", linewidth=2, linestyle="--")
    ax.plot(fechas_curva, tc_curva, label="99mTc (Hijo - Acumulación)", color="green", linewidth=2)

    for el in lista_eluciones:
        ax.axvline(el["datetime"], color="red", linestyle=":", alpha=0.7)
        
    ax.set_xlabel("Fecha y hora")
    ax.set_ylabel(f"Actividad ({unidad_gen})")
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend(loc="upper right")
    plt.xticks(rotation=25)
    st.pyplot(fig)

# ==========================================
# PESTAÑA 3: INFORMACIÓN
# ==========================================
with tab_info:
    st.subheader("Acerca de la herramienta")
    st.markdown("""
    Esta aplicación interactiva fue desarrollada para resolver y comprobar los problemas de la guía de trabajos prácticos de Radioquímica.
    
    * **Modelos físicos aplicados:** Ley de decaimiento exponencial simple y Ecuación de Bateman con factor de ramificación ($Br = 0.9625$).
    * **Institución:** Universidad de San Martín (UNSAM).
    * **Autores:** Exequiel Altamiranda, Cinthya Sturz y Lucia Gomez.
    """)

# --- PIE DE PÁGINA GENERAL ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 14px;'>Una creación de Exequiel Altamiranda, Cinthya Sturz, Lucia Gomez, para la Universidad de San Martin</p>",
    unsafe_allow_html=True
)
