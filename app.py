import io
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
    font-size: 1.25rem;
    font-weight: 800;
    color: #333;
}
@keyframes latido-rojo {
    0% { box-shadow: 0 0 10px rgba(255, 75, 75, 0.4); }
    50% { box-shadow: 0 0 25px rgba(255, 75, 75, 0.9); }
    100% { box-shadow: 0 0 10px rgba(255, 75, 75, 0.4); }
}
@keyframes latido-verde {
    0% { box-shadow: 0 0 10px rgba(40, 167, 69, 0.4); }
    50% { box-shadow: 0 0 25px rgba(40, 167, 69, 0.9); }
    100% { box-shadow: 0 0 10px rgba(40, 167, 69, 0.4); }
}
.kpi-card {
    background-color: white;
    border-radius: 30px;
    padding: 15px 25px;
    margin: 10px 0;
    text-align: center;
    font-family: sans-serif;
    transition: transform 0.2s ease;
}
.kpi-card:hover { transform: scale(1.02); }
.kpi-rojo { border: 4px solid #ff4b4b; color: #ff4b4b; }
.kpi-rojo:hover { animation: latido-rojo 1.5s infinite; }
.kpi-verde { border: 4px solid #28a745; color: #28a745; }
.kpi-verde:hover { animation: latido-verde 1.5s infinite; }
.kpi-titulo { font-size: 14px; font-weight: bold; color: #555; margin-bottom: 5px; }
.kpi-valor { font-size: 24px; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

def tarjeta_kpi(titulo, valor, aumento=True):
    clase = "kpi-rojo" if aumento else "kpi-verde"
    icono = "🔴 ⬆" if aumento else "🟢 ⬇"
    return f"""
    <div class="kpi-card {clase}">
        <div class="kpi-titulo">{titulo}</div>
        <div class="kpi-valor">{icono} {valor}</div>
    </div>
    """

# Funciones de formato argentino
def formato_arg(numero):
    if pd.isna(numero) or numero == 0: return "0,00"
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formato_pct(numero):
    if pd.isna(numero) or numero == 0: return "0,00%"
    return f"{numero*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

# --- 🔒 SISTEMA DE LOGIN CON ROLES ---
PASS_ADMIN = "admin123"
PASS_VISOR = "visor123"

if "rol" not in st.session_state:
    st.session_state.rol = None

if not st.session_state.rol:
    st.title("🔒 Acceso al Sistema de Reportes")
    password_ingresada = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if password_ingresada == PASS_ADMIN:
            st.session_state.rol = "admin"
            st.rerun()
        elif password_ingresada == PASS_VISOR:
            st.session_state.rol = "visor"
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.stop() 

# --- 📊 APLICACIÓN PRINCIPAL ---
st.title("📊 Generador de Reportes Trimestrales (NC)")

if st.button("Cerrar Sesión"):
    st.session_state.rol = None
    st.rerun()

tab_analisis, tab_top10, tab_motivo, tab_error = st.tabs([
    "Análisis", "Top 10 Clientes", "Motivos", "Error de Carga"
])

# --- SOLAPA 1: ANÁLISIS ---
with tab_analisis:
    if st.session_state.rol == "admin":
        with st.expander("📂 Zona de Carga de Archivos", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1: file_fcp = st.file_uploader("Facturación 2026", type=['xlsx'])
            with col2: file_nc = st.file_uploader("Notas de Crédito 2026", type=['xlsx'])
            with col3: file_historico = st.file_uploader("Histórico 2025", type=['xlsx'])
            
            if st.button("Procesar y Generar Reporte"):
                if file_fcp and file_nc and file_historico:
                    try:
                        df_ventas = pd.read_excel(file_fcp, header=2)
                        df_nc = pd.read_excel(file_nc, header=2)
                        df_hist = pd.read_excel(file_historico, header=2)
                        
                        for df in [df_ventas, df_nc, df_hist]:
                            df.columns = (df.columns.str.lower().str.strip().str.replace('ú', 'u').str.replace('í', 'i')
                                          .str.replace('ó', 'o').str.replace('á', 'a').str.replace('é', 'e'))
                        
                        df_ventas = df_ventas.drop_duplicates(subset=['numero'], keep='first')
                        df_nc = df_nc.drop_duplicates(subset=['numero'], keep='first')
                        df_hist = df_hist.drop_duplicates(subset=['numero'], keep='first')

                        df_hist['fecha'] = pd.to_datetime(df_hist['fecha'], errors='coerce')
                        df_hist = df_hist[df_hist['fecha'] >= '2025-01-01']
                        
                        if 'tipo' in df_hist.columns:
                            df_hist_nc = df_hist[df_hist['tipo'].astype(str).str.contains('NC', case=False, na=False)]
                            df_hist_v = df_hist[~df_hist['tipo'].astype(str).str.contains('NC|ND', case=False, na=False)]
                        else:
                            df_hist_nc, df_hist_v = df_hist, pd.DataFrame(columns=df_hist.columns)

                        st.session_state['d_nc26'], st.session_state['d_v26'] = df_nc, df_ventas
                        st.session_state['d_nc25'], st.session_state['d_v25'] = df_hist_nc, df_hist_v
                        
                    except Exception as e:
                        st.error(f"Error procesando: {e}")
                else:
                    st.warning("Faltan archivos por subir.")
    else:
        st.info("Modo Visor: Esperando conexión con base de datos para mostrar información histórica.")

    # --- MINI SOLAPAS ---
    if 'd_nc26' in st.session_state:
        st.markdown("---")
        
        def calc_mensual(df_v, df_nc):
            df_v['mes'] = pd.to_datetime(df_v['fecha']).dt.month
            df_nc['mes'] = pd.to_datetime(df_nc['fecha']).dt.month
            v_mes = df_v.groupby('mes')['importe total origen'].sum().reset_index()
            nc_mes = df_nc.groupby('mes')['importe total origen'].sum().reset_index()
            nc_cant = df_nc.groupby('mes')['numero'].count().reset_index()
            
            calc = pd.DataFrame({'mes': range(1, 13)})
            calc = pd.merge(calc, v_mes, on='mes', how='left').rename(columns={'importe total origen': 'ventas'})
            calc = pd.merge(calc, nc_mes, on='mes', how='left').rename(columns={'importe total origen': 'nc'})
            calc = pd.merge(calc, nc_cant, on='mes', how='left').rename(columns={'numero': 'cantidad'})
            calc.fillna(0, inplace=True)
            return calc

        d26 = calc_mensual(st.session_state['d_v26'], st.session_state['d_nc26'])
        d25 = calc_mensual(st.session_state['d_v25'], st.session_state['d_nc25'])
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        mini1, mini2, mini3 = st.tabs(["2026", "Cantidades y Días Hábiles", "Comparativa % sobre Venta"])

        with mini1:
            tot_nc_2026 = d26['nc'].sum()
            tot_cant_2026 = d26['cantidad'].sum()
            
            col_k1, col_k2 = st.columns(2)
            with col_k1: st.markdown(tarjeta_kpi("Total NC Emitidas (2026)", int(tot_cant_2026), aumento=True), unsafe_allow_html=True)
            with col_k2: st.markdown(tarjeta_kpi("Monto Total NC (2026)", f"$ {formato_arg(tot_nc_2026)}", aumento=True), unsafe_allow_html=True)

            df_m1 = pd.DataFrame({'Mes': meses, 'Cantidad': d26['cantidad'], 'Monto NC/ND': d26['nc'], 'Total Venta': d26['ventas']})
            df_m1['% s/Total NC'] = np.where(tot_nc_2026>0, df_m1['Monto NC/ND'] / tot_nc_2026, 0)
            df_m1['% s/Total Venta'] = np.where(df_m1['Total Venta']>0, df_m1['Monto NC/ND'] / df_m1['Total Venta'], 0)
            
            # Diccionario de formatos visuales para la tabla
            formatos_m1 = {
                'Monto NC/ND': lambda x: f"$ {formato_arg(x)}",
                'Total Venta': lambda x: f"$ {formato_arg(x)}",
                '% s/Total NC': formato_pct,
                '% s/Total Venta': formato_pct
            }
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Resumen NC**")
                # Aplicamos el degradado primero, y luego formateamos el texto a argentino
                st.dataframe(df_m1[['Mes', 'Cantidad', 'Monto NC/ND', '% s/Total NC']].style
                             .background_gradient(subset=['% s/Total NC'], cmap='Reds')
                             .format(formatos_m1))
            with c2:
                st.write("**Relación Venta vs NC**")
                st.dataframe(df_m1[['Mes', 'Total Venta', 'Monto NC/ND', '% s/Total Venta']].style
                             .background_gradient(subset=['% s/Total Venta'], cmap='Reds')
                             .format(formatos_m1))

        with mini2:
            st.write("### Días Hábiles (Editable)")
            if 'df_dias' not in st.session_state:
                st.session_state['df_dias'] = pd.DataFrame({'Mes': meses, 'Días Hábiles': [20]*12})
            
            dias_editados = st.data_editor(st.session_state['df_dias'], hide_index=True)
            
            df_m2 = pd.DataFrame({'Mes': meses, '2025': d25['cantidad'], '2026': d26['cantidad']})
            df_m2['Días Hábiles'] = dias_editados['Días Hábiles']
            df_m2['NC por Día (2026)'] = np.where(df_m2['Días Hábiles']>0, df_m2['2026'] / df_m2['Días Hábiles'], 0)
            
            variacion_cant = d26['cantidad'].sum() - d25['cantidad'].sum()
            st.markdown(tarjeta_kpi("Variación de Cantidad (2026 vs 2025)", f"{variacion_cant:+.0f} NC", aumento=(variacion_cant>0)), unsafe_allow_html=True)
            
            st.dataframe(df_m2.style.format({'NC por Día (2026)': lambda x: f"{x:,.2f}".replace('.', ',')}))

        with mini3:
            st.write("### Comparativa % NC sobre Total de Venta")
            df_m3 = pd.DataFrame({'Mes': meses})
            df_m3['2025 (%)'] = np.where(d25['ventas']>0, d25['nc']/d25['ventas'], 0)
            df_m3['2026 (%)'] = np.where(d26['ventas']>0, d26['nc']/d26['ventas'], 0)
            df_m3['Variación'] = df_m3['2026 (%)'] - df_m3['2025 (%)']
            
            def dar_color(val):
                if isinstance(val, (int, float)): # Solo evalúa si es un número real
                    if val > 0: return 'color: red; font-weight: bold;'
                    elif val < 0: return 'color: green; font-weight: bold;'
                return ''
                
            formatos_m3 = {
                '2025 (%)': formato_pct,
                '2026 (%)': formato_pct,
                'Variación': formato_pct
            }
            
            # Pintamos los números reales y luego los convertimos en texto formateado
            st.dataframe(df_m3.style.map(dar_color, subset=['Variación']).format(formatos_m3), use_container_width=True)

# Lógica preexistente validada (reducida visualmente)
if 'd_nc26' in st.session_state:
    with tab_top10: st.write("✅ Datos listos para gráficos Top 10")
    with tab_motivo: st.write("✅ Datos listos para Motivos")
    with tab_error: st.write("✅ Datos listos para Errores de Carga")
