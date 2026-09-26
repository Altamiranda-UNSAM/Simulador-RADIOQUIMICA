import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from scipy.optimize import minimize_scalar

st.set_page_config(page_title="Radioquímica - UNSAM", layout="wide")

# --- CONSTANTES ---
T12Mo = 66.0
T12Tc = 6.0067
FACTOR_TC_MO = 0.9625
lambdaMo = np.log(2) / T12Mo
lambdaTc = np.log(2) / T12Tc

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

def formatear_actividad(bq, unidad_res="mCi"):
    val = convertir_desde_bq(bq, unidad_res)
    if val == 0: return "0"
    elif abs(val) >= 0.01 and abs(val) < 1e5:
        return f"{val:.6f}".rstrip('0').rstrip('.')
    else:
        return f"{val:.6g}"

# --- TÍTULO PRINCIPAL ---
st.markdown("# ☢️ RADIOQUÍMICA", unsafe_allow_html=True)
st.markdown("Herramienta de cálculo de actividad radioquímica - Universidad de San Martín")
st.markdown("---")

# --- MENÚ PRINCIPAL (PESTAÑAS) ---
tab_calc, tab_planificador = st.tabs(["🧮 CALCULADORA", "📅 PLANIFICADOR DE ELUSIONES"])

# ==========================================
# PESTAÑA 1: CALCULADORA INDIVIDUAL
# ==========================================
with tab_calc:
    st.subheader("Módulo de Cálculos Puntuales")
    
    opcion_calc = st.selectbox("¿Qué querés calcular?", [
        "99Mo a partir de 99mTc",
        "99mTc a partir de 99Mo",
        "99Mo después de un tiempo",
        "99mTc después de un tiempo",
        "Conversion de unidades"
    ], key="op_calc")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Datos de entrada")
        actividad_val = st.number_input("Actividad:", value=500.0, min_value=0.0, key="val_c")
        unidad_val = st.selectbox("Unidad:", ['mCi', 'uCi', 'Bq', 'kBq', 'MBq', 'GBq', 'dpm'], key="un_c")
        
        tiempo_val = 0.0
        if "después de un tiempo" in opcion_calc:
            tiempo_val = st.number_input("Tiempo transcurrido:", value=24.0, min_value=0.0, key="t_c")
            unidad_t = st.selectbox("Unidad de tiempo:", ['horas', 'dias'], key="unt_c")
            if unidad_t == 'dias':
                tiempo_val *= 24.0  
                
        unidad_res = st.selectbox("Unidad resultado:", ['mCi', 'uCi', 'Bq', 'kBq', 'MBq', 'GBq', 'dpm'], key="unr_c")

    with col2:
        st.markdown("### Resultado y Fórmula")
        if st.button("CALCULAR", key="btn_calc_ind"):
            a_bq = convertir_a_bq(actividad_val, unidad_val)
            
            if opcion_calc == "99Mo a partir de 99mTc":
                r_bq = a_bq / FACTOR_TC_MO
                formula_txt = f"A_Mo = A_Tc / {FACTOR_TC_MO}\n({actividad_val} / {FACTOR_TC_MO})"
            elif opcion_calc == "99mTc a partir de 99Mo":
                r_bq = a_bq * FACTOR_TC_MO
                formula_txt = f"A_Tc = A_Mo * {FACTOR_TC_MO}\n({actividad_val} * {FACTOR_TC_MO})"
            elif opcion_calc == "99Mo después de un tiempo":
                r_bq = a_bq * np.exp(-lambdaMo * tiempo_val)
                formula_txt = f"A_f = A_0 * exp(-lambda * t)\nt = {tiempo_val} h"
            elif opcion_calc == "99mTc después de un tiempo":
                r_bq = a_bq * np.exp(-lambdaTc * tiempo_val)
                formula_txt = f"A_f = A_0 * exp(-lambda * t)\nt = {tiempo_val} h"
            else:
                r_bq = a_bq
                formula_txt = "Conversión directa mediante Bq como unidad intermedia."
                
            resultado_final = convertir_desde_bq(r_bq, unidad_res)
            st.success(f"**Resultado:** {resultado_final:.6g} {unidad_res}")
            st.code(formula_txt, language="text")

