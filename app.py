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

# --- INICIALIZAR ESTADO DE SESIÓN PARA EL PLANIFICADOR ---
if 'elusiones' not in st.session_state:
    st.session_state.elusiones = []
if 'elusion_pendiente' not in st.session_state:
    st.session_state.elusion_pendiente = None

# --- MENÚ PRINCIPAL (LATERAL) ---
st.sidebar.markdown("# ☢️ MEDICINA NUCLEAR")
st.sidebar.markdown("Herramientas de radioquímica")
menu = st.sidebar.radio("Menú Principal", ["CALCULADORA", "PLANIFICADOR DE ELUSIONES", "INFORMACIÓN"])

# ==========================================
# 1. MÓDULO CALCULADORA
# ==========================================
if menu == "CALCULADORA":
    st.markdown("# 🧪 RADIOQUÍMICA - Calculadora")
    st.markdown("Operaciones basadas en el script de MATLAB.")

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
        try:
            A_Bq = convertir_a_bq(actividad, unidad)
            formula_texto = ""
            
            if opcion == '99Mo a partir de 99mTc':
                R_bq = A_Bq / FACTOR_TC_MO
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"A_Mo = A_Tc / {FACTOR_TC_MO}\nA_Mo = {actividad} / {FACTOR_TC_MO} = {R:.8g} {unidad_resultado}"
                mensaje = "Actividad de 99Mo obtenida a partir de 99mTc."

            elif opcion == '99mTc a partir de 99Mo':
                R_bq = A_Bq * FACTOR_TC_MO
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"A_Tc = A_Mo x {FACTOR_TC_MO}\nA_Tc = {actividad} x {FACTOR_TC_MO} = {R:.8g} {unidad_resultado}"
                mensaje = "Actividad de 99mTc obtenida a partir de 99Mo."

            elif opcion == '99Mo después de un tiempo':
                t_h = tiempo * 24.0 if unidad_tiempo == 'días' else tiempo
                R_bq = A_Bq * np.exp(-lambda_mo * t_h)
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"A_f = A_0 x e^(-lambda*t)\nlambda = ln(2)/66 h\nt = {t_h} h\nA_f = {R:.8g} {unidad_resultado}"
                mensaje = "Decaimiento simple del 99Mo."

            elif opcion == '99mTc después de un tiempo':
                t_h = tiempo * 24.0 if unidad_tiempo == 'días' else tiempo
                R_bq = A_Bq * np.exp(-lambda_tc * t_h)
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"A_f = A_0 x e^(-lambda*t)\nlambda = ln(2)/6.0067 h\nt = {t_h} h\nA_f = {R:.8g} {unidad_resultado}"
                mensaje = "Decaimiento simple del 99mTc."

            elif opcion == 'Conversión de unidades':
                R_bq = A_Bq
                R = convertir_desde_bq(R_bq, unidad_resultado)
                formula_texto = f"Conversión mediante Bq como unidad intermedia.\nEntrada: {actividad} {unidad} -> Salida: {R:.8g} {unidad_resultado}"
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
    st.markdown("# 📋 Planificador de Eluciones - Generador <sup>99</sup>Mo / <sup>99m</sup>Tc", unsafe_allow_html=True)
    st.markdown("Gestión de eluciones y proyecciones.")

    col_izq, col_der = st.columns([1, 1.2])

    with col_izq:
        st.subheader("Datos Iniciales / Elusión Base")
        tipo_inicial = st.selectbox("Actividad conocida:", ['99mTc', '99Mo'], key="t_ini")
        act_inicial = st.number_input("Actividad:", value=600.0, min_value=0.0, key="a_ini")
        un_inicial = st.selectbox("Unidad:", ['mCi', 'uCi', 'Bq', 'kBq', 'MBq', 'GBq', 'dpm'], key="u_ini")
        f_inicial = st.date_input("Fecha:", value=datetime.today(), key="f_ini")
        h_inicial = st.text_input("Hora (HH:MM):", value="08:00", key="h_ini")

        if st.button("AGREGAR ELUSIÓN INICIAL", use_container_width=True):
            try:
                hh, mm = map(int, h_inicial.split(":"))
                dt_f = datetime.combine(f_inicial, datetime.min.time()) + timedelta(hours=hh, minutes=mm)
                A_bq = convertir_a_bq(act_inicial, un_inicial)
                if A_bq <= 0:
                    st.error("La actividad debe ser mayor que cero.")
                else:
                    if tipo_inicial == '99mTc':
                        Tc_bq = A_bq
                        Mo_bq = Tc_bq / FACTOR_TC_MO
                    else:
                        Mo_bq = A_bq
                        Tc_bq = Mo_bq * FACTOR_TC_MO
                    
                    st.session_state.elusiones = [[dt_f, Mo_bq, Tc_bq, Tc_bq, 0]]
                    st.session_state.elusion_pendiente = None
                    st.success("¡Elusión inicial agregada correctamente!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al procesar fecha/hora: {e}")

        st.markdown("---")
        st.subheader("Planificar por Tc Deseado")
        objetivo = st.number_input("Tc deseado:", value=300.0, min_value=0.0, key="obj_val")
        un_objetivo = st.selectbox("Unidad objetivo:", ['mCi', 'uCi', 'Bq', 'kBq', 'MBq', 'GBq', 'dpm'], key="obj_un")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("CONSULTAR ACTIVIDAD (OBJETIVO)", use_container_width=True):
                if not st.session_state.elusiones:
                    st.warning("Primero agregue la elusión inicial.")
                else:
                    try:
                        A_obj_bq = convertir_a_bq(objetivo, un_objetivo)
                        ultima = st.session_state.elusiones[-1]
                        fecha_ult = ultima[0]
                        Mo_ult = ultima[1]
                        
                        fun = lambda t: Mo_ult * np.exp(-lambda_mo * t) * FACTOR_TC_MO * (1 - np.exp(-lambda_tc * t)) - A_obj_bq
                        tt = np.linspace(0, 5000, 50001)
                        yy = np.array([fun(t) for t in tt])
                        idx_max = np.argmax(yy)
                        k = None
                        for ii in range(0, max(0, idx_max)):
                            if yy[ii] <= 0 and yy[ii+1] >= 0:
                                k = ii
                                break
                        
                        encontrado = False
                        if k is not None:
                            lo = tt[k]; hi = tt[k+1]
                            for _ in range(80):
                                mid = (lo + hi) / 2
                                if fun(lo) * fun(mid) <= 0:
                                    hi = mid
                                else:
                                    lo = mid
                            t_opt = (lo + hi) / 2
                            if t_opt > 1e-8:
                                nueva_fecha = fecha_ult + timedelta(hours=t_opt)
                                Mo_nuevo = Mo_ult * np.exp(-lambda_mo * t_opt)
                                Tc_nuevo = Mo_nuevo * FACTOR_TC_MO * (1 - np.exp(-lambda_tc * t_opt))
                                st.session_state.elusion_pendiente = [nueva_fecha, Mo_nuevo, Tc_nuevo, A_obj_bq, 1]
                                st.info(f"Fecha calculada (adelante): {nueva_fecha.strftime('%d/%m/%Y %H:%M')} (t = {t_opt:.2f} h)")
                                encontrado = True

                        if not encontrado:
                            Aeq_actual = Mo_ult * FACTOR_TC_MO
                            if A_obj_bq > Aeq_actual:
                                t_back = np.log(A_obj_bq / Aeq_actual) / lambda_mo
                                fecha_anterior = fecha_ult - timedelta(hours=t_back)
                                Mo_anterior = Mo_ult * np.exp(lambda_mo * t_back)
                                st.session_state.elusion_pendiente = [fecha_anterior, Mo_anterior, A_obj_bq, A_obj_bq, 1]
                                st.info(f"Fecha calculada hacia atrás: {fecha_anterior.strftime('%d/%m/%Y %H:%M')} (t = -{t_back:.2f} h)")
                            else:
                                st.warning("La actividad solicitada no puede alcanzarse desde la última elusión.")
                    except Exception as e:
                        st.error(f"Error en el cálculo: {e}")

        with col_b2:
            if st.button("AGREGAR COMO ELUSIÓN", use_container_width=True):
                if st.session_state.elusion_pendiente is None:
                    st.warning("Primero consulte/calcule la actividad objetivo.")
                else:
                    nueva = st.session_state.elusion_pendiente
                    st.session_state.elusiones.append(nueva)
                    st.session_state.elusiones = sorted(st.session_state.elusiones, key=lambda x: x[0])
                    st.session_state.elusion_pendiente = None
                    st.success("¡Elusión agregada al historial!")
                    st.rerun()

        st.markdown("---")
        st.subheader("Consultar Actividad en Fecha Específica")
        f_cons = st.date_input("Fecha consulta:", value=datetime.today(), key="f_c")
        h_cons = st.text_input("Hora consulta (HH:MM):", value="08:00", key="h_c")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("CONSULTAR FECHA", use_container_width=True):
                if not st.session_state.elusiones:
                    st.warning("Agregue una elusión inicial primero.")
                else:
                    try:
                        hh, mm = map(int, h_cons.split(":"))
                        dt_c = datetime.combine(f_cons, datetime.min.time()) + timedelta(hours=hh, minutes=mm)
                        anteriores = [e for e in st.session_state.elusiones if e[0] <= dt_c]
                        if anteriores:
                            e = anteriores[-1]
                            dt_h = (dt_c - e[0]).total_seconds() / 3600.0
                            mo_c = e[1] * np.exp(-lambda_mo * dt_h)
                            tc_c = e[3] if abs(dt_h) < 1e-10 else mo_c * FACTOR_TC_MO * (1 - np.exp(-lambda_tc * dt_h))
                            st.success(f"99Mo: {formatear_actividad(mo_c)} mCi | 99mTc: {formatear_actividad(tc_c)} mCi")
                        else:
                            e = st.session_state.elusiones[0]
                            dt_h = (dt_c - e[0]).total_seconds() / 3600.0
                            mo_c = e[1] * np.exp(-lambda_mo * dt_h)
                            tc_c = mo_c * FACTOR_TC_MO
                            st.success(f"Fecha anterior. 99Mo: {formatear_actividad(mo_c)} mCi | 99mTc: {formatear_actividad(tc_c)} mCi")
                    except Exception as e:
                        st.error(f"Error: {e}")
        with col_c2:
            if st.button("AGREGAR CONSULTA", use_container_width=True):
                try:
                    hh, mm = map(int, h_cons.split(":"))
                    dt_c = datetime.combine(f_cons, datetime.min.time()) + timedelta(hours=hh, minutes=mm)
                    anteriores = [e for e in st.session_state.elusiones if e[0] <= dt_c]
                    if anteriores:
                        e = anteriores[-1]
                        dt_h = (dt_c - e[0]).total_seconds() / 3600.0
                        mo_c = e[1] * np.exp(-lambda_mo * dt_h)
                        tc_c = e[3] if abs(dt_h) < 1e-10 else mo_c * FACTOR_TC_MO * (1 - np.exp(-lambda_tc * dt_h))
                        st.session_state.elusiones.append([dt_c, mo_c, tc_c, tc_c, 0])
                        st.session_state.elusiones = sorted(st.session_state.elusiones, key=lambda x: x[0])
                        st.success("¡Consulta agregada como elusión!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.button("BORRAR TODAS LAS ELUSIONES", type="primary", use_container_width=True):
            st.session_state.elusiones = []
            st.session_state.elusion_pendiente = None
            st.rerun()

    with col_der:
        st.subheader("Historial de Elusiones y Curva")
        if st.session_state.elusiones:
            data_tabla = []
            for idx, el in enumerate(st.session_state.elusiones):
                data_tabla.append({
                    "Elusión": f"Elusión {idx+1}",
                    "Fecha/Hora": el[0].strftime("%d/%m/%Y %H:%M"),
                    "99Mo disp. (mCi)": formatear_actividad(el[1]),
                    "99mTc disp. (mCi)": formatear_actividad(el[2])
                })
            st.dataframe(pd.DataFrame(data_tabla), use_container_width=True)

            fig, ax = plt.subplots(figsize=(10, 4.5))
            f1 = st.session_state.elusiones[0][0]
            f2 = st.session_state.elusiones[-1][0]
            if f2 <= f1: f2 = f1 + timedelta(hours=24)
            
            inicio_g = f1 - timedelta(hours=12)
            fin_g = f2 + timedelta(hours=24)
            
            duracion = (fin_g - inicio_g).total_seconds() / 3600.0
            tt = np.linspace(0, duracion, 300)
            fechas_g = [inicio_g + timedelta(hours=float(t)) for t in tt]
            
            mo_g = []
            tc_g = []
            for dt_val in fechas_g:
                anteriores = [e for e in st.session_state.elusiones if e[0] <= dt_val]
                if anteriores:
                    e = anteriores[-1]
                    dt_h = (dt_val - e[0]).total_seconds() / 3600.0
                    m_val = e[1] * np.exp(-lambda_mo * dt_h)
                    t_val = m_val * FACTOR_TC_MO * (1 - np.exp(-lambda_tc * dt_h)) if dt_h > 0 else e[2]
                else:
                    e = st.session_state.elusiones[0]
                    dt_h = (dt_val - e[0]).total_seconds() / 3600.0
                    m_val = e[1] * np.exp(-lambda_mo * dt_h)
                    t_val = m_val * FACTOR_TC_MO
                mo_g.append(convertir_desde_bq(m_val, 'mCi'))
                tc_g.append(convertir_desde_bq(t_val, 'mCi'))

            ax.plot(fechas_g, mo_g, label="99Mo", color="blue", linewidth=2, linestyle="--")
            ax.plot(fechas_g, tc_g, label="99mTc", color="green", linewidth=2)
            
            for el in st.session_state.elusiones:
                ax.axvline(el[0], color="red", linestyle=":", alpha=0.6)

            ax.set_title("Curva de actividad de 99Mo y 99mTc")
            ax.set_xlabel("Fecha y hora")
            ax.set_ylabel("Actividad (mCi)")
            ax.grid(True, linestyle=":", alpha=0.7)
            ax.legend(loc="best")
            plt.xticks(rotation=20)
            st.pyplot(fig)
        else:
            st.info("Agregue una elusión inicial para ver el historial y la curva.")

# ==========================================
# 3. MÓDULO INFORMACIÓN
# ==========================================
elif menu == "INFORMACIÓN":
    st.markdown("# ℹ️ Información General")
    st.markdown("""
    Herramientas de radioquímica adaptadas fielmente del script original de MATLAB:
    * **Calculadora:** Operaciones puntuales de decaimiento y conversiones.
    * **Planificador de Eluciones:** Permite calcular hacia adelante y hacia atrás en el tiempo según la actividad de Tecnecio deseada, manteniendo el historial completo y generando curvas de decaimiento exactas.
    """)

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 14px;'>Una creación de Exequiel Altamiranda, Cinthya Sturz, Lucia Gomez, para la Universidad de San Martin</p>",
    unsafe_allow_html=True
)
