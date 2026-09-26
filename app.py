import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="Radioquímica - Medicina Nuclear", layout="wide")

# --- CONSTANTES DE MATLAB ---
T12Mo = 66.0
T12Tc = 6.0067
FACTOR_TC_MO = 0.9625
lambda_mo = np.log(2) / T12Mo
lambda_tc = np.log(2) / T12Tc

# --- FUNCIONES DE CONVERSIÓN (Base Bq exacta MATLAB) ---
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

def formatear_actividad(bq):
    val = convertir_desde_bq(bq, 'mCi')
    if val == 0: return '0'
    elif abs(val) >= 0.01 and abs(val) < 1e5:
        return f"{val:.8f}".rstrip('0').rstrip('.')
    else:
        return f"{val:.8g}"

# --- MENÚ PRINCIPAL (LATERAL) ---
st.sidebar.markdown("# ☢️ MEDICINA NUCLEAR")
st.sidebar.markdown("Herramientas de radioquímica")
menu = st.sidebar.radio("Menú Principal", ["CALCULADORA", "PLANIFICADOR DE ELUSIONES", "INFORMACIÓN"])

# ==========================================
# 1. MÓDULO CALCULADORA
# ==========================================
if menu == "CALCULADORA":
    st.markdown("# 🧪 RADIOQUÍMICA - Calculadora")
    st.markdown("Herramienta interactiva basada en las operaciones del script de MATLAB.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Parámetros")
        opcion = st.selectbox("¿Qué querés calcular?", [
            '99Mo a partir de 99mTc', 
            '99mTc a partir de 99Mo', 
            '99Mo después de un tiempo', 
            '99mTc después de un tiempo', 
            'Conversión de unidades'
        ])

        actividad = st.number_input("Actividad:", value=500.0, min_value=0.0)
        unidades_disponibles = ['mCi', 'uCi', 'Bq', 'kBq', 'MBq', 'GBq', 'dpm']
        unidad = st.selectbox("Unidad:", unidades_disponibles, index=0)

        # Mostrar campos de tiempo solo si corresponde
        mostrar_tiempo = opcion in ['99Mo después de un tiempo', '99mTc después de un tiempo']
        if mostrar_tiempo:
            tiempo = st.number_input("Tiempo:", value=24.0, min_value=0.0)
            unidad_tiempo = st.selectbox("Unidad de tiempo:", ['horas', 'días'])
        else:
            tiempo = 0.0
            unidad_tiempo = 'horas'

        unidad_resultado = st.selectbox("Unidad resultado:", unidades_disponibles, index=0)

    with col2:
        st.subheader("Datos y Resultado")
        
        # Realizar cálculos según la opción seleccionada de MATLAB
        try:
            A_Bq = convertir_a_bq(actival := actividad, unidad)
            formula_texto = ""
            
            if opcion == '99Mo a partir de 99mTc':
                R_bq = A_Bq / FACTOR_TC_MO
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"A_Mo = A_Tc / {FACTOR_TC_MO}\nA_Mo = {actival} / {FACTOR_TC_MO} = {R:.8g} {unidad_resultado}"
                mensaje = "Actividad de 99Mo obtenida a partir de 99mTc."

            elif opcion == '99mTc a partir de 99Mo':
                R_bq = A_Bq * FACTOR_TC_MO
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"A_Tc = A_Mo x {FACTOR_TC_MO}\nA_Tc = {actival} x {FACTOR_TC_MO} = {R:.8g} {unidad_resultado}"
                mensaje = "Actividad de 99mTc obtenida a partir de 99Mo."

            elif opcion == '99Mo después de un tiempo':
                t_h = tiempo * 24.0 if unidad_tiempo == 'días' else tiempo
                R_bq = A_Bq * np.exp(-lambda_mo * t_h)
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"A_f = A_0 x e^(-lambda x t)\nlambda = ln(2)/66 h\nt = {t_h} h\nA_f = {R:.8g} {unidad_resultado}"
                mensaje = "Decaimiento simple del 99Mo."

            elif opcion == '99mTc después de un tiempo':
                t_h = tiempo * 24.0 if unidad_tiempo == 'días' else tiempo
                R_bq = A_Bq * np.exp(-lambda_tc * t_h)
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"A_f = A_0 x e^(-lambda x t)\nlambda = ln(2)/6.0067 h\nt = {t_h} h\nA_f = {R:.8g} {unidad_resultado}"
                mensaje = "Decaimiento simple del 99mTc."

            elif opcion == 'Conversión de unidades':
                R_bq = A_Bq
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"Conversión mediante Bq como unidad intermedia.\nEntrada: {actival} {unidad} -> Salida: {R:.8g} {unidad_resultado}"
                mensaje = "Conversión realizada correctamente."

            st.metric(label=f"Resultado ({unidad_resultado})", value=f"{R:.8g} {unidad_resultado}")
            st.markdown(f"**Mensaje:** {mensaje}")
            st.markdown("**Fórmula utilizada:**")
            st.code(formula_texto, language="text")

        except Exception as e:
            st.error(f"Error en el cálculo: {e}")