# ==========================================
# PESTAÑA 2: PLANIFICADOR DE ELUSIONES
# ==========================================
with tab_planificador:
    st.subheader("Simulador de Eluciones Sucesivas y Curvas de Bateman")

    if 'elusiones' not in st.session_state:
        dt_base = datetime(2016, 4, 25, 8, 0)
        a_ini = convertir_a_bq(450.0, 'mCi')
        st.session_state.elusiones = [
            [datetime.timestamp(dt_base), a_ini, a_ini * FACTOR_TC_MO, a_ini * FACTOR_TC_MO, 0]
        ]

    with st.sidebar:
        st.header("Parámetros del Generador")
        tipo_inicial = st.selectbox("Actividad conocida:", ['99mTc', '99Mo'], key="tp_ini")
        act_ini_val = st.number_input("Actividad:", value=450.0, min_value=0.0, key="ac_ini")
        unidad_gen_in = st.selectbox("Unidad de entrada:", ['mCi', 'uCi', 'Bq', 'kBq', 'MBq', 'GBq', 'dpm'], key="uni_ini")
        unidad_gen_res = st.selectbox("Unidad resultado:", ['mCi', 'uCi', 'Bq', 'kBq', 'MBq', 'GBq', 'dpm'], key="un_g_res")

        fecha_ini = st.date_input("Fecha inicial (Calibración)", value=datetime(2016, 4, 25).date())
        hora_ini_str = st.text_input("Hora inicial (HH:MM)", value="08:00")

        if st.button("🔄 Reiniciar con Datos Iniciales"):
            try:
                hh, mm = map(int, hora_ini_str.split(":"))
                dt_i = datetime.combine(fecha_ini, datetime.min.time()) + timedelta(hours=hh, minutes=mm)
                a_b = convertir_a_bq(act_ini_val, unidad_gen_in)
                if tipo_inicial == '99mTc':
                    tc_b = a_b
                    mo_b = tc_b / FACTOR_TC_MO
                else:
                    mo_b = a_b
                    tc_b = mo_b * FACTOR_TC_MO
                st.session_state.elusiones = [[datetime.timestamp(dt_i), mo_b, tc_b, tc_b, 0]]
                st.success("¡Generador reiniciado!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        st.header("Planificación por Objetivo")
        obj_val = st.number_input("Tc deseado:", value=300.0, min_value=0.0, key="obj_v")
        un_obj = st.selectbox("Unidad objetivo:", ['mCi', 'uCi', 'Bq', 'kBq', 'MBq', 'GBq', 'dpm'], key="un_obj")
        
        if st.button("🎯 Calcular Tiempo Objetivo"):
            if not st.session_state.elusiones:
                st.error("Agregue primero una elusión inicial.")
            else:
                a_obj_bq = convertir_a_bq(obj_val, un_obj)
                ultima = st.session_state.elusiones[-1]
                dt_ult = datetime.fromtimestamp(ultima[0])
                mo_ult = ultima[1]
                
                def fun(t):
                    if t < 0: return 1e9
                    return mo_ult * np.exp(-lambdaMo * t) * FACTOR_TC_MO * (1 - np.exp(-lambdaTc * t)) - a_obj_bq

                res = minimize_scalar(lambda t: abs(fun(t)), bounds=(0, 5000), method='bounded')
                if res.success and abs(fun(res.x)) < a_obj_bq * 0.01:
                    t_enc = res.x
                    nueva_fecha = dt_ult + timedelta(hours=t_enc)
                    mo_nuevo = mo_ult * np.exp(-lambdaMo * t_enc)
                    tc_nuevo = mo_nuevo * FACTOR_TC_MO * (1 - np.exp(-lambdaTc * t_enc))
                    
                    st.success(f"¡Fecha óptima hallada en {t_enc:.2f} hs!")
                    if st.button("➕ Agregar esta fecha al historial"):
                        st.session_state.elusiones.append([datetime.timestamp(nueva_fecha), mo_nuevo, tc_nuevo, a_obj_bq, 1])
                        st.rerun()
                else:
                    st.error("No se pudo alcanzar la actividad solicitada.")

        st.header("🔍 Consultar Actividad Específica")
        fecha_cons = st.date_input("Fecha de consulta:", value=datetime.today().date(), key="f_cons")
        hora_cons_str = st.text_input("Hora de consulta (HH:MM):", value="08:00", key="h_cons")

        if st.button("🔎 Consultar Fecha"):
            if not st.session_state.elusiones:
                st.error("Agregue primero una elusión inicial.")
            else:
                try:
                    hc, mc = map(int, hora_cons_str.split(":"))
                    dt_consulta = datetime.combine(fecha_cons, datetime.min.time()) + timedelta(hours=hc, minutes=mc)
                    ts_cons = datetime.timestamp(dt_consulta)
                    
                    # Lógica MATLAB para hallar actividad en fecha arbitraria (hacia adelante o atrás)
                    elus_ord = sorted(st.session_state.elusiones, key=lambda x: x[0])
                    idx_ant = [i for i, e in enumerate(elus_ord) if e[0] <= ts_cons]
                    
                    if idx_ant:
                        e_ref = elus_ord[idx_ant[-1]]
                        dt_ref = datetime.fromtimestamp(e_ref[0])
                        dt_h = (dt_consulta - dt_ref).total_seconds() / 3600.0
                        mo_c = e_ref[1] * np.exp(-lambdaMo * dt_h)
                        if abs(dt_h) < 1e-6:
                            tc_c = e_ref[2]
                            detalle_txt = f"Coincide con la elusión N° {idx_ant[-1] + 1}."
                        else:
                            tc_c = mo_c * FACTOR_TC_MO * (1 - np.exp(-lambdaTc * dt_h))
                            detalle_txt = f"Calculado a {dt_h:.2f} h de la elusión N° {idx_ant[-1] + 1}."
                    else:
                        # Si es anterior a la primera elusión
                        e_ref = elus_ord[0]
                        dt_ref = datetime.fromtimestamp(e_ref[0])
                        dt_h = (dt_consulta - dt_ref).total_seconds() / 3600.0  # Negativo
                        mo_c = e_ref[1] * np.exp(-lambdaMo * dt_h)
                        tc_c = mo_c * FACTOR_TC_MO
                        detalle_txt = f"Fecha anterior a la primera elusión (reconstruido en equilibrio a {abs(dt_h):.2f} h antes)."

                    st.session_state.resultado_consulta = {
                        "ts": ts_cons,
                        "mo": mo_c,
                        "tc": tc_c,
                        "detalle": detalle_txt,
                        "str_fecha": dt_consulta.strftime("%d/%m/%Y %H:%M")
                    }
                except Exception as e:
                    st.error(f"Error en consulta: {e}")

        if st.button("🗑️ Borrar Todo"):
            st.session_state.elusiones = []
            if 'resultado_consulta' in st.session_state:
                del st.session_state.resultado_consulta
            st.rerun()

    # Procesamiento y visualización principal
    elusiones = sorted(st.session_state.elusiones, key=lambda x: x[0])
    
    if len(elusiones) > 1:
        for kk in range(1, len(elusiones)):
            if elusiones[kk][4] == 1:
                ant = elusiones[kk-1]
                dt_h = (elusiones[kk][0] - ant[0]) / 3600.0
                if dt_h <= 0: dt_h = 1e-9
                mo_n = ant[1] * np.exp(-lambdaMo * dt_h)
                tc_n = mo_n * FACTOR_TC_MO * (1 - np.exp(-lambdaTc * dt_h))
                elusiones[kk][1] = mo_n
                elusiones[kk][2] = tc_n

    # Mostrar tarjeta de resultado de consulta si existe
    if 'resultado_consulta' in st.session_state:
        rc = st.session_state.resultado_consulta
        st.info(f"### 🔎 Resultado de Consulta ({rc['str_fecha']})\n"
                f"- **Mo-99:** {formatear_actividad(rc['mo'], unidad_gen_res)} {unidad_gen_res}\n"
                f"- **Tc-99m:** {formatear_actividad(rc['tc'], unidad_gen_res)} {unidad_gen_res}\n"
                f"- *{rc['detalle']}*")
        if st.button("➕ Agregar esta consulta como Elusión al Historial"):
            st.session_state.elusiones.append([rc['ts'], rc['mo'], rc['tc'], rc['tc'], 0])
            del st.session_state.resultado_consulta
            st.rerun()

    registros_tabla = []
    for idx, el in enumerate(elusiones):
        dt_f = datetime.fromtimestamp(el[0])
        registros_tabla.append({
            "Elusión N°": idx + 1,
            "Fecha/Hora": dt_f.strftime("%d/%m/%Y %H:%M"),
            f"Mo-99 ({unidad_gen_res})": float(formatear_actividad(el[1], unidad_gen_res)),
            f"Tc-99m Teórico ({unidad_gen_res})": float(formatear_actividad(el[2], unidad_gen_res))
        })

    df_res = pd.DataFrame(registros_tabla)

    st.subheader("📋 Tabla de Eluciones Sucesivas")
    if not df_res.empty:
        st.dataframe(df_res, use_container_width=True)
        
        col_del1, col_del2 = st.columns([1, 2])
        with col_del1:
            fila_a_borrar = st.number_input("N° a eliminar:", min_value=1, max_value=len(elusiones), step=1, key="del_idx")
        with col_del2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("❌ Eliminar Elusión Seleccionada"):
                if 1 <= fila_a_borrar <= len(elusiones):
                    elusiones.pop(fila_a_borrar - 1)
                    st.session_state.elusiones = elusiones
                    st.rerun()
    else:
        st.warning("No hay eluciones válidas cargadas.")

    st.markdown("---")
    st.subheader("📊 Proyección Gráfica")
    
    if elusiones:
        fig, ax = plt.subplots(figsize=(11, 5))
        
        f1 = datetime.fromtimestamp(elusiones[0][0])
        f2 = datetime.fromtimestamp(elusiones[-1][0])
        inicio_graf = f1 - timedelta(hours=12)
        fin_graf = f2 + timedelta(hours=36)
        
        t_pts = np.linspace(0, (fin_graf - inicio_graf).total_seconds()/3600.0, 300)
        fechas_pts = [inicio_graf + timedelta(hours=float(tp)) for tp in t_pts]
        
        mo_arr, tc_arr = [], []
        mo_base = elusiones[0][1]
        t_ini_ts = elusiones[0][0]
        
        for f_pt in fechas_pts:
            t_h = (datetime.timestamp(f_pt) - t_ini_ts) / 3600.0
            if t_h < 0:
                mo_val = mo_base * np.exp(-lambdaMo * t_h)
                tc_val = mo_val * FACTOR_TC_MO
            else:
                act_el = elusiones[0]
                for el in elusiones:
                    if el[0] <= datetime.timestamp(f_pt):
                        act_el = el
                dt_desde = (datetime.timestamp(f_pt) - act_el[0]) / 3600.0
                mo_val = act_el[1] * np.exp(-lambdaMo * dt_desde)
                if dt_desde == 0:
                    tc_val = act_el[2]
                else:
                    tc_val = mo_val * FACTOR_TC_MO * (1 - np.exp(-lambdaTc * dt_desde))
            
            mo_arr.append(convertir_desde_bq(mo_val, unidad_gen_res))
            tc_arr.append(convertir_desde_bq(tc_val, unidad_gen_res))

        ax.plot(fechas_pts, mo_arr, label=f"99Mo ({unidad_gen_res})", color="blue", linewidth=2, linestyle="--")
        ax.plot(fechas_pts, tc_arr, label=f"99mTc ({unidad_gen_res})", color="green", linewidth=2)

        for el in elusiones:
            ax.axvline(datetime.fromtimestamp(el[0]), color="red", linestyle=":", alpha=0.7)
            
        ax.set_xlabel("Fecha y hora")
        ax.set_ylabel(f"Actividad ({unidad_gen_res})")
        ax.grid(True, linestyle=":", alpha=0.7)
        ax.legend(loc="upper right")
        plt.xticks(rotation=25)
        st.pyplot(fig)
    else:
        st.info("Agregue eluciones para renderizar la curva.")

# --- PIE DE PÁGINA CON MARCA DE AGUA ORIGINAL ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 14px;'>Una creación de Exequiel Altamiranda, Cinthya Sturz, Lucia Gomez, para la Universidad de San Martin</p>",
    unsafe_allow_html=True
        )
    
