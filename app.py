import streamlit as st
import pandas as pd

st.set_page_config(page_title="Reporte de Notas de Crédito", layout="wide")

# Función para formatear números al estilo argentino (1.000.000,00)
def formato_arg(numero):
    if pd.isna(numero) or numero == 0:
        return ""
    # Formatea estilo US (1,000,000.00) y luego intercambia comas y puntos
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- 🔒 SISTEMA DE LOGIN ---
PASSWORD_CORRECTA = "admin123" 

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso al Sistema de Reportes")
    password_ingresada = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if password_ingresada == PASSWORD_CORRECTA:
            st.session_state.autenticado = True
            st.rerun() 
        else:
            st.error("Contraseña incorrecta.")
    st.stop() 

# --- 📊 APLICACIÓN PRINCIPAL ---
st.title("📊 Generador de Reportes Trimestrales (NC)")

tab_carga, tab_comparativa, tab_acumulado = st.tabs([
    "Carga de Archivos", "Comparativa Histórica", "Acumulado Anual"
])

with tab_carga:
    st.header("1. Carga de Archivos")
    col1, col2, col3 = st.columns(3)
    with col1: file_fcp = st.file_uploader("Facturación", type=['xlsx'])
    with col2: file_nc = st.file_uploader("Notas de Crédito", type=['xlsx'])
    with col3: file_historico = st.file_uploader("Histórico Base (NC2026 T1 v2)", type=['xlsx'])
    
    if st.button("Procesar y Generar Reporte"):
        if file_fcp and file_nc and file_historico:
            try:
                # Leer archivos saltando encabezados (header=2)
                df_ventas = pd.read_excel(file_fcp, header=2)
                df_nc = pd.read_excel(file_nc, header=2)
                
                df_ventas.columns = df_ventas.columns.str.lower().str.strip()
                df_nc.columns = df_nc.columns.str.lower().str.strip()

                col_comprobante = 'número' 
                col_monto = 'importe total origen'
                col_fecha = 'fecha'

                # Antiduplicados
                if col_comprobante in df_ventas.columns:
                    df_ventas = df_ventas.drop_duplicates(subset=[col_comprobante], keep='first')
                if col_comprobante in df_nc.columns:
                    df_nc = df_nc.drop_duplicates(subset=[col_comprobante], keep='first')

                # Calcular Totales y Porcentajes
                df_ventas['mes'] = pd.to_datetime(df_ventas[col_fecha]).dt.month
                df_nc['mes'] = pd.to_datetime(df_nc[col_fecha]).dt.month

                v_mes = df_ventas.groupby('mes')[col_monto].sum().reset_index()
                nc_mes = df_nc.groupby('mes')[col_monto].sum().reset_index()

                calculo = pd.merge(v_mes, nc_mes, on='mes', how='left', suffixes=('_venta', '_nc'))
                calculo[f'{col_monto}_nc'] = calculo[f'{col_monto}_nc'].fillna(0)
                calculo['2026_porcentaje'] = (calculo[f'{col_monto}_nc'] / calculo[f'{col_monto}_venta'])

                # Armar el cuadro principal
                meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
                df_final = pd.DataFrame({"Meses": meses, "mes": range(1, 13)})
                df_final = pd.merge(df_final, calculo, on='mes', how='left')

                # Renombrar columnas para la vista
                df_final = df_final.rename(columns={
                    f'{col_monto}_venta': 'Total Facturación ($)',
                    f'{col_monto}_nc': 'Total NC ($)',
                    '2026_porcentaje': '% NC (2026)'
                })

                # Guardar datos puros en sesión para usarlos en otras solapas
                st.session_state['datos_2026'] = df_final.copy()
                st.session_state['file_historico'] = file_historico.getvalue() # Guardamos el histórico en memoria

                # Aplicar formato visual
                df_visual = df_final.copy()
                df_visual['Total Facturación ($)'] = df_visual['Total Facturación ($)'].apply(formato_arg)
                df_visual['Total NC ($)'] = df_visual['Total NC ($)'].apply(formato_arg)
                df_visual['% NC (2026)'] = df_visual['% NC (2026)'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "")

                st.success("Cálculos procesados correctamente.")
                st.dataframe(df_visual.drop(columns=['mes']))

            except Exception as e:
                st.error(f"Error procesando: {e}")
        else:
            st.warning("Sube los 3 archivos.")

# --- LÓGICA DE SOLAPAS 2 y 3 ---
with tab_comparativa:
    st.header("Comparativa Histórica (% NC sobre Venta)")
    if 'datos_2026' in st.session_state and 'file_historico' in st.session_state:
        try:
            # Leemos el histórico desde la memoria de la sesión
            xls_hist = pd.ExcelFile(st.session_state['file_historico'])
            df_comp = pd.DataFrame({"Mes": st.session_state['datos_2026']['Meses']})
            
            # Extraer 2024 y 2025 asumiendo que están en las solapas homónimas 
            # y que la columna se llama '% NC' (Ajusta esto si se llama diferente en tu Excel histórico)
            if '2024' in xls_hist.sheet_names:
                d24 = pd.read_excel(xls_hist, sheet_name='2024')
                df_comp['2024'] = d24.iloc[:12, 1] if len(d24.columns) > 1 else None # Toma la 2da columna de los primeros 12 meses
            if '2025' in xls_hist.sheet_names:
                d25 = pd.read_excel(xls_hist, sheet_name='2025')
                df_comp['2025'] = d25.iloc[:12, 1] if len(d25.columns) > 1 else None

            # Agregar 2026 formateado
            df_comp['2026'] = st.session_state['datos_2026']['% NC (2026)'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "")
            
            st.dataframe(df_comp)
        except Exception as e:
            st.error(f"Error leyendo el histórico: {e}")
    else:
        st.info("Procesa los archivos en la primera solapa para ver la comparativa.")

with tab_acumulado:
    st.header("Acumulado Anual 2026")
    if 'datos_2026' in st.session_state:
        datos = st.session_state['datos_2026']
        tot_fac = datos['Total Facturación ($)'].sum()
        tot_nc = datos['Total NC ($)'].sum()
        pct_acumulado = (tot_nc / tot_fac) if tot_fac > 0 else 0
        
        st.metric("Total Facturado (Acumulado)", f"$ {formato_arg(tot_fac)}")
        st.metric("Total NC (Acumulado)", f"$ {formato_arg(tot_nc)}")
        st.metric("% NC Acumulado", f"{pct_acumulado*100:.2f}%")
        
        if st.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()
    else:
        st.info("Procesa los archivos en la primera solapa para ver el acumulado.")