# ==========================================
# 2. MÓDULO PLANIFICADOR DE ELUSIONES
# ==========================================
elif menu == "PLANIFICADOR DE ELUSIONES":
    st.markdown("# 📋 Simulador y Planificador de Eluciones - Generador <sup>99</sup>Mo / <sup>99m</sup>Tc", unsafe_allow_html=True)
    st.markdown("Herramienta interactiva basada en el modelo de Bateman, factor de ramificación y gestión de eluciones sucesivas.")

    st.sidebar.header("1. Parámetros del Generador")
    tipo_actividad = st.sidebar.selectbox("Actividad conocida:", ["99mTc en equilibrio", "99Mo"])
    unidad_ing = st.sidebar.selectbox("Unidad de Actividad:", ["mCi", "uCi", "MBq", "GBq", "Bq", "kBq", "dpm"], index=0)
    actividad_ingresada = st.sidebar.number_input("Actividad:", value=500.0, min_value=0.0)

    ain_bq = convertir_a_bq(actividad_ingresada, unidad_ing)
    if tipo_actividad == '99mTc en equilibrio':
        mo_ini_bq = ain_bq / FACTOR_TC_MO
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

    # Procesamiento de eluciones
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

    # Cálculos con Bateman y Factor Br
    registros_tabla = []
    for i, el in enumerate(lista_eluciones):
        t_abs = el["delta_inicio"]
        mo_el_bq = mo_ini_bq * np.exp(-lambda_mo * t_abs)
        
        if i == 0:
            t_acumulado = t_abs
            tc_el_bq = FACTOR_TC_MO * (lambda_tc / (lambda_tc - lambda_mo)) * mo_ini_bq * (np.exp(-lambda_mo * t_acumulado) - np.exp(-lambda_tc * t_acumulado))
        else:
            t_desde_anterior = (el["datetime"] - lista_eluciones[i-1]["datetime"]).total_seconds() / 3600.0
            dt_ant = lista_eluciones[i-1]["delta_inicio"]
            mo_anterior_bq = mo_ini_bq * np.exp(-lambda_mo * dt_ant)
            tc_el_bq = FACTOR_TC_MO * (lambda_tc / (lambda_tc - lambda_mo)) * mo_anterior_bq * (np.exp(-lambda_mo * t_desde_anterior) - np.exp(-lambda_tc * t_desde_anterior))

        mo_val = convertir_desde_bq(mo_el_bq, unidad_ing)
        tc_val = convertir_desde_bq(tc_el_bq, unidad_ing)
        dif_porcentual = abs(el["act_medida"] - tc_val) / el["act_medida"] * 100 if el["act_medida"] > 0 else 0.0
        
        registros_tabla.append({
            "Elusión N°": i + 1,
            "Fecha/Hora": f"{el['fecha_str']} {el['hora_str']}",
            "Δt Total (h)": round(t_abs, 2),
            f"Mo-99 Teórico ({unidad_ing})": round(mo_val, 2),
            f"Tc-99m Teórico ({unidad_ing})": round(tc_val, 2),
            f"Actividad Medida ({unidad_ing})": el["act_medida"],
            "Dif. (%)": round(dif_porcentual, 2)
        })

    df_res = pd.DataFrame(registros_tabla)

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
    mo_curva_res = [convertir_desde_bq(val, unidad_ing) for val in mo_curva_bq]

    tc_curva_bq = np.zeros_like(t_curva)
    fechas_el_dt = [el["datetime"] for el in lista_eluciones]

    for k, t_val in enumerate(t_curva):
        actual_dt = dt_inicial + timedelta(hours=float(t_val))
        anteriores = [f for f in fechas_el_dt if f <= actual_dt]
        
        if not anteriores:
            tc_curva_bq[k] = FACTOR_TC_MO * (lambda_tc / (lambda_tc - lambda_mo)) * mo_ini_bq * (np.exp(-lambda_mo * t_val) - np.exp(-lambda_tc * t_val))
        else:
            ultima_fecha = anteriores[-1]
            t_desde_ultima = (actual_dt - ultima_fecha).total_seconds() / 3600.0
            t_hasta_ultima = (ultima_fecha - dt_inicial).total_seconds() / 3600.0
            mo_ultima_bq = mo_ini_bq * np.exp(-lambda_mo * t_hasta_ultima)
            tc_curva_bq[k] = FACTOR_TC_MO * (lambda_tc / (lambda_tc - lambda_mo)) * mo_ultima_bq * (np.exp(-lambda_mo * t_desde_ultima) - np.exp(-lambda_tc * t_desde_ultima))

    tc_curva_res = [convertir_desde_bq(val, unidad_ing) for val in tc_curva_bq]

    ax.plot(fechas_curva, mo_curva_res, label=f"99Mo (Padre) [{unidad_ing}]", color="blue", linewidth=2, linestyle="--")
    ax.plot(fechas_curva, tc_curva_res, label=f"99mTc (Hijo - Acumulación) [{unidad_ing}]", color="green", linewidth=2)

    for el in lista_eluciones:
        ax.axvline(el["datetime"], color="red", linestyle=":", alpha=0.7)
        
    ax.set_xlabel("Fecha y hora")
    ax.set_ylabel(f"Actividad ({unidad_ing})")
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend(loc="upper right")
    plt.xticks(rotation=25)
    st.pyplot(fig)

# ==========================================
# 3. MÓDULO INFORMACIÓN
# ==========================================
elif menu == "INFORMACIÓN":
    st.markdown("# ℹ️ Información General")
    st.markdown("""
    Esta aplicación integra las herramientas de radioquímica del script original de MATLAB para la gestión de generadores de **${}^{99}Mo / {}^{99m}Tc$**:
    * **Calculadora:** Realiza conversiones y cálculos directos de decaimiento y relación padre-hijo usando el factor de ramificación ($0.9625$).
    * **Planificador de Eluciones:** Permite modelar el comportamiento del generador mediante el modelo de Bateman a lo largo del tiempo, registrando extracciones sucesivas y generando proyecciones gráficas automáticas.
    """)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 14px;'>Una creación de Exequiel Altamiranda, Cinthya Sturz, Lucia Gomez, para la Universidad de San Martin</p>",
    unsafe_allow_html=True
        )
